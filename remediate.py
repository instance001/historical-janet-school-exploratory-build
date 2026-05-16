import argparse
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple

from telemetry_engine import (
    EPISODES_FILE,
    TELEMETRY_JSON,
    build_telemetry,
    write_json,
    write_markdown,
)

# Output files for the remedial planner
REMEDIAL_JSON = "remedial_plan.json"
REMEDIAL_MD = "remedial_plan.md"

# Sentinel: means "this organ touches all concepts"
ALL = "__ALL__"

# --- Organ ↔ Concept bucket mapping (mirrors the ideas from telemetry_engine buckets) --- #
# You can tweak these names to exactly match whatever you used in telemetry_engine.
ORGAN_CONCEPT_BUCKETS: Dict[str, Any] = {
    "Sequence Perception Organ (SPO)": ALL,  # globally engaged
    "Rule Extraction Organ (REO)": ALL,
    "Bidirectional Reasoning Organ (BRO)": [
        "Reversed Cycle",
    ],
    "Nested Pattern Organ (NPO)": [
        "Nested Pattern",
    ],
    "Distractor Inhibition Organ (DIO)": [
        "Distractor-element Pattern",
    ],
    "Pattern Continuation Organ (PCO)": [
        "sequence_next",
        "Simple Alternation",
        "Double Alternation",
        "Long-cycle Repeat",
        "Offset Numeric Pattern",
        "Shape/shape/number Combo",
    ],
    "Meta-Restatement Organ (MRO)": ALL,
}


# --------------------------------------------------------------------
# Telemetry loading / building
# --------------------------------------------------------------------

def load_or_build_telemetry(
    telemetry_path: Path,
    episodes_path: Path,
) -> Dict[str, Any]:
    """
    Load telemetry_log.json if it exists, otherwise build it fresh from episodes.jsonl.
    """
    if telemetry_path.exists():
        with telemetry_path.open("r", encoding="utf-8") as f:
            return json.load(f)

    # Fallback: build telemetry from episodes
    telemetry = build_telemetry(episodes_path)
    write_json(telemetry, telemetry_path)
    write_markdown(telemetry, Path("telemetry_log.md"))
    return telemetry


# --------------------------------------------------------------------
# Weak organ selection
# --------------------------------------------------------------------

def pick_weak_organs(
    telemetry: Dict[str, Any],
    threshold: float = 0.7,
    min_episodes: int = 1,
) -> List[Tuple[str, Dict[str, Any]]]:
    """
    Return list of (organ_name, organ_info) for organs whose health < threshold
    and that have at least min_episodes.
    """
    organs = telemetry.get("organs", {})
    weak: List[Tuple[str, Dict[str, Any]]] = []

    for name, info in organs.items():
        health = float(info.get("health", 0.0))
        eps = int(info.get("episodes", 0))
        if eps >= min_episodes and health < threshold:
            weak.append((name, info))

    # sort by health ascending (weakest first)
    weak.sort(key=lambda x: x[1].get("health", 0.0))
    return weak


# --------------------------------------------------------------------
# Concept ranking per organ
# --------------------------------------------------------------------

def rank_concepts_for_organ(
    organ_name: str,
    concept_stats: Dict[str, Dict[str, Any]],
    top_k: int = 3,
) -> List[Tuple[str, Dict[str, Any]]]:
    """
    For a given organ, select concepts that most stress that organ, based on:
      - avg_spiral_score
      - idk_rate
      - episodes (to avoid 1-off flukes)

    Returns list of (concept_name, stats_with_difficulty).
    """
    bucket = ORGAN_CONCEPT_BUCKETS.get(organ_name, ALL)

    candidates: List[Tuple[str, Dict[str, Any]]] = []

    for concept, stats in concept_stats.items():
        eps = int(stats.get("episodes", 0))
        if eps == 0:
            continue

        # Filter by bucket if needed
        if bucket != ALL and concept not in bucket:
            continue

        spiral = float(stats.get("avg_spiral_score", 0.0))
        idk_rate = float(stats.get("idk_rate", 0.0))

        # simple composite difficulty score = more spirals + more "I don't know"
        difficulty = spiral * 0.7 + idk_rate * 0.3

        # Attach difficulty into a shallow copy of stats
        enriched = dict(stats)
        enriched["difficulty"] = difficulty

        candidates.append((concept, enriched))

    # sort hardest first
    candidates.sort(key=lambda x: x[1]["difficulty"], reverse=True)

    # return top_k or fewer
    return candidates[:top_k]


# --------------------------------------------------------------------
# Remedial plan construction
# --------------------------------------------------------------------

def build_remedial_plan(
    telemetry: Dict[str, Any],
    health_threshold: float = 0.7,
) -> Dict[str, Any]:
    """
    Construct a structured remedial plan object:

    {
      "janet_version": ...,
      "stage": ...,
      "episodes_file": ...,
      "health_threshold": 0.7,
      "weak_organs": [...],
      "recommendations": [
        {
          "organ": "...",
          "health": 0.42,
          "episodes": 5,
          "concepts": [
            {
              "name": "Reversed Cycle",
              "difficulty": 1.6,
              "episodes": 3,
              "avg_spiral_score": 1.5,
              "idk_rate": 0.2,
              "suggested_lessons": 4
            },
            ...
          ]
        },
        ...
      ]
    }
    """
    organs = telemetry.get("organs", {})
    concepts = telemetry.get("concepts", {})

    weak_organs = pick_weak_organs(telemetry, threshold=health_threshold)

    recs = []
    for organ_name, organ_info in weak_organs:
        ranked = rank_concepts_for_organ(organ_name, concepts, top_k=3)
        organ_health = float(organ_info.get("health", 0.0))
        organ_eps = int(organ_info.get("episodes", 0))

        concept_recs = []
        for cname, cstats in ranked:
            difficulty = float(cstats.get("difficulty", 0.0))
            episodes = int(cstats.get("episodes", 0))
            avg_spiral = float(cstats.get("avg_spiral_score", 0.0))
            idk_rate = float(cstats.get("idk_rate", 0.0))

            # crude heuristic for number of remedial lessons:
            # more difficulty, fewer existing episodes → more new lessons
            base = 2
            extra = 0
            if difficulty > 1.0:
                extra += 2
            if difficulty > 2.0:
                extra += 2
            if episodes < 3:
                extra += 1

            suggested_lessons = base + extra

            concept_recs.append(
                {
                    "name": cname,
                    "difficulty": round(difficulty, 3),
                    "episodes": episodes,
                    "avg_spiral_score": round(avg_spiral, 3),
                    "idk_rate": round(idk_rate, 3),
                    "suggested_lessons": suggested_lessons,
                }
            )

        recs.append(
            {
                "organ": organ_name,
                "health": round(organ_health, 3),
                "episodes": organ_eps,
                "concepts": concept_recs,
            }
        )

    return {
        "janet_version": telemetry.get("janet_version"),
        "stage": telemetry.get("stage"),
        "episodes_file": telemetry.get("episodes_file", EPISODES_FILE),
        "health_threshold": health_threshold,
        "weak_organs": [name for name, _ in weak_organs],
        "recommendations": recs,
    }


# --------------------------------------------------------------------
# Writers
# --------------------------------------------------------------------

def write_remedial_json(plan: Dict[str, Any], path: Path) -> None:
    path.write_text(json.dumps(plan, indent=2), encoding="utf-8")


def write_remedial_md(plan: Dict[str, Any], path: Path) -> None:
    lines: List[str] = []

    lines.append("# Janet Remedial Plan")
    lines.append("")
    lines.append(f"- Janet version: `{plan.get('janet_version')}`")
    lines.append(f"- Stage: `{plan.get('stage')}`")
    lines.append(f"- Episodes file: `{plan.get('episodes_file')}`")
    lines.append(f"- Health threshold: `{plan.get('health_threshold')}`")
    lines.append("")

    weak = plan.get("weak_organs", [])
    if not weak:
        lines.append("## All organs are at or above the health threshold. 🎉")
        lines.append("")
    else:
        lines.append("## Weak Organs (below threshold)")
        lines.append("")
        for name in weak:
            lines.append(f"- {name}")
        lines.append("")

    lines.append("## Organ-by-Organ Recommendations")
    lines.append("")
    for rec in plan.get("recommendations", []):
        lines.append(f"### {rec['organ']}")
        lines.append(f"- Health: `{rec['health']}`")
        lines.append(f"- Episodes exercising this organ: `{rec['episodes']}`")
        lines.append("")

        concepts = rec.get("concepts", [])
        if not concepts:
            lines.append("_No specific concepts identified for remediation._")
            lines.append("")
            continue

        lines.append("**Target concepts for remediation:**")
        lines.append("")
        for c in concepts:
            lines.append(f"- **{c['name']}**")
            lines.append(f"  - Difficulty score: `{c['difficulty']}`")
            lines.append(f"  - Episodes so far: `{c['episodes']}`")
            lines.append(f"  - Avg spiral score: `{c['avg_spiral_score']}`")
            lines.append(f"  - I-don't-know rate: `{c['idk_rate']}`")
            lines.append(f"  - ➜ Suggested new lessons: `{c['suggested_lessons']}`")
            lines.append("")

        # Suggested teacher prompt
        concept_list = ", ".join(c["name"] for c in concepts)
        lines.append("**Suggested teacher prompt template:**")
        lines.append("")
        lines.append("```text")
        lines.append(
            f"Generate {{N}} new remedial lessons for concept(s): {concept_list}."
        )
        lines.append(
            "Focus on strengthening Janet's understanding while reducing spirals "
            "and encouraging clear, concise restatements."
        )
        lines.append("```")
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


# --------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build a remedial lesson plan for Janet from telemetry."
    )
    parser.add_argument(
        "--telemetry",
        type=str,
        default=TELEMETRY_JSON,
        help="Path to telemetry_log.json (default: telemetry_log.json)",
    )
    parser.add_argument(
        "--episodes",
        type=str,
        default=EPISODES_FILE,
        help="Path to episodes.jsonl if telemetry needs rebuilding "
             "(default: episodes.jsonl)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.7,
        help="Health threshold for marking organs as weak (default: 0.7)",
    )
    parser.add_argument(
        "--out-json",
        type=str,
        default=REMEDIAL_JSON,
        help="Output JSON file (default: remedial_plan.json)",
    )
    parser.add_argument(
        "--out-md",
        type=str,
        default=REMEDIAL_MD,
        help="Output Markdown file (default: remedial_plan.md)",
    )
    args = parser.parse_args()

    telemetry_path = Path(args.telemetry)
    episodes_path = Path(args.episodes)

    telemetry = load_or_build_telemetry(telemetry_path, episodes_path)
    plan = build_remedial_plan(telemetry, health_threshold=args.threshold)

    write_remedial_json(plan, Path(args.out_json))
    write_remedial_md(plan, Path(args.out_md))

    print(f"[remediate] Using telemetry: {telemetry_path}")
    print(f"[remediate] Wrote remedial JSON to: {args.out_json}")
    print(f"[remediate] Wrote remedial Markdown to: {args.out_md}")


if __name__ == "__main__":
    main()
