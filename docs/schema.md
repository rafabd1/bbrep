# bbrep Data Schema

Program files live at:

```text
data/programs/{platform}/{slug}.yml
```

The path is part of the schema. `program.platform` must match `{platform}` and `program.slug` must match `{slug}`.

## Program File

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
    note: "Fast triage and payment timeline matched the policy."
```

## Supported Platforms

- `hackerone`
- `bugcrowd`
- `intigriti`
- `yeswehack`
- `immunefi`
- `code4rena`
- `sherlock`
- `cantina`
- `hackenproof`
- `hats`
- `codehawks`
- `self-hosted`
- `other`

## Review Fields

| Field | Required | Values |
| --- | --- | --- |
| `reviewer.github` | yes | GitHub username without `@`; must match the PR author for new or edited reviews |
| `reviewer.display` | yes | `github`, `anonymous` |
| `experience_date` | yes | `YYYY-MM` |
| `submitted_at` | yes | `YYYY-MM-DD` |
| `rating` | yes | integer `1` to `5` |
| `response_time` | yes | `fast`, `medium`, `slow`, `ghosted`, `unknown` |
| `triage_quality` | yes | `excellent`, `good`, `average`, `poor`, `unknown` |
| `payment_reliability` | yes | `excellent`, `good`, `average`, `poor`, `unpaid`, `not-applicable`, `unknown` |
| `scope_accuracy` | yes | `excellent`, `good`, `average`, `poor`, `unknown` |
| `communication` | yes | `excellent`, `good`, `average`, `poor`, `none`, `unknown` |
| `note` | no | max 500 characters |

## Duplicate Policy

One GitHub handle may have only one review per program. To update a review, edit the existing entry.

`reviewer.display: anonymous` hides the handle on the site, but the GitHub PR author remains the canonical dedup identity.
