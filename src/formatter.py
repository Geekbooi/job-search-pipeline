"""
Formats a filtered job dict into a clean Telegram message.
"""


def format_job(job: dict, index: int, total: int) -> str:
    title    = job.get("title", "Unknown Title")
    company  = job.get("company", "Unknown Company")
    location = job.get("location", "Remote")
    url      = job.get("url", "")
    source   = job.get("source", "")
    posted   = job.get("posted", "")

    sponsorship = job.get("sponsorship_note", "Not mentioned")
    requirements = job.get("key_requirements", [])
    experience   = job.get("experience_required", "")
    reason       = job.get("filter_reason", "")

    req_text = ""
    if requirements:
        req_text = "\n".join(f"  • {r}" for r in requirements[:5])

    lines = [
        f"🧑‍💻 *{index}/{total}* — {_esc(title)}",
        f"🏢 {_esc(company)}",
        f"📍 {_esc(location)}",
    ]

    if experience:
        lines.append(f"⏱ {_esc(experience)}")

    if sponsorship and sponsorship.lower() != "not mentioned":
        lines.append(f"🛂 {_esc(sponsorship)}")
    else:
        lines.append("🛂 Sponsorship: not explicitly mentioned")

    if req_text:
        lines.append(f"\n📋 *Key requirements:*\n{req_text}")

    if reason:
        lines.append(f"\n💡 _{_esc(reason)}_")

    if source:
        lines.append(f"\n🔗 Source: {_esc(source)}")

    if url:
        lines.append(f"[Apply here]({url})")

    if posted:
        lines.append(f"\n🕐 Posted: {_esc(str(posted)[:20])}")

    return "\n".join(lines)


def format_header(count: int) -> str:
    return (
        f"🔍 *Job Search Results*\n"
        f"Found *{count}* new matching job{'s' if count != 1 else ''} "
        f"with potential H1B sponsorship.\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )


def format_footer() -> str:
    return "━━━━━━━━━━━━━━━━━━━━\n✅ _End of today's results. Good luck!_"


def _esc(text: str) -> str:
    """Escape Telegram MarkdownV1 special chars."""
    for ch in ["_", "*", "`", "["]:
        text = text.replace(ch, f"\\{ch}")
    return text
