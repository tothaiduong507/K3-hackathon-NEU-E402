from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Paper:
    paper_id: str
    title: str
    abstract: str
    authors: list[str] = field(default_factory=list)
    year: int | None = None
    citation_count: int | None = None
    venue: str | None = None
    url: str | None = None
    external_ids: dict[str, str] = field(default_factory=dict)
    fields_of_study: list[str] = field(default_factory=list)
    open_access_pdf_url: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PageChunk:
    page: int
    text: str

    @property
    def label(self) -> str:
        return f"p.{self.page}"

    def to_dict(self) -> dict[str, Any]:
        return {"page": self.page, "label": self.label, "text": self.text}


@dataclass
class Conference:
    id: str
    acronym: str
    name: str
    official_url: str
    scope: str
    topics: list[str]
    scope_source_url: str
    scope_verified_at: str
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

