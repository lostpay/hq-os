"""The currency every source emits and every lens consumes."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Item:
    """One post, question, issue, or article from any source.

    `engagement` is recorded because it is weak secondary evidence worth seeing in the
    dump. It is never a sort key, threshold, or gate — see "the engagement trap".
    """

    source: str
    id: str
    url: str
    title: str
    body: str
    created_utc: str
    engagement: int

    @property
    def text(self) -> str:
        """What gets embedded and regex-matched."""
        return f"{self.title}\n\n{self.body}"

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "id": self.id,
            "url": self.url,
            "title": self.title,
            "body": self.body,
            "created_utc": self.created_utc,
            "engagement": self.engagement,
        }


@dataclass(frozen=True)
class SourceResult:
    name: str
    items: list[Item]
    error: str | None
    zero_yield: bool


@dataclass
class RunLog:
    """What happened during a run. Committed alongside the lens output so a gap is
    always visible in the repo rather than inferred from an absence."""

    date: str
    lens: str
    tier: str = "none"
    sources: list[SourceResult] = field(default_factory=list)
    counts: dict[str, int] = field(default_factory=dict)

    @property
    def failed(self) -> list[SourceResult]:
        return [s for s in self.sources if s.error]

    @property
    def silent(self) -> list[SourceResult]:
        return [s for s in self.sources if s.zero_yield]

    def to_markdown(self) -> str:
        lines = [
            f"# collect run — {self.date} ({self.lens} lens)",
            "",
            f"- Triage tier: **{self.tier}**",
            "",
            "## Sources",
            "",
            "| Source | Items | Status |",
            "|---|---|---|",
        ]
        for s in self.sources:
            if s.error:
                status = f"**FAILED** — {s.error}"
            elif s.zero_yield:
                status = "**returned zero** — suspect breakage"
            else:
                status = "ok"
            lines.append(f"| {s.name} | {len(s.items)} | {status} |")

        lines += ["", "## Funnel", "", "| Stage | Count |", "|---|---|"]
        for stage, n in self.counts.items():
            lines.append(f"| {stage} | {n} |")

        if self.failed or self.silent:
            lines += ["", "## Gaps", ""]
            for s in self.failed:
                lines.append(f"- `{s.name}` failed: {s.error}")
            for s in self.silent:
                lines.append(f"- `{s.name}` returned zero items without erroring")
        return "\n".join(lines) + "\n"
