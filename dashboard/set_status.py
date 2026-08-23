#!/usr/bin/env python3
"""Set a job's status on disk, so the board and the folders stay in sync.

    python3 dashboard/set_status.py 31 interview
    python3 dashboard/set_status.py 31 interview 23 applied     (several at once)

Writes or replaces the "Status:" line in that job's JOB-URL.txt, then rebuilds
the dashboard. The dashboard board's "Apply moves" button hands you exactly
this command with the pending changes filled in.
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APPS = os.path.join(ROOT, "applications")
VALID = ["to_prepare", "ready", "applied", "interview", "offer", "rejected",
         "not_eligible", "skipped"]


def find(num):
    for datedir in sorted(os.listdir(APPS)):
        if not re.match(r"^\d{2}\.\d{2}\.\d{2}$", datedir):
            continue
        for folder in os.listdir(os.path.join(APPS, datedir)):
            p = os.path.join(APPS, datedir, folder)
            if os.path.isdir(p) and re.match(rf"^0*{int(num)}\s*-\s", folder):
                return p, folder
    return None, None


def set_status(num, status):
    if status not in VALID:
        sys.exit(f"invalid status '{status}'. valid: {', '.join(VALID)}")
    path, folder = find(num)
    if not path:
        sys.exit(f"no job folder numbered {num}")
    f = os.path.join(path, "JOB-URL.txt")
    text = open(f, errors="ignore").read() if os.path.exists(f) else ""
    if re.search(r"^Status:.*$", text, re.M):
        text = re.sub(r"^Status:.*$", f"Status: {status}", text, count=1, flags=re.M)
    else:
        text = text.rstrip("\n") + f"\n\nStatus: {status}\n"
    with open(f, "w", encoding="utf-8") as fh:
        fh.write(text)
    print(f"  {folder}  ->  {status}")


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or len(args) % 2:
        sys.exit(__doc__)
    for i in range(0, len(args), 2):
        set_status(args[i], args[i + 1])
    subprocess.run([sys.executable, os.path.join(ROOT, "dashboard", "build.py")], check=True)
