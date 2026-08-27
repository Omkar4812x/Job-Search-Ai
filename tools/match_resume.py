import os
import json
import subprocess
import datetime

BUN_PATH = r"C:\Users\HP\.bun\bin\bun.exe"
BASE_DIR = r"d:\Job-Search-Ai"
SEEN_JOBS_FILE = os.path.join(BASE_DIR, "job_scraper", "seen_jobs.json")
DASHBOARD_FILE = os.path.join(BASE_DIR, "dashboard.html")

# Omkar's Exact Resume Skills
OMKAR_SKILLS = {
    "languages": ["core java", "java", "sql", "javascript", "html", "css", "wordpress"],
    "concepts": ["oop", "encapsulation", "inheritance", "polymorphism", "abstraction"],
    "backend": ["jdbc", "servlets", "mysql"],
    "tools": ["git", "github", "eclipse", "intellij", "vs code"],
    "education": "bca (9.64 cgpa) / mca pursuing",
    "experience": "java programming intern (vault of code)"
}

def run_linkedin_search(query, location="Pune, Maharashtra, India", limit=10):
    cli_path = os.path.join(BASE_DIR, ".agents", "skills", "linkedin-search", "cli", "src", "cli.ts")
    cmd = [BUN_PATH, "run", cli_path, "search", "-q", query, "-l", location, "--jobage", "7", "--limit", str(limit), "--format", "json"]
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

def calculate_resume_match(job_title, job_desc="", job_skills=[]):
    text = (job_title + " " + job_desc + " " + " ".join(job_skills)).lower()
    
    matches = []
    for category in ["languages", "backend", "tools"]:
        for skill in OMKAR_SKILLS[category]:
            if skill in text:
                matches.append(skill.title())
                
    if "fresher" in text or "junior" in text or "trainee" in text or "intern" in text:
        matches.append("Fresher/Junior Eligible")
        
    score = len(set(matches))
    return matches, score

def main():
    print("=== DEDICATED RESUME ALIGNMENT SEARCH FOR OMKAR BHANDALKAR ===")
    
    # Specific queries matching Omkar's exact projects and technologies
    queries = [
        ("Core Java Developer", "Pune, Maharashtra, India"),
        ("Java Web Developer", "Pune, Maharashtra, India"),
        ("Junior Java Developer", "Pune, Maharashtra, India"),
        ("Java MySQL Developer", "Pune, Maharashtra, India"),
        ("HTML CSS JavaScript Developer", "Pune, Maharashtra, India"),
        ("WordPress Developer", "Pune, Maharashtra, India"),
        ("Java Trainee", "Pune, Maharashtra, India"),
        ("Java Developer Intern", "Pune, Maharashtra, India")
    ]
    
    today_str = datetime.date.today().isoformat()
    matched_jobs = []
    seen_urls = set()
    
    for q, loc in queries:
        print(f"Searching for: '{q}' in {loc}...")
        results = run_linkedin_search(q, loc, limit=8)
        
        for j in results:
            url = j.get("url", "")
            if url in seen_urls:
                continue
            seen_urls.add(url)
            
            title = j.get("title", "")
            company = j.get("company", "")
            location = j.get("location", loc)
            
            matched_skills, score = calculate_resume_match(title, j.get("description", ""), j.get("skills", []))
            
            # Ensure Core Java / Web Dev / Fresher relevance
            if score >= 1 or "java" in title.lower() or "developer" in title.lower() or "web" in title.lower():
                matched_jobs.append({
                    "title": title,
                    "company": company,
                    "url": url,
                    "location": location,
                    "first_seen": today_str,
                    "fit": "high" if score >= 2 else "medium",
                    "portal": "linkedin-search",
                    "matched_resume_skills": list(set(matched_skills)),
                    "snippet": f"Role matching Omkar's skills: {', '.join(set(matched_skills)) if matched_skills else 'Java/Web Development'}"
                })
                
    # Update dashboard.html with exact resume matches
    if os.path.exists(DASHBOARD_FILE):
        with open(DASHBOARD_FILE, "r", encoding="utf-8") as f:
            content = f.read()
            
        formatted_list = []
        for j in matched_jobs:
            formatted_list.append({
                "title": j["title"],
                "company": j["company"],
                "url": j["url"],
                "location": j["location"],
                "first_seen": j["first_seen"],
                "fit": j["fit"],
                "portal": j["portal"],
                "skills": j["matched_resume_skills"] if j["matched_resume_skills"] else ["Core Java", "SQL", "HTML/CSS"],
                "snippet": j["snippet"]
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

    print(f"\nDone! Evaluated and matched {len(matched_jobs)} job postings directly against Omkar's resume.")

if __name__ == "__main__":
    main()
