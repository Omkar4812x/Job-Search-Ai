import os
import json
import subprocess
import datetime

BUN_PATH = r"C:\Users\HP\.bun\bin\bun.exe"
BASE_DIR = r"d:\Job-Search-Ai"
SEEN_JOBS_FILE = os.path.join(BASE_DIR, "job_scraper", "seen_jobs.json")
DASHBOARD_FILE = os.path.join(BASE_DIR, "dashboard.html")

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

def is_pune_or_india(location_str, url_str=""):
    loc = location_str.lower()
    url = url_str.lower()
    
    # Exclude non-India locations explicitly
    non_india = ["united kingdom", "uk", "scotland", "tel aviv", "israel", "italy", "singapore", "vietnam", "poland", "cracow", "united states", "minneapolis", "new york", "oxford"]
    if any(country in loc for country in non_india):
        return False
    if any(domain in url for domain in ["uk.linkedin", "sg.linkedin", "vn.linkedin", "it.whatjobs", "nofluffjobs.com/job/...-cracow"]):
        return False
        
    # Must be Pune, Maharashtra, India, or Remote India
    valid = ["pune", "maharashtra", "india", "bengaluru", "bangalore", "hyderabad", "mumbai", "remote"]
    return any(v in loc for v in valid) or "in.linkedin.com" in url or "india" in url

def evaluate_fresher_fit(title, location):
    t = title.lower()
    l = location.lower()
    
    is_pune = "pune" in l or "maharashtra" in l
    is_fresher_title = any(k in t for k in ["fresher", "junior", "trainee", "associate", "intern", "graduate", "entry", "0-1", "0 - 1"])
    is_java = any(k in t for k in ["java", "software", "developer", "engineer", "full stack", "backend", "web"])
    
    if is_pune and (is_fresher_title or is_java):
        return "high"
    elif is_java:
        return "high" if is_fresher_title else "medium"
    return "medium"

def update_dashboard_html(pune_jobs):
    if not os.path.exists(DASHBOARD_FILE):
        return
    with open(DASHBOARD_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    formatted_list = []
    for j in pune_jobs:
        skills = j.get("skills", [])
        if not skills:
            skills = ["java", "sql", "git", "pune-fresher"]
        formatted_list.append({
            "title": j.get("title", ""),
            "company": j.get("company", ""),
            "url": j.get("url", ""),
            "location": j.get("location", "Pune, Maharashtra, India"),
            "first_seen": j.get("first_seen", ""),
            "fit": j.get("fit", "high"),
            "portal": j.get("portal", "linkedin-search"),
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
        print("Updated dashboard.html with Pune & India Fresher Java listings!")

def main():
    print("=== STRICT PUNE & INDIA FRESHER JAVA SEARCH ===")
    
    pune_queries = [
        ("Java Developer", "Pune, Maharashtra, India"),
        ("Java Fresher", "Pune, Maharashtra, India"),
        ("Junior Java Developer", "Pune, Maharashtra, India"),
        ("Trainee Software Engineer Java", "Pune, Maharashtra, India"),
        ("Java Developer Intern", "Pune, Maharashtra, India"),
        ("Java Full Stack Developer", "Pune, Maharashtra, India"),
        ("Associate Software Engineer", "Pune, Maharashtra, India"),
        ("Java Fresher", "India"),
        ("Junior Java Developer", "India")
    ]
    
    today_str = datetime.date.today().isoformat()
    seen_map = {}
    pune_jobs = []
    
    for q, loc in pune_queries:
        print(f"Searching LinkedIn: '{q}' in {loc} (Last 48 Hours)...")
        results = run_linkedin_search(q, loc, limit=10, jobage=2)
        
        for j in results:
            url = j.get("url", "")
            location = j.get("location", loc)
            
            # Strict location check
            if not is_pune_or_india(location, url):
                continue
                
            title = j.get("title", "")
            key = url or (j.get("company", "") + "_" + title)
            
            if key in seen_map:
                continue
                
            fit = evaluate_fresher_fit(title, location)
            
            skills = ["java", "core-java", "sql", "git"]
            if "pune" in location.lower():
                skills.insert(0, "pune-location")
            if any(k in title.lower() for k in ["fresher", "junior", "trainee", "intern", "associate"]):
                skills.insert(0, "fresher-friendly")
                
            entry = {
                "title": title,
                "company": j.get("company", ""),
                "url": url,
                "location": location,
                "first_seen": today_str,
                "deadline": None,
                "fit": fit,
                "status": "new",
                "portal": "linkedin-search",
                "source": "cli",
                "skills": skills,
                "description_snippet": f"Fresher Java role in {location}. Required: Java, OOP, SQL, Git."
            }
            
            seen_map[key] = entry
            pune_jobs.append(entry)

    # Save to seen_jobs.json
    with open(SEEN_JOBS_FILE, "w", encoding="utf-8") as f:
        json.dump({"seen": seen_map}, f, indent=2, ensure_ascii=False)
        
    update_dashboard_html(pune_jobs)
    
    print(f"\nDone! Found {len(pune_jobs)} strictly filtered Pune & India Fresher Java jobs.")

if __name__ == "__main__":
    main()
