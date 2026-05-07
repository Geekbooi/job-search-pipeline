"""
Fetches job listings from free public APIs and RSS feeds.
Sources: RemoteOK, Jobicy, We Work Remotely, JSearch (RapidAPI — optional).
"""

import os
import re
import time
import email.utils
import requests
import feedparser
from datetime import datetime, timedelta, timezone

REQUEST_TIMEOUT = 15

# ── Target role keywords ───────────────────────────────────────────────────────

ROLE_KEYWORDS = [
    "cloud engineer", "devops engineer", "aws engineer", "site reliability",
    "sre", "java developer", "backend engineer", "software engineer",
    "platform engineer", "infrastructure engineer",
]

EXCLUDE_TITLE_KEYWORDS = [
    "senior", "sr.", "sr ", "staff", "principal", "lead ", "tech lead",
    "director", "manager", "head of", "vp ", "vice president", "architect",
    "associate", "intern", "junior",
]

EXCLUDE_BODY_KEYWORDS = [
    "us citizen", "u.s. citizen", "active clearance", "security clearance",
    "secret clearance", "top secret", "ts/sci", "green card required",
    "must be authorized", "no visa", "no sponsorship", "sponsorship not available",
    "sponsorship is not", "cannot sponsor", "will not sponsor",
]

TECH_KEYWORDS = [
    "aws", "kubernetes", "docker", "terraform", "ci/cd", "java", "spring boot",
    "devops", "cloud", "backend", "distributed", "microservices", "iac",
    "infrastructure as code",
]


RECENCY_HOURS = 72   # 3 days — dedup handles re-sends, this just blocks months-old listings


def _parse_posted(value: str) -> datetime | None:
    """Parse a posted date string into an aware datetime. Returns None if unparseable."""
    if not value:
        return None
    value = value.strip()
    # Try RFC 2822 (RSS feeds)
    try:
        return email.utils.parsedate_to_datetime(value)
    except Exception:
        pass
    # Try ISO 8601 (Z suffix or offset)
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        pass
    # Try plain date "YYYY-MM-DD"
    try:
        dt = datetime.strptime(value[:10], "%Y-%m-%d")
        return dt.replace(tzinfo=timezone.utc)
    except Exception:
        pass
    return None


def _is_recent(posted: str) -> bool:
    """Return True if posted within RECENCY_HOURS, or if date is unknown (include by default)."""
    dt = _parse_posted(posted)
    if dt is None:
        return True   # unknown date — don't exclude
    cutoff = datetime.now(timezone.utc) - timedelta(hours=RECENCY_HOURS)
    return dt >= cutoff


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", " ", text or "").strip()


def _passes_title_filter(title: str) -> bool:
    low = title.lower()
    has_role = any(k in low for k in ROLE_KEYWORDS)
    has_exclude = any(k in low for k in EXCLUDE_TITLE_KEYWORDS)
    return has_role and not has_exclude


def _passes_body_filter(text: str) -> bool:
    low = text.lower()
    return not any(k in low for k in EXCLUDE_BODY_KEYWORDS)


def _has_tech_match(text: str) -> bool:
    low = text.lower()
    return any(k in low for k in TECH_KEYWORDS)


def _normalise(raw: dict) -> dict | None:
    """Return a normalised job dict or None if it should be skipped."""
    title = raw.get("title", "").strip()
    body  = _strip_html(raw.get("description", ""))[:3000]
    url   = raw.get("url", "")
    uid   = raw.get("id") or url

    if not (title and url):
        return None
    if not _passes_title_filter(title):
        return None
    if not _passes_body_filter(body):
        return None
    if not _has_tech_match(title + " " + body):
        return None

    return {
        "id":          uid,
        "title":       title,
        "company":     raw.get("company", "Unknown"),
        "location":    raw.get("location", "Remote"),
        "url":         url,
        "description": body,
        "source":      raw.get("source", ""),
        "posted":      raw.get("posted", ""),
    }


# ── Source: RemoteOK ──────────────────────────────────────────────────────────

REMOTEOK_TAGS = ["devops", "aws", "backend", "java", "cloud", "kubernetes"]

def fetch_remoteok() -> list[dict]:
    jobs = []
    for tag in REMOTEOK_TAGS:
        try:
            resp = requests.get(
                f"https://remoteok.com/api?tag={tag}",
                headers={"User-Agent": "job-search-bot/1.0"},
                timeout=REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
            data = resp.json()
            for item in data[1:]:   # first element is metadata
                raw = {
                    "id":          item.get("slug", item.get("id", "")),
                    "title":       item.get("position", ""),
                    "company":     item.get("company", ""),
                    "location":    "Remote",
                    "url":         item.get("url", f"https://remoteok.com/l/{item.get('slug','')}"),
                    "description": _strip_html(item.get("description", "")),
                    "source":      "RemoteOK",
                    "posted":      item.get("date", ""),
                }
                job = _normalise(raw)
                if job:
                    jobs.append(job)
            time.sleep(1)   # be polite
        except Exception as e:
            print(f"[fetcher] RemoteOK tag={tag} error: {e}")
    print(f"[fetcher] RemoteOK: {len(jobs)} candidates")
    return jobs


# ── Source: Jobicy ────────────────────────────────────────────────────────────

JOBICY_TAGS = ["devops", "aws", "java", "cloud", "backend"]

def fetch_jobicy() -> list[dict]:
    jobs = []
    for tag in JOBICY_TAGS:
        try:
            resp = requests.get(
                "https://jobicy.com/api/v2/remote-jobs",
                params={"count": 50, "tag": tag, "geo": "usa"},
                timeout=REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
            data = resp.json().get("jobs", [])
            for item in data:
                job_types = [t.lower() for t in item.get("jobType", [])]
                if "full-time" not in " ".join(job_types):
                    continue
                raw = {
                    "id":          str(item.get("id", "")),
                    "title":       item.get("jobTitle", ""),
                    "company":     item.get("companyName", ""),
                    "location":    item.get("jobGeo", "Remote") or "Remote",
                    "url":         item.get("url", ""),
                    "description": _strip_html(item.get("jobDescription", "")),
                    "source":      "Jobicy",
                    "posted":      item.get("pubDate", ""),
                }
                job = _normalise(raw)
                if job:
                    jobs.append(job)
            time.sleep(0.5)
        except Exception as e:
            print(f"[fetcher] Jobicy tag={tag} error: {e}")
    print(f"[fetcher] Jobicy: {len(jobs)} candidates")
    return jobs


# ── Source: We Work Remotely (RSS) ───────────────────────────────────────────

WWR_FEEDS = [
    "https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss",
    "https://weworkremotely.com/categories/remote-back-end-programming-jobs.rss",
    "https://weworkremotely.com/categories/remote-full-stack-programming-jobs.rss",
]

def fetch_wwr() -> list[dict]:
    jobs = []
    for feed_url in WWR_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries:
                raw = {
                    "id":          entry.get("id", entry.get("link", "")),
                    "title":       entry.get("title", "").split(": ", 1)[-1],
                    "company":     entry.get("title", "").split(": ", 1)[0] if ": " in entry.get("title","") else "Unknown",
                    "location":    "Remote",
                    "url":         entry.get("link", ""),
                    "description": _strip_html(entry.get("summary", "")),
                    "source":      "We Work Remotely",
                    "posted":      entry.get("published", ""),
                }
                job = _normalise(raw)
                if job:
                    jobs.append(job)
        except Exception as e:
            print(f"[fetcher] WWR feed error: {e}")
    print(f"[fetcher] We Work Remotely: {len(jobs)} candidates")
    return jobs


# ── Source: JSearch via RapidAPI (optional) ───────────────────────────────────

JSEARCH_QUERIES = [
    "Cloud Engineer visa sponsorship remote",
    "DevOps Engineer H1B sponsorship remote USA",
    "AWS Engineer sponsorship remote",
    "Java Developer visa sponsorship remote",
    "Backend Engineer sponsorship USA",
]

def fetch_jsearch() -> list[dict]:
    api_key = os.getenv("RAPIDAPI_KEY")
    if not api_key:
        return []

    jobs = []
    headers = {
        "X-RapidAPI-Key":  api_key,
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
    }

    for query in JSEARCH_QUERIES:
        try:
            resp = requests.get(
                "https://jsearch.p.rapidapi.com/search",
                headers=headers,
                params={
                    "query":       query,
                    "page":        "1",
                    "num_pages":   "1",
                    "date_posted": "3days",
                },
                timeout=REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
            for item in resp.json().get("data", []):
                if item.get("job_employment_type", "").upper() != "FULLTIME":
                    continue
                raw = {
                    "id":          item.get("job_id", ""),
                    "title":       item.get("job_title", ""),
                    "company":     item.get("employer_name", ""),
                    "location":    "Remote" if item.get("job_is_remote") else f"{item.get('job_city','')}, {item.get('job_state','')}".strip(", "),
                    "url":         item.get("job_apply_link", ""),
                    "description": item.get("job_description", "")[:3000],
                    "source":      "JSearch",
                    "posted":      item.get("job_posted_at_datetime_utc", ""),
                }
                job = _normalise(raw)
                if job:
                    jobs.append(job)
            time.sleep(1)
        except Exception as e:
            print(f"[fetcher] JSearch query='{query}' error: {e}")

    print(f"[fetcher] JSearch: {len(jobs)} candidates")
    return jobs


# ── Combined fetch ─────────────────────────────────────────────────────────────

def fetch_all() -> list[dict]:
    all_jobs: list[dict] = []
    all_jobs += fetch_remoteok()
    all_jobs += fetch_jobicy()
    all_jobs += fetch_wwr()
    all_jobs += fetch_jsearch()

    # Deduplicate by URL within this batch
    seen_urls: set[str] = set()
    unique: list[dict] = []
    for job in all_jobs:
        if job["url"] not in seen_urls:
            seen_urls.add(job["url"])
            unique.append(job)

    # Filter to recent postings only
    recent = [j for j in unique if _is_recent(j.get("posted", ""))]
    print(f"[fetcher] {len(recent)} recent (last {RECENCY_HOURS}h) out of {len(unique)} unique candidates")
    return recent
