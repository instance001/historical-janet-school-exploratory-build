import json
from pathlib import Path
from datetime import datetime
from backend_miss_gpt import MissGPTBackend

BASE_DIR = Path(__file__).resolve().parent
MEMORY_DIR = BASE_DIR / "memory"
REPORTS_DIR = BASE_DIR / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

CONCEPTS_PATH = MEMORY_DIR / "concepts.jsonl"

AUDITOR_PROMPT_TEMPLATE = """
You are the Thought Auditor for a developing Modest Cognition Model (MCM) named Janet.

You will be given samples of Janet's thinking while she is learning concepts.
Each sample includes:
- the concept name
- the lesson summary
- Janet's inner monologue (which may mix thoughts and final answers)
- Janet's final output (same as inner monologue for now)

Your job:
1. Identify recurring reasoning patterns in Janet's inner monologue.
2. Detect any misunderstandings or misconceptions.
3. Detect any over-generalization or wrong rules she might be forming.
4. Identify which concepts look strong (good understanding).
5. Identify which concepts look weak or fragile.
6. Propose specific remedial lesson ideas for weak concepts.
7. Note any signs of abstraction or meta-thinking (e.g., talking about instructions, patterns, rules).

Output in this structure:

Summary of Reasoning Patterns:
- ...

Strong Concepts:
- <concept>: <why it seems strong>
- ...

Weak Concepts:
- <concept>: <why it seems weak>

Misconceptions Detected:
- <description of misconception and which concept it affects>

Suggested Remedial Lessons:
- <concept>: <concrete suggestion for new examples or explanations>

Notes on Cognitive Development:
- <observations about Janet's thinking style, meta-talk, and growth stage>

Here are the samples:

{samples}
"""


def load_concept_episodes(limit: int = 20):
    """Load last N concept records from memory/concepts.jsonl."""
    if not CONCEPTS_PATH.exists():
        print(f"No concepts file found at {CONCEPTS_PATH}")
        return []

    records = []
    with CONCEPTS_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                records.append(obj)
            except json.JSONDecodeError:
                continue

    # keep only the last `limit` episodes
    return records[-limit:]


def build_samples_text(records):
    """Format concept episodes into a text block for the auditor prompt."""
    chunks = []
    for rec in records:
        concept = rec.get("concept", "unknown_concept")
        data = rec.get("data", {})
        lesson = data.get("lesson", {})
        inner = data.get("janet_inner_monologue", "")
        final = data.get("janet_final_output", "")
        ts = rec.get("ts", "")

        lesson_explanation = ""
        if isinstance(lesson, dict):
            lesson_explanation = lesson.get("explanation", "")
        # If lesson wasn't a dict or lacked "explanation", we just leave it blank.

        chunk = (
            f"---\n"
            f"Timestamp: {ts}\n"
            f"Concept: {concept}\n\n"
            f"Lesson explanation (teacher): {lesson_explanation}\n\n"
            f"Janet inner monologue:\n{inner}\n\n"
            f"Janet final output:\n{final}\n"
        )
        chunks.append(chunk)

    return "\n".join(chunks) if chunks else "(No samples available.)"


def main():
    print("Loading Janet's concept episodes...")
    records = load_concept_episodes(limit=20)
    if not records:
        print("No concept data to audit.")
        return

    samples_text = build_samples_text(records)
    prompt = AUDITOR_PROMPT_TEMPLATE.format(samples=samples_text)

    backend = MissGPTBackend()
    print("Asking Miss DeepSeek (Miss GPT) to audit Janet's inner monologue...\n")
    report = backend.generate(prompt, max_tokens=2048)

    # Print to console
    print("===== THOUGHT AUDIT REPORT =====")
    print(report)

    # Save to reports/
    timestamp = datetime.utcnow().isoformat().replace(":", "-")
    report_path = REPORTS_DIR / f"thought_audit_{timestamp}.txt"
    report_path.write_text(report, encoding="utf-8")
    print(f"\nReport saved to: {report_path}")


if __name__ == "__main__":
    main()
