#!/usr/bin/env python3
"""Apply an inbox-sync action list to the job folders, safely and repeatably.

The assistant reads your application email (confirmations, rejections,
interview invites, sent applications) and writes a JSON list of actions. This
script is the only thing that touches the folders. It is deliberately strict,
so a mistake in the email reading cannot quietly corrupt the board:

    python3 scripts/apply_inbox_actions.py inbox-actions.json --dry-run
    python3 scripts/apply_inbox_actions.py inbox-actions.json

Each action is one of:

    {"action": "set_status", "number": 42, "status": "rejected",
     "applied_on": "02.09.26", "evidence": "Ashby | Update on your application | 05.09.26"}

    {"action": "note", "number": 42, "evidence": "...", "note": "Second role, same company: ..."}

    {"action": "create", "company": "Acme", "role": "Backend Engineer",
     "status": "applied", "applied_on": "28.09.26", "evidence": "..."}

Rules it enforces:
- Statuses never go backwards (an "applied" email does not undo "interview").
  A rejection always lands, except over an offer. Moving a rejected or skipped
  job back to applied needs "reapplied": true in the action.
- Re-running the same list changes nothing: each action is stamped with its
  evidence line, and an action whose evidence is already in the file is skipped.
- "create" never makes a duplicate company folder. If the company exists, the
  action becomes a note on the existing folder (usually a second role).
- Applied jobs get a "Follow up:" date 14 days after the application.

No dependencies. Rebuilds the board and the applied index afterwards unless
--no-build is passed.
"""
import datetime
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VALID = ["to_prepare", "ready", "applied", "interview", "offer", "rejected",
         "not_eligible", "skipped"]
RANK = {"to_prepare": 0, "ready": 1, "applied": 2, "interview": 3, "offer": 4}
CLOSED = {"rejected", "not_eligible", "skipped"}
FOLDER_RE = re.compile(r"^(\d+)\s*-\s*([^-]+?)\s*-\s*(.+)$")
DATE_RE = re.compile(r"^\d{2}\.\d{2}\.\d{2}$")


def safe(s):
    return re.sub(r"[/:\\*?\[\]]", " ", str(s)).strip()


def existing(apps):
    """[(number, company, path)] for every tracked job folder."""
    out = []
    if not os.path.isdir(apps):
        return out
    for d in sorted(os.listdir(apps)):
        if not DATE_RE.match(d):
            continue
        for f in sorted(os.listdir(os.path.join(apps, d))):
            p = os.path.join(apps, d, f)
            m = FOLDER_RE.match(f)
            if os.path.isdir(p) and m:
                out.append((int(m.group(1)), m.group(2).strip(), p))
    return out


def find_by_number(apps, num):
    for n, _, p in existing(apps):
        if n == int(num):
            return p
    return None


def find_by_company(apps, company):
    c = safe(company).lower()
    for _, comp, p in existing(apps):
        if comp.lower() == c:
            return p
    return None


def current_status(text):
    m = re.search(r"^Status:\s*([a-z_]+)", text, re.M)
    return m.group(1) if m else None


def allowed(current, new, reapplied=False):
    """Never move a job backwards; let real news through."""
    if new == current:
        return False
    if current is None:
        return True
    if new == "rejected":
        return current != "offer"
    if current in CLOSED:
        return new in RANK and (reapplied or RANK[new] >= RANK["interview"])
    if new in CLOSED:
        return current in ("to_prepare", "ready")
    return RANK.get(new, -1) > RANK.get(current, -1)


def follow_up(applied_on):
    try:
        d = datetime.datetime.strptime(applied_on, "%d.%m.%y")
    except (TypeError, ValueError):
        return None
    return (d + datetime.timedelta(days=14)).strftime("%d.%m.%y")


def set_line(text, key, value):
    pat = rf"^{re.escape(key)}:.*$"
    if re.search(pat, text, re.M):
        return re.sub(pat, f"{key}: {value}", text, count=1, flags=re.M)
    return text.rstrip() + f"\n{key}: {value}\n"


def stamp(today, title, a):
    lines = [f"=== inbox sync {today}: {title} ==="]
    if a.get("evidence"):
        lines.append(f"Evidence: {a['evidence']}")
    if a.get("note"):
        lines.append(str(a["note"]))
    return "\n" + "\n".join(lines) + "\n"


def apply(actions, root=ROOT, dry_run=False, today=None):
    apps = os.path.join(root, "applications")
    today = today or datetime.date.today()
    tstr = today.strftime("%d.%m.%y")
    report = []

    for a in actions:
        kind = a.get("action")
        ev = a.get("evidence", "")
        try:
            if kind in ("set_status", "note"):
                path = find_by_number(apps, a["number"])
                if not path:
                    report.append(("error", a, f"no folder numbered {a['number']}"))
                    continue
                f = os.path.join(path, "JOB-URL.txt")
                text = open(f, encoding="utf-8", errors="ignore").read() if os.path.exists(f) else ""
                if ev and ev in text:
                    report.append(("unchanged", a, "evidence already recorded"))
                    continue
                if kind == "note":
                    text = text.rstrip() + "\n" + stamp(tstr, "note", a)
                    report.append(("note", a, os.path.basename(path)))
                else:
                    new = a["status"]
                    if new not in VALID:
                        report.append(("error", a, f"invalid status {new}"))
                        continue
                    cur = current_status(text)
                    if not allowed(cur, new, a.get("reapplied", False)):
                        text = text.rstrip() + "\n" + stamp(tstr, f"kept {cur} (email said {new})", a)
                        report.append(("kept", a, f"{os.path.basename(path)}: {cur} stays"))
                    else:
                        text = set_line(text, "Status", new)
                        if a.get("applied_on"):
                            text = set_line(text, "Applied on", a["applied_on"])
                        if new == "applied" and follow_up(a.get("applied_on")):
                            text = set_line(text, "Follow up", follow_up(a["applied_on"]))
                        text = text.rstrip() + "\n" + stamp(tstr, f"{cur} -> {new}", a)
                        report.append(("status", a, f"{os.path.basename(path)}: {cur} -> {new}"))
                if not dry_run:
                    open(f, "w", encoding="utf-8").write(text)

            elif kind == "create":
                company, role = safe(a["company"]), safe(a.get("role") or "Role not named in email")
                status = a.get("status", "applied")
                if status not in VALID:
                    report.append(("error", a, f"invalid status {status}"))
                    continue
                path = find_by_company(apps, company)
                if path:
                    f = os.path.join(path, "JOB-URL.txt")
                    text = open(f, encoding="utf-8", errors="ignore").read() if os.path.exists(f) else ""
                    if ev and ev in text:
                        report.append(("unchanged", a, "evidence already recorded"))
                        continue
                    a2 = dict(a, note=f"Another role at this company: {role} ({status}"
                                      f"{', applied ' + a['applied_on'] if a.get('applied_on') else ''}).")
                    if not dry_run:
                        open(f, "w", encoding="utf-8").write(text.rstrip() + "\n" + stamp(tstr, "second role", a2))
                    report.append(("note", a, f"{os.path.basename(path)}: company exists, noted second role"))
                    continue
                num = max((n for n, _, _ in existing(apps)), default=0) + 1
                folder = os.path.join(apps, tstr, f"{num:02d} - {company} - {role}")
                ap = a.get("applied_on") or "____________"
                fu = follow_up(a.get("applied_on")) if status == "applied" else None
                body = (f"{company} - {role}\n{a.get('url', '')}\n\n"
                        f"Found by inbox sync on {tstr}.\n"
                        + (f"Evidence: {ev}\n" if ev else "")
                        + (f"{a['note']}\n" if a.get("note") else "")
                        + f"\nStatus: {status}\nApplied on: {ap}\n"
                        + (f"Follow up: {fu}\n" if fu else ""))
                if not dry_run:
                    os.makedirs(folder, exist_ok=True)
                    open(os.path.join(folder, "JOB-URL.txt"), "w", encoding="utf-8").write(body)
                report.append(("created", a, os.path.basename(folder)))
            else:
                report.append(("error", a, f"unknown action {kind!r}"))
        except (KeyError, OSError) as e:
            report.append(("error", a, repr(e)))
    return report


def main():
    args = [x for x in sys.argv[1:] if not x.startswith("--")]
    if not args:
        sys.exit(__doc__)
    dry = "--dry-run" in sys.argv
    actions = json.load(open(args[0], encoding="utf-8"))
    report = apply(actions, dry_run=dry)
    counts = {}
    for kind, _, msg in report:
        counts[kind] = counts.get(kind, 0) + 1
        print(f"{kind:9} {msg}")
    print(("DRY RUN, nothing written. " if dry else "") + str(counts))
    if not dry and "--no-build" not in sys.argv:
        for script in ("dashboard/build.py", "scripts/build_applied_index.py"):
            p = os.path.join(ROOT, script)
            if os.path.exists(p):
                subprocess.run([sys.executable, p], check=False, capture_output=True)
        print("board and index rebuilt")


if __name__ == "__main__":
    main()
