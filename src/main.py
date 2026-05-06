"""
Entry point — orchestrates the full pipeline:
  fetch → filter (Claude) → dedup → format → send to Telegram
"""

import sys
from fetcher   import fetch_all
from filter    import filter_jobs
from dedup     import filter_new
from formatter import format_job, format_header, format_footer
from sender    import send_jobs, send_message

MAX_RESULTS = 10   # cap Telegram messages per run


def main() -> None:
    print("=== Job Search Pipeline ===")

    # 1. Fetch candidates from all sources
    candidates = fetch_all()
    if not candidates:
        print("[main] No candidates fetched — exiting.")
        send_message("🔍 Job search ran — no candidates found from any source today.")
        return

    # 2. Claude filtering
    filtered = filter_jobs(candidates)
    if not filtered:
        print("[main] No jobs passed Claude filter — exiting.")
        send_message("🔍 Job search ran — no jobs matched your criteria today. Try again in 12h.")
        return

    # 3. Dedup against previously seen jobs
    new_jobs = filter_new(filtered)
    if not new_jobs:
        print("[main] All filtered jobs already seen — exiting.")
        send_message("🔍 Job search ran — all matches were already sent to you. Nothing new yet.")
        return

    # 4. Cap results
    to_send = new_jobs[:MAX_RESULTS]
    total   = len(to_send)

    # 5. Format
    header        = format_header(total)
    job_messages  = [format_job(job, i + 1, total) for i, job in enumerate(to_send)]
    footer        = format_footer()

    # 6. Send
    send_jobs(header, job_messages, footer)
    print(f"[main] Sent {total} job(s) to Telegram.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        print(f"[main] Fatal error: {e}")
        try:
            send_message(f"⚠️ Job search pipeline error: {e}")
        except Exception:
            pass
        raise
