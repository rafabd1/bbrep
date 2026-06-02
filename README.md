# bbrep

bbrep is a community-maintained reputation index for public bug bounty and vulnerability disclosure programs.

The site ranks programs from structured researcher reviews submitted through GitHub Issues or Pull Requests.

## Access

The public site is intended to run on Vercel. Until the first deployment is live, use the GitHub repository:

https://github.com/rafabd1/bbrep

## Submit a Review

Fast path:

1. Open a `Submit a program review` Issue.
2. Fill the structured fields.
3. Wait for maintainer review.

Pull Request path:

1. Open the contribution page on the site.
2. Fill the review form.
3. Copy the generated YAML.
4. Open a Pull Request in `rafabd1/bbrep`.
5. Create the generated file if the program is new, or edit the existing program file if it already exists.

Reviews are deduplicated by program and GitHub PR author. You can choose whether the site displays your GitHub handle or `anonymous`, but the PR author remains visible in GitHub history.

Platforms can be known platforms such as `hackerone` or `immunefi`, or custom lowercase slugs for platforms that are not listed yet.

## Legal Disclaimer

Reviews are individual opinions from independent researchers. This project is not affiliated with any bug bounty platform, company, or program owner. Companies and program owners may contest reviews by opening an Issue with evidence. Only public programs are accepted.
