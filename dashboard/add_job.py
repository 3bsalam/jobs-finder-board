#!/usr/bin/env python3
"""Create a new job folder, correctly numbered and dated, then rebuild the board.

    python3 dashboard/add_job.py "Example Company" "Senior Backend Engineer"
    python3 dashboard/add_job.py "Example Company" "Senior Backend Engineer" "https://..."

Numbering is global and continues from the highest existing number, so a job
added on a new day still follows the previous one. The folder lands under
today's date folder.

Refuses to create a duplicate if the company already appears anywhere, unless
--force is passed. That check is the whole reason this script exists rather
than doing it by hand.
"""
import os
import re
import subprocess
import sys
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APPS = os.path.join(ROOT, "applications")


def existing():
    """Every (number, company, folder path) already tracked."""
    out = []
    for d in sorted(os.listdir(APPS)):
        if not re.match(r"^\d{2}\.\d{2}\.\d{2}$", d):
            continue
        for f in sorted(os.listdir(os.path.join(APPS, d))):
            p = os.path.join(APPS, d, f)
            if not os.path.isdir(p):
                continue
            m = re.match(r"^(\d+)\s*-\s*([^-]+)", f)
            if m:
                out.append((int(m.group(1)), m.group(2).strip(), p))
    return out


def safe(s):
    """Strip characters that make a folder name awkward."""
    return re.sub(r"[/:]", " ", s).strip()


def create(company, role, url="", force=False):
    """Create the folder. Returns (ok, message). Used by the CLI and by serve.py."""
    company, role = safe(company), safe(role)
    if not company or not role:
        return False, "company and role are both required"

    rows = existing()
    clash = [r for r in rows if r[1].lower() == company.lower()]
    if clash and not force:
        lines = "; ".join(f"{n:02d} {os.path.basename(pp)}" for n, _, pp in clash)
        return False, f"'{company}' is already tracked: {lines}"

    num = max((r[0] for r in rows), default=0) + 1
    today = date.today().strftime("%d.%m.%y")
    folder = os.path.join(APPS, today, f"{num:02d} - {company} - {role}")
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, "JOB-URL.txt"), "w", encoding="utf-8") as fh:
        fh.write(f"""{company} - {role}
{url}

Location:   VERIFY ON THE EMPLOYER'S OWN PAGE, not the aggregator.
Reply SLA:
Salary:

Status: to_prepare
Applied on: ____________
""")
    return True, f"{num:02d} - {company} - {role}"


def main():
    args = [a for a in sys.argv[1:] if a != "--force"]
    force = "--force" in sys.argv
    if len(args) < 2:
        sys.exit(__doc__)
    ok, msg = create(args[0], args[1], args[2] if len(args) > 2 else "", force)
    if not ok:
        sys.exit(msg + "\n\nPass --force if this is a different role.")
    print("created  " + msg)
    for script in ("dashboard/build.py", ".scratch/build_applied_index.py"):
        subprocess.run([sys.executable, os.path.join(ROOT, script)],
                       check=False, capture_output=True)
    print("board and index rebuilt")


if __name__ == "__main__":
    main()
