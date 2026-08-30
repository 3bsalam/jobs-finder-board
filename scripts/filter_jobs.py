import os
import re
import sys
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APPS = os.path.join(ROOT, "applications")
PROFILE_PATH = os.path.join(ROOT, "config", "profile.yaml")

def load_profile(profile_path=PROFILE_PATH):
    if not os.path.exists(profile_path):
        raise FileNotFoundError(f"Profile configuration file not found at {profile_path}. Please copy profile.example.yaml to profile.yaml and customize it.")

    profile = {
        "residence": "",
        "disallowed_tech": [],
        "primary_stack": [],
        "disallowed_arrangements": []
    }
    
    with open(profile_path, "r", encoding="utf-8") as fh:
        text = fh.read()
        
        for line in text.split('\n'):
            line = line.strip()
            if line.startswith('residence_country:'):
                val = line.split(':', 1)[1].strip()
                val = val.split('#')[0].strip()
                val = val.strip('\'"')
                if val:
                    profile["residence"] = val
                break
                
        current_list = None
        for line in text.split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            if line.endswith(':'):
                current_list = line[:-1]
                continue
                
            if line.startswith('-') and current_list:
                val = line[1:].strip()
                if '"' in val:
                    val = val[:val.rfind('"')+1]
                elif "'" in val:
                    val = val[:val.rfind("'")+1]
                else:
                    val = val.split('#')[0].strip()
                    
                val = val.strip('\'"')
                
                if current_list == 'disallowed_technologies':
                    profile["disallowed_tech"].append(val)
                elif current_list == 'primary_stack':
                    profile["primary_stack"].append(val)
                elif current_list == 'disallowed_arrangements':
                    profile["disallowed_arrangements"].append(val)

    if not profile["residence"]:
        raise ValueError("Profile must contain a 'residence_country' value.")
    if not profile["primary_stack"]:
        raise ValueError("Profile must contain a 'primary_stack' with at least one item.")
        
    return profile

def update_jobs():
    profile = load_profile()
    residence = profile["residence"]
    disallowed_tech = profile["disallowed_tech"]

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
                
            for arr in profile["disallowed_arrangements"]:
                if arr.lower() not in ["hybrid", "on-site", "country-locked outside egypt", "specific foreign residency only"]:
                    if re.search(rf"\b{re.escape(arr)}\b", content, re.IGNORECASE):
                        reasons.append(f"Disallowed arrangement: {arr}")
            
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
