import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import tempfile
import json

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
sys.path.insert(0, os.path.join(ROOT, "dashboard"))

import search_apify_jobs as apify


class TestSearchApifyJobs(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    # --- Config loading tests ---

    def test_load_connectors(self):
        yaml_content = """
# Connectors config
linkedin:
  - keywords: "python backend"
    location: "Remote"
    datePosted: "pastMonth"
    limitPerSource: 10
    scrapeCompany: true
  - keywords: "fullstack react"
    location: "Worldwide"
"""
        config_dir = os.path.join(self.temp_dir.name, "config")
        os.makedirs(config_dir, exist_ok=True)
        with open(os.path.join(config_dir, "connectors.yaml"), "w", encoding="utf-8") as f:
            f.write(yaml_content)

        with patch.object(apify, "ROOT", self.temp_dir.name):
            searches = apify.load_connectors()

        self.assertEqual(len(searches), 2)
        self.assertEqual(searches[0]["keywords"], "python backend")
        self.assertEqual(searches[0]["location"], "Remote")
        self.assertEqual(searches[0]["datePosted"], "pastMonth")
        self.assertEqual(searches[0]["limitPerSource"], 10)
        self.assertTrue(searches[0]["scrapeCompany"])
        self.assertEqual(searches[1]["keywords"], "fullstack react")

    def test_load_connectors_missing_file(self):
        with patch.object(apify, "ROOT", self.temp_dir.name):
            searches = apify.load_connectors()
            self.assertEqual(searches, {})

    def test_load_enabled_connector(self):
        yaml_content = """
apify-actor-1:
  enabled: false
  actor_id: "user1/actor-one"

apify-actor-2:
  enabled: true
  actor_id: "user2/actor-two"
"""
        config_dir = os.path.join(self.temp_dir.name, "config")
        os.makedirs(config_dir, exist_ok=True)
        with open(os.path.join(config_dir, "connectors.yaml"), "w", encoding="utf-8") as f:
            f.write(yaml_content)

        with patch.object(apify, "ROOT", self.temp_dir.name):
            actor_id = apify.load_enabled_connector()
            self.assertEqual(actor_id, "user2~actor-two")

    def test_load_enabled_connector_missing_file_fallback(self):
        with patch.object(apify, "ROOT", self.temp_dir.name):
            actor_id = apify.load_enabled_connector()
            self.assertEqual(actor_id, "curious_coder~linkedin-jobs-scraper")

    # --- URL extraction tests ---

    def test_extract_job_url_keys(self):
        candidate_keys = [
            ("link", "https://linkedin.com/jobs/view/101"),
            ("url", "https://linkedin.com/jobs/view/102"),
            ("jobUrl", "https://linkedin.com/jobs/view/103"),
            ("applyUrl", "https://linkedin.com/jobs/view/104"),
            ("linkedinUrl", "https://linkedin.com/jobs/view/105"),
            ("job_url", "https://linkedin.com/jobs/view/106"),
            ("jobPostingUrl", "https://linkedin.com/jobs/view/107"),
            ("externalApplyLink", "https://linkedin.com/jobs/view/108"),
            ("externalUrl", "https://linkedin.com/jobs/view/109"),
            ("linkUrl", "https://linkedin.com/jobs/view/110"),
        ]
        for key, val in candidate_keys:
            item = {key: val}
            extracted = apify.extract_job_url(item)
            self.assertEqual(extracted, val)

    def test_extract_job_url_job_id_fallback(self):
        self.assertEqual(apify.extract_job_url({"jobId": 1234567}), "https://www.linkedin.com/jobs/view/1234567")
        self.assertEqual(apify.extract_job_url({"id": "9876543"}), "https://www.linkedin.com/jobs/view/9876543")

    def test_extract_job_url_invalid(self):
        self.assertEqual(apify.extract_job_url(None), "")
        self.assertEqual(apify.extract_job_url({}), "")
        self.assertEqual(apify.extract_job_url({"url": "invalid-url"}), "")

    # --- API calls tests ---

    def test_start_run_missing_token_raises(self):
        with patch.object(apify, "TOKEN", None):
            with self.assertRaises(RuntimeError) as ctx:
                apify.start_run({"keywords": "test"})
            self.assertIn("APIFY_TOKEN environment variable is not set", str(ctx.exception))

    @patch("urllib.request.urlopen")
    def test_start_run_success(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "data": {"id": "run123", "defaultDatasetId": "dataset456"}
        }).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        with patch.object(apify, "TOKEN", "dummy_token"):
            run_id, dataset_id = apify.start_run({"keywords": "python"}, actor_id="my_actor")
            self.assertEqual(run_id, "run123")
            self.assertEqual(dataset_id, "dataset456")

    @patch("urllib.request.urlopen")
    @patch("time.sleep", return_value=None)
    def test_wait_for_run_succeeded(self, mock_sleep, mock_urlopen):
        resp1 = MagicMock()
        resp1.read.return_value = json.dumps({"data": {"status": "RUNNING"}}).encode("utf-8")
        resp1.__enter__.return_value = resp1

        resp2 = MagicMock()
        resp2.read.return_value = json.dumps({"data": {"status": "SUCCEEDED"}}).encode("utf-8")
        resp2.__enter__.return_value = resp2

        mock_urlopen.side_effect = [resp1, resp2]

        progress_logs = []
        with patch.object(apify, "TOKEN", "dummy_token"):
            result = apify.wait_for_run("run123", on_progress=progress_logs.append)
            self.assertTrue(result)
            self.assertEqual(progress_logs, ["Run status: RUNNING", "Run status: SUCCEEDED"])

    @patch("urllib.request.urlopen")
    @patch("time.sleep", return_value=None)
    def test_wait_for_run_failed(self, mock_sleep, mock_urlopen):
        resp = MagicMock()
        resp.read.return_value = json.dumps({"data": {"status": "FAILED"}}).encode("utf-8")
        resp.__enter__.return_value = resp
        mock_urlopen.return_value = resp

        with patch.object(apify, "TOKEN", "dummy_token"):
            result = apify.wait_for_run("run123")
            self.assertFalse(result)

    @patch("urllib.request.urlopen")
    def test_fetch_dataset(self, mock_urlopen):
        mock_items = [{"title": "Dev", "companyName": "Acme"}]
        resp = MagicMock()
        resp.read.return_value = json.dumps(mock_items).encode("utf-8")
        resp.__enter__.return_value = resp
        mock_urlopen.return_value = resp

        with patch.object(apify, "TOKEN", "dummy_token"):
            items = apify.fetch_dataset("ds123")
            self.assertEqual(items, mock_items)

    # --- Search orchestrator tests ---

    def test_run_search_no_token(self):
        with patch.object(apify, "TOKEN", None):
            res = apify.run_search()
            self.assertIn("APIFY_TOKEN not set", res["error"])
            self.assertEqual(res["added"], 0)

    @patch("add_job.create")
    @patch("search_apify_jobs.fetch_dataset")
    @patch("search_apify_jobs.wait_for_run")
    @patch("search_apify_jobs.start_run")
    @patch("search_apify_jobs.load_connectors")
    @patch("search_apify_jobs.load_profile")
    def test_run_search_success_with_dedup_and_add(
        self, mock_profile, mock_connectors, mock_start, mock_wait, mock_fetch, mock_add
    ):
        mock_profile.return_value = {"primary_stack": ["Python"], "disallowed_tech": []}
        mock_connectors.return_value = [{"keywords": "Python Developer"}]
        mock_start.return_value = ("r1", "d1")
        mock_wait.return_value = True

        mock_fetch.return_value = [
            {"companyName": "Alpha Inc", "title": "Python Dev", "url": "https://job1"},
            {"companyName": "Alpha Inc", "title": "Python Dev Dup", "url": "https://job1"},
            {"companyName": "Beta Corp", "title": "Backend Eng", "url": "https://job2"},
            {"companyName": "Unknown", "title": "No Co", "url": "https://job3"},
        ]

        mock_add.side_effect = [
            (True, "Created folder"),
            (False, "Already on board"),
        ]

        progress_msgs = []
        with patch.object(apify, "TOKEN", "token123"):
            res = apify.run_search(on_progress=progress_msgs.append)

        self.assertEqual(res["total"], 3)
        self.assertEqual(res["added"], 1)
        self.assertEqual(res["skipped"], 2)
        self.assertIsNone(res["error"])
        self.assertTrue(any("Starting search" in msg for msg in progress_msgs))

    @patch("add_job.create")
    @patch("search_apify_jobs.fetch_dataset")
    @patch("search_apify_jobs.wait_for_run")
    @patch("search_apify_jobs.start_run")
    @patch("search_apify_jobs.load_connectors")
    @patch("search_apify_jobs.load_profile")
    def test_run_search_fallback_to_profile(
        self, mock_profile, mock_connectors, mock_start, mock_wait, mock_fetch, mock_add
    ):
        mock_profile.return_value = {"primary_stack": ["Python", "FastAPI"], "disallowed_tech": ["PHP"]}
        mock_connectors.return_value = []
        mock_start.return_value = ("r1", "d1")
        mock_wait.return_value = True
        mock_fetch.return_value = []

        with patch.object(apify, "TOKEN", "token123"):
            res = apify.run_search()

        self.assertEqual(res["total"], 0)
        self.assertEqual(res["added"], 0)
        search_arg = mock_start.call_args[0][0]
        self.assertIn("Python FastAPI", search_arg["keywords"])
        self.assertIn("-PHP", search_arg["keywords"])


if __name__ == "__main__":
    unittest.main()
