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

## Add or Update a Program

The primary submission path is the GitHub Issue Form labeled `review-submission`.

1. Open the `Submit a program review` Issue Form.
2. Fill the structured fields.
3. GitHub Actions converts the Issue into `data/programs/{platform}/{slug}.yml`.
4. The action opens or updates a Pull Request for maintainer review.

The Issue author becomes the canonical reviewer identity. If the same account submits another review for the same program, the generated Pull Request updates that account's existing review instead of adding a duplicate.

## Rating Guidance

Use the overall `rating` as a practical researcher experience score:

- `5`: consistently excellent and worth prioritizing.
- `4`: good program with minor friction.
- `3`: workable but mixed.
- `2`: significant friction; researchers should be cautious.
- `1`: severe issues such as ghosting, unreliable payment, or materially misleading scope.

## Validation

The Pull Request checks validate schema, path consistency, platform URL shape, duplicate reviewers, whether public program URLs are reachable, and whether a PR only adds or updates the review belonging to the PR author. Maintainers still perform editorial review before merge.
