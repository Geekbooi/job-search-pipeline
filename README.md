# Job Search Pipeline

Automated job search assistant that runs every 12 hours, finds relevant mid-level engineering roles with H1B/visa sponsorship, and delivers curated results to Telegram.

## What it does

1. **Fetches** job listings from RemoteOK, Jobicy, We Work Remotely, and optionally JSearch (RapidAPI)
2. **Pre-filters** by role keywords, excludes senior/lead/intern titles, excludes postings that explicitly reject sponsorship or require clearance
3. **Claude filtering** — batches shortlisted jobs through Claude (claude-sonnet-4-6) to score each on role match, experience level (3–5 years), employment type, and sponsorship signals
4. **Deduplicates** against previously seen job IDs to avoid repeat notifications
5. **Sends** up to 10 new results to your Telegram chat with sponsorship notes, key requirements, and apply link

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

### 2. Create a Telegram bot

1. Message [@BotFather](https://t.me/BotFather) → `/newbot`
2. Copy the bot token
3. Start a chat with your bot, then run:
   ```bash
   curl "https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates"
   ```
   Find your `chat.id` in the response.

### 3. Configure secrets

Copy `.env.example` to `.env` and fill in:

```
ANTHROPIC_API_KEY=sk-ant-...
TELEGRAM_BOT_TOKEN=123456789:ABC...
TELEGRAM_CHAT_ID=your_chat_id
RAPIDAPI_KEY=optional_for_jsearch
```

### 4. Run locally

```bash
cd src
python main.py
```

### 5. GitHub Actions (automated every 12h)

Add these repository secrets under **Settings → Secrets → Actions**:

| Secret | Required |
|--------|----------|
| `ANTHROPIC_API_KEY` | Yes |
| `TELEGRAM_BOT_TOKEN` | Yes |
| `TELEGRAM_CHAT_ID` | Yes |
| `RAPIDAPI_KEY` | No (enables JSearch) |

The workflow at `.github/workflows/job_search.yml` runs at 00:00 and 12:00 UTC daily. It also commits the updated `data/seen_jobs.json` back to the repo after each run so deduplication persists across runs.

You can also trigger a manual run from **Actions → Job Search Pipeline → Run workflow**.

## Project structure

```
job-search-pipeline/
├── src/
│   ├── main.py        # orchestration
│   ├── fetcher.py     # multi-source job fetching + pre-filter
│   ├── filter.py      # Claude batch filtering
│   ├── dedup.py       # seen_jobs.json deduplication
│   ├── formatter.py   # Telegram message formatting
│   └── sender.py      # Telegram Bot API sender
├── data/
│   └── seen_jobs.json # persisted seen job IDs (auto-committed)
├── .github/
│   └── workflows/
│       └── job_search.yml
├── .env.example
├── requirements.txt
└── README.md
```
