---
name: inbox-sync
description: Scan the email account you apply with for application confirmations, rejections, interview invites, assessments, offers and applications you sent, then bring the board up to date. Use when the user says "check my email", "update the board from email", or after a batch of manual applications.
---

# Inbox sync

You apply in many places: company sites, LinkedIn, recruiter emails. Almost
every one sends a confirmation email, and every outcome arrives by email too.
This skill reads that mail and makes the board match it, without the user
re-typing anything.

**Read-only on the mailbox. Never send, draft, label, archive or delete mail
while running this skill.** The only writes go through
`scripts/apply_inbox_actions.py`.

## 0. Check you are in the right inbox

People often have the email tool connected to a work account. Before searching,
run one small search (for example the last two days, metadata only) and look at
the recipient address. If it is not the account the user applies with, stop and
say so. Do not report "no updates" from the wrong inbox.

## 1. Search

Use the connected email tool's search. Work in a date window: since the last
sync, or since the job search started for a first run. Paginate until done.

Look for:
- **Confirmations.** Senders from applicant-tracking systems: greenhouse,
  ashbyhq, workable / workablemail, lever, bamboohr, smartrecruiters,
  teamtailor, recruitee, applytojob / jazzhr, personio, breezy, icims,
  myworkday, successfactors, taleo, jobvite, pinpoint, homerun, comeet,
  rippling, join.com, plus company domains. Subjects like "Thank you for
  applying", "Application received", "We received your application", in any
  language.
- **Outcomes.** Rejections ("unfortunately", "not moving forward", "other
  candidates", "decided not to", "position has been filled"), interview
  invitations and scheduling links, assessments and coding challenges, offers.
- **Applications the user sent.** The sent folder: emails to recruiters or
  companies with a CV attached or linked.
- **Meeting recaps**, if the user records calls (for example a notetaker's
  summary email): they often contain next steps and dates worth recording.

Ignore everything that is not about the job search: social, security alerts,
banking, newsletters, job-alert digests, and notifications from the user's own
projects. Do not report them.

## 2. Match against the board

Read `applications/APPLIED-INDEX.md` (run `python3 scripts/build_applied_index.py`
first) and, for matched companies, the `Status:` line in each folder's
`JOB-URL.txt`. Match company names loosely ("Acme Inc" = "Acme", "Foo.io &
Bar" = "Foo.io"). A company already on the board with a different role is a
second role, not a new folder.

## 3. Write the action list

Write a JSON array to `inbox-actions.json` in the repo root (it is gitignored,
because it names companies). One object per finding:

```json
[
  {"action": "set_status", "number": 42, "status": "rejected",
   "evidence": "Ashby | Update on your application | 05.10.26"},
  {"action": "create", "company": "Acme", "role": "Backend Engineer",
   "status": "applied", "applied_on": "28.09.26",
   "evidence": "Greenhouse | Thank you for applying to Acme | 28.09.26"},
  {"action": "note", "number": 17,
   "evidence": "Calendly invite | Intro call | 14.10.26",
   "note": "Intro call booked 16.10.26 14:00. Prepare salary range."}
]
```

- `status`: one of to_prepare, ready, applied, interview, offer, rejected,
  not_eligible, skipped. A confirmation means applied; an assessment or an
  interview invite means interview.
- `evidence`: sender, subject, date. It is what makes re-runs safe, so always
  fill it in.
- `applied_on`: DD.MM.YY, local time. Leave it out when the email does not say.
- `reapplied: true` only when the user applied again after a rejection.
- Never invent a company, role or date. Use "Role not named in email" when the
  email does not say.

## 4. Apply

```bash
python3 scripts/apply_inbox_actions.py inbox-actions.json --dry-run
python3 scripts/apply_inbox_actions.py inbox-actions.json
```

Read the dry run before the real run. The script will not move a status
backwards, will not create a duplicate company folder, adds a follow-up date 14
days after each application, and skips any action whose evidence is already in
the folder, so running it twice is harmless.

## 5. Report

Keep it short: what was created, what changed status, anything that needs the
user (an interview to confirm, an assessment to take, a deadline). Flag what the
email could not tell you (no role named, no date). Point out applications the
inbox cannot see: LinkedIn Easy Apply often sends no email, so those need adding
by hand.
