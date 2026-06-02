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

Create or edit:

```text
data/programs/{platform}/{slug}.yml
```

Example:

```yaml
schema_version: 1
program:
  name: "Example Security Program"
  platform: self-hosted
  slug: example-security
  program_url: "https://example.com/security"

reviews:
  - reviewer:
      github: octocat
      display: github
    experience_date: "2026-05"
    submitted_at: "2026-06-02"
    rating: 4
    response_time: fast
    triage_quality: good
    payment_reliability: good
    scope_accuracy: good
    communication: good
    note: "Fast triage, clear scope, and payout timeline matched the policy."
```

Anonymous review:

```yaml
reviews:
  - reviewer:
      github: octocat
      display: anonymous
    experience_date: "2026-05"
    submitted_at: "2026-06-02"
    rating: 3
    response_time: medium
    triage_quality: average
    payment_reliability: unknown
    scope_accuracy: good
    communication: average
    note: "Scope was clear, but communication required follow-up."
```

## Rating Guidance

Use the overall `rating` as a practical researcher experience score:

- `5`: consistently excellent and worth prioritizing.
- `4`: good program with minor friction.
- `3`: workable but mixed.
- `2`: significant friction; researchers should be cautious.
- `1`: severe issues such as ghosting, unreliable payment, or materially misleading scope.

## Validation

The Pull Request checks validate schema, path consistency, platform URL shape, duplicate reviewers, whether public program URLs are reachable, and whether a PR only adds or updates the review belonging to the PR author. Maintainers still perform editorial review before merge.
