import json
import sqlite3
from datetime import date, datetime
from urllib.parse import quote_plus

import pandas as pd
import streamlit as st

APP_DIR = __import__("pathlib").Path(__file__).parent
DB_PATH = APP_DIR / "data" / "jobs.db"
PROFILE_PATH = APP_DIR / "profile.json"

DEFAULT_PROFILE = {
    "experience_summary": "19+ years IT; 9+ years DevOps/SRE; 9+ years .NET development; cloud, automation, enterprise modernization and technical leadership.",
    "locations": ["Hyderabad", "Bengaluru", "Remote India"],
    "target_roles": [
        "Platform Engineer", "Platform Engineering Lead", "Platform Engineering Manager",
        "Senior SRE", "Staff SRE", "SRE Engineering Manager", "Lead DevOps Engineer",
        "Principal DevOps Engineer", "Cloud Platform Engineer", "Cloud Architect",
        "Senior Cloud Engineer", "Senior .NET Developer", "Technical Lead", "Engineering Manager"
    ],
    "skills": [
        "Azure", "AWS", "Kubernetes", "AKS", "EKS", "Terraform", "CI/CD",
        "Azure DevOps", "GitHub Actions", "Docker", "Jenkins", "SRE",
        "observability", "Prometheus", "Grafana", "incident management",
        "automation", ".NET", "C#", "ASP.NET Core", "enterprise modernization",
        "ITIL", "technical leadership", "cost optimization", "infrastructure as code",
        "Backstage", "GitOps", "Crossplane"
    ],
    "minimum_salary_lpa": None
}

def load_profile():
    if PROFILE_PATH.exists():
        try:
            return json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    PROFILE_PATH.write_text(json.dumps(DEFAULT_PROFILE, indent=2), encoding="utf-8")
    return DEFAULT_PROFILE.copy()

def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            company TEXT DEFAULT '',
            location TEXT DEFAULT '',
            work_mode TEXT DEFAULT '',
            url TEXT DEFAULT '',
            posted_date TEXT DEFAULT '',
            description TEXT DEFAULT '',
            salary_lpa REAL,
            fit_score INTEGER DEFAULT 0,
            matched_skills TEXT DEFAULT '',
            gaps TEXT DEFAULT '',
            status TEXT DEFAULT 'Saved',
            notes TEXT DEFAULT '',
            added_at TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn

def score_job(title, description, location, profile):
    text = f"{title} {description}".lower()
    skills = profile.get("skills", [])
    matched = [s for s in skills if s.lower() in text]
    missing = [s for s in skills if s.lower() not in text]
    role_words = ["sre", "devops", "platform", "cloud", "site reliability", "engineering manager",
                  "architect", "principal", "staff", ".net", "technical lead", "infrastructure"]
    role_score = min(25, round(25 * sum(1 for w in role_words if w in title.lower()) / 3))
    skill_score = min(45, round(45 * len(matched) / max(1, min(10, len(skills)))))
    loc = (location or "").lower()
    location_score = 15 if any(x in loc for x in ["hyderabad", "bengaluru", "bangalore", "remote", "india"]) else 5
    senior_score = 15 if any(x in title.lower() for x in ["senior", "lead", "principal", "staff", "manager", "architect"]) else 8
    score = max(0, min(100, role_score + skill_score + location_score + senior_score))
    return score, matched, missing[:8]

def search_links():
    queries = [
        "Senior SRE Kubernetes Terraform Hyderabad OR Bengaluru",
        "Platform Engineering Backstage GitOps Crossplane India",
        "Lead DevOps Engineer Azure AWS Kubernetes Terraform India",
        "Cloud Platform Architect Azure AKS Terraform Hyderabad Bengaluru",
        "SRE Engineering Manager India",
        "Senior Staff Engineer Site Reliability India remote",
        "Senior .NET Technical Lead enterprise modernization Hyderabad Bengaluru",
    ]
    sources = {
        "LinkedIn Jobs": "https://www.linkedin.com/jobs/search/?keywords={q}&location=India",
        "Indeed India": "https://in.indeed.com/jobs?q={q}&l=India",
        "Naukri": "https://www.naukri.com/{slug}-jobs",
        "Google Jobs/Search": "https://www.google.com/search?q={q}+jobs",
    }
    rows = []
    for q in queries:
        for name, template in sources.items():
            if name == "Naukri":
                slug = q.lower().replace(" OR ", "-").replace(" ", "-").replace("/", "-")
                url = template.format(slug=quote_plus(slug))
            else:
                url = template.format(q=quote_plus(q))
            rows.append({"Search focus": q, "Source": name, "Open search": url})
    return pd.DataFrame(rows)

st.set_page_config(page_title="AI Job Search Agent", page_icon="🎯", layout="wide")
profile = load_profile()
conn = connect()

st.title("🎯 AI Job Search Agent")
st.caption("Personalized for senior DevOps/SRE, cloud platform, platform engineering, and technology leadership roles.")
with st.sidebar:
    st.header("Your profile")
    st.write("**Experience:**", profile.get("experience_summary", ""))
    st.write("**Target locations:**", ", ".join(profile.get("locations", [])))
    st.write("**Target roles**")
    st.write(", ".join(profile.get("target_roles", [])))
    st.info("Matching is explainable keyword-based scoring. Validate each vacancy and tailor claims only to experience you can substantiate.")
    st.caption("Edit profile.json to customize your skills and target roles.")

tabs = st.tabs(["Dashboard", "Find jobs", "Add / score a job", "Application tracker", "Profile & setup"])

with tabs[0]:
    df = pd.read_sql_query("SELECT * FROM jobs ORDER BY fit_score DESC, added_at DESC", conn)
    a, b, c, d = st.columns(4)
    a.metric("Jobs saved", len(df))
    b.metric("High match (80+)", int((df["fit_score"] >= 80).sum()) if not df.empty else 0)
    c.metric("Applied", int((df["status"] == "Applied").sum()) if not df.empty else 0)
    d.metric("Interviews", int((df["status"] == "Interview").sum()) if not df.empty else 0)
    if df.empty:
        st.info("Your tracker is empty. Use **Find jobs** to open targeted searches, then add a vacancy under **Add / score a job**.")
    else:
        show_cols = ["fit_score", "title", "company", "location", "status", "url", "added_at"]
        st.dataframe(df[show_cols], use_container_width=True, hide_index=True,
                     column_config={"url": st.column_config.LinkColumn("Job link")})
        st.download_button("Export tracker CSV", df.to_csv(index=False).encode("utf-8"),
                           "job_tracker.csv", "text/csv")

with tabs[1]:
    st.subheader("Targeted job searches")
    st.write("Open a live search on a job board. Search results can change; verify the original posting, date, and eligibility.")
    links = search_links()
    selected_focus = st.selectbox("Role family", sorted(links["Search focus"].unique()))
    view = links[links["Search focus"] == selected_focus]
    for _, row in view.iterrows():
        st.markdown(f"- [{row['Source']}]({row['Open search']})")
    st.divider()
    st.subheader("Suggested daily search routine")
    st.markdown("""
    1. Search the highest-priority role families first.
    2. Prefer direct company career pages and vacancies posted recently.
    3. Save only unique, open roles and record the original posting URL.
    4. Score the job description and review the matched skills and gaps.
    5. Tailor your résumé, then submit the application yourself.
    """)

with tabs[2]:
    st.subheader("Add a vacancy and calculate a match score")
    with st.form("job_form", clear_on_submit=True):
        title = st.text_input("Job title *")
        company = st.text_input("Company")
        location = st.text_input("Location / work mode", placeholder="Hyderabad / Hybrid or Remote India")
        work_mode = st.selectbox("Work arrangement", ["Not specified", "On-site", "Hybrid", "Remote"])
        url = st.text_input("Original job posting URL")
        posted_date = st.text_input("Posted date (if known)", placeholder="e.g. 2026-10-26")
        salary_lpa = st.number_input("Salary (LPA, if listed)", min_value=0.0, max_value=1000.0, value=0.0, step=1.0)
        description = st.text_area("Job description / responsibilities *", height=220)
        submitted = st.form_submit_button("Score and save job")
    if submitted:
        if not title.strip() or not description.strip():
            st.error("Please provide both a job title and job description.")
        else:
            score, matched, gaps = score_job(title, description, location, profile)
            exists = conn.execute("SELECT id FROM jobs WHERE url=? AND url<>''", (url.strip(),)).fetchone() if url.strip() else None
            if exists:
                st.warning(f"This URL is already saved (job ID {exists['id']}). Update the existing entry in the tracker instead.")
            else:
                conn.execute("""INSERT INTO jobs
                    (title, company, location, work_mode, url, posted_date, description, salary_lpa,
                     fit_score, matched_skills, gaps, status, added_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Saved', ?)""",
                    (title.strip(), company.strip(), location.strip(), work_mode, url.strip(), posted_date.strip(),
                     description.strip(), salary_lpa if salary_lpa else None, score,
                     ", ".join(matched), ", ".join(gaps), datetime.now().isoformat(timespec="seconds")))
                conn.commit()
                st.success(f"Saved. Initial fit score: {score}/100")
                st.write("**Skills found in description:**", ", ".join(matched) or "No configured skills found")
                st.write("**Skills not mentioned (not necessarily missing):**", ", ".join(gaps))
                st.caption("This score is a triage aid, not a prediction of interview success. The description may omit skills.")

with tabs[3]:
    st.subheader("Application tracker")
    df = pd.read_sql_query("SELECT * FROM jobs ORDER BY fit_score DESC, added_at DESC", conn)
    if df.empty:
        st.info("Add a job to start tracking applications.")
    else:
        ids = df["id"].tolist()
        choice = st.selectbox("Select job", ids, format_func=lambda i: f"#{i} · {df.loc[df.id == i, 'title'].iloc[0]} — {df.loc[df.id == i, 'company'].iloc[0]}")
        selected = conn.execute("SELECT * FROM jobs WHERE id=?", (int(choice),)).fetchone()
        with st.form("update_job"):
            status_options = ["Saved", "To Review", "Ready to Apply", "Applied", "Recruiter Screen", "Interview", "Offer", "Rejected", "Withdrawn"]
            current_status = selected["status"] if selected["status"] in status_options else "Saved"
            status = st.selectbox("Status", status_options, index=status_options.index(current_status))
            notes = st.text_area("Notes / next action", value=selected["notes"] or "")
            save = st.form_submit_button("Update tracker")
        if save:
            conn.execute("UPDATE jobs SET status=?, notes=? WHERE id=?", (status, notes, int(choice)))
            conn.commit()
            st.success("Tracker updated.")
        st.markdown(f"**Fit score:** {selected['fit_score']}/100")
        st.markdown(f"**Matched skills:** {selected['matched_skills'] or 'None detected'}")
        st.markdown(f"**Review carefully:** {selected['gaps'] or 'No unmentioned configured skills'}")
        if selected["url"]:
            st.markdown(f"[Open original job posting]({selected['url']})")
        if st.button("Delete selected job", type="secondary"):
            conn.execute("DELETE FROM jobs WHERE id=?", (int(choice),))
            conn.commit()
            st.rerun()

with tabs[4]:
    st.subheader("Profile configuration")
    st.write("The starter profile is stored in `profile.json`. Edit it to reflect your verified skills, preferred roles, and any salary requirements.")
    st.json(profile)
    st.subheader("Scoring guide")
    st.markdown("""
    - **80–100:** Priority for human review
    - **65–79:** Worth reviewing
    - **Below 65:** Usually lower priority
    - Scores combine title relevance, skill keyword overlap, location, and seniority.
    - A skill not mentioned in a job description is not proof you lack it.
    """)
    st.subheader("Privacy and application safety")
    st.markdown("""
    - The local app stores jobs in `data/jobs.db` on your machine.
    - Do not paste passwords, one-time codes, or sensitive personal identifiers.
    - It does not scrape behind logins, bypass job-board restrictions, or submit applications.
    - Always review résumé claims and application answers before sending.
    """)

conn.close()
