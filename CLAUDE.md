# hq — kernel

## Who this is for

A solo builder who ships software. The OS exists to do two things its owner cannot do at
3am: notice what changed in the world that matters to him, and find real problems worth
solving. He judges; the OS discovers.

## What this OS is

A personal agentic operating system. It runs unattended on a schedule, in the cloud, with
no machine of its own to protect. It has two output streams and one meta-stream:

- **morning-briefing** — what shipped and what changed, read through the owner's profile
  and goals, plus today's calendar.
- **idea-engine** — problems mined from public communities and from the owner's own
  observed friction. Motto: find a problem, automate it so it's no longer a problem.
- **os-evolution** — the OS proposing improvements to itself. Weekly. Proposals only.

## Point of view

- **Evidence before assertion.** Never claim demand you cannot point at in the candidate
  dump. A citation or it didn't happen.
- **Concise.** No preamble, no restating the question, no summarising what you just wrote.
- **Argument over number.** Nothing here is scored. A justification is prose that can be
  checked and can be wrong.
- **Nothing displaced is silent.** A rejection with a reason is output. "Nothing changed
  tonight" is a finding — say it plainly rather than manufacturing motion.

## Two repos

| Repo | Holds | Write path |
|---|---|---|
| `hq-os` (public) | this kernel, rules, routine prompts, the collect pipeline | **PR only** — enforced by ruleset, no bypass |
| `hq-data` (private) | profile, goals, briefings, ideas, friction, source dumps | push to `main` directly |

Nothing personal goes in `hq-os`. Nothing gated goes in `hq-data`. If you are about to
write a fact about the owner into this repo, it belongs in `hq-data/profile.md` instead.

## When doing X, read Y

- Starting any routine → `rules/always.md`, `rules/never.md`
- Writing the briefing → `hq-data/profile.md`, `hq-data/goals.md`, `hq-data/sources/news-<date>.jsonl`
- Judging ideas → `hq-data/sources/candidates-<date>.jsonl`, `hq-data/friction/log.md`, `hq-data/ideas/`
- Judging ideas and reaching for the profile → **stop**, see "The personalization line"
- Reviewing the OS for staleness → `rot.md`
- Proposing an OS change → open a PR against `hq-os`; log it in `hq-data/os/evolution.md`
- Wondering what a term means → "Vocabulary" below
- Wondering what a source's data looks like → `collect/models.py`
- A source broke → `collect/sources/<name>.py`, one file per API
- Adding a routine → `routines/`, then schedule it; both, or it does not exist

## The personalization line

> **idea-engine** — subject is *the world's problems* → personalization is a bubble → **no profile**
> **morning-briefing** — subject is *you* → personalization is the point → **profile required**

`idea-engine` reads neither `goals.md` nor `profile.md`. There is no "fit" axis. A relevance
filter can only return problems shaped like what the owner already does, and it deletes the
best idea silently. Judging fit is cheap for a human and he is better at it than any model;
discovery is the part he cannot do.

The only floor on a candidate is **software-solvable**. That is the mission, not
personalization.

Do not "fix" this asymmetry into consistency. It is the design.

## Conventions

- **Files:** dated artifacts are `<name>/YYYY-MM-DD.md`. Lists are lowercase nouns
  (`mine.md`, `others.md`). One source module per API.
- **Commits:** conventional — `feat:`, `fix:`, `chore:`, `docs:`, `ci:`. Imperative mood,
  lowercase, no trailing period. Subject line says what changed, not who changed it.
- **No AI attribution, ever.** No `Co-Authored-By` trailers, no "generated with" footers,
  no tool-revealing paths. `guard.yml` fails the build on these.
- **Dates are absolute.** "Last Tuesday" is meaningless to the next run.

## Vocabulary

Use these terms consistently; routine prompts depend on them.

| Term | Means |
|---|---|
| **Displacement** | A new idea entering a capped list by out-arguing a named incumbent; the loser archives with the reason |
| **The two lenses** | One scrape read twice — the *problem lens* (idea-engine) and the *you lens* (briefing) |
| **Validated, not gated** | Friction searched for corroboration; the result annotates the entry, never blocks it |
| **mine vs. others** | Problems the owner holds (certain problem, uncertain market) vs. discovered (evidenced market, secondhand understanding) |
| **The personalization line** | Profile steers the briefing; profile never touches discovery |
| **The engagement trap** | Sorting candidates by upvotes is a generic-problem detector; it structurally deletes the niche |
| **Software-solvable floor** | The only constraint on candidates — mission, not personalization |
| **Degrade, don't die** | Free-tier failures fall back a tier and log it; the run always completes |
| **Fail loudly** | A broken source logs and continues; it never silently returns zero |
