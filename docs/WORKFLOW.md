# The workflow

Five steps, in order. Steps 2 and 5 are the ones people skip, and skipping
either means the board lies to you.

```
   SEARCH  ->  ELIGIBILITY GATE  ->  FIT ANALYSIS  ->  PREPARE  ->  APPLY
             (the expensive filter)
```

---

## 1. Search

Run the connectors, or read a direct source. See [APIFY.md](APIFY.md).

**Search on scope, not job title.** The phrase that decides whether you can take
a job is rarely in the title. Queries built around scope words consistently
outperform ones built around seniority or stack:

```
"<stack> remote worldwide contractor"
"work from anywhere" <stack>
"anywhere in the world" <stack>
"remote (any location)" <stack>
<stack> EMEA remote
<stack> contractor B2B remote
```

**The single highest-signal phrase is an employer-of-record statement.** A
posting that says "we hire through an EOR", or names Deel, Remote.com or Oyster,
has already solved the legal problem that actually blocks cross-border hiring.
That is worth more than any number of "remote" tags.

## 2. The eligibility gate

**This is the step that saves entire evenings, and it comes before any
enthusiasm about fit.**

Open the employer's own page and read the location text. Not the aggregator's
tag. Not the board's badge. The employer's own words.

Aggregators mis-tag country-locked roles as worldwide routinely. In one week of
real use, five roles tagged "Anywhere in the World" were US-only on the
employer's page.

Ask three questions:

1. **Can they legally engage someone resident where I live?** Employee via an
   entity or EOR, or independent contractor (see `config/profile.yaml`). If the answer is "only with a visa",
   stop here. Must be 100% remote with no office visits required.
2. **Is the time zone workable, honestly?** Not "I could manage", but would you
   keep it up for a year.
3. **Is the primary language of the codebase one I actually work in?** This is
   the quiet killer. Roles routinely pass the location gate and then fail on
   stack, so check it at the gate (see stack constraints in `config/profile.yaml`).

Record the verdict in `JOB-URL.txt` **as a quote from the posting**, so future
you can see the evidence rather than trusting past you.

## 3. Fit analysis

Only for roles that passed the gate.

Write the requirements as a list and mark each one: met with proof, partly met,
or not met. Be honest in writing, because that list becomes the cover letter,
and a gap you have named is one you can address rather than be caught by.

Judge the responsibilities, not just the title. A role called "Senior" that asks
the holder to mentor a team is a different job from the one the title suggests.

## 4. Prepare

```bash
python3 dashboard/add_job.py "Company" "Role" "https://apply.url"
```

Creates the next globally numbered folder under today's date, writes a
`JOB-URL.txt` skeleton, and refuses a company already on the board.

Then fill in `JOB-URL.txt`, write `NOTES.md`, and build the documents into the
same folder. Filenames stay consistent across every folder, because the folder
already carries the company name; putting it in the filename too means one day
attaching the wrong one.

Set `Status: ready` when the documents exist.

## 5. Apply, and record it

Move the card to **applied** on the board, or:

```bash
python3 dashboard/set_status.py 42 applied
```

Then rebuild:

```bash
python3 dashboard/build.py
```

**A folder on disk that is not on the board is invisible.** That is how
applications get forgotten.

---

## Statuses

| Value | Meaning |
|---|---|
| `to_prepare` | Folder exists, no documents yet |
| `ready` | Documents built, not sent |
| `applied` | Submitted |
| `interview` | They replied and want to talk |
| `offer` | Offer received |
| `rejected` | They turned you down |
| `not_eligible` | **They cannot take you**: location, sponsorship, stack. Never a judgement on your work |
| `skipped` | **You decided against it**: pay, platform, not interested |

**Keep `rejected` and `not_eligible` separate.** Collapsing them hides the most
useful pattern in the data. A pile of `not_eligible` means your search is aimed
wrong; a pile of `rejected` means your application is landing wrong. Those need
opposite responses, and you cannot tell them apart if they share a column.

## Habits worth keeping

**Check for duplicates before creating a folder.** `add_job.py` refuses a
repeat, but run `scripts/build_applied_index.py` and read the index too.
Applying twice to one company is worse than not applying.

**Keep dead entries.** Put the reason in the folder name:
`22 - Example Corp - NOT ELIGIBLE US ONLY`. Otherwise you will rediscover the
same dead end in a month.

**Write down why you rejected something.** In six months "I skipped this" is
useless and "on-site only, verified on their page" is a decision you can trust.
