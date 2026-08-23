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

### With Docker (recommended)

Nothing to install but Docker. No Python version to get right, no dependencies.

```bash
git clone https://github.com/3bsalam/jobs-finder-board.git
cd jobs-finder-board
UID=$(id -u) GID=$(id -g) docker compose up --build
```

Then open <http://localhost:8765>.

**Your data stays on your machine.** `applications/` is bind-mounted from the
host, so the folders are the source of truth exactly as they are without Docker.
Delete the container whenever you like; nothing of yours is inside it.

Passing `UID` and `GID` makes files written by the container belong to you
rather than to root. On macOS Docker Desktop it matters less, but it costs
nothing and saves a permissions problem on Linux.

**One thing does not work in a container:** the **Reveal folder** button. It
shells out to your file manager, and the container has none. Everything else
behaves identically, and `applications/` is right there on your host anyway.

The port is published to `127.0.0.1` only, so the board is not reachable from
your network. `BOARD_HOST=0.0.0.0` inside the container is what lets your host
reach it at all; it is safe *because* of how the port is published. If you edit
`compose.yaml` to publish `8765:8765` instead, you put your entire job search on
your local network.

### Without Docker

Requires Python 3.9+. No dependencies.

```bash
git clone https://github.com/3bsalam/jobs-finder-board.git
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

# bind address. Leave as loopback unless you are in a container and know why.
export BOARD_HOST=127.0.0.1
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

## Three ways to add a job

**1. The board.** Click **+ Add job**, fill in company, role and URL.

**2. The command line.**

```bash
python3 dashboard/add_job.py "Company" "Senior Backend Engineer" "https://apply.url"

# in Docker
docker compose exec board python dashboard/add_job.py "Company" "Role" "https://apply.url"
```

Picks the next global number, files it under today's date, writes a `JOB-URL.txt`
skeleton and refuses a company already on the board.

**3. Hand the link to an AI assistant.**

This is the one the workflow is built around. With the `job-hunt` skill installed
(see [docs/SKILLS.md](docs/SKILLS.md)), paste a job URL and say:

> add this job to the board: https://example.com/careers/senior-backend-engineer

The assistant reads the posting, runs the eligibility gate against the employer's
own page rather than an aggregator's tag, creates the folder, fills `JOB-URL.txt`
with the **quoted** location and contract terms, writes its verdict into
`NOTES.md`, and rebuilds the board.

You can also point it at a search rather than a single role:

> find remote Rails roles posted this week that can hire someone in <country>

which runs the connectors in [docs/APIFY.md](docs/APIFY.md), applies the gate,
and adds only the roles that pass.

The value is not the typing it saves. It is that the assistant checks eligibility
*before* the folder exists, so the board never fills up with roles that were
never open to you.

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
