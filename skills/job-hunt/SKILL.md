---
name: job-hunt
description: Find, verify, analyse and prepare remote roles that are genuinely open to this candidate. Use when searching for jobs, checking whether a posting is worth applying to, or working through the to-prepare pile.
---

# Job hunt

Finding roles is easy. Finding roles that will actually engage someone in this
candidate's situation is the hard part, and it is the only part that matters.

**Apply the eligibility gate before doing anything else.** Not after the fit
analysis, and not after the excitement. The gate is cheap and everything after
it is expensive.

## Order of work

```
SEARCH  ->  ELIGIBILITY GATE  ->  FIT ANALYSIS  ->  PREPARE  ->  RECORD
```

Never reorder these. A beautiful cover letter for a role that cannot hire the
candidate is worse than no work at all, because it feels like progress.

## 1. Search

Search on **scope**, not job title. See `references/sources.md` for what has
worked, and keep that file updated with outcomes, including the failures.

Highest-signal query shape:

```
"<stack> remote worldwide contractor"
"work from anywhere" <stack>
"remote (any location)" <stack>
<stack> EMEA remote
```

**The strongest single indicator is an employer-of-record statement.** A posting
that says it hires through an EOR, or names Deel, Remote.com or Oyster, has
already solved the legal problem that blocks cross-border hiring.

## 2. The eligibility gate

**Open the employer's own page. Read the location text there.** An aggregator's
tag is discovery data, never evidence. Country-locked roles are tagged
"worldwide" constantly.

Read candidate constraints from `config/profile.yaml` (private/gitignored) for location, timezone, stack, and hard dealbreakers.

Three questions, all of which must pass:

1. **Can they legally engage someone resident where the candidate lives (`config/profile.yaml`)?**
   Entity, EOR, or independent contractor. "Only with a visa" is a stop. Must be 100% remote with no office visits required.
2. **Is the time zone genuinely sustainable?** Not heroically, routinely (match against timezone in profile).
3. **Is the primary language of the codebase one the candidate works in?**
   This is the quiet killer: roles pass the location gate and fail on stack. Verify requirements against allowed/disallowed stack in `config/profile.yaml`.

Quote the posting verbatim into `JOB-URL.txt`. Evidence, not recollection.

## 3. Fit analysis

List the requirements. Mark each: met with proof, partly met, not met. Write it
down honestly, because that list is the raw material for the cover letter, and a
named gap can be addressed while an unnamed one is a trap.

Judge responsibilities, not titles. A role called "Senior" that asks its holder
to mentor a team is a different job from the one the title implies.

## 4. Prepare

```bash
python3 dashboard/add_job.py "Company" "Role" "https://apply.url"
```

Check for duplicates first. Fill in `JOB-URL.txt` fully, including the quoted
location text and the reply SLA. Build the documents with consistent filenames.

## 5. Record

Move the card, or `python3 dashboard/set_status.py <num> <status>`, then rebuild
the board. **A folder that is not on the board is invisible.**

## Rules that exist because they were learned the hard way

- **Never estimate a number for a CV.** Every figure traces to the candidate's
  source-of-truth file or it does not appear.
- **Keep dead entries** with the reason in the folder name, or the same dead end
  gets rediscovered next month.
- **Separate "they cannot take you" from "they said no."** They call for
  opposite responses, and one column cannot tell you which you are looking at.
- **Blacklist with a reason.** In six months the name alone means nothing.
- **Verify a source before trusting a zero.** An empty result set could be an
  empty market or a broken actor, and those are not the same.
