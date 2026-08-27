import os
import json
import subprocess
import datetime

BUN_PATH = r"C:\Users\HP\.bun\bin\bun.exe"
BASE_DIR = r"d:\Job-Search-Ai"
SEEN_JOBS_FILE = os.path.join(BASE_DIR, "job_scraper", "seen_jobs.json")
DASHBOARD_FILE = os.path.join(BASE_DIR, "dashboard.html")

def load_seen_jobs():
    if os.path.exists(SEEN_JOBS_FILE):
        try:
            with open(SEEN_JOBS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"seen": {}}

def save_seen_jobs(data):
    os.makedirs(os.path.dirname(SEEN_JOBS_FILE), exist_ok=True)
    with open(SEEN_JOBS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def run_linkedin_search(query, location, limit=10, jobage=2):
    cli_path = os.path.join(BASE_DIR, ".agents", "skills", "linkedin-search", "cli", "src", "cli.ts")
    cmd = [BUN_PATH, "run", cli_path, "search", "-q", query, "-l", location, "--jobage", str(jobage), "--limit", str(limit), "--format", "json"]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8", errors="ignore")
    if proc.returncode == 0 and proc.stdout:
        try:
            return json.loads(proc.stdout).get("results", [])
        except Exception:
            pass
    return []

def run_freehire_search(query, limit=10):
    cli_path = os.path.join(BASE_DIR, ".agents", "skills", "freehire-search", "cli", "src", "cli.ts")
    cmd = [BUN_PATH, "run", cli_path, "search", "-q", query, "--limit", str(limit), "--format", "json"]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8", errors="ignore")
    if proc.returncode == 0 and proc.stdout:
        try:
            return json.loads(proc.stdout).get("results", [])
        except Exception:
            pass
    return []

def evaluate_fit_for_fresher(title, snippet=""):
    t_lower = (title + " " + snippet).lower()
    
    # Highest match if explicitly mentions fresher / entry-level / junior / trainee / intern
    if any(k in t_lower for k in ["fresher", "trainee", "entry level", "junior", "intern", "associate", "graduate"]):
        return "high"
    elif any(k in t_lower for k in ["java", "software developer", "full stack"]):
        return "high"
    return "medium"

def update_dashboard_html(all_jobs):
    if not os.path.exists(DASHBOARD_FILE):
        return
    with open(DASHBOARD_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    formatted_list = []
    for j in all_jobs:
        skills = j.get("skills", [])
        if not skills:
            skills = ["java", "sql", "git", "fresher-friendly"]
        formatted_list.append({
            "title": j.get("title", ""),
            "company": j.get("company", ""),
            "url": j.get("url", ""),
            "location": j.get("location", "Pune / Remote"),
            "first_seen": j.get("first_seen", ""),
            "fit": j.get("fit", "high"),
            "portal": j.get("portal", "cli"),
            "skills": skills,
            "snippet": (j.get("description_snippet", "") or j.get("title", ""))[:200].replace("\n", " ").replace('"', "'")
        })

    js_str = json.dumps(formatted_list, indent=6, ensure_ascii=False)
    
    start_marker = "const jobData = ["
    end_marker = "];\n\n    // DOM Elements"
    
    if start_marker in content and end_marker in content:
        start_idx = content.find(start_marker)
        end_idx = content.find(end_marker)
        new_content = content[:start_idx] + "const jobData = " + js_str + content[end_idx + 1:]
        with open(DASHBOARD_FILE, "w", encoding="utf-8") as f:
            f.write(new_content)
        print("Updated dashboard.html with fresh Fresher Java listings!")

def main():
    seen_data = load_seen_jobs()
    seen_map = seen_data.get("seen", {})
    
    print("--- Tailored Fresher Search for Omkar Bhandalkar (Java Fresher / Pune & India - Last 48 Hours) ---")
    
    # Fresher-specific target queries
    fresher_queries = [
        ("linkedin-search", "Fresher Java Developer", "Pune, Maharashtra, India"),
        ("linkedin-search", "Junior Java Developer", "Pune, Maharashtra, India"),
        ("linkedin-search", "Trainee Software Engineer Java", "Pune, Maharashtra, India"),
        ("linkedin-search", "Java Developer Fresher", "India"),
        ("linkedin-search", "Graduate Engineer Trainee Java", "India"),
        ("linkedin-search", "Java Intern", "Pune, Maharashtra, India"),
        ("freehire-search", "fresher java developer", ""),
        ("freehire-search", "junior java developer", "")
    ]
    
    today_str = datetime.date.today().isoformat()
    
    for portal_name, q, loc in fresher_queries:
        if portal_name == "linkedin-search":
            print(f"Searching LinkedIn: '{q}' in {loc} (Last 48h)...")
            results = run_linkedin_search(q, loc, limit=10, jobage=2)
        else:
            print(f"Searching Freehire: '{q}'...")
            results = run_freehire_search(q, limit=10)
            
        for j in results:
            url = j.get("url", "")
            key = url or (j.get("company", "") + "_" + j.get("title", ""))
            
            title = j.get("title", "")
            fit = evaluate_fit_for_fresher(title, j.get("description", ""))
            
            skills = j.get("skills", [])
            if "fresher" not in [s.lower() for s in skills]:
                skills.insert(0, "fresher-eligible")
            
            entry = {
                "title": title,
                "company": j.get("company", ""),
                "url": url,
                "location": j.get("location", loc or "Pune / Remote"),
                "first_seen": today_str,
                "deadline": None,
                "fit": fit,
                "status": "new",
                "portal": portal_name,
                "source": "cli",
                "skills": skills,
                "description_snippet": j.get("description", title)
            }
            
            seen_map[key] = entry

    seen_data["seen"] = seen_map
    save_seen_jobs(seen_data)
    
    all_jobs = list(seen_map.values())
    update_dashboard_html(all_jobs)
    
    print(f"\nDone! Processed {len(all_jobs)} Fresher-focused jobs for Omkar Bhandalkar.")

if __name__ == "__main__":
    main()
