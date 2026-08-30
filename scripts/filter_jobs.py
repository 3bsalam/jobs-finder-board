import os
import re
import sys
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APPS = os.path.join(ROOT, "applications")
PROFILE_PATH = os.path.join(ROOT, "config", "profile.yaml")

def load_profile():
    residence = "Egypt"
    disallowed_tech = ["AWS"]
    
    if os.path.exists(PROFILE_PATH):
        try:
            with open(PROFILE_PATH, "r", encoding="utf-8") as fh:
                text = fh.read()
                m_country = re.search(r'residence_country:\s*["\']?([^"\n\r]+)["\']?', text)
                if m_country:
                    residence = m_country.group(1).strip()
                
                # Check disallowed tech
                m_tech = re.findall(r'-\s*["\']?([^"\n\r#]+)["\']?', text)
                if m_tech:
                    # Look under disallowed_technologies section if possible
                    sec = re.search(r'disallowed_technologies:\s*\n((?:\s*-\s*.+\n?)+)', text)
                    if sec:
                        disallowed_tech = [t.strip().strip('"\'') for t in re.findall(r'-\s*["\']?([^"\n\r#]+)["\']?', sec.group(1))]
        except Exception:
            pass
            
    return residence, disallowed_tech

def update_jobs():
    residence, disallowed_tech = load_profile()

    for datedir in sorted(os.listdir(APPS)):
        if not re.match(r"^\d{2}\.\d{2}\.\d{2}$", datedir):
            continue
        for folder in os.listdir(os.path.join(APPS, datedir)):
            p = os.path.join(APPS, datedir, folder)
            if not os.path.isdir(p):
                continue
            
            # Extract job number
            m = re.match(r"^(\d+)\s*-\s", folder)
            if not m:
                continue
            num = int(m.group(1))
            
            job_url_path = os.path.join(p, "JOB-URL.txt")
            notes_path = os.path.join(p, "NOTES.md")
            
            content = folder + " "
            if os.path.exists(job_url_path):
                content += open(job_url_path, errors="ignore").read() + " "
            if os.path.exists(notes_path):
                content += open(notes_path, errors="ignore").read() + " "
                
            # Current status check
            status_match = re.search(r"^Status:\s*(.+)$", content, re.M)
            if status_match and status_match.group(1).strip() == "not_eligible":
                continue # Already not eligible
                
            reasons = []
            for tech in disallowed_tech:
                if re.search(rf"\b{re.escape(tech)}\b", content, re.IGNORECASE):
                    reasons.append(f"Requires {tech} (disallowed in candidate profile)")
            
            if re.search(r"\b(hybrid|on-site|onsite|office based)\b", content, re.IGNORECASE):
                reasons.append("Not fully remote (mentions hybrid/on-site/office)")
            if re.search(r"\b(based in uk|uk resident|uk only|uk & i|uk based)\b", content, re.IGNORECASE):
                reasons.append(f"Restricted to UK location (candidate is resident in {residence})")
            
            if reasons:
                print(f"Job {num} ({folder}) failing because: {', '.join(reasons)}")
                # set status
                subprocess.run([sys.executable, os.path.join(ROOT, "dashboard", "set_status.py"), str(num), "not_eligible"], check=True)
                
                # prepend reason to notes
                if os.path.exists(notes_path):
                    old_notes = open(notes_path, errors="ignore").read()
                    with open(notes_path, "w", encoding="utf-8") as fh:
                        fh.write(f"**AI Filtered as not_eligible**: {', '.join(reasons)}\n\n" + old_notes)

if __name__ == "__main__":
    update_jobs()
