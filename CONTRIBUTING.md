# Contributing to bbrep

Thanks for helping make bug bounty program reputation more transparent.

This repository is public. Do not include private report details, confidential program data, vulnerability payloads, customer data, bounty IDs, internal emails, or anything covered by a program's disclosure restrictions.

## Review Rules

- Only public VDP/BBP programs are accepted.
- Use a public program URL as evidence that the program exists.
- Keep notes factual, concise, and useful to other researchers.
- Do not include private vulnerability details or confidential communications.
- If you already submitted a review for the same program, update that entry instead of adding another one.
- Set `reviewer.display` to `anonymous` if you do not want your handle shown on the site. The PR author remains visible in GitHub history.

## Submit by Issue

The normal submission path is a GitHub Issue labeled `review-submission`. You do not need to edit YAML by hand.

1. Fill the review fields on the contribution page.
2. Copy the generated Issue body.
3. Create a GitHub Issue with the `review-submission` label.
4. GitHub Actions converts the Issue into `data/programs/{platform}/{slug}.yml`.
5. The action opens or updates a Pull Request for maintainer review.

The Issue author becomes the canonical reviewer identity. If the same GitHub account submits another review for the same program, the generated Pull Request updates that account's existing review instead of adding a duplicate.

Manual Pull Requests are still supported for maintainers and advanced contributors, but public contributors should prefer the Issue flow.

## Program Matching

Issue submissions are matched to existing programs by public program URL, then by platform/slug, then by normalized program name. If a match is found, the new review is added to that program. If the same Issue author already reviewed that program, their old review is replaced.

Use the public program page as `Program URL`. Platform can be a known platform such as `hackerone`, `bugcrowd`, `intigriti`, `immunefi`, or a custom slug for self-hosted/custom programs.

## Rating Guidance

Use the overall `rating` as a practical researcher experience score:

- `5`: consistently excellent and worth prioritizing.
- `4`: good program with minor friction.
- `3`: workable but mixed.
- `2`: significant friction; researchers should be cautious.
- `1`: severe issues such as ghosting, unreliable payment, or materially misleading scope.

## Problem Tags

Problem tags are optional short markers for common bad-program patterns. Add them directly inside the public note as hashtags. The CI extracts known tags, normalizes aliases, and counts them on the site like small reaction counters.

Available tags:

| Tag | Meaning |
| --- | --- |
| `#cvssmagic` | severity is reduced through questionable CVSS interpretation |
| `#scam` | strong warning signs around legitimacy or payout behavior |
| `#ghosting` | reports are left without meaningful response |
| `#lowball` | payout appears materially lower than impact or policy expectation |
| `#slowpay` | payment is accepted but unusually slow or unreliable |
| `#scopechaos` | scope or policy interpretation is inconsistent or confusing |
| `#wontfix` | repeated weak closures or wontfix loops |

Use tags sparingly. The public note should still explain the practical issue in plain language.

## Validation

The Pull Request checks validate schema, path consistency, platform URL shape, duplicate reviewers, whether public program URLs are reachable, and whether a PR only adds or updates the review belonging to the PR author. Maintainers still perform editorial review before merge.
