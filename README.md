# Job Search Pipeline

Automated job search assistant that runs every 12 hours, finds relevant mid-level engineering roles with H1B/visa sponsorship, and delivers curated results to your inbox as a styled HTML email.

## What it does

1. **Fetches** job listings from RemoteOK, Jobicy, We Work Remotely, and optionally JSearch (RapidAPI)
2. **Pre-filters** by role keywords, excludes senior/lead/intern titles, excludes postings that explicitly reject sponsorship or require clearance
3. **Claude filtering** — batches shortlisted jobs through Claude (claude-sonnet-4-6) to score each on role match, experience level (3–5 years), employment type, and sponsorship signals
4. **Deduplicates** against previously seen job IDs to avoid repeat notifications
5. **Emails** up to 10 new results as a clean HTML digest with sponsorship notes, key requirements, and apply links

## Target roles

- Cloud Engineer, DevOps Engineer, AWS Engineer
- Java Developer, Backend Engineer, Platform/Infrastructure Engineer

Excludes: senior, staff, principal, lead, director, intern, associate titles.

## Setup

### 1. Clone and install

```bash
git clone https://github.com/Geekboii/job-search-pipeline.git
cd job-search-pipeline
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Gmail app password

If using Gmail you must use an **App Password** (not your account password):

1. Enable 2-step verification on your Google account
2. Go to **Google Account → Security → App Passwords**
3. Create a new app password (name it "Job Pipeline")
4. Use that 16-character password as `EMAIL_PASSWORD`

### 3. Configure environment

Copy `.env.example` to `.env` and fill in:

```
ANTHROPIC_API_KEY=sk-ant-...
EMAIL_USER=you@gmail.com
EMAIL_PASSWORD=your_16char_app_password
EMAIL_TO=you@gmail.com
RAPIDAPI_KEY=optional_for_jsearch
```

### 4. Run locally

```bash
cd src
python main.py
```

### 5. GitHub Actions (automated every 12h)

Add these repository secrets under **Settings → Secrets and variables → Actions**:

| Secret | Required | Notes |
|--------|----------|-------|
| `ANTHROPIC_API_KEY` | Yes | |
| `EMAIL_USER` | Yes | Gmail address used to send |
| `EMAIL_PASSWORD` | Yes | Gmail app password |
| `EMAIL_TO` | Yes | Recipient address (can be same as EMAIL_USER) |
| `EMAIL_SMTP_HOST` | No | Defaults to `smtp.gmail.com` |
| `EMAIL_SMTP_PORT` | No | Defaults to `587` |
| `RAPIDAPI_KEY` | No | Enables JSearch as a 4th source |

The workflow runs at 00:00 and 12:00 UTC daily and commits the updated `data/seen_jobs.json` back after each run so deduplication persists across runs.

Trigger a manual run anytime from **Actions → Job Search Pipeline → Run workflow**.

## Project structure

```
job-search-pipeline/
├── src/
│   ├── main.py        # orchestration
│   ├── fetcher.py     # multi-source job fetching + pre-filter
│   ├── filter.py      # Claude batch filtering
│   ├── dedup.py       # seen_jobs.json deduplication
│   ├── formatter.py   # HTML email builder
│   └── sender.py      # SMTP email sender
├── data/
│   └── seen_jobs.json # persisted seen job IDs (auto-committed)
├── .github/
│   └── workflows/
│       └── job_search.yml
├── .env.example
├── requirements.txt
└── README.md
```
