import os
import sys
import unittest
import json
import tempfile
import time
from unittest.mock import patch, MagicMock
from io import BytesIO

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
DASHBOARD_DIR = os.path.dirname(TEST_DIR)
ROOT_DIR = os.path.dirname(DASHBOARD_DIR)
sys.path.insert(0, DASHBOARD_DIR)
sys.path.insert(0, os.path.join(ROOT_DIR, "scripts"))

import serve as board_serve


class DummyRequest:
    def makefile(self, *args, **kwargs):
        return BytesIO(b"")


class TestBoardServe(unittest.TestCase):
    def setUp(self):
        with board_serve._search_lock:
            board_serve._search_running = False
            board_serve._search_log = []
            board_serve._search_result = None

    def tearDown(self):
        with board_serve._search_lock:
            board_serve._search_running = False
            board_serve._search_log = []
            board_serve._search_result = None

    def make_handler(self, method="GET", path="/", body=b""):
        request = DummyRequest()
        client_address = ("127.0.0.1", 12345)
        server = MagicMock()

        handler = board_serve.Handler.__new__(board_serve.Handler)
        handler.request = request
        handler.client_address = client_address
        handler.server = server
        handler.command = method
        handler.path = path
        handler.rfile = BytesIO(body)
        handler.wfile = BytesIO()
        handler.headers = {"Content-Length": str(len(body))}

        handler.sent_status = None
        handler.sent_body = None
        handler.sent_ctype = None

        def mock_send(code, data, ctype="application/json"):
            handler.sent_status = code
            handler.sent_body = data
            handler.sent_ctype = ctype
            return None

        handler._send = mock_send
        return handler

    def test_handle_search_status_idle(self):
        handler = self.make_handler("GET", "/api/search-status")
        handler._handle_search_status()

        self.assertEqual(handler.sent_status, 200)
        data = json.loads(handler.sent_body)
        self.assertFalse(data["running"])
        self.assertEqual(data["log"], [])
        self.assertIsNone(data["result"])

    @patch("search_apify_jobs.run_search")
    @patch("serve.rebuild")
    def test_handle_search_start(self, mock_rebuild, mock_run_search):
        mock_run_search.return_value = {"added": 2, "skipped": 1, "total": 3, "error": None}

        handler = self.make_handler("POST", "/api/search", b"{}")
        handler._handle_search()

        self.assertEqual(handler.sent_status, 200)
        data = json.loads(handler.sent_body)
        self.assertTrue(data["ok"])
        self.assertEqual(data["message"], "Search started")

        time.sleep(0.1)

        mock_run_search.assert_called_once()
        mock_rebuild.assert_called_once()

        self.assertFalse(board_serve._search_running)
        self.assertEqual(board_serve._search_result, {"added": 2, "skipped": 1, "total": 3, "error": None})

    def test_handle_search_already_running(self):
        with board_serve._search_lock:
            board_serve._search_running = True

        handler = self.make_handler("POST", "/api/search", b"{}")
        handler._handle_search()

        self.assertEqual(handler.sent_status, 409)
        data = json.loads(handler.sent_body)
        self.assertFalse(data["ok"])
        self.assertIn("already running", data["error"])

    @patch("search_apify_jobs.run_search")
    def test_handle_search_fatal_error(self, mock_run_search):
        mock_run_search.side_effect = RuntimeError("Apify API connection failed")

        handler = self.make_handler("POST", "/api/search", b"{}")
        handler._handle_search()

        self.assertEqual(handler.sent_status, 200)

        time.sleep(0.1)

        self.assertFalse(board_serve._search_running)
        self.assertIsNotNone(board_serve._search_result)
        self.assertIn("Apify API connection failed", board_serve._search_result["error"])
        self.assertTrue(any("Fatal error" in log for log in board_serve._search_log))

    def test_env_loading(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            env_file = os.path.join(tmp_dir, ".env")
            with open(env_file, "w", encoding="utf-8") as f:
                f.write("# comment\nTEST_SERVE_VAR=hello_world\n")

            with patch.dict(os.environ, {}, clear=False):
                if os.path.exists(env_file):
                    with open(env_file, encoding="utf-8") as ef:
                        for line in ef:
                            line = line.strip()
                            if line and not line.startswith("#") and "=" in line:
                                k, v = line.split("=", 1)
                                os.environ.setdefault(k.strip(), v.strip())
                self.assertEqual(os.environ.get("TEST_SERVE_VAR"), "hello_world")


if __name__ == "__main__":
    unittest.main()
