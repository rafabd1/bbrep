#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any
import re

import yaml


ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = ROOT / "data" / "programs"
DOCS_ROOT = ROOT / "docs"

KNOWN_PROBLEM_TAGS = {
    "cvssmagic": "CVSS magic",
    "scam": "scam",
    "ghosting": "ghosting",
    "lowball": "lowball",
    "slowpay": "slow pay",
    "scopechaos": "scope chaos",
    "wontfix": "wontfix loop",
}
PROBLEM_TAG_ALIASES = {
    "cvss-magic": "cvssmagic",
    "ghosted": "ghosting",
    "slow-pay": "slowpay",
    "scope-chaos": "scopechaos",
    "scopebait": "scopechaos",
    "wont-fix": "wontfix",
    "wontfixloop": "wontfix",
}
HASH_TAG_RE = re.compile(r"#([a-z0-9][a-z0-9-]*)", re.I)


def program_files() -> list[Path]:
    if not DATA_ROOT.exists():
        return []
    return sorted(DATA_ROOT.glob("*/*.yml")) + sorted(DATA_ROOT.glob("*/*.yaml"))


def load_program(path: Path) -> dict[str, Any] | None:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    return data if isinstance(data, dict) else None


def escape(value: Any) -> str:
    text = "" if value is None else str(value)
    return text.replace("|", "\\|").replace("\n", " ").strip()


def reviewer_label(review: dict[str, Any]) -> str:
    reviewer = review.get("reviewer")
    if not isinstance(reviewer, dict):
        return "unknown"
    if reviewer.get("display") == "anonymous":
        return "anonymous"
    github = reviewer.get("github")
    return f"@{github}" if github else "unknown"


def rating_symbol(rating: Any) -> str:
    try:
        value = int(rating)
    except (TypeError, ValueError):
        return "-"
    if value >= 4:
        return "up"
    if value >= 3:
        return "mid"
    return "down"


def normalize_problem_tag(value: Any) -> str:
    text = str(value or "").lower().lstrip("#")
    text = re.sub(r"[^a-z0-9-]+", "-", text)
    text = re.sub(r"-{2,}", "-", text).strip("-")
    return PROBLEM_TAG_ALIASES.get(text, text)


def review_problem_tags(review: dict[str, Any]) -> list[str]:
    raw_tags = review.get("tags", [])
    if not isinstance(raw_tags, list):
        raw_tags = []
    note_tags = HASH_TAG_RE.findall(str(review.get("note", "")))

    tags: list[str] = []
    seen: set[str] = set()
    for raw in [*raw_tags, *note_tags]:
        tag = normalize_problem_tag(raw)
        if tag in KNOWN_PROBLEM_TAGS and tag not in seen:
            tags.append(tag)
            seen.add(tag)
    return tags


def collect() -> list[dict[str, Any]]:
    programs: list[dict[str, Any]] = []
    for path in program_files():
        data = load_program(path)
        if not data:
            continue
        program = data.get("program")
        reviews = data.get("reviews")
        if not isinstance(program, dict) or not isinstance(reviews, list):
            continue

        normalized_reviews = [
            review for review in reviews
            if isinstance(review, dict)
        ]
        average_rating = 0.0
        if normalized_reviews:
            average_rating = round(
                sum(int(review.get("rating", 0)) for review in normalized_reviews) / len(normalized_reviews),
                2,
            )

        programs.append(
            {
                "name": program.get("name", ""),
                "platform": program.get("platform", ""),
                "slug": program.get("slug", ""),
                "program_url": program.get("program_url", ""),
                "source_path": path.relative_to(ROOT).as_posix(),
                "average_rating": average_rating,
                "review_count": len(normalized_reviews),
                "reviews": normalized_reviews,
            }
        )
    return programs


def build_stats(programs: list[dict[str, Any]]) -> str:
    review_count = sum(program["review_count"] for program in programs)
    platforms = Counter(program["platform"] for program in programs)
    rated_programs = [program for program in programs if program["review_count"]]
    average_rating = (
        round(sum(program["average_rating"] for program in rated_programs) / len(rated_programs), 2)
        if rated_programs
        else 0
    )
    problem_tags = Counter(
        tag
        for program in programs
        for review in program["reviews"]
        for tag in review_problem_tags(review)
    )

    lines = [
        "# bbrep stats",
        "",
        "Static snapshot generated from `data/programs`.",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Programs | {len(programs)} |",
        f"| Reviews | {review_count} |",
        f"| Platforms | {len(platforms)} |",
        f"| Average program rating | {average_rating:.2f} |",
        "",
        "## Platforms",
        "",
    ]

    if platforms:
        lines.extend(["| Platform | Programs |", "| --- | ---: |"])
        for platform, count in sorted(platforms.items()):
            lines.append(f"| {escape(platform)} | {count} |")
    else:
        lines.append("No programs yet.")

    lines.extend(["", "## Problem Tags", ""])
    if problem_tags:
        lines.extend(["| Tag | Meaning | Reviews |", "| --- | --- | ---: |"])
        for tag, count in sorted(problem_tags.items(), key=lambda item: (-item[1], item[0])):
            lines.append(f"| `#{escape(tag)}` | {escape(KNOWN_PROBLEM_TAGS[tag])} | {count} |")
    else:
        lines.append("No known problem tags yet.")

    lines.extend(["", "## Programs", ""])
    if programs:
        lines.extend(["| Program | Platform | Reviews | Rating | Source |", "| --- | --- | ---: | ---: | --- |"])
        for program in sorted(programs, key=lambda item: (-item["average_rating"], item["name"].lower())):
            lines.append(
                "| "
                f"{escape(program['name'])} | "
                f"{escape(program['platform'])} | "
                f"{program['review_count']} | "
                f"{program['average_rating']:.2f} | "
                f"`{escape(program['source_path'])}` |"
            )
    else:
        lines.append("No programs yet.")

    return "\n".join(lines).strip() + "\n"


def build_reviews(programs: list[dict[str, Any]]) -> str:
    reviews: list[dict[str, Any]] = []
    for program in programs:
        for review in program["reviews"]:
            reviews.append(
                {
                    "program": program["name"],
                    "platform": program["platform"],
                    "rating": review.get("rating"),
                    "symbol": rating_symbol(review.get("rating")),
                    "reviewer": reviewer_label(review),
                    "submitted_at": review.get("submitted_at", ""),
                    "tags": review_problem_tags(review),
                    "note": review.get("note", ""),
                }
            )

    reviews.sort(key=lambda item: (str(item["submitted_at"]), str(item["program"])), reverse=True)

    lines = [
        "# bbrep reviews",
        "",
        "Static review index generated from `data/programs`.",
        "",
    ]

    if reviews:
        lines.extend(
            [
                "| Submitted | Program | Platform | Rating | Reviewer | Tags | Note |",
                "| --- | --- | --- | ---: | --- | --- | --- |",
            ]
        )
        for review in reviews:
            tags = " ".join(f"#{tag}" for tag in review["tags"])
            lines.append(
                "| "
                f"{escape(review['submitted_at'])} | "
                f"{escape(review['program'])} | "
                f"{escape(review['platform'])} | "
                f"{escape(review['symbol'])} {escape(review['rating'])}/5 | "
                f"{escape(review['reviewer'])} | "
                f"{escape(tags)} | "
                f"{escape(review['note'])} |"
            )
    else:
        lines.append("No reviews yet.")

    return "\n".join(lines).strip() + "\n"


def main() -> int:
    programs = collect()
    DOCS_ROOT.mkdir(parents=True, exist_ok=True)
    (DOCS_ROOT / "stats.md").write_text(build_stats(programs), encoding="utf-8")
    (DOCS_ROOT / "reviews.md").write_text(build_reviews(programs), encoding="utf-8")
    print("Built docs/stats.md and docs/reviews.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
