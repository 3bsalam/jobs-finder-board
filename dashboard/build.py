#!/usr/bin/env python3
"""Build the job-search board from the applications/ folder tree.

Writes a single self-contained dashboard/index.html: a Jira/GitLab style board
with a column per status, drag-and-drop between columns, and a detail drawer per
card. No server, no dependencies, nothing uploaded. Served by dashboard/serve.py, which saves status changes to disk
immediately and streams the documents. Run that, not this file directly.

Status resolution, in order:
  1. "Status:" line in JOB-URL.txt        (authoritative, set via set_status.py)
  2. REJECTED / NOT ELIGIBLE in folder name
  3. "Applied on: <date>" filled in
  4. a rendered CV present               -> ready
  5. otherwise                           -> to_prepare

Run:  python3 dashboard/build.py
"""
import json
import os
import re
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# A folder counts as "ready" once a CV file is present. Set RESUME_MARKER to
# whatever substring your CV filenames share, e.g. "Jane_Doe_Resume".
RESUME_MARKER = os.environ.get("RESUME_MARKER", "Resume")
APPS = os.path.join(ROOT, "applications")
OUT = os.path.join(ROOT, "dashboard", "index.html")

COLUMNS = [
    ("to_prepare", "To prepare", "Folder exists, documents not built yet"),
    ("ready", "Ready to apply", "CV and cover letter built, not sent"),
    ("applied", "Applied", "Submitted, waiting"),
    ("interview", "Interview", "They replied and want to talk"),
    ("offer", "Offer", "Offer on the table"),
    ("rejected", "Rejected", "Turned down"),
    ("not_eligible", "Not eligible", "They cannot take you: location, sponsorship, stack"),
    ("skipped", "Skipped", "You decided against it"),
]
VALID = {k for k, _, _ in COLUMNS}


def read(path):
    try:
        with open(path, errors="ignore") as fh:
            return fh.read()
    except OSError:
        return ""


def first(pattern, text, group=1):
    m = re.search(pattern, text, re.I | re.M)
    return m.group(group).strip() if m else ""


PAY_RE = re.compile(
    r"(?:USD|EUR|GBP|QAR|AED|SAR|\$|€|£)\s?[\d][\d,.]*\s?[Kk]?"
    r"(?:\s*(?:-|–|to)\s*(?:USD|EUR|GBP|QAR|AED|SAR|\$|€|£)?\s?[\d][\d,.]*\s?[Kk]?)?"
    r"(?:\s*(?:/|per\s)\s*(?:year|yr|month|mo|hour|hr))?", re.I)


def pay_of(text):
    """Short, card-sized pay string. Empty when nothing reliable is stated."""
    line = first(r"^(?:Salary|Compensation|Pay|Rate):\s*(.+)$", text)
    if not line:
        return ""
    if re.match(r"^\s*(not\s+(stated|disclosed|published|listed)|unknown|n/?a)\b", line, re.I):
        return ""
    m = PAY_RE.search(line)
    if not m:
        return ""
    out = " ".join(m.group(0).split())
    return out[:34]


def collect():
    jobs = []
    if not os.path.isdir(APPS):
        return jobs
    for datedir in sorted(os.listdir(APPS)):
        if not re.match(r"^\d{2}\.\d{2}\.\d{2}$", datedir):
            continue
        dpath = os.path.join(APPS, datedir)
        for folder in sorted(os.listdir(dpath)):
            fpath = os.path.join(dpath, folder)
            if not os.path.isdir(fpath):
                continue
            m = re.match(r"^(\d+)\s*-\s*(.+)$", folder)
            if not m:
                continue
            num, rest = m.group(1), m.group(2)
            parts = [p.strip() for p in rest.split(" - ")]
            company = parts[0]
            role = " - ".join(parts[1:]) if len(parts) > 1 else ""

            files = sorted(os.listdir(fpath))
            joburl = read(os.path.join(fpath, "JOB-URL.txt"))
            notes = read(os.path.join(fpath, "NOTES.md"))
            mynotes = read(os.path.join(fpath, "MY-NOTES.md"))

            status = first(r"^Status:\s*([a-z_]+)\s*$", joburl).lower()
            if status not in VALID:
                upper = rest.upper()
                if "REJECTED" in upper:
                    status = "rejected"
                elif "NOT ELIGIBLE" in upper:
                    status = "not_eligible"
                elif re.search(r"^Applied on:\s*\d", joburl, re.I | re.M):
                    status = "applied"
                elif any(RESUME_MARKER.lower() in f.lower() for f in files):
                    status = "ready"
                else:
                    status = "to_prepare"

            docs = [f for f in files if f.endswith((".pdf", ".docx"))]
            guides = [f for f in files if f.endswith(".md") or f == "JOB-URL.txt"]

            jobs.append({
                "num": num,
                "company": company,
                "role": role,
                "date": datedir,
                "status": status,
                "url": first(r"(https?://\S+)", joburl),
                "applied_on": first(r"^Applied on:\s*([0-9.]{6,})", joburl),
                "location": first(r"^Location:\s*(.+)$", joburl) or first(r"^Location:\s*(.+)$", notes),
                "verdict": first(r"^Verdict:\s*(.+)$", joburl) or first(r"^Verdict:\s*(.+)$", notes),
                "followup": first(r"^Follow up:\s*(.+)$", joburl),
                "salary": first(r"^(?:Salary|Compensation|Pay|Rate):\s*(.+)$", joburl + notes),
                "pay": pay_of(joburl + "\n" + notes),
                "folder": fpath,
                "docs": docs,
                "guides": guides,
                "notes": (notes or joburl)[:2000],
                "mynotes": mynotes,
            })
    return jobs


TEMPLATE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Job search board</title>
<style>
:root{
  --bg:#fbfbfa; --panel:#fff; --card:#fff; --ink:#1a1a18; --muted:#6f6f69;
  --line:#e6e5e1; --accent:#7a5cff;
  --shadow:0 1px 2px rgba(0,0,0,.05); --shadow-lg:0 12px 32px rgba(0,0,0,.13);
  --to_prepare:#8a8a84; --ready:#b26b00; --applied:#2f7d5d; --interview:#7a5cff;
  --offer:#1a7f37; --rejected:#b3403a; --not_eligible:#8a8a84; --skipped:#6b6b8a;
}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){
  --bg:#121214; --panel:#191a1d; --card:#1e1f23; --ink:#ecebe7; --muted:#9b988f;
  --line:#2b2c31; --shadow:0 1px 2px rgba(0,0,0,.4); --shadow-lg:0 12px 32px rgba(0,0,0,.5);
}}
:root[data-theme=dark]{
  --bg:#121214; --panel:#191a1d; --card:#1e1f23; --ink:#ecebe7; --muted:#9b988f;
  --line:#2b2c31; --shadow:0 1px 2px rgba(0,0,0,.4); --shadow-lg:0 12px 32px rgba(0,0,0,.5);
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
 font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Inter,sans-serif}
header{padding:20px 24px 0;display:flex;align-items:baseline;gap:14px;flex-wrap:wrap}
h1{font-size:20px;margin:0;letter-spacing:-.02em}
.sub{color:var(--muted);font-size:12.5px}
.spacer{flex:1}
#q{padding:8px 12px;border:1px solid var(--line);border-radius:9px;background:var(--panel);
 color:var(--ink);font:inherit;font-size:13px;min-width:230px}
#q:focus{outline:2px solid color-mix(in srgb,var(--accent) 40%,transparent);outline-offset:1px}

.board{display:flex;gap:12px;padding:18px 24px 40px;overflow-x:auto;align-items:flex-start}
.col{background:var(--panel);border:1px solid var(--line);border-radius:12px;
 min-width:262px;max-width:262px;flex:0 0 auto;display:flex;flex-direction:column;max-height:78vh}
.col.drag{border-color:var(--accent);box-shadow:0 0 0 2px color-mix(in srgb,var(--accent) 20%,transparent)}
.colhead{padding:11px 13px 9px;border-bottom:1px solid var(--line);position:sticky;top:0;
 background:var(--panel);border-radius:12px 12px 0 0;z-index:1}
.colhead .t{display:flex;align-items:center;gap:7px;font-weight:600;font-size:13px}
.dot{width:8px;height:8px;border-radius:50%;flex:0 0 auto}
.cnt{margin-left:auto;color:var(--muted);font-size:12px;font-variant-numeric:tabular-nums}
.colhead .d{color:var(--muted);font-size:11.5px;margin-top:3px;line-height:1.35}
.cards{padding:9px;overflow-y:auto;flex:1;min-height:56px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:10px 11px;
 margin-bottom:8px;cursor:grab;box-shadow:var(--shadow);transition:transform .1s,border-color .1s}
.card:hover{border-color:var(--accent);transform:translateY(-1px)}
.card:active{cursor:grabbing}
.card.ghost{opacity:.35}
.card .co{font-weight:600;font-size:13px;line-height:1.3}
.card .ro{color:var(--muted);font-size:12px;margin-top:2px;line-height:1.35}
.card .foot{display:flex;gap:5px;align-items:center;margin-top:8px;flex-wrap:wrap}
.tag{font-size:10.5px;padding:2px 7px;border-radius:6px;background:var(--bg);
 border:1px solid var(--line);color:var(--muted)}
.tag.n{font-variant-numeric:tabular-nums}
.tag.pay,.chip.pay{color:var(--offer);border-color:color-mix(in srgb,var(--offer) 45%,var(--line));
 font-variant-numeric:tabular-nums;font-weight:600}
.tag.sent{color:var(--applied);border-color:color-mix(in srgb,var(--applied) 50%,var(--line));
 font-weight:600}
.card.sent{border-left:3px solid var(--applied)}
.sentcount{display:block;margin-top:4px;color:var(--applied);font-weight:600}
.sentrow{display:flex;gap:6px;flex-wrap:wrap;align-items:center}
.sentrow input{width:130px;padding:7px 10px;font:inherit;font-size:13px;
 border:1px solid var(--line);border-radius:8px;background:var(--bg);color:var(--ink)}
.sentrow button{font-size:12.5px;padding:7px 11px}
.notes{width:100%;min-height:120px;resize:vertical;padding:10px 12px;font:inherit;
 font-size:13px;line-height:1.5;border:1px solid var(--line);border-radius:9px;
 background:var(--bg);color:var(--ink)}
.notes:focus{outline:2px solid color-mix(in srgb,var(--accent) 40%,transparent);outline-offset:1px}
.tag.note{color:var(--interview);border-color:color-mix(in srgb,var(--interview) 45%,var(--line))}
button.danger{color:var(--rejected);border-color:color-mix(in srgb,var(--rejected) 40%,var(--line))}
button.danger.armed{background:var(--rejected);border-color:var(--rejected);color:#fff}
.modal code,.drawer code{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:11.5px}
.empty{color:var(--muted);font-size:12px;text-align:center;padding:14px 8px}

.toast{position:fixed;left:50%;transform:translateX(-50%) translateY(8px);bottom:24px;
 z-index:40;background:var(--panel);border:1px solid var(--line);border-radius:10px;
 padding:9px 15px;box-shadow:var(--shadow-lg);font-size:12.5px;opacity:0;
 pointer-events:none;transition:opacity .18s,transform .18s;white-space:nowrap}
.toast.on{opacity:1;transform:translateX(-50%) translateY(0)}
.toast.err{border-color:var(--rejected);color:var(--rejected)}
button{font:inherit;font-size:12.5px;padding:7px 12px;border-radius:8px;border:1px solid var(--line);
 background:var(--bg);color:var(--ink);cursor:pointer}
button.primary{background:var(--accent);border-color:var(--accent);color:#fff}
button:hover{filter:brightness(1.06)}

.scrim{position:fixed;inset:0;background:rgba(0,0,0,.32);opacity:0;pointer-events:none;
 transition:opacity .16s;z-index:50}
.scrim.on{opacity:1;pointer-events:auto}
.drawer{position:fixed;top:0;right:0;height:100%;width:min(520px,94vw);background:var(--panel);
 border-left:1px solid var(--line);z-index:60;transform:translateX(100%);transition:transform .2s;
 overflow-y:auto;padding:22px 24px 60px}
.drawer.on{transform:none}
.drawer h2{font-size:18px;margin:0 0 2px;letter-spacing:-.01em}
.drawer .role{color:var(--muted);font-size:13px;margin-bottom:14px}
.meta{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:16px}
.chip{font-size:11.5px;padding:4px 9px;border-radius:7px;background:var(--bg);
 border:1px solid var(--line);color:var(--muted)}
h3{font-size:11.5px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);
 margin:18px 0 7px;font-weight:600}
a{color:var(--accent)}
.btnrow{display:flex;flex-wrap:wrap;gap:7px}
.btnlink{display:inline-block;font-size:12.5px;padding:7px 12px;border-radius:8px;
 border:1px solid var(--line);background:var(--bg);color:var(--ink);text-decoration:none}
.btnlink:hover{border-color:var(--accent)}
.filelist a{display:block;font-size:12.5px;padding:3px 0;word-break:break-all}
pre{white-space:pre-wrap;font-size:12px;color:var(--muted);background:var(--bg);
 border:1px solid var(--line);border-radius:9px;padding:12px;overflow-x:auto;margin:0}
.path{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:11px;color:var(--muted);
 word-break:break-all;margin-top:14px}
.close{position:absolute;top:16px;right:20px}
select{font:inherit;font-size:12.5px;padding:6px 9px;border-radius:8px;
 border:1px solid var(--line);background:var(--bg);color:var(--ink)}
.modal{position:fixed;top:50%;left:50%;transform:translate(-50%,-50%) scale(.97);
 width:min(520px,94vw);background:var(--panel);border:1px solid var(--line);
 border-radius:14px;padding:22px 24px;box-shadow:var(--shadow-lg);z-index:70;
 opacity:0;pointer-events:none;transition:opacity .15s,transform .15s}
.modal.on{opacity:1;pointer-events:auto;transform:translate(-50%,-50%) scale(1)}
.modal label{display:block;font-size:12px;color:var(--muted);margin-bottom:11px}
.modal input{display:block;width:100%;margin-top:4px;padding:8px 11px;font:inherit;
 font-size:13.5px;border:1px solid var(--line);border-radius:8px;
 background:var(--bg);color:var(--ink)}
.modal input:focus{outline:2px solid color-mix(in srgb,var(--accent) 40%,transparent);
 outline-offset:1px}
.modal .hint{font-size:11.5px;color:var(--muted);line-height:1.45;margin:2px 0 10px}
.modal code{display:block;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;
 font-size:11.5px;color:var(--muted);background:var(--bg);border:1px solid var(--line);
 border-radius:8px;padding:10px;word-break:break-all;min-height:38px}
</style></head><body>

<header>
  <h1>Job search board</h1>
  <span class="sub">%%COUNT%% roles &middot; %%TODAY%% &middot; saves as you drag</span>
  <span class="spacer"></span>
  <input id="q" placeholder="Search company, role, location, notes...">
  <button id="prepbtn" title="Open the interview preparation folder">Interview prep</button>
  <button class="primary" id="addbtn">+ Add job</button>
</header>

<div class="modal" id="addmodal">
  <h3 style="margin-top:0">Add a job</h3>
  <label>Company<input id="a_co" placeholder="Example Company"></label>
  <label>Role<input id="a_ro" placeholder="Senior Backend Engineer"></label>
  <label>Job URL (optional)<input id="a_url" placeholder="https://..."></label>
  <p class="hint">Picks the next global number, files it under today's date,
    and refuses a company already on the board.</p>
  <code id="a_cmd"></code>
  <div class="btnrow" style="margin-top:14px">
    <button class="primary" id="a_create">Create folder</button>
    <button id="a_close">Cancel</button>
  </div>
</div>

<div class="board" id="board"></div>

<div class="toast" id="toast"></div>

<div class="scrim" id="scrim"></div>
<div class="drawer" id="drawer"></div>

<script>
const JOBS = %%JOBS%%;
const COLUMNS = %%COLUMNS%%;
const LABELS = Object.fromEntries(COLUMNS.map(c => [c[0], c[1]]));
// Status changes POST straight to the local server, which writes the Status: line
// into JOB-URL.txt and rebuilds. There is no pending state to reconcile.
function toast(msg, isErr) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.classList.toggle('err', !!isErr);
  t.classList.add('on');
  clearTimeout(t._t);
  t._t = setTimeout(() => t.classList.remove('on'), 2200);
}

async function saveStatus(num, status) {
  const job = JOBS.find(j => j.num === num);
  if (!job || job.status === status) return;
  const previous = job.status;
  job.status = status;                 // optimistic
  renderBoard();
  let saved = false;
  try {
    const r = await fetch('/api/status', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({num, status})
    });
    const d = await r.json();
    if (!d.ok) throw new Error(d.error || `server said no (${r.status})`);
    saved = true;
  } catch (e) {
    job.status = previous;             // roll back only if the write failed
    renderBoard();
    toast('Not saved: ' + (e && e.message ? e.message : 'server unreachable'), true);
    return;
  }
  // Past this point the write is on disk. Never show a failure for a UI slip.
  try { toast(`${job.company} to ${LABELS[status] || status}`); } catch (e) {}
}

const PREP_DIR = %%PREPDIR%%;
const esc = s => (s||'').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const fileUrl = p => '/files' + p.split('/').map(encodeURIComponent).join('/');
const statusOf = j => j.status;

function matches(j) {
  const q = document.getElementById('q').value.toLowerCase().trim();
  if (!q) return true;
  return (j.company+' '+j.role+' '+j.location+' '+j.notes).toLowerCase().includes(q);
}

function renderBoard() {
  const visible = JOBS.filter(matches);
  document.getElementById('board').innerHTML = COLUMNS.map(([key,label,desc]) => {
    const items = visible.filter(j => statusOf(j) === key);
    return `<div class="col" data-col="${key}">
      <div class="colhead">
        <div class="t"><span class="dot" style="background:var(--${key})"></span>${label}
          <span class="cnt">${items.length}</span></div>
        <div class="d">${desc}${(() => {
            const n = items.filter(x => x.applied_on).length;
            return (n && !['applied','interview','offer'].includes(key))
              ? ` <span class="sentcount">&#10003; ${n} you applied to</span>` : '';
          })()}</div>
      </div>
      <div class="cards" data-col="${key}">
        ${items.length ? items.map(j => `
          <div class="card${j.applied_on ? ' sent' : ''}" draggable="true" data-num="${j.num}">
            <div class="co">${esc(j.company)}</div>
            <div class="ro">${esc(j.role)}</div>
            <div class="foot">
              <span class="tag n">#${j.num}</span>
              ${j.applied_on && !['applied','interview','offer'].includes(statusOf(j))
                ? `<span class="tag sent">&#10003; sent ${esc(j.applied_on)}</span>` : ''}
              ${j.pay ? `<span class="tag pay">${esc(j.pay)}</span>` : ''}
              ${j.mynotes && j.mynotes.trim() ? `<span class="tag note">note</span>` : ''}
              ${j.docs.length ? `<span class="tag">${j.docs.length} files</span>` : ''}
              ${j.location ? `<span class="tag">${esc(j.location.slice(0,26))}</span>` : ''}
            </div>
          </div>`).join('') : '<div class="empty">Nothing here</div>'}
      </div></div>`;
  }).join('');
  wire();
}

function wire() {
  document.querySelectorAll('.card').forEach(c => {
    c.addEventListener('dragstart', e => {
      e.dataTransfer.setData('text/plain', c.dataset.num);
      setTimeout(() => c.classList.add('ghost'), 0);
    });
    c.addEventListener('dragend', () => c.classList.remove('ghost'));
    c.addEventListener('click', () => openDrawer(c.dataset.num));
  });
  document.querySelectorAll('.cards').forEach(z => {
    z.addEventListener('dragover', e => { e.preventDefault(); z.closest('.col').classList.add('drag'); });
    z.addEventListener('dragleave', () => z.closest('.col').classList.remove('drag'));
    z.addEventListener('drop', e => {
      e.preventDefault();
      z.closest('.col').classList.remove('drag');
      const num = e.dataTransfer.getData('text/plain');
      saveStatus(num, z.dataset.col);
    });
  });
}

let _delArmed = null;
async function deleteJob(num, company) {
  const btn = document.getElementById('d_del');
  if (_delArmed !== num) {                    // first click arms, second confirms
    _delArmed = num;
    btn.textContent = `Click again to delete ${company}`;
    btn.classList.add('armed');
    setTimeout(() => {
      if (_delArmed === num) {
        _delArmed = null;
        const b = document.getElementById('d_del');
        if (b) { b.textContent = 'Delete job'; b.classList.remove('armed'); }
      }
    }, 4000);
    return;
  }
  _delArmed = null;
  try {
    const r = await fetch('/api/delete', {method:'POST',
      headers:{'Content-Type':'application/json'}, body: JSON.stringify({num})});
    const d = await r.json();
    if (!d.ok) throw new Error(d.error || 'delete failed');
    toast(`Deleted. Recoverable at ${d.moved_to}`);
    closeDrawer();
    location.reload();
  } catch (e) {
    toast('Not deleted: ' + (e && e.message ? e.message : 'server unreachable'), true);
  }
}

async function saveNotes(num) {
  const text = document.getElementById('d_notes').value;
  try {
    const r = await fetch('/api/notes', {method:'POST',
      headers:{'Content-Type':'application/json'}, body: JSON.stringify({num, text})});
    const d = await r.json();
    if (!d.ok) throw new Error(d.error || 'save failed');
    const job = JOBS.find(j => j.num === num);
    if (job) job.mynotes = text;
    document.getElementById('d_notes_hint').textContent = 'Saved';
    setTimeout(() => { const h=document.getElementById('d_notes_hint'); if (h) h.textContent=''; }, 1800);
    toast('Notes saved');
  } catch (e) {
    toast('Notes not saved: ' + (e && e.message ? e.message : 'server unreachable'), true);
  }
}

function todayStr() {
  const d = new Date();
  return `${String(d.getDate()).padStart(2,'0')}.${String(d.getMonth()+1).padStart(2,'0')}.${d.getFullYear()}`;
}
async function markSent(num, date) {
  try {
    const r = await fetch('/api/applied', {method:'POST',
      headers:{'Content-Type':'application/json'}, body: JSON.stringify({num, date})});
    const d = await r.json();
    if (!d.ok) throw new Error();
    const job = JOBS.find(j => j.num === num);
    if (job) job.applied_on = date;
    toast(date ? `Marked sent ${date}` : 'Sent date cleared');
    renderBoard(); openDrawer(num);
  } catch (e) {
    toast('Not saved. Is dashboard/serve.py running?', true);
  }
}

function revealFolder(path) {
  fetch('/api/open', {method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({path})}).then(r => r.json())
    .then(d => toast(d.ok ? 'Opened in Finder' : 'Could not open', !d.ok))
    .catch(() => toast('Not connected. Is dashboard/serve.py running?', true));
}

document.getElementById('prepbtn').onclick = () => revealFolder(PREP_DIR);

function openDrawer(num) {
  const j = JOBS.find(x => x.num === num);
  if (!j) return;
  const cur = statusOf(j);
  const d = document.getElementById('drawer');
  d.innerHTML = `
    <button class="close" onclick="closeDrawer()">Close</button>
    <h2>${esc(j.company)}</h2>
    <div class="role">${esc(j.role)}</div>
    <div class="meta">
      <span class="chip" style="color:var(--${cur})">${COLUMNS.find(c=>c[0]===cur)[1]}</span>
      <span class="chip">#${j.num}</span>
      <span class="chip">prepared ${j.date}</span>
      ${j.applied_on ? `<span class="chip">applied ${esc(j.applied_on)}</span>` : ''}
      ${j.location ? `<span class="chip">${esc(j.location)}</span>` : ''}
      ${j.verdict ? `<span class="chip">${esc(j.verdict)}</span>` : ''}
    </div>
    ${j.followup ? `<h3>Follow up</h3><div class="chip">${esc(j.followup)}</div>` : ''}
    <h3>Open</h3>
    <div class="btnrow">
      ${j.url ? `<a class="btnlink" href="${esc(j.url)}" target="_blank" rel="noopener">Job posting &nearr;</a>` : ''}
      <a class="btnlink" href="#" onclick="revealFolder('${j.folder.replace(/'/g,"\\'")}');return false">Reveal folder</a>
    </div>
    ${j.docs.length ? `<h3>Documents</h3><div class="filelist">` +
      j.docs.map(f => `<a href="${fileUrl(j.folder+'/'+f)}">${esc(f)}</a>`).join('') + `</div>` : ''}
    ${j.guides.length ? `<h3>Instructions</h3><div class="filelist">` +
      j.guides.map(f => `<a href="${fileUrl(j.folder+'/'+f)}">${esc(f)}</a>`).join('') + `</div>` : ''}
    <h3>My notes</h3>
    <textarea id="d_notes" class="notes" placeholder="Anything you want to remember about this one: who you spoke to, what they said, what to follow up.">${esc(j.mynotes || '')}</textarea>
    <div class="btnrow" style="margin-top:6px">
      <button onclick="saveNotes('${j.num}')">Save notes</button>
      <span class="hint" id="d_notes_hint"></span>
    </div>

    <h3>Application sent</h3>
    <div class="sentrow">
      <input type="text" id="d_sent" value="${esc(j.applied_on || '')}" placeholder="DD.MM.YYYY">
      <button onclick="markSent('${j.num}', document.getElementById('d_sent').value)">Save</button>
      <button onclick="markSent('${j.num}', '')">Clear</button>
      <button onclick="markSent('${j.num}', todayStr())">Today</button>
    </div>
    <p class="hint" style="margin-top:6px">Records that you sent it, without moving the card. Use this for anything you apply to from another column.</p>

    <h3>Move to</h3>
    <select onchange="move('${j.num}', this.value)">
      ${COLUMNS.map(([k,l]) => `<option value="${k}" ${k===cur?'selected':''}>${l}</option>`).join('')}
    </select>
    <h3>Research notes (from Claude)</h3><pre>${esc(j.notes)}</pre>
    <div class="path">${esc(j.folder)}</div>`;
  d.classList.add('on'); document.getElementById('scrim').classList.add('on');
}
async function move(num, target) {
  await saveStatus(num, target);
  openDrawer(num);
}
function closeDrawer() {
  document.getElementById('drawer').classList.remove('on');
  document.getElementById('scrim').classList.remove('on');
}
// ---- add job ----------------------------------------------------------------
function addFields() {
  return {
    company: document.getElementById('a_co').value.trim(),
    role: document.getElementById('a_ro').value.trim(),
    url: document.getElementById('a_url').value.trim()
  };
}
function refreshAdd() {
  const f = addFields();
  const ready = f.company && f.role;
  document.getElementById('a_cmd').textContent = ready
    ? `applications/<today>/<next#> - ${f.company} - ${f.role}`
    : 'Enter a company and a role.';
  document.getElementById('a_create').disabled = !ready;
}
function openAdd() {
  document.getElementById('addmodal').classList.add('on');
  document.getElementById('scrim').classList.add('on');
  refreshAdd();
  document.getElementById('a_co').focus();
}
function closeAdd() {
  document.getElementById('addmodal').classList.remove('on');
  document.getElementById('scrim').classList.remove('on');
  ['a_co','a_ro','a_url'].forEach(id => document.getElementById(id).value = '');
}
document.getElementById('addbtn').onclick = openAdd;
document.getElementById('a_close').onclick = closeAdd;
['a_co','a_ro','a_url'].forEach(id => document.getElementById(id).oninput = refreshAdd);
document.getElementById('a_create').onclick = async () => {
  const f = addFields();
  if (!f.company || !f.role) return;
  const b = document.getElementById('a_create');
  b.disabled = true; b.textContent = 'Creating...';
  try {
    const r = await fetch('/api/add', {method:'POST',
      headers:{'Content-Type':'application/json'}, body: JSON.stringify(f)});
    const d = await r.json();
    if (!d.ok) { toast(d.message, true); b.disabled = false; b.textContent = 'Create folder'; return; }
    toast('Created ' + d.message);
    closeAdd();
    b.disabled = false; b.textContent = 'Create folder';
    location.reload();
  } catch (e) {
    toast('Not connected. Is dashboard/serve.py running?', true);
    b.disabled = false; b.textContent = 'Create folder';
  }
};

document.getElementById('scrim').onclick = () => { closeDrawer(); closeAdd(); };
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') { closeDrawer(); closeAdd(); }
});
document.getElementById('q').oninput = renderBoard;
renderBoard();
</script></body></html>
"""


def build(jobs):
    html = TEMPLATE
    html = html.replace("%%JOBS%%", json.dumps(jobs, ensure_ascii=False))
    html = html.replace("%%COLUMNS%%", json.dumps(COLUMNS, ensure_ascii=False))
    html = html.replace("%%COUNT%%", str(len(jobs)))
    html = html.replace("%%TODAY%%", date.today().strftime("%d %B %Y"))
    html = html.replace("%%PREPDIR%%",
                        json.dumps(os.path.join(ROOT, "interview preparation")))
    return html


if __name__ == "__main__":
    jobs = collect()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(build(jobs))
    counts = {}
    for j in jobs:
        counts[j["status"]] = counts.get(j["status"], 0) + 1
    print(f"wrote {OUT}")
    for key, label, _ in COLUMNS:
        if counts.get(key):
            print(f"  {label:<16} {counts[key]}")
