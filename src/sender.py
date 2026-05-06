"""
Sends messages to a Telegram chat via Bot API.
"""

import os
import time
import requests

TELEGRAM_TOKEN   = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

_BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
_DELAY    = 1.2   # seconds between messages (Telegram rate limit: 30/min per chat)


def send_message(text: str, parse_mode: str = "Markdown") -> bool:
    try:
        resp = requests.post(
            f"{_BASE_URL}/sendMessage",
            json={
                "chat_id":    TELEGRAM_CHAT_ID,
                "text":       text,
                "parse_mode": parse_mode,
                "disable_web_page_preview": False,
            },
            timeout=15,
        )
        resp.raise_for_status()
        return True
    except Exception as e:
        print(f"[sender] Telegram error: {e}")
        return False


def send_jobs(header: str, job_messages: list[str], footer: str) -> None:
    send_message(header)
    time.sleep(_DELAY)

    for msg in job_messages:
        send_message(msg)
        time.sleep(_DELAY)

    send_message(footer)
