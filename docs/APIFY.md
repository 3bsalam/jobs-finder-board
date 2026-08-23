# Apify actors: setup and use

Apify runs third-party scrapers ("actors") in the cloud. This project uses two,
and both are cheap enough that cost is not a factor in how often you run them.

## 1. Account and credit

1. Create an account at [apify.com](https://apify.com). The free tier includes
   monthly credit that comfortably covers a personal job search.
2. Get your API token from **Settings, Integrations, Personal API tokens**.

**Never commit that token.** Keep it in the environment or in your MCP client's
config, both of which are gitignored here.

```bash
export APIFY_TOKEN="apify_api_..."
```

## 2. Two ways to run an actor

### Through an AI assistant (what this workflow assumes)

Connect Apify's MCP server to your assistant. It exposes `call-actor`,
`fetch-actor-details` and `get-dataset-items`, so the assistant can run a search
and read the results without you copying JSON around.

Add to your MCP client config:

```json
{
  "mcpServers": {
    "apify": {
      "command": "npx",
      "args": ["-y", "@apify/actors-mcp-server"],
      "env": { "APIFY_TOKEN": "your_token_here" }
    }
  }
}
```

### Directly over HTTP

```bash
curl -X POST "https://api.apify.com/v2/acts/curious_coder~linkedin-jobs-scraper/runs?token=$APIFY_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"keywords":"ruby on rails remote worldwide contractor","location":"Remote","datePosted":"pastWeek","limitPerSource":50,"scrapeCompany":false}'
```

Then read the run's dataset:

```bash
curl -s "https://api.apify.com/v2/datasets/<datasetId>/items?token=$APIFY_TOKEN&limit=50"
```

Note the `~` in the actor path over HTTP where the store uses `/`.

## 3. The two actors

### LinkedIn: `curious_coder/linkedin-jobs-scraper`

Scrapes the public jobs page. **No login, no session cookie**, so your own
account is never at risk. This matters: actors that require a logged-in session
can get the account restricted, which costs you the profile and the network.

| Field | Notes |
|---|---|
| `keywords` | Free text. Scope words beat job titles, see below |
| `location` | City, region or country as LinkedIn spells it, or "Remote" |
| `datePosted` | `anyTime`, `past24Hours`, `pastWeek`, `pastMonth` |
| `limitPerSource` | Max results per search |
| `scrapeCompany` | Set `false`. Much faster and you rarely need it |

### Indeed: `valig/indeed-jobs-scraper`

| Field | Notes |
|---|---|
| `country` | ISO alpha-2, lowercase. **One country per run** |
| `title` | Job title or keywords |
| `location` | City, state, zip, or the literal string `"remote"` |
| `limit` | Integer, default 100 |
| `datePosted` | `"1"`, `"3"`, `"7"`, `"14"` days, **as a string** |

Its real value is `baseSalary.min` / `.max` / `.currencyCode` / `.unitOfWork`,
which fills the board's salary column without manual lookup, and the `expired`
flag, which catches dead postings before you spend an evening on one.

## 4. Before you trust an actor

Actors are third-party code and they break silently. Before enabling one:

```
fetch-actor-details -> check it is not deprecated, look at the rating and the
                       last update date, and read the input schema
call-actor          -> run it once with a small limit
```

**Run a query you know should return results.** If a search comes back empty,
you cannot tell whether the market is empty or the actor is broken. Establishing
a known-good baseline first is what makes a later zero meaningful.

## 5. Cost

Both actors are pay-per-event and cost roughly a cent per run at these volumes.
Cost should never be the reason you skip a sweep. Time spent reading bad results
is the real expense, which is why the eligibility gate matters more than the
search.

## 6. Where aggregators fall down

Both are dominated by staffing intermediaries and country-scoped roles. In
practice, direct sources outperform them for anything that needs a specific
eligibility:

- **Hacker News "Who is hiring"**, monthly. Its posting rule is the point:
  *"only from people personally part of the hiring company, no recruiting firms
  or job boards."* Query it through the Algolia API rather than reading by hand,
  and note it must be HTTPS:

  ```
  https://hn.algolia.com/api/v1/search?tags=comment,story_<ID>&query=<stack>&hitsPerPage=60
  https://hn.algolia.com/api/v1/search?tags=comment,story_<ID>&query=worldwide&hitsPerPage=40
  ```

- **The employer's own careers page**, always, as the final check.

Use the actors for breadth and the direct sources for the roles you can actually
take.
