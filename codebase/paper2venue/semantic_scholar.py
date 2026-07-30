from __future__ import annotations

import os
import time
from typing import Any

import requests

from .models import Paper


BASE_URL = "https://api.semanticscholar.org/graph/v1"
PAPER_FIELDS = ",".join(
    [
        "paperId",
        "title",
        "abstract",
        "authors",
        "year",
        "citationCount",
        "venue",
        "url",
        "externalIds",
        "fieldsOfStudy",
        "openAccessPdf",
    ]
)


class SemanticScholarClient:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        session: requests.Session | None = None,
        timeout: int = 30,
    ) -> None:
        self.api_key = api_key if api_key is not None else os.getenv("SEMANTIC_SCHOLAR_API_KEY", "")
        self.session = session or requests.Session()
        self.timeout = timeout

    @property
    def headers(self) -> dict[str, str]:
        headers = {"User-Agent": "Paper2Venue-Hackathon/0.1"}
        if self.api_key:
            headers["x-api-key"] = self.api_key
        return headers

    def _get(self, path: str, *, params: dict[str, Any]) -> dict[str, Any]:
        response: requests.Response | None = None
        for attempt in range(3):
            response = self.session.get(
                f"{BASE_URL}{path}",
                params=params,
                headers=self.headers,
                timeout=self.timeout,
            )
            if response.status_code != 429:
                break
            time.sleep(1.5 * (attempt + 1))
        assert response is not None
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("Semantic Scholar returned an unexpected response")
        return payload

    def search(self, query: str, *, limit: int = 5, year: str | None = None) -> list[Paper]:
        query = " ".join((query or "").split())
        if not query:
            raise ValueError("query is required")
        params: dict[str, Any] = {
            "query": query,
            "limit": max(1, min(int(limit), 20)),
            "fields": PAPER_FIELDS,
        }
        if year:
            params["year"] = year
        payload = self._get("/paper/search", params=params)
        return [self._normalize(item) for item in payload.get("data", []) if item.get("title")]

    def get_paper(self, paper_id: str) -> Paper:
        paper_id = (paper_id or "").strip()
        if not paper_id:
            raise ValueError("paper_id is required")
        payload = self._get(f"/paper/{paper_id}", params={"fields": PAPER_FIELDS})
        return self._normalize(payload)

    @staticmethod
    def _normalize(item: dict[str, Any]) -> Paper:
        external_ids = {
            str(key): str(value)
            for key, value in (item.get("externalIds") or {}).items()
            if value is not None
        }
        pdf = item.get("openAccessPdf") or {}
        return Paper(
            paper_id=str(item.get("paperId") or ""),
            title=str(item.get("title") or "").strip(),
            abstract=str(item.get("abstract") or "").strip(),
            authors=[
                str(author.get("name") or "").strip()
                for author in (item.get("authors") or [])
                if author.get("name")
            ],
            year=item.get("year"),
            citation_count=item.get("citationCount"),
            venue=str(item.get("venue") or "").strip() or None,
            url=str(item.get("url") or "").strip() or None,
            external_ids=external_ids,
            fields_of_study=[str(value) for value in (item.get("fieldsOfStudy") or [])],
            open_access_pdf_url=str(pdf.get("url") or "").strip() or None,
        )

