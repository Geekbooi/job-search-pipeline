"""
Tracks seen job IDs across pipeline runs using data/seen_jobs.json.
Capped at 500 entries (FIFO eviction) to keep the file small.
"""

import json
import os

_DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "seen_jobs.json")
_MAX_IDS   = 500


def _load() -> list[str]:
    try:
        with open(_DATA_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _save(ids: list[str]) -> None:
    os.makedirs(os.path.dirname(_DATA_FILE), exist_ok=True)
    with open(_DATA_FILE, "w") as f:
        json.dump(ids, f, indent=2)


def filter_new(jobs: list[dict]) -> list[dict]:
    """Return only jobs whose IDs haven't been seen before, then persist."""
    seen = set(_load())
    new_jobs = [j for j in jobs if j["id"] not in seen]

    if new_jobs:
        all_ids = _load() + [j["id"] for j in new_jobs]
        _save(all_ids[-_MAX_IDS:])   # keep newest _MAX_IDS

    print(f"[dedup] {len(new_jobs)} new jobs (skipped {len(jobs) - len(new_jobs)} already seen)")
    return new_jobs
