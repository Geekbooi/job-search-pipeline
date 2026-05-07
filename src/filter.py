"""
Claude-powered filtering: sponsorship check, experience level, quality score.
Batches jobs to minimise API calls.
"""

import os
import json
import anthropic

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

FILTER_SYSTEM = """You are a job listing evaluator for a mid-level engineer job search targeting H1B visa holders.

PASS a job if ALL of these are true:
- Role matches: Cloud Engineer, DevOps Engineer, AWS Engineer, Java Developer, Backend Engineer, Platform Engineer, Infrastructure Engineer, or SRE
- Experience: listing asks for 5 years or fewer (or does not specify). Reject only if it explicitly requires 6+ years.
- Employment: Full-time. Reject contract, C2C, freelance, part-time.
- Location: Remote, remote-US, or anywhere in the United States.
- Sponsorship: DO NOT require the listing to mention sponsorship. Pass the job UNLESS it explicitly says any of: "no sponsorship", "will not sponsor", "cannot sponsor", "US citizen only", "requires green card", "requires clearance", "active clearance required".
- Tech: at least some overlap with AWS, cloud, Kubernetes, Docker, Terraform, CI/CD, Java, Spring Boot, backend, or DevOps.

FAIL a job only if:
- Wrong role type (frontend, mobile, data science, QA, sales, etc.)
- Explicitly requires 6+ years of experience
- Explicitly rejects visa sponsorship or requires citizenship/clearance
- Contract or freelance only

For each job respond with a JSON array. Each element:
{
  "id": "<job id>",
  "pass": true or false,
  "reason": "one sentence why",
  "sponsorship_note": "exact quote about sponsorship if mentioned, or 'Not mentioned — no explicit rejection'",
  "key_requirements": ["req1", "req2", "req3"],
  "experience_required": "e.g. 3-5 years or 'Not specified'"
}

When in doubt, PASS the job. The user will do final vetting."""


def filter_jobs(jobs: list[dict]) -> list[dict]:
    if not jobs:
        return []

    BATCH_SIZE = 8
    passed: list[dict] = []

    for i in range(0, len(jobs), BATCH_SIZE):
        batch = jobs[i : i + BATCH_SIZE]
        batch_text = json.dumps([
            {
                "id":          j["id"],
                "title":       j["title"],
                "company":     j["company"],
                "location":    j["location"],
                "description": j["description"][:1500],
            }
            for j in batch
        ], indent=2)

        try:
            resp = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=2048,
                system=FILTER_SYSTEM,
                messages=[{
                    "role": "user",
                    "content": f"Evaluate these {len(batch)} job listings:\n\n{batch_text}",
                }],
            )

            raw = resp.content[0].text.strip()
            # Extract JSON array from response (may have surrounding text)
            start = raw.find("[")
            end   = raw.rfind("]") + 1
            results: list[dict] = json.loads(raw[start:end])

        except Exception as e:
            print(f"[filter] Claude batch {i//BATCH_SIZE + 1} error: {e}")
            continue

        id_to_job = {j["id"]: j for j in batch}
        for result in results:
            if not result.get("pass"):
                continue
            jid = result.get("id")
            if jid not in id_to_job:
                continue
            job = id_to_job[jid].copy()
            job["sponsorship_note"]    = result.get("sponsorship_note", "Not mentioned")
            job["key_requirements"]    = result.get("key_requirements", [])
            job["experience_required"] = result.get("experience_required", "")
            job["filter_reason"]       = result.get("reason", "")
            passed.append(job)

    print(f"[filter] {len(passed)} jobs passed Claude filter out of {len(jobs)} candidates")
    return passed
