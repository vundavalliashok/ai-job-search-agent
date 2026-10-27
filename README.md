# AI Job Search Agent

A local Streamlit MVP for a senior technology job search. It provides targeted live job-board searches, an explainable keyword-based match score, a SQLite application tracker, and CSV export.

## Target profile

- 19+ years IT experience
- DevOps/SRE, Azure/AWS, Kubernetes, Terraform, CI/CD
- .NET development and enterprise modernization
- Automation and technical leadership
- Locations: Hyderabad, Bengaluru, Remote India
- Both senior technical and leadership roles

## Requirements

- Python 3.10+
- Internet browser for job-board search links

## Run on Windows (PowerShell)

```powershell
cd ai_job_search_agent
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

If `py` is not recognized, install Python from https://www.python.org/downloads/ and enable **Add Python to PATH**, then reopen PowerShell and use `python` instead of `py`.

## Run on macOS/Linux

```bash
cd ai_job_search_agent
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

Streamlit will print a local URL, usually http://localhost:8501.

## How to use

1. Open **Find jobs** and choose a role family.
2. Open a job-board search and verify the vacancy on its original page.
3. Paste the title, company, location, URL, and description into **Add / score a job**.
4. Review the score and skills. A skill not mentioned in a description is not necessarily a missing skill.
5. Use **Application tracker** to record status and next actions.
6. Export the tracker to CSV from the dashboard.

## Current limitations

- This is a working MVP, not an autonomous crawler. Job-board search links open live results, but vacancies must be verified and saved by the user.
- The score is deterministic keyword matching, not an LLM judgement or guarantee of fit.
- It does not apply for jobs, send messages, or bypass login, anti-bot controls, or job-board terms.
- Salary is optional and never inferred if not listed.

## Suggested next development stages

1. Add authorized job data feeds/APIs and scheduled ingestion.
2. Add duplicate detection by canonical URL and normalized company/title.
3. Add LLM-assisted scoring with evidence snippets and explicit unknowns.
4. Add email alerts and a daily digest.
5. Deploy to Render with persistent storage or use PostgreSQL; a local SQLite file is not suitable for ephemeral hosting.
6. Add tests for scoring, deduplication, and tracker status transitions.

## GitHub portfolio suggestions

Repository name: `ai-job-search-agent`

Include screenshots of the dashboard, an architecture diagram, tests, and a sample redacted job record. Never commit credentials, private résumé details, or application account tokens.
