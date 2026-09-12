"""Search for jobs via the Apify LinkedIn scraper and add matches to the board.

Can be run standalone:
    python scripts/search_apify_jobs.py

Or imported by dashboard/serve.py to power the UI "Search jobs" button.
"""
import os
import json
import time
import urllib.request
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
sys.path.insert(0, os.path.join(ROOT, "dashboard"))
from filter_jobs import load_profile

TOKEN = os.getenv("APIFY_TOKEN")

# ---------------------------------------------------------------------------
# Config loaders
# ---------------------------------------------------------------------------

def load_connectors():
    """Parse connectors.yaml with the same minimal YAML reader the project uses."""
    path = os.path.join(ROOT, "config", "connectors.yaml")
    if not os.path.exists(path):
        return {}

    with open(path, "r", encoding="utf-8") as fh:
        text = fh.read()

    # Extract the linkedin searches block
    searches = []
    in_linkedin = False
    current = None
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("#") or not stripped:
            continue
        if stripped == "linkedin:":
            in_linkedin = True
            continue
        if in_linkedin:
            # End of linkedin block if we hit a non-indented, non-list key
            if not line.startswith(" ") and not line.startswith("\t") and ":" in stripped:
                break
            if stripped.startswith("- keywords:"):
                if current:
                    searches.append(current)
                val = stripped.split(":", 1)[1].strip().strip("'\"")
                current = {"keywords": val}
            elif current and ":" in stripped:
                key, val = stripped.split(":", 1)
                key = key.strip()
                val = val.strip().strip("'\"")
                if key == "limitPerSource":
                    val = int(val)
                elif key == "scrapeCompany":
                    val = val.lower() == "true"
                current[key] = val
    if current:
        searches.append(current)

    return searches


def load_enabled_connector():
    """Return the actor_id for the first enabled apify connector."""
    path = os.path.join(ROOT, "config", "connectors.yaml")
    if not os.path.exists(path):
        return "curious_coder~linkedin-jobs-scraper"

    with open(path, "r", encoding="utf-8") as fh:
        text = fh.read()

    # Find first enabled connector's actor_id
    current_connector = None
    enabled = False
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("#") or not stripped:
            continue
        if stripped.startswith("apify-") and stripped.endswith(":"):
            current_connector = stripped[:-1]
            enabled = False
        elif current_connector and stripped.startswith("enabled:"):
            enabled = stripped.split(":", 1)[1].strip().lower() == "true"
        elif current_connector and enabled and stripped.startswith("actor_id:"):
            actor = stripped.split(":", 1)[1].strip().strip("'\"")
            # Apify API uses ~ instead of /
            return actor.replace("/", "~")

    return "curious_coder~linkedin-jobs-scraper"


# ---------------------------------------------------------------------------
# Apify API
# ---------------------------------------------------------------------------

def start_run(search_params, actor_id=None):
    """Start an Apify actor run with the given search parameters."""
    if not TOKEN:
        raise RuntimeError("APIFY_TOKEN environment variable is not set. "
                           "Add it to .env or export it.")
    if actor_id is None:
        actor_id = load_enabled_connector()

    url = f"https://api.apify.com/v2/acts/{actor_id}/runs?token={TOKEN}"
    payload = {
        "keywords": search_params.get("keywords", ""),
        "location": search_params.get("location", "Remote"),
        "datePosted": search_params.get("datePosted", "pastWeek"),
        "limitPerSource": search_params.get("limitPerSource", 5),
        "scrapeCompany": search_params.get("scrapeCompany", False),
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req) as response:
        res = json.loads(response.read().decode())
        return res["data"]["id"], res["data"]["defaultDatasetId"]


def wait_for_run(run_id, on_progress=None):
    """Poll until the run finishes. Returns True on success."""
    url = f"https://api.apify.com/v2/actor-runs/{run_id}?token={TOKEN}"
    while True:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read().decode())
            status = res["data"]["status"]
            if on_progress:
                on_progress(f"Run status: {status}")
            if status == "SUCCEEDED":
                return True
            elif status in ["FAILED", "ABORTED", "TIMED-OUT"]:
                return False
        time.sleep(5)


def fetch_dataset(dataset_id):
    url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={TOKEN}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode())


def extract_job_url(item):
    """Extract job posting URL from an Apify dataset item dict."""
    if not isinstance(item, dict):
        return ""
    candidates = [
        "link", "url", "jobUrl", "applyUrl", "linkedinUrl",
        "job_url", "jobPostingUrl", "externalApplyLink",
        "externalUrl", "linkUrl"
    ]
    for key in candidates:
        val = item.get(key)
        if val and isinstance(val, str) and val.strip().startswith("http"):
            return val.strip()

    job_id = item.get("id") or item.get("jobId")
    if job_id and str(job_id).isdigit():
        return f"https://www.linkedin.com/jobs/view/{job_id}"

    return ""


# ---------------------------------------------------------------------------
# Main search orchestrator
# ---------------------------------------------------------------------------

def run_search(on_progress=None):
    """Run all configured LinkedIn searches and add results to the board.

    on_progress(message: str) is called at each step so the UI can show status.
    Returns a dict with summary stats.
    """
    # Late import so the module can be loaded without dashboard on sys.path
    import add_job as board_add

    def log(msg):
        print(msg)
        if on_progress:
            on_progress(msg)

    if not TOKEN:
        msg = "APIFY_TOKEN not set. Add it to .env and restart the server."
        log(msg)
        return {"error": msg, "added": 0, "skipped": 0, "total": 0}

    profile = load_profile()
    searches = load_connectors()

    # Fall back to a profile-derived search if connectors.yaml has no searches
    if not searches:
        keywords = " ".join(profile["primary_stack"])
        keywords += " remote worldwide contractor"
        if profile["disallowed_tech"]:
            keywords += " -" + " -".join(profile["disallowed_tech"])
        searches = [{
            "keywords": keywords,
            "location": "Remote",
            "datePosted": "pastWeek",
            "limitPerSource": 5,
        }]

    actor_id = load_enabled_connector()
    all_items = []
    total_searches = len(searches)

    for idx, search in enumerate(searches, 1):
        log(f"[{idx}/{total_searches}] Starting search: {search['keywords'][:60]}...")
        try:
            run_id, dataset_id = start_run(search, actor_id)
            log(f"[{idx}/{total_searches}] Run started (ID: {run_id}). Waiting...")

            if wait_for_run(run_id, on_progress=on_progress):
                items = fetch_dataset(dataset_id)
                log(f"[{idx}/{total_searches}] Fetched {len(items)} jobs")
                all_items.extend(items)
            else:
                log(f"[{idx}/{total_searches}] Run failed or timed out")
        except Exception as e:
            log(f"[{idx}/{total_searches}] Error: {e}")

    # Deduplicate by URL
    seen_urls = set()
    unique = []
    for item in all_items:
        url = extract_job_url(item)
        if url and url in seen_urls:
            continue
        if url:
            seen_urls.add(url)
        unique.append(item)

    log(f"Found {len(unique)} unique jobs (from {len(all_items)} total)")

    added = 0
    skipped = 0
    for item in unique:
        company = item.get("companyName", "Unknown").strip()
        title = item.get("title", "Unknown Role").strip()
        url = extract_job_url(item)

        if not company or company == "Unknown":
            skipped += 1
            continue

        ok, msg = board_add.create(company, title, url, force=False)
        if ok:
            added += 1
            log(f"  + Added: {company} — {title}")
        else:
            skipped += 1
            log(f"  ~ Skipped: {company} — {msg}")

    log(f"Done! Added {added} new jobs, skipped {skipped}")
    return {"added": added, "skipped": skipped, "total": len(unique), "error": None}


def main():
    run_search()


if __name__ == "__main__":
    main()
