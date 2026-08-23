# Jobs Finder Board

A local, private job-search board and workflow. Folders on disk are the source
of truth; the board is a view over them.

Built for one specific problem: **applying to remote roles that will not
actually hire you is the biggest waste of time in a job search.** The workflow
puts an eligibility gate before everything else, and the board keeps the answer
where you can see it.

```
applications/                      the truth, one folder per role
  DD.MM.YY/
    NN - Company - Role/
      JOB-URL.txt                  apply link, quoted location rules, Status:
      NOTES.md                     research
      <Name>_Resume.pdf
      <Name>_Cover_Letter.pdf

dashboard/                         a view over the folders
```

## Why local only

Deliberate, for two reasons.

**A public page naming every employer you have approached, with your status at
each, is visible to anyone with the URL, including your current employer.** If
you are job hunting while employed, that page is the one thing that makes it
undeniable.

**Document links only work locally.** Browsers refuse `file://` links from an
`https://` page, so the one-click access to each CV, which is the point of the
board, stops functioning the moment it is hosted.

Keep it in a **private** repository if you want history and a backup.

---

## Install

Requires Python 3.9+. No dependencies for the board itself.

```bash
git clone https://github.com/<you>/jobs-finder-board.git
cd jobs-finder-board
python3 dashboard/serve.py
```

Then open <http://localhost:8765>.

Or double-click **`Start board.command`** in Finder on macOS. If the board is
already running it just opens the tab.

The server binds to `127.0.0.1` only and refuses to serve anything outside the
project directory.

### Optional configuration

```bash
# what substring your CV filenames share, used to detect a "ready" folder
export RESUME_MARKER="Jane_Doe_Resume"

# change the port
export BOARD_PORT=8765
```

### Optional: job-discovery connectors

```bash
cp config/connectors.example.yaml config/connectors.yaml
```

`config/connectors.yaml` is gitignored, because it will end up naming real
companies. See [docs/APIFY.md](docs/APIFY.md).

---

## Using the board

**Drag a card between columns and it saves immediately.** The server writes the
`Status:` line into that job's `JOB-URL.txt` and rebuilds. There is no pending
state and nothing to remember. If the server is not running, the card springs
back and says so, so the board never shows something that is not on disk.

| Control | What it does |
|---|---|
| **+ Add job** | Creates the folder: next global number, today's date, refuses a duplicate company |
| **Card drawer** | Documents, research notes, your own editable notes, applied date |
| **Reveal folder** | Opens it in your file manager |
| **Search** | Company, role, location, notes |
| **Interview prep** | Opens `interview-preparation/`, where reusable prep lives |
| **Delete** | Two-step. Moves to `applications/_deleted/`, never erases |

### Columns

| Status | Meaning |
|---|---|
| `to_prepare` | Folder exists, no documents yet |
| `ready` | Documents built, not sent |
| `applied` | Submitted |
| `interview` | They want to talk |
| `offer` | Offer received |
| `rejected` | They said no |
| `not_eligible` | **They cannot take you**: location, sponsorship, stack |
| `skipped` | **You decided against it**: pay, platform, not interested |

**Keep the last two separate.** A pile of `not_eligible` means your search is
aimed wrong. A pile of `rejected` means your applications are landing wrong.
Those need opposite responses and one column cannot tell you which you have.

---

## Command line

```bash
# add a job: next global number, today's date folder, refuses duplicates
python3 dashboard/add_job.py "Company" "Senior Backend Engineer" "https://apply.url"

# change status, one or many at once
python3 dashboard/set_status.py 42 applied
python3 dashboard/set_status.py 42 applied 43 ready 44 rejected

# rebuild the static board
python3 dashboard/build.py

# rebuild the company index used for duplicate checks
python3 scripts/build_applied_index.py
```

`dashboard/index.html` is generated. Never hand-edit it.

**`serve.py` imports `build` at startup**, so a change to `build.py` needs a
server restart, not just a rebuild. A stale server will happily serve the old
page forever.

---

## The workflow

Full version in **[docs/WORKFLOW.md](docs/WORKFLOW.md)**.

```
SEARCH  ->  ELIGIBILITY GATE  ->  FIT ANALYSIS  ->  PREPARE  ->  APPLY
          (do this one first, always)
```

The gate is three questions, asked against **the employer's own page**, never an
aggregator's tag:

1. Can they legally engage someone resident where you live? Entity, employer of
   record, or independent contractor.
2. Is the time zone sustainable for a year, not just survivable for a week?
3. Is the primary language of the codebase one you actually work in?

That third one is the quiet killer. Roles routinely clear the location gate and
then fail on stack, after you have already written the cover letter.

**The highest-signal phrase in any posting is an employer-of-record statement.**
A company that says it hires through an EOR, or names Deel, Remote.com or
Oyster, has already solved the problem that blocks cross-border hiring. That is
worth more than any number of "remote" badges.

---

## AI assistant skills

The workflow assumes an assistant with skills installed. Full list and install
instructions in **[docs/SKILLS.md](docs/SKILLS.md)**.

- **[`skills/job-hunt/`](skills/job-hunt/)**, bundled here. Encodes the gate-first
  workflow, plus a `references/sources.md` for recording what has actually
  worked, ranked by outcome rather than traffic.
- **[ResumeSkills](https://github.com/Paramchoudhary/ResumeSkills)**, an
  open-source pack of 23 skills for the document work:
  `job-description-analyzer`, `resume-tailor`, `resume-bullet-writer`,
  `resume-ats-optimizer`, `cover-letter-generator`, `application-form-filler`,
  `tech-resume-optimizer`, `interview-prep-generator`, `cold-email-writer`,
  `linkedin-profile-optimizer`, `salary-negotiation-prep`,
  `offer-comparison-analyzer`, `portfolio-case-study-writer`, and more.

**One rule that matters more than any skill:** never let a tool invent a number.
Keep one file with your real figures and verify every CV against it, because an
estimated metric is a claim you cannot defend in an interview.

---

## Job discovery

**[docs/APIFY.md](docs/APIFY.md)** covers running the LinkedIn and Indeed
scrapers through [Apify](https://apify.com), including the MCP setup so an
assistant can run searches and read results directly.

Two things worth knowing before you rely on them:

**Use an actor that scrapes public pages.** Actors requiring a logged-in session
put your own account at risk, and an account restriction costs you the profile
and the network along with it.

**Aggregators are dominated by staffing intermediaries.** For roles with a
specific eligibility requirement, direct sources outperform them consistently.
The **Hacker News "Who is hiring"** thread is the best of them, because its
posting rule is *"only from people personally part of the hiring company, no
recruiting firms or job boards."*

---

## Contributing

The board is deliberately small: four Python files, no dependencies, no
database. Folders on disk are the source of truth and everything else is a view.
Please keep it that way.

## License

MIT. See [LICENSE](LICENSE).
