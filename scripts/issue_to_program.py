#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = ROOT / "data" / "programs"

HEADING_RE = re.compile(r"^###\s+(.+?)\s*$", re.M)
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

FIELD_MAP = {
    "program name": "program_name",
    "platform": "platform",
    "program url": "program_url",
    "display on site": "display",
    "experience month": "experience_date",
    "review month": "experience_date",
    "overall rating": "rating",
    "response time": "response_time",
    "triage quality": "triage_quality",
    "payment reliability": "payment_reliability",
    "scope accuracy": "scope_accuracy",
    "communication": "communication",
    "public note": "note",
}

RESPONSE_TIME = {"fast", "medium", "slow", "ghosted", "unknown"}
QUALITY = {"excellent", "good", "average", "poor", "unknown"}
PAYMENT = {"excellent", "good", "average", "poor", "unpaid", "not-applicable", "unknown"}
COMMUNICATION = {"excellent", "good", "average", "poor", "none", "unknown"}
DISPLAY_MODES = {"github", "anonymous"}

PLATFORM_ALIASES = {
    "hacker-one": "hackerone",
    "hackerone": "hackerone",
    "bug-crowd": "bugcrowd",
    "bugcrowd": "bugcrowd",
    "inti-griti": "intigriti",
    "intigriti": "intigriti",
    "yes-we-hack": "yeswehack",
    "yeswehack": "yeswehack",
    "immune-fi": "immunefi",
    "immunefi": "immunefi",
    "code-4-rena": "code4rena",
    "code4rena": "code4rena",
    "hacken-proof": "hackenproof",
    "hackenproof": "hackenproof",
    "code-hawks": "codehawks",
    "codehawks": "codehawks",
    "self-hosted": "self-hosted",
    "selfhosted": "self-hosted",
}


class IndentedDumper(yaml.SafeDumper):
    def increase_indent(self, flow: bool = False, indentless: bool = False) -> Any:
        return super().increase_indent(flow, False)


def slugify(value: str, fallback: str) -> str:
    normalized = (
        value.encode("ascii", "ignore")
        .decode("ascii")
        .lower()
    )
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized)
    normalized = re.sub(r"-{2,}", "-", normalized).strip("-")
    return normalized if SLUG_RE.match(normalized) else fallback


def normalize_platform(value: str, program_url: str) -> str:
    raw = slugify(value, "")
    if raw in PLATFORM_ALIASES:
        return PLATFORM_ALIASES[raw]

    url = program_url.lower()
    if not raw:
        if "hackerone.com/" in url:
            return "hackerone"
        if "bugcrowd.com/" in url:
            return "bugcrowd"
        if "intigriti.com/programs/" in url:
            return "intigriti"
        if "yeswehack.com/programs/" in url:
            return "yeswehack"
        if "immunefi.com/bug-bounty/" in url:
            return "immunefi"
        if "code4rena.com/" in url:
            return "code4rena"
        if "sherlock.xyz/" in url:
            return "sherlock"
        if "cantina.xyz/" in url:
            return "cantina"
        if "hackenproof.com/" in url:
            return "hackenproof"
        if "hats.finance/" in url:
            return "hats"
        if "codehawks.com/" in url:
            return "codehawks"
        return "self-hosted"

    return raw


def parse_issue_form(body: str) -> dict[str, str]:
    matches = list(HEADING_RE.finditer(body))
    fields: dict[str, str] = {}

    for index, match in enumerate(matches):
        label = match.group(1).strip().lower()
        key = FIELD_MAP.get(label)
        if not key:
            continue

        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        value = body[start:end].strip()
        if value == "_No response_":
            value = ""
        fields[key] = value

    return fields


def load_yaml(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    return data if isinstance(data, dict) else None


def dump_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        yaml.dump(data, handle, Dumper=IndentedDumper, sort_keys=False, allow_unicode=False)


def program_files() -> list[Path]:
    if not DATA_ROOT.exists():
        return []
    return sorted(DATA_ROOT.glob("*/*.yml")) + sorted(DATA_ROOT.glob("*/*.yaml"))


def normalized_url(value: str) -> str:
    return value.strip().rstrip("/").lower()


def find_program(platform: str, slug: str, name: str, program_url: str) -> Path:
    target_url = normalized_url(program_url)
    target_name = name.strip().lower()

    fallback = DATA_ROOT / platform / f"{slug}.yml"
    for path in program_files():
        data = load_yaml(path)
        program = data.get("program") if data else None
        if not isinstance(program, dict):
            continue

        existing_url = program.get("program_url")
        if isinstance(existing_url, str) and normalized_url(existing_url) == target_url:
            return path

        existing_platform = program.get("platform")
        existing_slug = program.get("slug")
        if existing_platform == platform and existing_slug == slug:
            return path

        existing_name = program.get("name")
        if isinstance(existing_name, str) and existing_name.strip().lower() == target_name:
            return path

    return fallback


def required(fields: dict[str, str], key: str) -> str:
    value = fields.get(key, "").strip()
    if not value:
        raise ValueError(f"missing required Issue Form field: {key}")
    return value


def is_date(value: str, fmt: str) -> bool:
    try:
        dt.datetime.strptime(value, fmt)
        return True
    except ValueError:
        return False


def validate_choice(fields: dict[str, str], key: str, allowed: set[str]) -> str:
    value = required(fields, key)
    if value not in allowed:
        raise ValueError(f"invalid Issue Form field: {key} must be one of {', '.join(sorted(allowed))}")
    return value


def validate_issue_fields(fields: dict[str, str], platform: str) -> int:
    required(fields, "program_name")
    required(fields, "platform")
    program_url = required(fields, "program_url")
    if not program_url.startswith("https://"):
        raise ValueError("invalid Issue Form field: program_url must be an https URL")
    if not SLUG_RE.match(platform):
        raise ValueError("invalid Issue Form field: platform must normalize to a lowercase slug")

    validate_choice(fields, "display", DISPLAY_MODES)
    rating_text = required(fields, "rating")
    try:
        rating = int(rating_text)
    except ValueError as exc:
        raise ValueError("invalid Issue Form field: rating must be an integer from 1 to 5") from exc
    if not 1 <= rating <= 5:
        raise ValueError("invalid Issue Form field: rating must be an integer from 1 to 5")

    validate_choice(fields, "response_time", RESPONSE_TIME)
    validate_choice(fields, "triage_quality", QUALITY)
    validate_choice(fields, "payment_reliability", PAYMENT)
    validate_choice(fields, "scope_accuracy", QUALITY)
    validate_choice(fields, "communication", COMMUNICATION)

    note = fields.get("note", "")
    if len(note) > 500:
        raise ValueError("invalid Issue Form field: note must be 500 characters or fewer")

    return rating


def submitted_date(issue: dict[str, Any]) -> str:
    created_at = issue.get("created_at")
    if isinstance(created_at, str) and created_at:
        return created_at[:10]
    return dt.date.today().isoformat()


def review_month(issue: dict[str, Any]) -> str:
    return submitted_date(issue)[:7]


def build_review(fields: dict[str, str], author: str, issue: dict[str, Any], rating: int) -> dict[str, Any]:
    note = fields.get("note", "").strip()
    review: dict[str, Any] = {
        "reviewer": {
            "github": author,
            "display": required(fields, "display"),
        },
        "experience_date": review_month(issue),
        "submitted_at": submitted_date(issue),
        "rating": rating,
        "response_time": required(fields, "response_time"),
        "triage_quality": required(fields, "triage_quality"),
        "payment_reliability": required(fields, "payment_reliability"),
        "scope_accuracy": required(fields, "scope_accuracy"),
        "communication": required(fields, "communication"),
    }
    if note:
        review["note"] = note
    return review


def upsert_review(data: dict[str, Any], review: dict[str, Any], author: str) -> str:
    reviews = data.setdefault("reviews", [])
    if not isinstance(reviews, list):
        raise ValueError("target program file has invalid reviews field")

    for index, existing in enumerate(reviews):
        if not isinstance(existing, dict):
            continue
        reviewer = existing.get("reviewer")
        if isinstance(reviewer, dict) and str(reviewer.get("github", "")).lower() == author.lower():
            reviews[index] = review
            return "updated"

    reviews.append(review)
    return "created"


def build_program_data(fields: dict[str, str], platform: str, slug: str, review: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "program": {
            "name": required(fields, "program_name"),
            "platform": platform,
            "slug": slug,
            "program_url": required(fields, "program_url"),
        },
        "reviews": [review],
    }


def write_outputs(path: Path, action: str, data: dict[str, str], output_path: Path | None, report_path: Path | None) -> None:
    report = "\n".join(
        [
            "# Review submission conversion",
            "",
            f"Status: {action}",
            f"Program: {data['program_name']}",
            f"Platform: {data['platform']}",
            f"Path: `{path.relative_to(ROOT).as_posix()}`",
            "",
        ]
    )
    print(report)

    if report_path:
        report_path.write_text(report, encoding="utf-8")

    if output_path:
        with output_path.open("a", encoding="utf-8") as handle:
            handle.write(f"program_name={data['program_name']}\n")
            handle.write(f"platform={data['platform']}\n")
            handle.write(f"program_path={path.relative_to(ROOT).as_posix()}\n")
            handle.write(f"conversion_status={action}\n")


def convert(event_path: Path, github_output: Path | None, report_path: Path | None) -> int:
    event = json.loads(event_path.read_text(encoding="utf-8-sig"))
    issue = event.get("issue")
    if not isinstance(issue, dict):
        raise ValueError("event does not contain an issue object")

    user = issue.get("user")
    author = user.get("login") if isinstance(user, dict) else None
    if not isinstance(author, str) or not author:
        raise ValueError("issue author is missing")

    body = issue.get("body")
    if not isinstance(body, str) or not body.strip():
        raise ValueError("issue body is empty")

    fields = parse_issue_form(body)
    program_name = required(fields, "program_name")
    program_url = required(fields, "program_url")
    platform = normalize_platform(fields.get("platform", ""), program_url)
    rating = validate_issue_fields(fields, platform)
    slug = slugify(program_name, "program")
    review = build_review(fields, author, issue, rating)
    path = find_program(platform, slug, program_name, program_url)

    existing = load_yaml(path)
    if existing:
        action = upsert_review(existing, review, author)
        dump_yaml(path, existing)
    else:
        action = "created"
        dump_yaml(path, build_program_data(fields, platform, slug, review))

    output_data = {
        "program_name": program_name,
        "platform": platform,
    }
    write_outputs(path, action, output_data, github_output, report_path)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert a review-submission Issue Form into bbrep YAML.")
    parser.add_argument("--event", type=Path, required=True, help="Path to the GitHub event JSON.")
    parser.add_argument("--github-output", type=Path, help="Path from the GITHUB_OUTPUT environment variable.")
    parser.add_argument("--report", type=Path, help="Write a Markdown conversion report.")
    args = parser.parse_args()

    try:
        return convert(args.event, args.github_output, args.report)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
