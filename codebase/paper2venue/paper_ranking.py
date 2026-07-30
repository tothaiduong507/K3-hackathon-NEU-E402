from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any

from .conference_catalog import terms
from .models import Paper


def rank_papers(query: str, papers: list[Paper]) -> list[dict[str, Any]]:
    """Rank papers transparently while preserving the source API's relevance signal."""
    query_terms = terms(query)
    current_year = datetime.now(timezone.utc).year
    total = max(1, len(papers))
    ranked: list[dict[str, Any]] = []

    for source_rank, paper in enumerate(papers, start=1):
        title_terms = terms(paper.title)
        abstract_terms = terms(paper.abstract)
        denominator = max(1, len(query_terms))
        title_overlap = query_terms & title_terms
        abstract_overlap = query_terms & abstract_terms

        title_score = 50.0 * len(title_overlap) / denominator
        abstract_score = 25.0 * len(abstract_overlap) / denominator
        source_score = 15.0 * (1.0 - (source_rank - 1) / total)

        citations = max(0, int(paper.citation_count or 0))
        citation_score = min(5.0, math.log10(citations + 1) if citations else 0.0)

        recency_score = 0.0
        if paper.year:
            age = max(0, current_year - int(paper.year))
            recency_score = max(0.0, 5.0 * (1.0 - age / 10.0))

        score = title_score + abstract_score + source_score + citation_score + recency_score
        ranked.append(
            {
                "source_rank": source_rank,
                "paper": paper.to_dict(),
                "relevance_score": round(score, 2),
                "matched_query_terms": sorted(title_overlap | abstract_overlap),
                "score_breakdown": {
                    "title_overlap": round(title_score, 2),
                    "abstract_overlap": round(abstract_score, 2),
                    "source_api_rank": round(source_score, 2),
                    "citation_signal": round(citation_score, 2),
                    "recency_signal": round(recency_score, 2),
                },
            }
        )

    ranked.sort(
        key=lambda item: (
            item["relevance_score"],
            -item["source_rank"],
        ),
        reverse=True,
    )
    for final_rank, item in enumerate(ranked, start=1):
        item["rank"] = final_rank
    return ranked

