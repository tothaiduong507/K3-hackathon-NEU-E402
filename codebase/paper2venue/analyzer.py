from __future__ import annotations

import json
from typing import Any

from .llm import Provider, function_tool, required_tool_choice, tool_payload
from .models import PageChunk, Paper


SUMMARY_TOOL_NAME = "submit_paper_summary"
RECOMMEND_TOOL_NAME = "submit_conference_recommendations"
LITERATURE_REVIEW_TOOL_NAME = "submit_literature_review"


SUMMARY_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "problem": {"type": "string"},
        "method": {"type": "string"},
        "data_or_experiments": {"type": "string"},
        "key_findings": {"type": "array", "items": {"type": "string"}},
        "limitations": {"type": "array", "items": {"type": "string"}},
        "keywords": {"type": "array", "items": {"type": "string"}},
        "fields": {"type": "array", "items": {"type": "string"}},
        "evidence": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "claim": {"type": "string"},
                    "source_refs": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["claim", "source_refs"],
                "additionalProperties": False,
            },
        },
    },
    "required": [
        "problem",
        "method",
        "data_or_experiments",
        "key_findings",
        "limitations",
        "keywords",
        "fields",
        "evidence",
    ],
    "additionalProperties": False,
}


RECOMMEND_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "recommendations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "conference_id": {"type": "string"},
                    "fit_score": {"type": "integer", "minimum": 0, "maximum": 100},
                    "confidence": {"type": "string", "enum": ["low", "medium", "high"]},
                    "reasons": {"type": "array", "items": {"type": "string"}},
                    "risks": {"type": "array", "items": {"type": "string"}},
                    "evidence_topics": {"type": "array", "items": {"type": "string"}},
                },
                "required": [
                    "conference_id",
                    "fit_score",
                    "confidence",
                    "reasons",
                    "risks",
                    "evidence_topics",
                ],
                "additionalProperties": False,
            },
        }
    },
    "required": ["recommendations"],
    "additionalProperties": False,
}


LITERATURE_REVIEW_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "paper_summaries": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "paper_id": {"type": "string"},
                    "problem": {"type": "string"},
                    "method": {"type": "string"},
                    "key_findings": {"type": "array", "items": {"type": "string"}},
                    "limitations": {"type": "array", "items": {"type": "string"}},
                    "relevance_explanation": {"type": "string"},
                    "source_refs": {"type": "array", "items": {"type": "string"}},
                },
                "required": [
                    "paper_id",
                    "problem",
                    "method",
                    "key_findings",
                    "limitations",
                    "relevance_explanation",
                    "source_refs",
                ],
                "additionalProperties": False,
            },
        },
        "comparison": {
            "type": "object",
            "properties": {
                "common_themes": {"type": "array", "items": {"type": "string"}},
                "methodological_differences": {"type": "array", "items": {"type": "string"}},
                "evidence_gaps": {"type": "array", "items": {"type": "string"}},
                "suggested_reading_order": {"type": "array", "items": {"type": "string"}},
            },
            "required": [
                "common_themes",
                "methodological_differences",
                "evidence_gaps",
                "suggested_reading_order",
            ],
            "additionalProperties": False,
        },
        "topic_profile": {
            "type": "object",
            "properties": {
                "keywords": {"type": "array", "items": {"type": "string"}},
                "fields": {"type": "array", "items": {"type": "string"}},
                "venue_fit_description": {"type": "string"},
            },
            "required": ["keywords", "fields", "venue_fit_description"],
            "additionalProperties": False,
        },
    },
    "required": ["paper_summaries", "comparison", "topic_profile"],
    "additionalProperties": False,
}


class ResearchAnalyzer:
    def __init__(self, provider: Provider, *, model: str | None = None) -> None:
        self.provider = provider
        self.model = model

    def summarize(self, paper: Paper, pages: list[PageChunk]) -> dict[str, Any]:
        source_blocks = [f"[abstract]\n{paper.abstract}"] if paper.abstract else []
        source_blocks.extend(f"[{page.label}]\n{page.text}" for page in pages)
        if not source_blocks:
            raise ValueError("No abstract or PDF text is available to summarize")
        allowed_refs = {"abstract", *(page.label for page in pages)}
        source_text = "\n\n".join(source_blocks)
        messages = [
            {
                "role": "system",
                "content": (
                    "You summarize scholarly work only from the supplied source blocks. "
                    "Do not add facts from memory. Every material claim must cite one or "
                    "more exact source labels. If a limitation is not stated or strongly "
                    "supported, say that it is not available in the supplied text."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Paper title: {paper.title}\n\n"
                    f"Create a structured research summary from these sources:\n\n{source_text}"
                ),
            },
        ]
        response = self.provider.complete(
            messages,
            [
                function_tool(
                    SUMMARY_TOOL_NAME,
                    "Return a grounded structured summary of the supplied paper sources.",
                    SUMMARY_SCHEMA,
                )
            ],
            model=self.model,
            temperature=0.0,
            tool_choice=required_tool_choice(SUMMARY_TOOL_NAME),
        )
        summary = tool_payload(response, SUMMARY_TOOL_NAME)
        self._validate_summary(summary, allowed_refs)
        summary["source_level"] = "full_text_excerpt" if pages else "abstract_only"
        summary["source_labels"] = sorted(allowed_refs)
        return summary

    def recommend(
        self,
        summary: dict[str, Any],
        candidates: list[dict[str, Any]],
        *,
        top_k: int = 3,
    ) -> list[dict[str, Any]]:
        top_k = max(1, min(int(top_k), 5))
        candidate_payload = [
            {
                "id": item["conference"]["id"],
                "acronym": item["conference"]["acronym"],
                "name": item["conference"]["name"],
                "scope": item["conference"]["scope"],
                "topics": item["conference"]["topics"],
                "retrieval_score": item["retrieval_score"],
                "matched_terms": item["matched_terms"],
            }
            for item in candidates
        ]
        messages = [
            {
                "role": "system",
                "content": (
                    "Rank conferences only by topical and methodological scope fit. "
                    "Use only candidate IDs supplied by the user. Do not predict acceptance, "
                    "invent deadlines, or invent conference facts. A low-confidence result "
                    "is preferable to an unsupported claim."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Paper summary:\n{json.dumps(summary, ensure_ascii=False)}\n\n"
                    f"Conference candidates:\n{json.dumps(candidate_payload, ensure_ascii=False)}\n\n"
                    f"Return at most {top_k} recommendations."
                ),
            },
        ]
        response = self.provider.complete(
            messages,
            [
                function_tool(
                    RECOMMEND_TOOL_NAME,
                    "Return a source-bounded conference scope-fit shortlist.",
                    RECOMMEND_SCHEMA,
                )
            ],
            model=self.model,
            temperature=0.0,
            tool_choice=required_tool_choice(RECOMMEND_TOOL_NAME),
        )
        payload = tool_payload(response, RECOMMEND_TOOL_NAME)
        raw_recommendations = payload.get("recommendations")
        if not isinstance(raw_recommendations, list):
            raise ValueError("recommendations must be a list")

        by_id = {item["conference"]["id"]: item for item in candidates}
        seen: set[str] = set()
        enriched: list[dict[str, Any]] = []
        for recommendation in raw_recommendations:
            conference_id = recommendation.get("conference_id")
            if conference_id not in by_id or conference_id in seen:
                continue
            seen.add(conference_id)
            source = by_id[conference_id]["conference"]
            fit_score = max(0, min(int(recommendation.get("fit_score", 0)), 100))
            enriched.append(
                {
                    "conference_id": conference_id,
                    "acronym": source["acronym"],
                    "name": source["name"],
                    "fit_score": fit_score,
                    "confidence": recommendation.get("confidence", "low"),
                    "reasons": list(recommendation.get("reasons") or []),
                    "risks": list(recommendation.get("risks") or []),
                    "evidence_topics": list(recommendation.get("evidence_topics") or []),
                    "official_url": source["official_url"],
                    "scope_source_url": source["scope_source_url"],
                    "scope_verified_at": source["scope_verified_at"],
                }
            )
            if len(enriched) >= top_k:
                break
        if not enriched:
            raise ValueError("Model returned no valid conference candidate")
        return enriched

    def review_collection(
        self,
        *,
        query: str,
        ranked_papers: list[dict[str, Any]],
    ) -> dict[str, Any]:
        if len(ranked_papers) < 2:
            raise ValueError("At least two papers are required for a literature comparison")

        allowed_ids = {
            str(item["paper"]["paper_id"])
            for item in ranked_papers
        }
        allowed_refs = {
            f"paper:{paper_id}:abstract"
            for paper_id in allowed_ids
        }
        source_blocks = []
        for item in ranked_papers:
            paper = item["paper"]
            source_ref = f"paper:{paper['paper_id']}:abstract"
            source_blocks.append(
                "\n".join(
                    [
                        f"[{source_ref}]",
                        f"Title: {paper['title']}",
                        f"Year: {paper.get('year') or 'unknown'}",
                        f"Venue: {paper.get('venue') or 'unknown'}",
                        f"Abstract: {paper['abstract']}",
                    ]
                )
            )

        messages = [
            {
                "role": "system",
                "content": (
                    "You create a compact literature-review brief using only supplied "
                    "paper abstracts. Do not treat an abstract as full-paper evidence. "
                    "Every paper summary must cite its exact source label. Do not infer "
                    "unstated limitations; explicitly say when the abstract is insufficient."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Research query: {query}\n\n"
                    "Compare the selected papers, identify common themes, methodological "
                    "differences, evidence gaps, and a useful reading order.\n\n"
                    + "\n\n".join(source_blocks)
                ),
            },
        ]
        response = self.provider.complete(
            messages,
            [
                function_tool(
                    LITERATURE_REVIEW_TOOL_NAME,
                    "Return a source-bounded structured literature review.",
                    LITERATURE_REVIEW_SCHEMA,
                )
            ],
            model=self.model,
            temperature=0.0,
            tool_choice=required_tool_choice(LITERATURE_REVIEW_TOOL_NAME),
        )
        review = tool_payload(response, LITERATURE_REVIEW_TOOL_NAME)
        summaries = review.get("paper_summaries")
        if not isinstance(summaries, list):
            raise ValueError("paper_summaries must be a list")
        returned_ids: set[str] = set()
        for summary in summaries:
            paper_id = str(summary.get("paper_id") or "")
            if paper_id not in allowed_ids:
                raise ValueError(f"Review returned an unknown paper ID: {paper_id}")
            returned_ids.add(paper_id)
            expected_ref = f"paper:{paper_id}:abstract"
            normalized_refs: list[str] = []
            for raw_ref in summary.get("source_refs") or []:
                clean_ref = str(raw_ref).strip().strip("[]")
                if clean_ref in {paper_id, expected_ref}:
                    normalized_refs.append(expected_ref)
                else:
                    raise ValueError(
                        f"Review summary for {paper_id} cited another or unavailable source: "
                        f"{raw_ref}"
                    )
            if expected_ref not in normalized_refs:
                raise ValueError(f"Review summary for {paper_id} does not cite its abstract")
            summary["source_refs"] = [expected_ref]
        missing_ids = sorted(allowed_ids - returned_ids)
        if missing_ids:
            raise ValueError(f"Review omitted selected papers: {missing_ids}")
        review["source_level"] = "abstract_only"
        review["source_labels"] = sorted(allowed_refs)
        return review

    @staticmethod
    def _validate_summary(summary: dict[str, Any], allowed_refs: set[str]) -> None:
        required = {
            "problem",
            "method",
            "data_or_experiments",
            "key_findings",
            "limitations",
            "keywords",
            "fields",
            "evidence",
        }
        missing = sorted(required - set(summary))
        if missing:
            raise ValueError(f"Summary is missing fields: {', '.join(missing)}")
        for evidence in summary.get("evidence") or []:
            refs = evidence.get("source_refs") or []
            invalid = sorted(set(refs) - allowed_refs)
            if invalid:
                raise ValueError(f"Summary cited unavailable source labels: {invalid}")
