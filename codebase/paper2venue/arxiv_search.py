from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from typing import Any

import requests

from .models import Paper


ARXIV_API_URL = "https://export.arxiv.org/api/query"
QUERY_STOPWORDS = {
    "a", "an", "and", "for", "from", "in", "of", "on", "or", "the", "to",
    "using", "with",
}
NAMESPACES = {
    "atom": "http://www.w3.org/2005/Atom",
    "opensearch": "http://a9.com/-/spec/opensearch/1.1/",
    "arxiv": "http://arxiv.org/schemas/atom",
}


def _text(entry: ET.Element, path: str) -> str:
    node = entry.find(path, NAMESPACES)
    return (node.text or "").strip() if node is not None and node.text else ""


def _arxiv_query(query: str) -> str:
    query_terms = [
        term.lower()
        for term in re.findall(r"[A-Za-z0-9_\-]+", query or "")
        if len(term) > 1 and term.lower() not in QUERY_STOPWORDS
    ]
    # Long all-AND queries frequently return zero results on arXiv. The first
    # four meaningful terms retain user intent while keeping recall usable.
    return " AND ".join(f"all:{term}" for term in query_terms[:4])


def _year_matches(value: int | None, expression: str) -> bool:
    if value is None:
        return False
    expression = expression.strip()
    if re.fullmatch(r"\d{4}", expression):
        return value == int(expression)
    match = re.fullmatch(r"(\d{4})-(\d{4})?", expression)
    if not match:
        return True
    start = int(match.group(1))
    end = int(match.group(2)) if match.group(2) else None
    return value >= start and (end is None or value <= end)


def _papers_from_feed(root: ET.Element, *, year: str | None = None) -> list[Paper]:
    papers: list[Paper] = []
    for entry in root.findall(".//atom:entry", NAMESPACES):
        url = _text(entry, "./atom:id")
        match = re.search(r"(\d{4}\.\d{4,5}(?:v\d+)?)", url)
        arxiv_id = match.group(1) if match else ""
        categories = [
            str(node.get("term"))
            for node in entry.findall("./atom:category", NAMESPACES)
            if node.get("term")
        ]
        published = _text(entry, "./atom:published")
        published_year = int(published[:4]) if published[:4].isdigit() else None
        if year and not _year_matches(published_year, year):
            continue
        papers.append(
            Paper(
                paper_id=f"ARXIV:{arxiv_id}",
                title=" ".join(_text(entry, "./atom:title").split()),
                abstract=" ".join(_text(entry, "./atom:summary").split()),
                authors=[
                    _text(author, "./atom:name")
                    for author in entry.findall("./atom:author", NAMESPACES)
                ],
                year=published_year,
                citation_count=None,
                venue="arXiv",
                url=url,
                external_ids={"ArXiv": arxiv_id},
                fields_of_study=categories,
                open_access_pdf_url=f"https://arxiv.org/pdf/{arxiv_id}.pdf",
            )
        )
    return papers


def _parse_arxiv_id(value: str) -> str:
    match = re.search(r"(\d{4}\.\d{4,5}(?:v\d+)?)", value or "")
    if not match:
        raise ValueError("paper_id is not a supported arXiv ID")
    return match.group(1)


class ArxivSearchClient:
    def __init__(
        self,
        *,
        session: requests.Session | None = None,
        timeout: int = 30,
    ) -> None:
        self.session = session or requests.Session()
        self.timeout = timeout

    def search(self, query: str, *, limit: int = 5, year: str | None = None) -> list[Paper]:
        query = " ".join((query or "").split())
        if not query:
            raise ValueError("query is required")
        response = self.session.get(
            ARXIV_API_URL,
            params={
                "search_query": _arxiv_query(query),
                "max_results": max(1, min(int(limit), 20)),
                "sortBy": "relevance",
                "sortOrder": "descending",
            },
            headers={"User-Agent": "Paper2Venue-Hackathon/0.1"},
            timeout=self.timeout,
        )
        response.raise_for_status()
        root = ET.fromstring(response.text)
        return _papers_from_feed(root, year=year)

    def get_paper(self, paper_id: str) -> Paper:
        arxiv_id = _parse_arxiv_id(paper_id)
        response = self.session.get(
            ARXIV_API_URL,
            params={"id_list": arxiv_id, "max_results": 1},
            headers={"User-Agent": "Paper2Venue-Hackathon/0.1"},
            timeout=self.timeout,
        )
        response.raise_for_status()
        papers = _papers_from_feed(ET.fromstring(response.text))
        if not papers:
            raise LookupError(f"arXiv paper not found: {arxiv_id}")
        return papers[0]


class ResilientPaperSearch:
    """Use Semantic Scholar first, then arXiv when it is throttled or unavailable."""

    def __init__(self, primary: Any, fallback: Any | None = None) -> None:
        self.primary = primary
        self.fallback = fallback or ArxivSearchClient()
        self.last_source = "unknown"
        self.last_primary_error: str | None = None

    def search(self, query: str, *, limit: int = 5, year: str | None = None) -> list[Paper]:
        try:
            results = self.primary.search(query, limit=limit, year=year)
            if results:
                self.last_source = "semantic_scholar"
                self.last_primary_error = None
                return results
        except Exception as exc:
            self.last_primary_error = f"{type(exc).__name__}: {exc}"
        results = self.fallback.search(query, limit=limit, year=year)
        self.last_source = "arxiv"
        return results

    def get_paper(self, paper_id: str) -> Paper:
        """Resolve exact IDs, falling back to arXiv for arXiv identifiers."""
        try:
            paper = self.primary.get_paper(paper_id)
            self.last_source = "semantic_scholar"
            self.last_primary_error = None
            return paper
        except Exception as exc:
            self.last_primary_error = f"{type(exc).__name__}: {exc}"

        try:
            paper = self.fallback.get_paper(paper_id)
        except Exception as fallback_exc:
            raise RuntimeError(
                "Unable to resolve paper ID. Semantic Scholar failed and the ID "
                f"could not be resolved through arXiv: {fallback_exc}"
            ) from fallback_exc
        self.last_source = "arxiv"
        return paper
