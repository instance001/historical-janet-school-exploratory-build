import json
from pathlib import Path
from typing import Dict, Any, List


EPISODES_FILE = "memory/episodes.jsonl"
TELEMETRY_JSON = "telemetry_log.json"
TELEMETRY_MD = "telemetry_log.md"


def load_episodes(path: Path) -> List[Dict[str, Any]]:
    """Load Janet's reasoning episodes from a JSONL file."""
    episodes: List[Dict[str, Any]] = []
    if not path.exists():
        raise FileNotFoundError(f"episodes file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            episodes.append(json.loads(line))
    return episodes


def spiral_score(text: str) -> int:
    """Very rough 'spiral' detector based on repetitive 'We...' fragments."""
    score = 0
    # rough heuristics – you can tweak these over time
    score += text.count("We…")
    score += text.count("We...")
    score += text.count("We..")
    # sometimes it's just "We." repeated a lot
    score += text.count("We.\n")
    # big clumps of 'We' are extra weight
    score += text.count("We\nWe")
    return score


def extract_monologue_and_final(text: str) -> Dict[str, Any]:
    """
    Split inner monologue vs final answer heuristically.

    Anything before the first 'Restatement:' is treated as inner monologue,
    anything from 'Restatement:' onward as final output.
    """
    idx = text.find("Restatement:")
    if idx == -1:
        return {"monologue": text, "final": ""}
    return {
        "monologue": text[:idx],
        "final": text[idx:],
    }


def compute_concept_stats(episodes: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Aggregate basic stats per concept."""
    stats: Dict[str, Dict[str, Any]] = {}
    for ep in episodes:
        concept = ep.get("meta", {}).get("concept", "UNKNOWN")
        grade = ep.get("state_snapshot", {}).get("grade")
        out = ep.get("output", "")
        split = extract_monologue_and_final(out)
        mono = split["monologue"]

        if concept not in stats:
            stats[concept] = {
                "count": 0,
                "grades": set(),
                "total_monologue_chars": 0,
                "total_monologue_tokens": 0,
                "total_spiral_score": 0,
                "idk_count": 0,
            }

        s = stats[concept]
        s["count"] += 1
        if grade is not None:
            s["grades"].add(grade)
        s["total_monologue_chars"] += len(mono)
        s["total_monologue_tokens"] += max(1, len(mono.split()))
        s["total_spiral_score"] += spiral_score(mono)
        if "I don't know" in out:
            s["idk_count"] += 1

    # finalize and normalize
    finalized: Dict[str, Dict[str, Any]] = {}
    for concept, s in stats.items():
        count = max(1, s["count"])
        finalized[concept] = {
            "episodes": s["count"],
            "grades": sorted(str(g) for g in s["grades"]),
            "avg_monologue_chars": s["total_monologue_chars"] / count,
            "avg_monologue_tokens": s["total_monologue_tokens"] / count,
            "avg_spiral_score": s["total_spiral_score"] / count,
            "idk_rate": s["idk_count"] / count,
        }
    return finalized


def compute_global_metrics(concept_stats: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Compute coarse global telemetry from per-concept stats."""
    if not concept_stats:
        return {}

    total_eps = sum(s["episodes"] for s in concept_stats.values())
    if total_eps == 0:
        return {}

    total_spirals = sum(s["avg_spiral_score"] * s["episodes"] for s in concept_stats.values())
    total_idk = sum(s["idk_rate"] * s["episodes"] for s in concept_stats.values())
    total_tokens = sum(s["avg_monologue_tokens"] * s["episodes"] for s in concept_stats.values())

    # simple, tunable heuristics
    spiral_per_episode = total_spirals / total_eps
    idk_rate = total_idk / total_eps

    # normalize spiral into [0,1] where 0 = none, 1 = a lot
    spiral_norm = min(1.0, spiral_per_episode / 10.0)
    stability_index = max(0.0, 1.0 - spiral_norm)

    # coherence: fewer "I don't know" = higher
    coherence_index = max(0.0, 1.0 - idk_rate)

    # average "thinking volume"
    avg_tokens = total_tokens / total_eps if total_eps else 0.0

    return {
        "total_episodes": total_eps,
        "avg_spiral_per_episode": spiral_per_episode,
        "idk_rate": idk_rate,
        "stability_index": stability_index,
        "coherence_index": coherence_index,
        "avg_monologue_tokens": avg_tokens,
    }


def build_organ_view(concept_stats: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Map coarse stats into organ-health estimates.

    This is deliberately simple and transparent so you can tweak the mapping later.
    """
    # Helper to extract aggregate over a concept set
    def agg(concepts: List[str]) -> Dict[str, float]:
        eps = 0
        spirals = 0.0
        idk = 0.0
        for c in concepts:
            s = concept_stats.get(c)
            if not s:
                continue
            eps += s["episodes"]
            spirals += s["avg_spiral_score"] * s["episodes"]
            idk += s["idk_rate"] * s["episodes"]
        if eps == 0:
            return {"spirals": 0.0, "idk": 0.0, "eps": 0}
        return {"spirals": spirals / eps, "idk": idk / eps, "eps": eps}

    # buckets of concepts that roughly exercise each organ
    spo_bucket = list(concept_stats.keys())  # almost everything touches sequence perception
    reo_bucket = list(concept_stats.keys())
    bro_bucket = ["Reversed Cycle"]
    npo_bucket = ["Nested Pattern"]
    dio_bucket = ["Distractor-element Pattern"]
    pco_bucket = [
        "sequence_next",
        "Simple Alternation",
        "Double Alternation",
        "Long-cycle Repeat",
        "Offset Numeric Pattern",
        "Shape/shape/number Combo",
    ]
    mro_bucket = list(concept_stats.keys())

    spo = agg(spo_bucket)
    reo = agg(reo_bucket)
    bro = agg(bro_bucket)
    npo = agg(npo_bucket)
    dio = agg(dio_bucket)
    pco = agg(pco_bucket)
    mro = agg(mro_bucket)

    def health_from_spiral(sp: float) -> float:
        # very soft curve: more spirals => lower health
        return max(0.0, 1.0 - min(1.0, sp / 10.0))

    organs = {
        "Sequence Perception Organ (SPO)": {
            "episodes": spo["eps"],
            "avg_spiral": spo["spirals"],
            "health": health_from_spiral(spo["spirals"]),
        },
        "Rule Extraction Organ (REO)": {
            "episodes": reo["eps"],
            "avg_spiral": reo["spirals"],
            "health": health_from_spiral(reo["spirals"]),
        },
        "Bidirectional Reasoning Organ (BRO)": {
            "episodes": bro["eps"],
            "avg_spiral": bro["spirals"],
            "health": health_from_spiral(bro["spirals"]),
        },
        "Nested Pattern Organ (NPO)": {
            "episodes": npo["eps"],
            "avg_spiral": npo["spirals"],
            "health": health_from_spiral(npo["spirals"]),
        },
        "Distractor Inhibition Organ (DIO)": {
            "episodes": dio["eps"],
            "avg_spiral": dio["spirals"],
            "health": health_from_spiral(dio["spirals"]),
        },
        "Pattern Continuation Organ (PCO)": {
            "episodes": pco["eps"],
            "avg_spiral": pco["spirals"],
            "health": health_from_spiral(pco["spirals"]),
        },
        "Meta-Restatement Organ (MRO)": {
            "episodes": mro["eps"],
            "avg_spiral": mro["spirals"],
            "health": health_from_spiral(mro["spirals"]),
        },
    }
    return organs


def build_telemetry(episodes_path: Path) -> Dict[str, Any]:
    episodes = load_episodes(episodes_path)
    concept_stats = compute_concept_stats(episodes)
    global_metrics = compute_global_metrics(concept_stats)
    organs = build_organ_view(concept_stats)

    return {
        "janet_version": "MCM-v0.1",
        "stage": "Early curriculum (Grade 0–0.5)",
        "episodes_file": str(episodes_path),
        "global": global_metrics,
        "concepts": concept_stats,
        "organs": organs,
    }


def write_json(telemetry: Dict[str, Any], out_path: Path) -> None:
    out_path.write_text(json.dumps(telemetry, indent=2), encoding="utf-8")


def write_markdown(telemetry: Dict[str, Any], out_path: Path) -> None:
    lines: List[str] = []
    g = telemetry.get("global", {})
    lines.append("# Janet Telemetry Log")
    lines.append("")
    lines.append(f"- Janet version: {telemetry.get('janet_version')}")
    lines.append(f"- Stage: {telemetry.get('stage')}")
    lines.append(f"- Episodes file: `{telemetry.get('episodes_file')}`")
    lines.append("")
    lines.append("## Global Metrics")
    lines.append("")
    for k, v in g.items():
        lines.append(f"- **{k}**: {v}")
    lines.append("")
    lines.append("## Organ Health")
    lines.append("")
    for organ, info in telemetry.get("organs", {}).items():
        h = info.get("health", 0.0)
        eps = info.get("episodes", 0)
        spirals = info.get("avg_spiral", 0.0)
        bar_len = int(h * 10)
        bar = "█" * bar_len + "░" * (10 - bar_len)
        lines.append(f"### {organ}")
        lines.append(f"- Episodes: {eps}")
        lines.append(f"- Avg spiral score: {spirals:.2f}")
        lines.append(f"- Health: `{bar}` ({h:.2f})")
        lines.append("")
    lines.append("## Concepts")
    lines.append("")
    for concept, s in telemetry.get("concepts", {}).items():
        lines.append(f"### {concept}")
        lines.append(f"- Episodes: {s['episodes']}")
        lines.append(f"- Grades: {s['grades']}")
        lines.append(f"- Avg monologue chars: {s['avg_monologue_chars']:.1f}")
        lines.append(f"- Avg monologue tokens: {s['avg_monologue_tokens']:.1f}")
        lines.append(f"- Avg spiral score: {s['avg_spiral_score']:.2f}")
        lines.append(f"- I-don't-know rate: {s['idk_rate']:.2f}")
        lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")
