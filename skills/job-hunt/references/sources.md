# Search sources

**Rank these by what has actually produced an eligible role, not by traffic.**
Replace the contents with your own findings as you go; the value of this file is
that it is specific to your situation.

## Tier 1: reliable location data

Applicant tracking systems, read on the employer's own board rather than through
an aggregator. Per-posting location tends to be accurate because the employer
set it.

- **Ashby**: `https://jobs.ashbyhq.com/<company>`
- **Greenhouse**: `https://job-boards.greenhouse.io/<company>/jobs/<id>`
- **Lever**: `https://jobs.lever.co/<company>`
- **Breezy**: `https://<company>.breezy.hr`, shows "Remote (Any Location)"
  explicitly when it is true
- **The employer's own careers page**, always, as the final check

## Tier 2: direct-from-employer sources

**Hacker News "Who is hiring", monthly.** The highest-yield source found. Its
posting rule solves the staffing-agency problem outright: *"only from people
personally part of the hiring company, no recruiting firms or job boards."*

Query it through the Algolia API rather than reading by hand. **It must be
HTTPS**; plain http returns an empty body.

```
https://hn.algolia.com/api/v1/search?tags=comment,story_<ID>&query=<stack>&hitsPerPage=60
https://hn.algolia.com/api/v1/search?tags=comment,story_<ID>&query=worldwide&hitsPerPage=40
```

Query "worldwide" and "anywhere" as well as your stack. Scope is what gates you,
not keywords.

## Tier 3: aggregators, do not trust the location tag

LinkedIn and Indeed via Apify. Good for breadth, dominated by staffing
intermediaries and country-scoped roles. Useful for discovering that a role
exists; worthless as evidence of eligibility.

Remote job boards frequently mis-tag country-locked roles as worldwide. Always
follow the "Apply" link to the employer before believing anything.

## Deprioritised: vetted talent networks

Track your own hit rate here before investing time. These networks screen on
demonstrable public work, which is a poor fit if most of your work sits in
private repositories. A cover letter can carry that evidence; a network profile
usually cannot.

## Search phrases that work

```
"work from anywhere" <stack>
"anywhere in the world" <stack>
"remote (any location)" <stack>
<stack> EMEA remote
<stack> contractor B2B remote
"employer of record" <stack>
```

**The contractor and B2B phrasing is the highest-signal filter of all.** It
removes the employment-entity problem, which is what actually blocks
cross-border hiring.

## Keep a log

Record what you searched, how many results, and how many were genuinely
eligible. Without those numbers you cannot tell a bad source from a bad week,
and you will keep re-running searches that have never once produced a lead.
