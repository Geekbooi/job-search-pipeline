"""
Builds an HTML email body for the job search results.
"""

from datetime import datetime, timezone


def build_html_email(jobs: list[dict]) -> str:
    cards = "\n".join(_job_card(job, i + 1, len(jobs)) for i, job in enumerate(jobs))
    now   = datetime.now(timezone.utc).strftime("%b %d, %Y — %H:%M UTC")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Job Search Results</title>
<style>
  body      {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
               background: #0f1117; color: #e2e8f0; margin: 0; padding: 0; }}
  .wrapper  {{ max-width: 680px; margin: 0 auto; padding: 32px 16px; }}
  .header   {{ background: linear-gradient(135deg, #1e3a8a 0%, #4f46e5 100%);
               border-radius: 12px; padding: 28px 32px; margin-bottom: 24px; }}
  .header h1{{ margin: 0 0 6px; font-size: 22px; color: #fff; }}
  .header p {{ margin: 0; font-size: 13px; color: #a5b4fc; }}
  .card     {{ background: #1a1d27; border: 1px solid #2d3148;
               border-radius: 10px; padding: 24px; margin-bottom: 16px; }}
  .card-num {{ font-size: 11px; font-weight: 700; color: #6366f1; letter-spacing: .08em;
               text-transform: uppercase; margin-bottom: 8px; }}
  .card h2  {{ margin: 0 0 4px; font-size: 17px; color: #f1f5f9; }}
  .card .co {{ font-size: 14px; color: #94a3b8; margin-bottom: 12px; }}
  .tags     {{ display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 14px; }}
  .tag      {{ background: #1e2235; border: 1px solid #374151; border-radius: 6px;
               padding: 3px 10px; font-size: 12px; color: #cbd5e1; }}
  .tag.blue {{ background: #1e3a8a22; border-color: #3b82f6; color: #93c5fd; }}
  .sponsorship {{ background: #064e3b22; border: 1px solid #10b981;
                  border-radius: 8px; padding: 10px 14px; font-size: 13px;
                  color: #6ee7b7; margin-bottom: 14px; }}
  .reqs     {{ margin: 0 0 14px; padding-left: 18px; }}
  .reqs li  {{ font-size: 13px; color: #94a3b8; margin-bottom: 4px; }}
  .reason   {{ font-size: 13px; color: #64748b; font-style: italic;
               border-left: 3px solid #334155; padding-left: 10px; margin-bottom: 16px; }}
  .apply    {{ display: inline-block; background: #4f46e5; color: #fff;
               text-decoration: none; border-radius: 8px; padding: 10px 20px;
               font-size: 14px; font-weight: 600; }}
  .apply:hover {{ background: #4338ca; }}
  .meta     {{ font-size: 11px; color: #475569; margin-top: 10px; }}
  .footer   {{ text-align: center; padding: 24px 0 0; font-size: 12px; color: #475569; }}
</style>
</head>
<body>
<div class="wrapper">
  <div class="header">
    <h1>🔍 {len(jobs)} New Job Match{'es' if len(jobs) != 1 else ''}</h1>
    <p>Filtered for mid-level roles with H1B/visa sponsorship &bull; {now}</p>
  </div>

  {cards}

  <div class="footer">
    <p>Job Search Pipeline &bull; Runs every 12 hours<br>
    Only jobs with potential sponsorship pass through Claude filtering.</p>
  </div>
</div>
</body>
</html>"""


def _job_card(job: dict, index: int, total: int) -> str:
    title       = _h(job.get("title", "Unknown Title"))
    company     = _h(job.get("company", "Unknown"))
    location    = _h(job.get("location", "Remote"))
    source      = _h(job.get("source", ""))
    url         = job.get("url", "#")
    posted      = str(job.get("posted", ""))[:16]
    sponsorship = job.get("sponsorship_note", "Not mentioned")
    reqs        = job.get("key_requirements", [])
    experience  = _h(job.get("experience_required", ""))
    reason      = _h(job.get("filter_reason", ""))

    tags_html = f'<span class="tag blue">{_h(location)}</span>'
    if experience:
        tags_html += f'<span class="tag">{experience}</span>'
    if source:
        tags_html += f'<span class="tag">{source}</span>'

    sponsorship_html = ""
    if sponsorship and sponsorship.lower() != "not mentioned":
        sponsorship_html = f'<div class="sponsorship">🛂 {_h(sponsorship)}</div>'

    reqs_html = ""
    if reqs:
        items = "".join(f"<li>{_h(r)}</li>" for r in reqs[:5])
        reqs_html = f'<ul class="reqs">{items}</ul>'

    reason_html = f'<p class="reason">{reason}</p>' if reason else ""
    posted_html = f'<div class="meta">Posted: {_h(posted)}</div>' if posted else ""

    return f"""<div class="card">
  <div class="card-num">Match {index} of {total}</div>
  <h2>{title}</h2>
  <div class="co">{company}</div>
  <div class="tags">{tags_html}</div>
  {sponsorship_html}
  {reqs_html}
  {reason_html}
  <a class="apply" href="{url}" target="_blank">Apply Now →</a>
  {posted_html}
</div>"""


def _h(text: str) -> str:
    """HTML-escape a string."""
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))
