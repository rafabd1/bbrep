# bbrep

bbrep is a community-maintained reputation index for public bug bounty and vulnerability disclosure programs.

The site ranks programs from structured researcher reviews submitted through a GitHub Issue Form.

## Access

The public site is intended to run on Vercel. Until the first deployment is live, use the GitHub repository:

https://github.com/rafabd1/bbrep

## Submit a Review

1. Open a `Submit a program review` Issue.
2. Fill the structured fields.
3. The `review-submission` label triggers an automated Pull Request with the generated YAML.
4. Wait for maintainer review.

Issue submissions are deduplicated by program and GitHub Issue author. You can choose whether the site displays your GitHub handle or `anonymous`, but GitHub history still records the submitting account.

Platforms can be known platforms such as `hackerone` or `immunefi`, or custom lowercase slugs for platforms that are not listed yet.

## Legal Disclaimer

Reviews are individual opinions from independent researchers. This project is not affiliated with any bug bounty platform, company, or program owner. Companies and program owners may contest reviews by opening an Issue with evidence. Only public programs are accepted.
