#!/usr/bin/env python3
"""Serve the job board locally so drag-and-drop saves straight to disk.

    python3 dashboard/serve.py

Opens http://localhost:8765 in the browser. Dragging a card writes the Status:
line into that job's JOB-URL.txt immediately and rebuilds the board. No pending
state, no command to copy.

Why a server at all: a page opened as file:// cannot write to disk, which is why
the old board could only hand you a command. The server also streams the CV and
cover letter PDFs, because browsers refuse file:// links from an http origin,
and shells out to `open` to reveal a folder in Finder.

Binds to 127.0.0.1 only. Nothing is exposed off this machine.
"""
import http.server
import json
import os
import socketserver
import subprocess
import sys
import shutil
import threading
import urllib.parse
import webbrowser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DASH = os.path.join(ROOT, "dashboard")
PORT = int(os.environ.get("BOARD_PORT", "8765"))

sys.path.insert(0, DASH)
import build as board_build          # noqa: E402
import set_status as board_status    # noqa: E402
import add_job as board_add          # noqa: E402


def rebuild():
    jobs = board_build.collect()
    with open(board_build.OUT, "w", encoding="utf-8") as fh:
        fh.write(board_build.build(jobs))
    return jobs


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # quiet; the board is chatty enough

    def _send(self, code, body, ctype="application/json"):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    # ---- GET ----------------------------------------------------------------

    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path

        if path in ("/", "/index.html"):
            rebuild()
            with open(board_build.OUT, "rb") as fh:
                return self._send(200, fh.read(), "text/html; charset=utf-8")

        if path.startswith("/files/"):
            target = urllib.parse.unquote(path[len("/files/"):])
            if not target.startswith("/"):
                target = "/" + target
            real = os.path.realpath(target)
            # Only ever serve from inside the workspace.
            if not real.startswith(os.path.realpath(ROOT)) or not os.path.isfile(real):
                return self._send(404, b"not found", "text/plain")
            ctype = {
                ".pdf": "application/pdf",
                ".md": "text/plain; charset=utf-8",
                ".txt": "text/plain; charset=utf-8",
                ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            }.get(os.path.splitext(real)[1].lower(), "application/octet-stream")
            with open(real, "rb") as fh:
                return self._send(200, fh.read(), ctype)

        self._send(404, b"not found", "text/plain")

    # ---- POST ---------------------------------------------------------------

    def do_POST(self):
        path = urllib.parse.urlparse(self.path).path
        length = int(self.headers.get("Content-Length", 0))
        try:
            payload = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            return self._send(400, json.dumps({"ok": False, "error": "bad json"}))

        if path == "/api/status":
            num, status = str(payload.get("num", "")), payload.get("status", "")
            if status not in board_status.VALID:
                return self._send(400, json.dumps({"ok": False, "error": "bad status"}))
            folder, name = board_status.find(num)
            if not folder:
                return self._send(404, json.dumps({"ok": False, "error": "no such job"}))
            board_status.set_status(num, status)
            rebuild()
            return self._send(200, json.dumps({"ok": True, "job": name, "status": status}))

        if path == "/api/applied":
            num = str(payload.get("num", ""))
            date_str = (payload.get("date") or "").strip()
            folder, name = board_status.find(num)
            if not folder:
                return self._send(404, json.dumps({"ok": False, "error": "no such job"}))
            f = os.path.join(folder, "JOB-URL.txt")
            text = open(f, errors="ignore").read() if os.path.exists(f) else ""
            if date_str:
                line = f"Applied on: {date_str}"
            else:
                line = "Applied on: ____________"
            import re as _re
            if _re.search(r"^Applied on:.*$", text, _re.M):
                text = _re.sub(r"^Applied on:.*$", line, text, count=1, flags=_re.M)
            else:
                text = text.rstrip("\n") + "\n" + line + "\n"
            with open(f, "w", encoding="utf-8") as fh:
                fh.write(text)
            rebuild()
            return self._send(200, json.dumps({"ok": True, "job": name, "date": date_str}))

        if path == "/api/notes":
            num = str(payload.get("num", ""))
            body = payload.get("text", "")
            folder, name = board_status.find(num)
            if not folder:
                return self._send(404, json.dumps({"ok": False, "error": "no such job"}))
            with open(os.path.join(folder, "MY-NOTES.md"), "w", encoding="utf-8") as fh:
                fh.write(body)
            rebuild()
            return self._send(200, json.dumps({"ok": True, "job": name}))

        if path == "/api/add":
            ok, msg = board_add.create(payload.get("company", ""),
                                       payload.get("role", ""),
                                       payload.get("url", ""),
                                       bool(payload.get("force")))
            if ok:
                rebuild()
            return self._send(200 if ok else 409, json.dumps({"ok": ok, "message": msg}))

        if path == "/api/delete":
            num = str(payload.get("num", ""))
            folder, name = board_status.find(num)
            if not folder:
                return self._send(404, json.dumps({"ok": False, "error": "no such job"}))
            # Never hard-delete. Move into applications/_deleted/, which
            # collect() ignores because it only scans DD.MM.YY directories.
            trash = os.path.join(ROOT, "applications", "_deleted")
            os.makedirs(trash, exist_ok=True)
            stamp = __import__("datetime").datetime.now().strftime("%Y%m%d-%H%M%S")
            dest = os.path.join(trash, f"{stamp} {name}")
            shutil.move(folder, dest)
            rebuild()
            return self._send(200, json.dumps({"ok": True, "job": name,
                                               "moved_to": os.path.relpath(dest, ROOT)}))

        if path == "/api/open":
            target = os.path.realpath(payload.get("path", ""))
            if not target.startswith(os.path.realpath(ROOT)) or not os.path.exists(target):
                return self._send(404, json.dumps({"ok": False}))
            subprocess.run(["open", target], check=False)
            return self._send(200, json.dumps({"ok": True}))

        self._send(404, json.dumps({"ok": False}))


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


if __name__ == "__main__":
    jobs = rebuild()
    url = f"http://localhost:{PORT}"
    print(f"Job board: {url}   ({len(jobs)} roles)")
    print("Drag a card and it saves immediately. Ctrl-C to stop.")
    threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        with Server(("127.0.0.1", PORT), Handler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
