from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from uuid import uuid4

from .analyzer import ResearchAnalyzer
from .arxiv_pdf import ArxivPdfExtractor
from .arxiv_search import ResilientPaperSearch
from .conference_catalog import ConferenceCatalog
from .config import CACHE_DIR, RUNS_DIR
from .deep_summary import DEEP_SUMMARY_PROMPT_VERSION, DeepPaperAnalyzer
from .guardrails import validate_request
from .llm import Provider
from .models import Paper
from .paper_ranking import rank_papers
from .semantic_scholar import SemanticScholarClient


class Paper2VenuePipeline:
    def __init__(
        self,
        *,
        provider: Provider,
        model: str | None = None,
        papers: Any | None = None,
        pdfs: ArxivPdfExtractor | None = None,
        catalog: ConferenceCatalog | None = None,
        runs_dir: Path | None = None,
        cache_dir: Path | None = None,
    ) -> None:
        self.provider = provider
        self.model = model
        self.papers = papers or ResilientPaperSearch(SemanticScholarClient())
        self.pdfs = pdfs or ArxivPdfExtractor()
        self.catalog = catalog or ConferenceCatalog()
        self.analyzer = ResearchAnalyzer(provider, model=model)
        self.deep_analyzer = DeepPaperAnalyzer(provider, model=model)
        self.runs_dir = runs_dir or RUNS_DIR
        self.cache_dir = cache_dir or CACHE_DIR / "deep_summary"

    def search(self, query: str, *, limit: int = 5, year: str | None = None) -> list[Paper]:
        return self.papers.search(query, limit=limit, year=year)

    def search_and_rank(
        self,
        query: str,
        *,
        limit: int = 10,
        year: str | None = None,
    ) -> list[dict[str, Any]]:
        return rank_papers(
            query,
            self.search(query, limit=limit, year=year),
        )

    def build_from_query(
        self,
        query: str,
        *,
        select: int = 1,
        search_limit: int = 5,
        user_goal: str = "",
        use_pdf: bool = True,
        top_conferences: int = 3,
    ) -> dict[str, Any]:
        results = self.search(query, limit=search_limit)
        if not results:
            return {
                "status": "no_results",
                "message": "No papers were found. Refine the topic or remove filters.",
                "query": query,
            }
        index = max(1, int(select)) - 1
        if index >= len(results):
            raise ValueError(f"select must be between 1 and {len(results)}")
        return self.build_brief(
            results[index],
            user_goal=user_goal,
            use_pdf=use_pdf,
            top_conferences=top_conferences,
            search_context={
                "query": query,
                "selected_rank": index + 1,
                "result_count": len(results),
                "search_source": getattr(self.papers, "last_source", "custom"),
                "primary_search_error": getattr(self.papers, "last_primary_error", None),
            },
        )

    def build_literature_review(
        self,
        query: str,
        *,
        search_limit: int = 10,
        analyze_top: int = 3,
        top_conferences: int = 3,
        min_year: int | None = None,
        min_citations: int = 0,
        progress: Callable[[str, dict[str, Any]], None] | None = None,
    ) -> dict[str, Any]:
        search_limit = max(3, min(int(search_limit), 20))
        analyze_top = max(1, min(int(analyze_top), 5))
        min_citations = max(0, int(min_citations))
        year_filter = f"{int(min_year)}-" if min_year else None

        def notify(event: str, **details: Any) -> None:
            if progress:
                progress(event, details)

        notify("search_started", search_limit=search_limit, year=year_filter)
        papers = self.search(query, limit=search_limit, year=year_filter)
        notify(
            "search_completed",
            result_count=len(papers),
            source=getattr(self.papers, "last_source", "custom"),
        )
        if not papers:
            return {
                "status": "no_results",
                "message": "No papers were found. Refine the research query.",
                "query": query,
            }

        filtered_papers = [
            paper
            for paper in papers
            if (
                min_citations == 0
                or (
                    paper.citation_count is not None
                    and int(paper.citation_count) >= min_citations
                )
            )
        ]
        notify(
            "filter_completed",
            kept_count=len(filtered_papers),
            removed_count=len(papers) - len(filtered_papers),
            min_year=min_year,
            min_citations=min_citations,
        )
        if not filtered_papers:
            return {
                "status": "no_results_after_filter",
                "message": (
                    "Papers were found, but none passed the selected citation filter. "
                    "Try setting minimum citations to 0; arXiv fallback results do not "
                    "include citation counts."
                ),
                "query": query,
                "search": {
                    "source": getattr(self.papers, "last_source", "custom"),
                    "result_count": len(papers),
                    "filtered_count": 0,
                },
            }

        ranked = rank_papers(query, filtered_papers)
        notify("ranking_completed", ranked_count=len(ranked))
        eligible = [
            item for item in ranked
            if len(" ".join((item["paper"].get("abstract") or "").split())) >= 80
        ]
        selected = eligible[:analyze_top]
        if not selected:
            return {
                "status": "insufficient_sources",
                "message": "At least one paper with a usable abstract is required.",
                "query": query,
                "ranked_papers": ranked,
            }

        notify("analysis_started", selected_count=len(selected))
        if len(selected) == 1:
            selected_item = selected[0]
            paper = Paper(**selected_item["paper"])
            summary = self.analyzer.summarize(paper, [])
            source_ref = f"paper:{paper.paper_id}:abstract"
            review = {
                "paper_summaries": [
                    {
                        "paper_id": paper.paper_id,
                        "problem": summary["problem"],
                        "method": summary["method"],
                        "key_findings": summary["key_findings"],
                        "limitations": summary["limitations"],
                        "relevance_explanation": (
                            "This was the highest-ranked eligible source for the query "
                            f"(transparent relevance score "
                            f"{selected_item['relevance_score']}/100)."
                        ),
                        "source_refs": [source_ref],
                    }
                ],
                "comparison": {
                    "common_themes": [
                        "Only one paper was analyzed; cross-paper themes are unavailable."
                    ],
                    "methodological_differences": [
                        "At least two papers are required to compare methods."
                    ],
                    "evidence_gaps": [
                        "Cross-paper research gaps cannot be assessed from one abstract."
                    ],
                    "suggested_reading_order": [paper.paper_id],
                },
                "topic_profile": {
                    "keywords": summary["keywords"],
                    "fields": summary["fields"],
                    "venue_fit_description": (
                        f"Scope fit for research on {query}, based on one paper abstract."
                    ),
                },
                "source_level": "abstract_only",
                "source_labels": [source_ref],
                "analysis_mode": "single_paper_brief",
            }
            recommendation_input = summary
        else:
            review = self.analyzer.review_collection(
                query=query,
                ranked_papers=selected,
            )
            review["analysis_mode"] = "cross_paper_review"
            recommendation_input = review
        notify("analysis_completed", summary_count=len(review["paper_summaries"]))
        topic_profile = review["topic_profile"]
        profile_text = " ".join(
            [
                query,
                " ".join(topic_profile["keywords"]),
                " ".join(topic_profile["fields"]),
                topic_profile["venue_fit_description"],
            ]
        )
        candidates = self.catalog.shortlist(profile_text, limit=6)
        recommendations = self.analyzer.recommend(
            recommendation_input,
            candidates,
            top_k=top_conferences,
        )
        notify(
            "conference_completed",
            recommendation_count=len(recommendations),
        )
        now = datetime.now(timezone.utc)
        run_id = f"review_{now.strftime('%Y%m%dT%H%M%SZ')}_{uuid4().hex[:8]}"
        result = {
            "status": "completed",
            "run_type": "smart_literature_review",
            "run_id": run_id,
            "created_at": now.isoformat(),
            "model": self.model or getattr(self.provider, "default_model", None),
            "query": query,
            "search": {
                "source": getattr(self.papers, "last_source", "custom"),
                "primary_error": getattr(self.papers, "last_primary_error", None),
                "result_count": len(papers),
                "filtered_count": len(filtered_papers),
                "filters": {
                    "min_year": min_year,
                    "min_citations": min_citations,
                },
                "ranked_papers": ranked,
                "selected_paper_ids": [
                    item["paper"]["paper_id"]
                    for item in selected
                ],
            },
            "literature_review": review,
            "conference_recommendations": recommendations,
            "guardrails": {
                "summary_source_level": "abstract_only",
                "acceptance_prediction": False,
                "deadlines_included": False,
                "disclaimer": (
                    (
                        "Only one paper was analyzed, so no cross-paper conclusions "
                        "should be drawn. "
                    )
                    if len(selected) == 1
                    else "The comparison is based on abstracts, not full papers. "
                )
                + (
                    "Conference results are topical-fit suggestions only. Verify "
                    "scope and deadlines on official conference sites."
                ),
            },
        }
        self._write_run(result)
        return result

    def build_from_abstract(
        self,
        *,
        title: str,
        abstract: str,
        user_goal: str = "",
        top_conferences: int = 3,
    ) -> dict[str, Any]:
        paper = Paper(
            paper_id=f"user:{uuid4().hex[:12]}",
            title=title.strip() or "Untitled research description",
            abstract=abstract.strip(),
            url=None,
        )
        return self.build_brief(
            paper,
            user_goal=user_goal,
            use_pdf=False,
            top_conferences=top_conferences,
            search_context={"source": "user_abstract"},
        )

    def build_from_paper_id(
        self,
        paper_id: str,
        *,
        user_goal: str = "",
        use_pdf: bool = True,
        top_conferences: int = 3,
    ) -> dict[str, Any]:
        if not hasattr(self.papers, "get_paper"):
            raise RuntimeError("The configured paper source cannot resolve exact paper IDs")
        paper = self.papers.get_paper(paper_id)
        return self.build_brief(
            paper,
            user_goal=user_goal,
            use_pdf=use_pdf,
            top_conferences=top_conferences,
            search_context={
                "source": "paper_id",
                "paper_id": paper_id,
                "search_source": getattr(self.papers, "last_source", "custom"),
            },
        )

    def build_deep_summary(
        self,
        paper_id: str,
        *,
        language: str = "vi",
        max_pages: int = 80,
        progress: Callable[[str, dict[str, Any]], None] | None = None,
    ) -> dict[str, Any]:
        def notify(event: str, **details: Any) -> None:
            if progress:
                progress(event, details)

        if not hasattr(self.papers, "get_paper"):
            raise RuntimeError("The configured paper source cannot resolve exact paper IDs")
        notify("paper_started", paper_id=paper_id)
        paper = self.papers.get_paper(paper_id)
        notify(
            "paper_resolved",
            title=paper.title,
            source=getattr(self.papers, "last_source", "custom"),
        )
        arxiv_id = paper.external_ids.get("ArXiv") or paper.external_ids.get("ARXIV")
        if not arxiv_id:
            return {
                "status": "full_text_unavailable",
                "message": (
                    "A deep summary requires an arXiv full-text PDF. This paper does "
                    "not expose a supported arXiv ID."
                ),
                "paper": paper.to_dict(),
            }

        notify("pdf_started", arxiv_id=arxiv_id)
        try:
            pages = self.pdfs.extract(
                arxiv_id,
                max_pages=max(1, min(int(max_pages), 80)),
                max_chars=400_000,
            )
        except Exception as exc:
            return {
                "status": "pdf_error",
                "message": str(exc),
                "error": type(exc).__name__,
                "paper": paper.to_dict(),
                "pdf": {"attempted": True, "used": False, "arxiv_id": arxiv_id},
            }
        if not pages:
            return {
                "status": "full_text_unavailable",
                "message": "The PDF was downloaded but no usable text was extracted.",
                "paper": paper.to_dict(),
                "pdf": {"attempted": True, "used": False, "arxiv_id": arxiv_id},
            }

        metadata = dict(getattr(self.pdfs, "last_document_metadata", {}) or {})
        total_pages = int(metadata.get("total_pages") or len(pages))
        notify(
            "pdf_completed",
            extracted_pages=len(pages),
            total_pages=total_pages,
        )
        content_hash = hashlib.sha256(
            "\n".join(f"{page.label}:{page.text}" for page in pages).encode("utf-8")
        ).hexdigest()
        cache_key = hashlib.sha256(
            "|".join(
                [
                    content_hash,
                    language.lower(),
                    str(self.model or getattr(self.provider, "default_model", "")),
                    DEEP_SUMMARY_PROMPT_VERSION,
                ]
            ).encode("utf-8")
        ).hexdigest()
        cache_path = self.cache_dir / f"{cache_key}.json"
        if cache_path.exists():
            cached = json.loads(cache_path.read_text(encoding="utf-8"))
            cached.setdefault("cache", {})["hit"] = True
            notify("cache_hit", run_id=cached.get("run_id"))
            return cached

        summary = self.deep_analyzer.summarize(
            paper=paper,
            pages=pages,
            language=language,
            progress=progress,
        )
        now = datetime.now(timezone.utc)
        run_id = f"deep_{now.strftime('%Y%m%dT%H%M%SZ')}_{uuid4().hex[:8]}"
        extracted_pages = len(pages)
        result = {
            "status": "completed",
            "run_type": "deep_paper_summary",
            "run_id": run_id,
            "created_at": now.isoformat(),
            "model": self.model or getattr(self.provider, "default_model", None),
            "language": language,
            "paper": paper.to_dict(),
            "pdf": {
                "attempted": True,
                "used": True,
                "arxiv_id": arxiv_id,
                "total_pages": total_pages,
                "extracted_pages": extracted_pages,
                "extracted_characters": metadata.get("extracted_characters"),
                "coverage_percent": round(
                    100.0 * extracted_pages / max(1, total_pages),
                    1,
                ),
            },
            "deep_summary": summary,
            "cache": {
                "hit": False,
                "key": cache_key,
                "prompt_version": DEEP_SUMMARY_PROMPT_VERSION,
            },
            "guardrails": {
                "source_level": "full_text",
                "page_references_required": True,
                "disclaimer": (
                    "This summary is generated from extracted PDF text. Equations, "
                    "figures, and complex tables may not be fully represented; verify "
                    "critical claims against the cited pages in the original paper."
                ),
            },
        }
        self._write_run(result)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(
            json.dumps(result, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        notify("deep_summary_completed", run_id=run_id)
        return result

    def build_brief(
        self,
        paper: Paper,
        *,
        user_goal: str = "",
        use_pdf: bool = True,
        top_conferences: int = 3,
        search_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        boundary = validate_request(abstract=paper.abstract, user_goal=user_goal)
        if boundary["status"] != "ready":
            return {
                **boundary,
                "paper": paper.to_dict(),
                "search_context": search_context or {},
            }

        pages = []
        pdf_status: dict[str, Any] = {"attempted": False, "used": False}
        arxiv_id = paper.external_ids.get("ArXiv") or paper.external_ids.get("ARXIV")
        if use_pdf and arxiv_id:
            pdf_status["attempted"] = True
            try:
                pages = self.pdfs.extract(arxiv_id)
                pdf_status.update({"used": bool(pages), "arxiv_id": arxiv_id})
            except Exception as exc:
                pdf_status.update(
                    {
                        "used": False,
                        "error": type(exc).__name__,
                        "message": str(exc),
                    }
                )

        summary = self.analyzer.summarize(paper, pages)
        profile_text = " ".join(
            [
                paper.title,
                summary["problem"],
                summary["method"],
                " ".join(summary["keywords"]),
                " ".join(summary["fields"]),
            ]
        )
        candidates = self.catalog.shortlist(profile_text, limit=6)
        recommendations = self.analyzer.recommend(
            summary,
            candidates,
            top_k=top_conferences,
        )
        now = datetime.now(timezone.utc)
        run_id = f"brief_{now.strftime('%Y%m%dT%H%M%SZ')}_{uuid4().hex[:8]}"
        result = {
            "status": "completed",
            "run_id": run_id,
            "created_at": now.isoformat(),
            "model": self.model or getattr(self.provider, "default_model", None),
            "search_context": search_context or {},
            "paper": paper.to_dict(),
            "pdf": pdf_status,
            "summary": summary,
            "conference_recommendations": recommendations,
            "guardrails": {
                "recommendation_type": "scope_fit_shortlist",
                "acceptance_prediction": False,
                "deadlines_included": False,
                "disclaimer": (
                    "This is a topical-fit shortlist, not an acceptance forecast. "
                    "Verify the current call for papers and deadlines on each official site."
                ),
            },
        }
        self._write_run(result)
        return result

    def _write_run(self, payload: dict[str, Any]) -> Path:
        self.runs_dir.mkdir(parents=True, exist_ok=True)
        path = self.runs_dir / f"{payload['run_id']}.json"
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return path
