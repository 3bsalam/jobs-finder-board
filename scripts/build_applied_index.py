#!/usr/bin/env python3
"""Regenerate applications/APPLIED-INDEX.md from the date folders.

Run before creating any new job folder, to check the company is not already
covered from a previous day.
"""
import os, re, datetime

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "applications")
RESUME_MARKER = os.environ.get("RESUME_MARKER", "Resume")
rows = []
for d in sorted(os.listdir(ROOT)):
    if not re.match(r'^\d{2}\.\d{2}\.\d{2}$', d):
        continue
    for j in sorted(os.listdir(os.path.join(ROOT, d))):
        p = os.path.join(ROOT, d, j)
        if not os.path.isdir(p):
            continue
        m = re.match(r'^(\d+)\s*-\s*(.+)$', j)
        if not m:
            continue
        num, rest = m.group(1), m.group(2)
        parts = [x.strip() for x in rest.split(' - ')]
        company, role = parts[0], ' - '.join(parts[1:])
        if 'REJECTED' in rest.upper():
            status = 'REJECTED'
        elif 'NOT ELIGIBLE' in rest.upper():
            status = 'NOT ELIGIBLE'
        else:
            u = os.path.join(p, 'JOB-URL.txt')
            t = open(u, errors='ignore').read() if os.path.exists(u) else ''
            if re.search(r'Applied on:\s*\d', t):
                status = 'APPLIED'
            elif any(RESUME_MARKER.lower() in f.lower() for f in os.listdir(p)):
                status = 'docs ready'
            else:
                status = 'no docs'
        rows.append((num, d, company, role, status))

out = ['# Applied index', '',
       'Every company and role across all date folders. **Check this before creating a new',
       'job folder.** If the company already appears, do not create a second folder for the',
       'same role. A different role at the same company is fine, but note it against the',
       'existing row so the history stays in one place.', '',
       f'Last regenerated: {datetime.date.today().strftime("%d.%m.%Y")}', '',
       '| # | Date folder | Company | Role | Status |', '|---|---|---|---|---|']
out += [f'| {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} |' for r in rows]
out += ['', '## Companies already covered', '',
        ', '.join(sorted({r[2] for r in rows})), '',
        '## Regenerate', '', '```bash', 'python3 .scratch/build_applied_index.py', '```']
open(os.path.join(ROOT, 'APPLIED-INDEX.md'), 'w').write('\n'.join(out) + '\n')
print(f'wrote APPLIED-INDEX.md: {len(rows)} entries')
