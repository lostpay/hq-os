# rot

Every layer of this OS decays at a different rate. This table declares the expected rate
and when each layer was last actually reviewed. os-evolution job (a) reads it weekly and
flags what is overdue; a human updates the date when a review really happens.

A date here is a claim that someone looked. Do not update it because a file changed.

| Layer | Expected rot | Cadence | Last reviewed |
|---|---|---|---|
| Identity (`CLAUDE.md`) | slow | quarterly | 2026-07-16 |
| `hq-data/profile.md` | slow | quarterly | 2026-07-16 |
| Rules and guards | slow-medium | monthly | 2026-07-16 |
| `hq-data/goals.md` | medium | monthly | 2026-07-16 |
| Routines (`routines/`) | medium | weekly | 2026-07-16 |
| Scrapers (`collect/sources/`, per source) | **fast** | weekly | 2026-07-16 |
| Triage ladder (`collect/triage.py`) | **fast** | weekly | 2026-07-16 |
| Agents | fast | n/a until first hire | — |
| Tools and connectors | medium-fast | monthly | 2026-07-16 |

**Why scrapers are fast:** each one is somebody else's API and can change shape without
warning. **Why the triage ladder is fast:** free model tiers are the least stable thing in
this system — endpoints get renamed, deprecated, and rate-limited without notice. A
`collect` run that silently drops to the bottom tier every night is a broken OS wearing a
green checkmark; job (a) should be reading the tier log, not just this table.
