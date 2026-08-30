import os
import json
import time
import urllib.request
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKEN = os.getenv("APIFY_TOKEN")

def start_run():
    url = f"https://api.apify.com/v2/acts/curious_coder~linkedin-jobs-scraper/runs?token={TOKEN}"
    payload = {
        "keywords": ".NET remote worldwide contractor -AWS Azure",
        "location": "Remote",
        "datePosted": "pastWeek",
        "limitPerSource": 5,
        "scrapeCompany": False
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    print("Starting Apify run...")
    with urllib.request.urlopen(req) as response:
        res = json.loads(response.read().decode())
        return res["data"]["id"], res["data"]["defaultDatasetId"]

def wait_for_run(run_id):
    url = f"https://api.apify.com/v2/actor-runs/{run_id}?token={TOKEN}"
    while True:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read().decode())
            status = res["data"]["status"]
            print(f"Run status: {status}")
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

def main():
    try:
        run_id, dataset_id = start_run()
        print(f"Run ID: {run_id}, Dataset ID: {dataset_id}")
        
        if wait_for_run(run_id):
            items = fetch_dataset(dataset_id)
            print(f"Fetched {len(items)} jobs.")
            
            for item in items:
                company = item.get("companyName", "Unknown")
                title = item.get("title", "Unknown Role")
                url = item.get("url", "")
                
                # Double check eligibility gate logic
                # Just adding them to board so the user can see them
                print(f"Adding: {company} - {title}")
                cmd = [sys.executable, os.path.join(ROOT, "dashboard", "add_job.py"), company, title, url]
                subprocess.run(cmd, check=False)
        else:
            print("Run failed.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
