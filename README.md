<img src="site/public/bbrep-icon.svg" alt="bbrep icon" width="72" height="72" />

# bbrep

bbrep is a community-maintained reputation index for public bug bounty and vulnerability disclosure programs.

The site ranks programs from researcher reviews submitted through GitHub Issues.

## Access

Public site:

https://bbrep.vercel.app/

Repository:

https://github.com/rafabd1/bbrep

## Submit a Review

1. Fill the review fields on the contribution page.
2. Copy the generated Issue body.
3. Create a GitHub Issue with the `review-submission` label.
4. The label triggers an automated Pull Request with the generated YAML.
5. Wait for maintainer review.

Issue submissions are deduplicated by program and GitHub Issue author. You can choose whether the site displays your GitHub handle or `anonymous`, but GitHub history still records the submitting account.

Platforms can be known platforms such as `hackerone` or `immunefi`, or custom lowercase slugs for platforms that are not listed yet.

## Legal Disclaimer

Reviews are individual opinions from independent researchers. This project is not affiliated with any bug bounty platform, company, or program owner. Companies and program owners may contest reviews by opening an Issue with evidence. Only public programs are accepted.
