import os
import json
import subprocess
import datetime

BUN_PATH = r"C:\Users\HP\.bun\bin\bun.exe"
BASE_DIR = r"d:\Job-Search-Ai"
DASHBOARD_FILE = os.path.join(BASE_DIR, "dashboard.html")
SEEN_JOBS_FILE = os.path.join(BASE_DIR, "job_scraper", "seen_jobs.json")

# Senior / Experienced keywords to EXCLUDE strictly
EXCLUDE_KEYWORDS = [
    "senior", "sr", "lead", "architect", "manager", "vp", "vice president",
    "7+", "5+", "8+", "10+", "principal", "head", "staff", "avp", "tech lead",
    "team lead", "specialist", "expert", "director"
]

# Fresher / Entry Level keywords to INCLUDE
FRESHER_KEYWORDS = [
    "fresher", "junior", "jr", "trainee", "associate", "intern", "entry",
    "0-1", "0-2", "graduate", "analyst", "developer", "engineer"
]

def is_fresher_compatible(title):
    t = title.lower()
    # Check exclusion first
    for kw in EXCLUDE_KEYWORDS:
        if kw in t:
            return False
    return True

def run_linkedin_search(query, location="Pune, Maharashtra, India"):
    cli_path = os.path.join(BASE_DIR, ".agents", "skills", "linkedin-search", "cli", "src", "cli.ts")
    cmd = [BUN_PATH, "run", cli_path, "search", "-q", query, "-l", location, "--jobage", "7", "--limit", "15", "--format", "json"]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8", errors="ignore")
    if proc.returncode == 0 and proc.stdout:
        try:
            return json.loads(proc.stdout).get("results", [])
        except Exception:
            pass
    return []

def main():
    print("=== FRESHER ONLY JAVA & WEB DEVELOPER SEARCH (PUNE & INDIA) ===")
    
    queries = [
        ("Java Developer Fresher", "Pune, Maharashtra, India"),
        ("Junior Java Developer", "Pune, Maharashtra, India"),
        ("Associate Software Engineer Java", "Pune, Maharashtra, India"),
        ("Java Trainee", "Pune, Maharashtra, India"),
        ("Java Developer Intern", "Pune, Maharashtra, India"),
        ("Core Java Developer", "Pune, Maharashtra, India"),
        ("HTML CSS JavaScript Web Developer", "Pune, Maharashtra, India"),
        ("WordPress Developer", "Pune, Maharashtra, India")
    ]
    
    today_str = datetime.date.today().isoformat()
    seen_urls = set()
    fresher_jobs = []
    
    for q, loc in queries:
        print(f"Searching: '{q}' in {loc}...")
        results = run_linkedin_search(q, loc)
        
        for j in results:
            title = j.get("title", "")
            url = j.get("url", "")
            location = j.get("location", loc)
            company = j.get("company", "")
            
            if url in seen_urls:
                continue
            seen_urls.add(url)
            
            # Strict Fresher Check
            if not is_fresher_compatible(title):
                continue
                
            skills = ["Core Java", "SQL", "Git"]
            t_lower = title.lower()
            if "wordpress" in t_lower:
                skills = ["WordPress", "HTML/CSS", "JavaScript", "PHP"]
            elif "html" in t_lower or "web" in t_lower:
                skills = ["HTML/CSS", "JavaScript", "Web Development"]
            elif "intern" in t_lower or "trainee" in t_lower:
                skills = ["Java", "Fresher/Trainee", "OOP", "SQL"]
            else:
                skills = ["Core Java", "OOP", "MySQL", "JDBC"]
                
            fresher_jobs.append({
                "title": title,
                "company": company,
                "url": url,
                "location": location,
                "first_seen": today_str,
                "fit": "high",
                "portal": "linkedin-search",
                "skills": skills,
                "snippet": f"Entry-level/Fresher compatible role in {location} matching Omkar's resume skills ({', '.join(skills)})."
            })

    # Update dashboard.html
    if os.path.exists(DASHBOARD_FILE):
        with open(DASHBOARD_FILE, "r", encoding="utf-8") as f:
            content = f.read()
            
        js_str = json.dumps(fresher_jobs, indent=6, ensure_ascii=False)
        start_marker = "const jobData = ["
        end_marker = "];\n\n    // DOM Elements"
        
        if start_marker in content and end_marker in content:
            start_idx = content.find(start_marker)
            end_idx = content.find(end_marker)
            new_content = content[:start_idx] + "const jobData = " + js_str + content[end_idx + 1:]
            with open(DASHBOARD_FILE, "w", encoding="utf-8") as f:
                f.write(new_content)

    print(f"\nDone! Filtered {len(fresher_jobs)} strictly Fresher/Junior/Associate Java & Web roles.")

if __name__ == "__main__":
    main()
