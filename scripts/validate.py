#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = ROOT / "data" / "programs"

KNOWN_PLATFORMS = {
    "hackerone",
    "bugcrowd",
    "intigriti",
    "yeswehack",
    "immunefi",
    "code4rena",
    "sherlock",
    "cantina",
    "hackenproof",
    "hats",
    "codehawks",
    "self-hosted",
}
URL_PATTERNS = {
    "hackerone": re.compile(r"^https://(www\.)?hackerone\.com/[^/?#]+/?(?:[?#].*)?$", re.I),
    "bugcrowd": re.compile(r"^https://(www\.)?bugcrowd\.com/[^/?#]+/?(?:[?#].*)?$", re.I),
    "intigriti": re.compile(
        r"^https://((www\.)?intigriti\.com/programs/[^/?#]+/[^/?#]+/?|app\.intigriti\.com/researcher/programs/[^/?#]+/[^/?#]+/detail)(?:[?#].*)?$",
        re.I,
    ),
    "yeswehack": re.compile(r"^https://(www\.)?yeswehack\.com/programs/[^/?#]+/?(?:[?#].*)?$", re.I),
    "immunefi": re.compile(r"^https://(www\.)?immunefi\.com/bug-bounty/[^/?#]+/?(?:[?#].*)?$", re.I),
    "code4rena": re.compile(r"^https://(www\.)?code4rena\.com/[^ ]+$", re.I),
    "sherlock": re.compile(r"^https://(www\.)?sherlock\.xyz/[^ ]+$", re.I),
    "cantina": re.compile(r"^https://(www\.)?cantina\.xyz/[^ ]+$", re.I),
    "hackenproof": re.compile(r"^https://(www\.)?hackenproof\.com/[^ ]+$", re.I),
    "hats": re.compile(r"^https://([^/]+\.)?hats\.finance/[^ ]+$", re.I),
    "codehawks": re.compile(r"^https://(www\.)?codehawks\.com/[^ ]+$", re.I),
}

RESPONSE_TIME = {"fast", "medium", "slow", "ghosted", "unknown"}
QUALITY = {"excellent", "good", "average", "poor", "unknown"}
PAYMENT = {"excellent", "good", "average", "poor", "unpaid", "not-applicable", "unknown"}
COMMUNICATION = {"excellent", "good", "average", "poor", "none", "unknown"}
DISPLAY_MODES = {"github", "anonymous"}

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
GITHUB_HANDLE_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?$")
TAG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class ValidationReport:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.checked_urls: list[str] = []

    @property
    def ok(self) -> bool:
        return not self.errors

    def error(self, path: Path, message: str) -> None:
        self.errors.append(f"{path.as_posix()}: {message}")

    def warn(self, path: Path, message: str) -> None:
        self.warnings.append(f"{path.as_posix()}: {message}")

    def markdown(self) -> str:
        lines = ["# bbrep validation report", ""]
        lines.append("Status: PASS" if self.ok else "Status: FAIL")
        lines.append("")

        if self.errors:
            lines.append("## Errors")
            lines.extend(f"- {item}" for item in self.errors)
            lines.append("")

        if self.warnings:
            lines.append("## Warnings")
            lines.extend(f"- {item}" for item in self.warnings)
            lines.append("")

        if self.checked_urls:
            lines.append("## Checked URLs")
            lines.extend(f"- {item}" for item in self.checked_urls)
            lines.append("")

        if self.ok and not self.warnings:
            lines.append("Schema, URL shape, duplicate reviewer, and reachability checks passed.")

        return "\n".join(lines).strip() + "\n"


def load_yaml(path: Path, report: ValidationReport) -> dict[str, Any] | None:
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
    except yaml.YAMLError as exc:
        report.error(path, f"invalid YAML: {exc}")
        return None

    if not isinstance(data, dict):
        report.error(path, "root document must be a mapping")
        return None

    return data


def load_yaml_text(text: str) -> dict[str, Any] | None:
    data = yaml.safe_load(text)
    return data if isinstance(data, dict) else None


def is_date(value: Any, fmt: str) -> bool:
    if not isinstance(value, str):
        return False
    try:
        dt.datetime.strptime(value, fmt)
        return True
    except ValueError:
        return False


def validate_url_reachable(url: str, timeout: float) -> tuple[bool, str]:
    request = urllib.request.Request(
        url,
        method="HEAD",
        headers={"User-Agent": "bbrep-validator/0.1 (+https://github.com/rafabd1/bbrep)"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return 200 <= response.status < 400, f"HTTP {response.status}"
    except urllib.error.HTTPError as exc:
        if exc.code == 405:
            get_request = urllib.request.Request(
                url,
                method="GET",
                headers={"User-Agent": "bbrep-validator/0.1 (+https://github.com/rafabd1/bbrep)"},
            )
            try:
                with urllib.request.urlopen(get_request, timeout=timeout) as response:
                    return 200 <= response.status < 400, f"HTTP {response.status}"
            except Exception as inner_exc:
                return False, str(inner_exc)
        return False, f"HTTP {exc.code}"
    except Exception as exc:
        return False, str(exc)


def validate_program_file(path: Path, report: ValidationReport, check_urls: bool, timeout: float) -> None:
    data = load_yaml(path, report)
    if data is None:
        return

    rel = path.relative_to(ROOT)
    expected_platform = rel.parts[-2]
    expected_slug = path.stem

    if data.get("schema_version") != 1:
        report.error(rel, "schema_version must be 1")

    program = data.get("program")
    if not isinstance(program, dict):
        report.error(rel, "program must be a mapping")
        return

    name = program.get("name")
    platform = program.get("platform")
    slug = program.get("slug")
    program_url = program.get("program_url")
    policy_url = program.get("policy_url")

    if not isinstance(name, str) or not name.strip():
        report.error(rel, "program.name is required")
    if not isinstance(platform, str) or not SLUG_RE.match(platform):
        report.error(rel, "program.platform must be a lowercase slug")
    elif platform != expected_platform:
        report.error(rel, f"program.platform must match path platform '{expected_platform}'")
    if not isinstance(slug, str) or not SLUG_RE.match(slug):
        report.error(rel, "program.slug must be a lowercase slug")
    elif slug != expected_slug:
        report.error(rel, f"program.slug must match filename '{expected_slug}'")

    if not isinstance(program_url, str) or not program_url.startswith("https://"):
        report.error(rel, "program.program_url must be an https URL")
    elif platform in URL_PATTERNS and not URL_PATTERNS[platform].match(program_url):
        report.error(rel, f"program.program_url does not match platform '{platform}'")
    elif check_urls:
        reachable, detail = validate_url_reachable(program_url, timeout)
        if reachable:
            report.checked_urls.append(f"{program_url} ({detail})")
        else:
            report.error(rel, f"program.program_url is not reachable: {detail}")

    if policy_url is not None and (not isinstance(policy_url, str) or not policy_url.startswith("https://")):
        report.error(rel, "program.policy_url must be an https URL when present")

    reviews = data.get("reviews")
    if not isinstance(reviews, list):
        report.error(rel, "reviews must be a list")
        return
    if not reviews:
        report.warn(rel, "program has no reviews yet")

    reviewers: dict[str, int] = {}
    for index, review in enumerate(reviews):
        validate_review(rel, index, review, report, reviewers)


def validate_review(
    rel: Path,
    index: int,
    review: Any,
    report: ValidationReport,
    reviewers: dict[str, int],
) -> None:
    prefix = f"reviews[{index}]"
    if not isinstance(review, dict):
        report.error(rel, f"{prefix} must be a mapping")
        return

    reviewer = review.get("reviewer")
    if not isinstance(reviewer, dict):
        report.error(rel, f"{prefix}.reviewer must be a mapping")
    else:
        github = reviewer.get("github")
        display = reviewer.get("display")
        if not isinstance(github, str) or not GITHUB_HANDLE_RE.match(github):
            report.error(rel, f"{prefix}.reviewer.github must be the PR author's GitHub handle")
        else:
            key = github.lower()
            if key in reviewers:
                report.error(
                    rel,
                    f"{prefix}.reviewer.github duplicates reviews[{reviewers[key]}]; update the existing review instead",
                )
            reviewers[key] = index

        if display not in DISPLAY_MODES:
            report.error(rel, f"{prefix}.reviewer.display must be github or anonymous")

    if not is_date(review.get("experience_date"), "%Y-%m"):
        report.error(rel, f"{prefix}.experience_date must use YYYY-MM")
    if not is_date(review.get("submitted_at"), "%Y-%m-%d"):
        report.error(rel, f"{prefix}.submitted_at must use YYYY-MM-DD")

    rating = review.get("rating")
    if not isinstance(rating, int) or isinstance(rating, bool) or not 1 <= rating <= 5:
        report.error(rel, f"{prefix}.rating must be an integer from 1 to 5")

    check_enum(rel, report, prefix, review, "response_time", RESPONSE_TIME)
    check_enum(rel, report, prefix, review, "triage_quality", QUALITY)
    check_enum(rel, report, prefix, review, "payment_reliability", PAYMENT)
    check_enum(rel, report, prefix, review, "scope_accuracy", QUALITY)
    check_enum(rel, report, prefix, review, "communication", COMMUNICATION)

    tags = review.get("tags", [])
    if tags is None:
        tags = []
    if not isinstance(tags, list) or any(not isinstance(tag, str) or not TAG_RE.match(tag) for tag in tags):
        report.error(rel, f"{prefix}.tags must be a list of lowercase slugs")

    note = review.get("note", "")
    if note is not None:
        if not isinstance(note, str):
            report.error(rel, f"{prefix}.note must be a string")
        elif len(note) > 500:
            report.error(rel, f"{prefix}.note must be 500 characters or fewer")


def check_enum(
    rel: Path,
    report: ValidationReport,
    prefix: str,
    review: dict[str, Any],
    key: str,
    allowed: set[str],
) -> None:
    value = review.get(key)
    if value not in allowed:
        report.error(rel, f"{prefix}.{key} must be one of: {', '.join(sorted(allowed))}")


def program_files() -> list[Path]:
    if not DATA_ROOT.exists():
        return []
    return sorted(DATA_ROOT.glob("*/*.yml")) + sorted(DATA_ROOT.glob("*/*.yaml"))


def review_map(data: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not data:
        return {}
    reviews = data.get("reviews")
    if not isinstance(reviews, list):
        return {}

    mapped: dict[str, dict[str, Any]] = {}
    for review in reviews:
        if not isinstance(review, dict):
            continue
        reviewer = review.get("reviewer")
        if not isinstance(reviewer, dict):
            continue
        github = reviewer.get("github")
        if isinstance(github, str):
            mapped[github.lower()] = review
    return mapped


def git_output(args: list[str]) -> str:
    return subprocess.check_output(args, cwd=ROOT, text=True, stderr=subprocess.DEVNULL)


def git_show_text(ref: str, rel_path: str) -> str | None:
    try:
        return git_output(["git", "show", f"{ref}:{rel_path}"])
    except subprocess.CalledProcessError:
        return None


def changed_program_files(base_ref: str) -> list[Path]:
    try:
        output = git_output(["git", "diff", "--name-only", f"{base_ref}...HEAD", "--", "data/programs"])
    except subprocess.CalledProcessError:
        output = git_output(["git", "diff", "--name-only", f"{base_ref}", "--", "data/programs"])

    try:
        untracked = git_output(["git", "ls-files", "--others", "--exclude-standard", "--", "data/programs"])
    except subprocess.CalledProcessError:
        untracked = ""

    files = []
    for line in [*output.splitlines(), *untracked.splitlines()]:
        rel = Path(line.strip())
        if rel.suffix.lower() in {".yml", ".yaml"}:
            files.append(ROOT / rel)
    return sorted(set(files))


def validate_pr_author(report: ValidationReport, pr_author: str, base_ref: str) -> None:
    expected = pr_author.lower()
    for path in changed_program_files(base_ref):
        rel = path.relative_to(ROOT)
        current = load_yaml(path, report) if path.exists() else None
        base_text = git_show_text(base_ref, rel.as_posix())
        base = load_yaml_text(base_text) if base_text else None

        current_reviews = review_map(current)
        base_reviews = review_map(base)
        changed_handles = {
            handle
            for handle, review in current_reviews.items()
            if base_reviews.get(handle) != review
        }
        removed_handles = set(base_reviews) - set(current_reviews)

        for handle in sorted(changed_handles | removed_handles):
            if handle != expected:
                report.error(
                    rel,
                    f"PR author '{pr_author}' cannot add, update, or remove review for GitHub user '{handle}'",
                )


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate bbrep data files.")
    parser.add_argument("--no-url-check", action="store_true", help="Skip HTTP reachability checks.")
    parser.add_argument("--timeout", type=float, default=8.0, help="URL check timeout in seconds.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument("--report", type=Path, help="Write a Markdown validation report.")
    parser.add_argument("--pr-author", default=os.getenv("BBREP_PR_AUTHOR"), help="GitHub PR author handle.")
    parser.add_argument("--base-ref", default=os.getenv("BBREP_BASE_REF", "origin/main"), help="Base git ref for PR diff checks.")
    parser.add_argument(
        "--allow-generated-review-submission",
        action="store_true",
        default=os.getenv("BBREP_ALLOW_GENERATED_REVIEW_SUBMISSION", "").lower() == "true",
        help="Allow GitHub Actions generated review-submission PRs to contain the Issue author's review.",
    )
    args = parser.parse_args()

    report = ValidationReport()
    for path in program_files():
        validate_program_file(path, report, check_urls=not args.no_url_check, timeout=args.timeout)

    if args.pr_author and not args.allow_generated_review_submission:
        validate_pr_author(report, args.pr_author, args.base_ref)

    if args.report:
        args.report.write_text(report.markdown(), encoding="utf-8")

    if args.json:
        print(json.dumps({"ok": report.ok, "errors": report.errors, "warnings": report.warnings}, indent=2))
    else:
        print(report.markdown())

    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
