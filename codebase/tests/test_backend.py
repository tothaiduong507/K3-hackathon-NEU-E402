from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from typing import Any

from paper2venue.analyzer import ResearchAnalyzer
from paper2venue.arxiv_search import ResilientPaperSearch, _arxiv_query
from paper2venue.conference_catalog import ConferenceCatalog
from paper2venue.deep_summary import (
    DEEP_SUMMARY_TOOL_NAME,
    SECTION_TOOL_NAME,
    DeepPaperAnalyzer,
    build_document_chunks,
)
from paper2venue.guardrails import validate_request
from paper2venue.llm import ModelResponse, ToolCall
from paper2venue.models import PageChunk, Paper
from paper2venue.paper_ranking import rank_papers
from paper2venue.pipeline import Paper2VenuePipeline
from paper2venue.semantic_scholar import SemanticScholarClient


LONG_NLP_ABSTRACT = (
    "We introduce a retrieval augmented language model for multilingual question "
    "answering. The method retrieves passages from a curated corpus and trains a "
    "generator with citation-aware supervision. Experiments on three multilingual "
    "benchmarks improve factual accuracy and source attribution over baselines."
)


class FakeProvider:
    default_model = "fake-structured-model"

    def __init__(
        self,
        *,
        invalid_ref: bool = False,
        shorthand_review_refs: bool = False,
    ) -> None:
        self.invalid_ref = invalid_ref
        self.shorthand_review_refs = shorthand_review_refs

    def complete(
        self,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]] | None = None,
        *,
        model: str | None = None,
        temperature: float = 0.0,
        tool_choice: Any | None = None,
    ) -> ModelResponse:
        name = tools[0]["function"]["name"]
        if name == "submit_paper_summary":
            ref = "p.999" if self.invalid_ref else "abstract"
            return ModelResponse(
                tool_calls=[
                    ToolCall(
                        name=name,
                        args={
                            "problem": "Multilingual question answering lacks reliable attribution.",
                            "method": "Retrieval-augmented generation with citation-aware supervision.",
                            "data_or_experiments": "Three multilingual benchmarks.",
                            "key_findings": ["The method improves factual accuracy."],
                            "limitations": ["The supplied text does not report deployment results."],
                            "keywords": ["retrieval augmented generation", "language models", "multilingual NLP"],
                            "fields": ["natural language processing"],
                            "evidence": [
                                {
                                    "claim": "The work evaluates three multilingual benchmarks.",
                                    "source_refs": [ref],
                                }
                            ],
                        },
                    )
                ]
            )
        if name == "submit_conference_recommendations":
            return ModelResponse(
                tool_calls=[
                    ToolCall(
                        name=name,
                        args={
                            "recommendations": [
                                {
                                    "conference_id": "acl",
                                    "fit_score": 91,
                                    "confidence": "high",
                                    "reasons": ["The primary contribution is in NLP."],
                                    "risks": ["The full paper was not supplied."],
                                    "evidence_topics": ["natural language processing"],
                                },
                                {
                                    "conference_id": "emnlp",
                                    "fit_score": 87,
                                    "confidence": "medium",
                                    "reasons": ["The method is empirically evaluated."],
                                    "risks": ["Track-level scope needs verification."],
                                    "evidence_topics": ["empirical NLP"],
                                },
                            ]
                        },
                    )
                ]
            )
        if name == "submit_literature_review":
            return ModelResponse(
                tool_calls=[
                    ToolCall(
                        name=name,
                        args={
                            "paper_summaries": [
                                {
                                    "paper_id": paper_id,
                                    "problem": "Grounding multilingual answers.",
                                    "method": "Retrieval-augmented generation.",
                                    "key_findings": ["Grounding improves factuality."],
                                    "limitations": ["Only abstract evidence is available."],
                                    "relevance_explanation": "Directly studies the requested topic.",
                                    "source_refs": [
                                        paper_id
                                        if self.shorthand_review_refs
                                        else f"paper:{paper_id}:abstract"
                                    ],
                                }
                                for paper_id in ["p1", "p2", "p3"]
                            ],
                            "comparison": {
                                "common_themes": ["Retrieval and grounded generation."],
                                "methodological_differences": ["Different retrieval objectives."],
                                "evidence_gaps": ["Limited multilingual deployment evidence."],
                                "suggested_reading_order": ["p1", "p2", "p3"],
                            },
                            "topic_profile": {
                                "keywords": [
                                    "retrieval augmented generation",
                                    "language models",
                                    "multilingual NLP",
                                ],
                                "fields": ["natural language processing"],
                                "venue_fit_description": "Empirical NLP and language-model research.",
                            },
                        },
                    )
                ]
            )
        raise AssertionError(name)


class FakePapers:
    def search(self, query: str, *, limit: int = 5, year: str | None = None) -> list[Paper]:
        return [
            Paper(
                paper_id="fake-paper",
                title="Grounded multilingual question answering",
                abstract=LONG_NLP_ABSTRACT,
                external_ids={},
                url="https://example.test/paper",
            )
        ]

    def get_paper(self, paper_id: str) -> Paper:
        return self.search(paper_id)[0]


class FakeArxivPapers(FakePapers):
    def get_paper(self, paper_id: str) -> Paper:
        paper = super().get_paper(paper_id)
        paper.paper_id = "ARXIV:1706.03762"
        paper.external_ids = {"ArXiv": "1706.03762"}
        return paper


class FakePdfExtractor:
    last_document_metadata = {
        "total_pages": 3,
        "extracted_pages": 3,
        "extracted_characters": 1500,
    }

    def extract(self, paper_id: str, **kwargs: Any) -> list[PageChunk]:
        return [
            PageChunk(
                page=1,
                text=(
                    "1 Introduction\nThis paper studies grounded multilingual "
                    "question answering and motivates retrieval augmentation. " * 5
                ),
            ),
            PageChunk(
                page=2,
                text=(
                    "2 Methodology\nThe model retrieves evidence and trains a "
                    "citation-aware generator with supervised objectives. " * 5
                ),
            ),
            PageChunk(
                page=3,
                text=(
                    "3 Experiments\nExperiments use three multilingual benchmarks "
                    "and compare against retrieval-free baselines. " * 5
                ),
            ),
        ]


class FakeDeepProvider:
    default_model = "fake-deep-model"

    def __init__(self, *, invalid_ref: bool = False) -> None:
        self.calls = 0
        self.invalid_ref = invalid_ref

    def complete(
        self,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]] | None = None,
        *,
        model: str | None = None,
        temperature: float = 0.0,
        tool_choice: Any | None = None,
    ) -> ModelResponse:
        self.calls += 1
        name = tools[0]["function"]["name"]
        if name == SECTION_TOOL_NAME:
            user_text = messages[-1]["content"]
            marker = "Allowed source labels: "
            allowed_line = user_text.split(marker, 1)[1].splitlines()[0]
            ref = allowed_line.split(",", 1)[0].strip()
            if self.invalid_ref:
                ref = "p.999"
            return ModelResponse(
                tool_calls=[
                    ToolCall(
                        name=name,
                        args={
                            "section": "Detected section",
                            "summary": "A detailed summary of the supplied section.",
                            "important_details": ["The section contains grounded details."],
                            "methods": ["Retrieval-augmented generation."],
                            "results": ["The paper reports comparative experiments."],
                            "limitations": ["Only supplied PDF text was considered."],
                            "terms": [
                                {
                                    "term": "retrieval augmentation",
                                    "explanation": "Retrieving evidence before generation.",
                                    "source_refs": [ref],
                                }
                            ],
                            "claims": [
                                {
                                    "claim": "The section describes the paper contribution.",
                                    "source_refs": [ref],
                                }
                            ],
                        },
                    )
                ]
            )
        if name == DEEP_SUMMARY_TOOL_NAME:
            return ModelResponse(
                tool_calls=[
                    ToolCall(
                        name=name,
                        args={
                            "executive_summary": "The paper proposes grounded multilingual QA.",
                            "research_problem": "Multilingual answers need reliable grounding.",
                            "motivation": "Ungrounded generators can produce unsupported answers.",
                            "contributions": [
                                {
                                    "contribution": "A retrieval-augmented QA method.",
                                    "source_refs": ["p.1", "p.2"],
                                }
                            ],
                            "methodology": {
                                "overview": "Retrieve evidence before answer generation.",
                                "steps": ["Retrieve passages.", "Generate a cited answer."],
                                "components": ["Retriever", "Generator"],
                            },
                            "data_and_experiments": {
                                "datasets": ["Three multilingual benchmarks."],
                                "experimental_setup": ["Compare with retrieval-free systems."],
                                "metrics": ["Factual accuracy."],
                                "baselines": ["Retrieval-free generator."],
                            },
                            "results": [
                                {
                                    "finding": "Grounding improves factual accuracy.",
                                    "source_refs": ["p.3"],
                                }
                            ],
                            "ablation_studies": [],
                            "limitations": {
                                "author_stated": ["Deployment was not evaluated."],
                                "analyst_observations": [
                                    "The extracted text does not establish production behavior."
                                ],
                            },
                            "section_summaries": [
                                {
                                    "section": "Introduction",
                                    "summary": "Motivates grounded multilingual QA.",
                                    "source_refs": ["p.1"],
                                },
                                {
                                    "section": "Methodology",
                                    "summary": "Describes retrieval and generation.",
                                    "source_refs": ["p.2"],
                                },
                                {
                                    "section": "Experiments",
                                    "summary": "Evaluates three benchmarks.",
                                    "source_refs": ["p.3"],
                                },
                            ],
                            "key_takeaways": [
                                {
                                    "takeaway": "Retrieval improves grounding.",
                                    "source_refs": ["p.2", "p.3"],
                                }
                            ],
                            "glossary": [
                                {
                                    "term": "grounding",
                                    "explanation": "Connecting answers to retrieved evidence.",
                                    "source_refs": ["p.2"],
                                }
                            ],
                        },
                    )
                ]
            )
        raise AssertionError(name)


class FailingPapers:
    def search(self, query: str, *, limit: int = 5, year: str | None = None) -> list[Paper]:
        raise RuntimeError("throttled")

    def get_paper(self, paper_id: str) -> Paper:
        raise RuntimeError("forbidden")


class FakePaperCollection:
    def search(self, query: str, *, limit: int = 5, year: str | None = None) -> list[Paper]:
        return [
            Paper(
                paper_id=f"p{index}",
                title=f"Retrieval augmented multilingual generation {index}",
                abstract=(
                    LONG_NLP_ABSTRACT
                    + f" Study {index} uses a distinct retrieval objective and evaluation set."
                ),
                citation_count=index * 10,
                year=2022 + index,
                url=f"https://example.test/p{index}",
            )
            for index in range(1, 4)
        ]


class FakeResponse:
    status_code = 200

    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, Any]:
        return self.payload


class FakeSession:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload
        self.last_request: dict[str, Any] | None = None

    def get(self, url: str, **kwargs: Any) -> FakeResponse:
        self.last_request = {"url": url, **kwargs}
        return FakeResponse(self.payload)


class BackendTests(unittest.TestCase):
    def test_guardrail_requests_more_information(self) -> None:
        result = validate_request(abstract="AI paper")
        self.assertEqual(result["status"], "needs_clarification")

    def test_guardrail_rejects_acceptance_guarantee(self) -> None:
        result = validate_request(
            abstract=LONG_NLP_ABSTRACT,
            user_goal="Hãy đảm bảo được nhận tại conference này",
        )
        self.assertEqual(result["status"], "out_of_scope")

    def test_catalog_prefers_nlp_venues(self) -> None:
        catalog = ConferenceCatalog()
        shortlist = catalog.shortlist(LONG_NLP_ABSTRACT, limit=3)
        ids = [item["conference"]["id"] for item in shortlist]
        self.assertTrue({"acl", "emnlp"} & set(ids))

    def test_paper_ranking_exposes_score_breakdown(self) -> None:
        papers = [
            Paper(
                paper_id="relevant",
                title="Retrieval augmented generation for question answering",
                abstract=LONG_NLP_ABSTRACT,
                year=2025,
            ),
            Paper(
                paper_id="other",
                title="Image segmentation for medical scans",
                abstract="This paper studies image segmentation with convolutional networks. " * 3,
                year=2026,
                citation_count=500,
            ),
        ]
        ranked = rank_papers("retrieval augmented generation", papers)
        self.assertEqual(ranked[0]["paper"]["paper_id"], "relevant")
        self.assertIn("title_overlap", ranked[0]["score_breakdown"])

    def test_hyphenated_query_terms_are_matched_separately(self) -> None:
        ranked = rank_papers(
            "retrieval augmented generation",
            [
                Paper(
                    paper_id="exact",
                    title="Retrieval-Augmented Generation for Literature Review",
                    abstract=LONG_NLP_ABSTRACT,
                ),
                Paper(
                    paper_id="partial",
                    title="Retrieval for Image Generation",
                    abstract="Image retrieval and generation for computer vision. " * 3,
                    citation_count=1000,
                ),
            ],
        )
        self.assertEqual(ranked[0]["paper"]["paper_id"], "exact")
        self.assertEqual(
            ranked[0]["matched_query_terms"],
            ["augmented", "generation", "retrieval"],
        )

    def test_pipeline_search_and_rank(self) -> None:
        pipeline = Paper2VenuePipeline(
            provider=FakeProvider(),
            papers=FakePaperCollection(),
        )
        ranked = pipeline.search_and_rank("retrieval multilingual", limit=3)
        self.assertEqual(len(ranked), 3)
        self.assertEqual([item["rank"] for item in ranked], [1, 2, 3])

    def test_semantic_scholar_normalization(self) -> None:
        session = FakeSession(
            {
                "data": [
                    {
                        "paperId": "p1",
                        "title": "Test paper",
                        "abstract": LONG_NLP_ABSTRACT,
                        "authors": [{"name": "A. Author"}],
                        "year": 2026,
                        "citationCount": 4,
                        "venue": "TestConf",
                        "url": "https://example.test/p1",
                        "externalIds": {"ArXiv": "2601.12345"},
                        "fieldsOfStudy": ["Computer Science"],
                        "openAccessPdf": {"url": "https://arxiv.org/pdf/2601.12345"},
                    }
                ]
            }
        )
        client = SemanticScholarClient(session=session)
        papers = client.search("test")
        self.assertEqual(papers[0].external_ids["ArXiv"], "2601.12345")
        self.assertEqual(papers[0].authors, ["A. Author"])
        assert session.last_request is not None
        self.assertIn("/paper/search", session.last_request["url"])

    def test_search_falls_back_when_primary_is_throttled(self) -> None:
        search = ResilientPaperSearch(FailingPapers(), FakePapers())
        results = search.search("multilingual retrieval")
        self.assertEqual(results[0].paper_id, "fake-paper")
        self.assertEqual(search.last_source, "arxiv")
        self.assertIn("throttled", search.last_primary_error or "")

    def test_arxiv_query_drops_stopwords_and_caps_terms(self) -> None:
        query = _arxiv_query(
            "retrieval augmented generation for automated literature review systems"
        )
        self.assertNotIn("all:for", query)
        self.assertEqual(query.count("all:"), 4)

    def test_exact_arxiv_id_falls_back_when_primary_is_forbidden(self) -> None:
        search = ResilientPaperSearch(FailingPapers(), FakePapers())
        paper = search.get_paper("ARXIV:2005.11401")
        self.assertEqual(paper.paper_id, "fake-paper")
        self.assertEqual(search.last_source, "arxiv")
        self.assertIn("forbidden", search.last_primary_error or "")

    def test_pipeline_runs_end_to_end_with_fake_provider(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            pipeline = Paper2VenuePipeline(
                provider=FakeProvider(),
                papers=FakePapers(),
                runs_dir=Path(directory),
            )
            result = pipeline.build_from_query("multilingual retrieval")
            self.assertEqual(result["status"], "completed")
            self.assertEqual(result["summary"]["source_level"], "abstract_only")
            self.assertEqual(result["conference_recommendations"][0]["conference_id"], "acl")
            self.assertEqual(
                result["conference_recommendations"][0]["official_url"],
                "https://www.aclweb.org/portal/acl",
            )
            self.assertEqual(len(list(Path(directory).glob("*.json"))), 1)

    def test_pipeline_can_resolve_exact_paper_id(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            pipeline = Paper2VenuePipeline(
                provider=FakeProvider(),
                papers=FakePapers(),
                runs_dir=Path(directory),
            )
            result = pipeline.build_from_paper_id("ARXIV:2005.11401", use_pdf=False)
            self.assertEqual(result["status"], "completed")
            self.assertEqual(result["search_context"]["paper_id"], "ARXIV:2005.11401")

    def test_smart_literature_review_runs_end_to_end(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            pipeline = Paper2VenuePipeline(
                provider=FakeProvider(),
                papers=FakePaperCollection(),
                runs_dir=Path(directory),
            )
            result = pipeline.build_literature_review(
                "retrieval augmented multilingual NLP",
                search_limit=3,
                analyze_top=3,
                top_conferences=2,
            )
            self.assertEqual(result["status"], "completed")
            self.assertEqual(result["run_type"], "smart_literature_review")
            self.assertEqual(len(result["literature_review"]["paper_summaries"]), 3)
            self.assertEqual(result["literature_review"]["source_level"], "abstract_only")
            self.assertEqual(len(result["conference_recommendations"]), 2)

    def test_review_filters_citations_and_reports_progress(self) -> None:
        events: list[str] = []
        with tempfile.TemporaryDirectory() as directory:
            pipeline = Paper2VenuePipeline(
                provider=FakeProvider(),
                papers=FakePaperCollection(),
                runs_dir=Path(directory),
            )
            result = pipeline.build_literature_review(
                "retrieval augmented multilingual NLP",
                search_limit=3,
                analyze_top=3,
                min_year=2022,
                min_citations=10,
                progress=lambda event, details: events.append(event),
            )
            self.assertEqual(result["status"], "completed")
            self.assertEqual(result["search"]["result_count"], 3)
            self.assertEqual(result["search"]["filtered_count"], 3)
            self.assertEqual(result["search"]["filters"]["min_citations"], 10)
            self.assertEqual(
                events,
                [
                    "search_started",
                    "search_completed",
                    "filter_completed",
                    "ranking_completed",
                    "analysis_started",
                    "analysis_completed",
                    "conference_completed",
                ],
            )

    def test_review_explains_empty_citation_filter(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            pipeline = Paper2VenuePipeline(
                provider=FakeProvider(),
                papers=FakePaperCollection(),
                runs_dir=Path(directory),
            )
            result = pipeline.build_literature_review(
                "retrieval augmented multilingual NLP",
                search_limit=3,
                min_citations=1000,
            )
            self.assertEqual(result["status"], "no_results_after_filter")
            self.assertIn("arXiv", result["message"])

    def test_review_supports_single_eligible_paper(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            pipeline = Paper2VenuePipeline(
                provider=FakeProvider(),
                papers=FakePapers(),
                runs_dir=Path(directory),
            )
            result = pipeline.build_literature_review(
                "multilingual retrieval",
                search_limit=3,
                analyze_top=1,
            )
            review = result["literature_review"]
            self.assertEqual(result["status"], "completed")
            self.assertEqual(review["analysis_mode"], "single_paper_brief")
            self.assertEqual(len(review["paper_summaries"]), 1)
            self.assertEqual(
                review["comparison"]["suggested_reading_order"],
                ["fake-paper"],
            )
            self.assertIn(
                "no cross-paper conclusions",
                result["guardrails"]["disclaimer"],
            )

    def test_document_chunks_detect_sections_and_skip_references(self) -> None:
        pages = [
            PageChunk(page=1, text="1 Introduction\n" + "Motivation text. " * 30),
            PageChunk(page=2, text="2 Methodology\n" + "Method text. " * 30),
            PageChunk(
                page=3,
                text=(
                    "Conclusion\n"
                    + "Conclusion text. " * 20
                    + "\nReferences\n"
                    + "Citation entry. " * 30
                ),
            ),
            PageChunk(page=4, text="Methodology in a cited title. " * 30),
        ]
        chunks = build_document_chunks(pages)
        self.assertEqual(
            [chunk.section for chunk in chunks],
            ["Introduction", "Methodology", "Conclusion"],
        )
        self.assertEqual([chunk.pages for chunk in chunks], [[1], [2], [3]])
        self.assertNotIn("Citation entry", chunks[-1].text)

    def test_deep_summary_runs_and_uses_cache(self) -> None:
        provider = FakeDeepProvider()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pipeline = Paper2VenuePipeline(
                provider=provider,
                papers=FakeArxivPapers(),
                pdfs=FakePdfExtractor(),
                runs_dir=root / "runs",
                cache_dir=root / "cache",
            )
            first = pipeline.build_deep_summary("ARXIV:1706.03762")
            call_count = provider.calls
            second = pipeline.build_deep_summary("ARXIV:1706.03762")
            self.assertEqual(first["status"], "completed")
            self.assertEqual(first["deep_summary"]["source_level"], "full_text")
            self.assertEqual(first["pdf"]["coverage_percent"], 100.0)
            self.assertFalse(first["cache"]["hit"])
            self.assertTrue(second["cache"]["hit"])
            self.assertEqual(provider.calls, call_count)
            self.assertEqual(len(list((root / "runs").glob("deep_*.json"))), 1)

    def test_deep_summary_rejects_unavailable_page_reference(self) -> None:
        analyzer = DeepPaperAnalyzer(FakeDeepProvider(invalid_ref=True))
        paper = FakeArxivPapers().get_paper("ARXIV:1706.03762")
        with self.assertRaisesRegex(ValueError, "unavailable page labels"):
            analyzer.summarize(
                paper=paper,
                pages=[PageChunk(page=1, text="1 Introduction\n" + "Text. " * 100)],
            )

    def test_review_normalizes_same_paper_id_reference_shorthand(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            pipeline = Paper2VenuePipeline(
                provider=FakeProvider(shorthand_review_refs=True),
                papers=FakePaperCollection(),
                runs_dir=Path(directory),
            )
            result = pipeline.build_literature_review(
                "retrieval augmented multilingual NLP",
                search_limit=3,
                analyze_top=3,
            )
            refs = result["literature_review"]["paper_summaries"][0]["source_refs"]
            self.assertEqual(refs, ["paper:p1:abstract"])

    def test_summary_rejects_invented_page_reference(self) -> None:
        analyzer = ResearchAnalyzer(FakeProvider(invalid_ref=True))
        paper = Paper(
            paper_id="p1",
            title="Test",
            abstract=LONG_NLP_ABSTRACT,
        )
        with self.assertRaisesRegex(ValueError, "unavailable source labels"):
            analyzer.summarize(paper, [])


if __name__ == "__main__":
    unittest.main()
