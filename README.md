# hq-os

The mechanical half of a personal agentic operating system: identity kernel, rules,
scheduled routine prompts, and the collection pipeline that feeds them.

Scheduled cloud sessions read this repo, judge what the pipeline collected, and write
their output to a separate private store. This repo is public and contains no personal
data by construction — see `CLAUDE.md` for the layer map.

Every change to `main` here requires a pull request. That is enforced by a repository
ruleset with no bypass actors, which is the mechanism behind the OS's propose → approve →
apply loop: nothing changes the OS without a human merging it.

Contact: someone@realdomain.com
