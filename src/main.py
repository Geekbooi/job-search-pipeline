"""
Entry point — orchestrates the full pipeline:
  fetch → filter (Claude) → dedup → format → send via email
"""

import sys
from dotenv import load_dotenv
load_dotenv()

from fetcher import fetch_all
from filter  import filter_jobs
from dedup   import filter_new
from sender  import send_jobs, send_notice

MAX_RESULTS = 10


def main() -> None:
    print("=== Job Search Pipeline ===")

    candidates = fetch_all()
    if not candidates:
        print("[main] No candidates fetched — exiting.")
        send_notice("Job search ran — no candidates found from any source today.")
        return

    filtered = filter_jobs(candidates)
    if not filtered:
        print("[main] No jobs passed Claude filter — exiting.")
        send_notice("Job search ran — no jobs matched your criteria today. Try again in 12h.")
        return

    new_jobs = filter_new(filtered)
    if not new_jobs:
        print("[main] All filtered jobs already seen — exiting.")
        return

    to_send = new_jobs[:MAX_RESULTS]
    send_jobs(to_send, len(to_send))
    print(f"[main] Sent {len(to_send)} job(s) via email.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        print(f"[main] Fatal error: {e}")
        try:
            send_notice(f"Pipeline error: {e}")
        except Exception:
            pass
        raise
