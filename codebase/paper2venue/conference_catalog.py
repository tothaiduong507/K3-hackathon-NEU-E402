from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any

from .config import CONFERENCE_CATALOG_PATH
from .models import Conference


STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "by", "for", "from", "in", "is",
    "of", "on", "or", "the", "to", "using", "with", "we", "this", "that",
    "study", "paper", "method", "results", "research",
}


def terms(text: str) -> set[str]:
    normalized = unicodedata.normalize("NFKD", (text or "").lower())
    ascii_text = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    return {
        token
        for token in re.findall(r"[a-z0-9][a-z0-9+]{1,}", ascii_text)
        if token not in STOPWORDS
    }


class ConferenceCatalog:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or CONFERENCE_CATALOG_PATH
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        raw_items = payload.get("conferences", [])
        self.metadata = {
            "catalog_version": payload.get("catalog_version"),
            "catalog_scope": payload.get("catalog_scope"),
            "deadline_policy": payload.get("deadline_policy"),
        }
        self.items = [Conference(**item) for item in raw_items]
        self._validate()

    def _validate(self) -> None:
        if not self.items:
            raise ValueError("Conference catalog is empty")
        ids = [item.id for item in self.items]
        if len(ids) != len(set(ids)):
            raise ValueError("Conference catalog contains duplicate IDs")
        for item in self.items:
            if not item.official_url.startswith("https://"):
                raise ValueError(f"{item.id}: official_url must use HTTPS")
            if not item.scope_source_url.startswith("https://"):
                raise ValueError(f"{item.id}: scope_source_url must use HTTPS")

    def get(self, conference_id: str) -> Conference:
        for item in self.items:
            if item.id == conference_id:
                return item
        raise KeyError(conference_id)

    def shortlist(self, profile_text: str, *, limit: int = 6) -> list[dict[str, Any]]:
        profile_terms = terms(profile_text)
        scored: list[dict[str, Any]] = []
        for conference in self.items:
            topic_text = " ".join(conference.topics)
            conference_terms = terms(f"{topic_text} {conference.scope}")
            overlap = sorted(profile_terms & conference_terms)
            topic_phrases = [
                topic for topic in conference.topics
                if topic.lower() in profile_text.lower()
            ]
            score = len(overlap) * 3 + len(topic_phrases) * 6
            scored.append(
                {
                    "conference": conference.to_dict(),
                    "retrieval_score": score,
                    "matched_terms": overlap[:15],
                    "matched_topics": topic_phrases[:10],
                }
            )
        scored.sort(
            key=lambda item: (
                item["retrieval_score"],
                item["conference"]["acronym"],
            ),
            reverse=True,
        )
        return scored[: max(1, min(int(limit), len(scored)))]
