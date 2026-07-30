from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .config import RUNS_DIR, load_dotenv
from .llm import make_provider
from .pipeline import Paper2VenuePipeline
from .render import (
    render_brief,
    render_literature_review,
    render_ranked_results,
    render_search_results,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Paper search, summary, and conference shortlist")
    parser.add_argument("--provider", choices=["openai", "openrouter"], default="openai")
    parser.add_argument("--model", default=None)
    subparsers = parser.add_subparsers(dest="command", required=True)

    search = subparsers.add_parser("search", help="Search Semantic Scholar")
    search.add_argument("query")
    search.add_argument("--limit", type=int, default=5)
    search.add_argument("--year", default=None, help="Semantic Scholar year filter, e.g. 2023-")
    search.add_argument("--json", action="store_true")

    rank = subparsers.add_parser(
        "rank",
        help="Search and transparently re-rank papers without a model call",
    )
    rank.add_argument("query")
    rank.add_argument("--limit", type=int, default=10)
    rank.add_argument("--year", default=None)
    rank.add_argument("--json", action="store_true")

    brief = subparsers.add_parser("brief", help="Build a paper summary and venue shortlist")
    source = brief.add_mutually_exclusive_group(required=True)
    source.add_argument("--query")
    source.add_argument(
        "--paper-id",
        help="Semantic Scholar ID, DOI:<doi>, ARXIV:<id>, PMID:<id>, or other supported ID",
    )
    source.add_argument("--abstract-file", type=Path)
    brief.add_argument("--title", default="Untitled research description")
    brief.add_argument("--select", type=int, default=1)
    brief.add_argument("--search-limit", type=int, default=5)
    brief.add_argument("--goal", default="")
    brief.add_argument("--no-pdf", action="store_true")
    brief.add_argument("--top-conferences", type=int, default=3)
    brief.add_argument("--json", action="store_true")

    review = subparsers.add_parser(
        "review",
        help="Rank, summarize, and compare a set of papers for one research query",
    )
    review.add_argument("query")
    review.add_argument("--search-limit", type=int, default=10)
    review.add_argument("--analyze-top", type=int, default=3)
    review.add_argument("--top-conferences", type=int, default=3)
    review.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    load_dotenv()
    args = build_parser().parse_args(argv)
    try:
        provider = make_provider(args.provider)
        pipeline = Paper2VenuePipeline(provider=provider, model=args.model)

        if args.command == "search":
            papers = pipeline.search(args.query, limit=args.limit, year=args.year)
            values = [paper.to_dict() for paper in papers]
            print(
                json.dumps(values, ensure_ascii=False, indent=2)
                if args.json
                else render_search_results(values)
            )
            return 0

        if args.command == "rank":
            values = pipeline.search_and_rank(
                args.query,
                limit=args.limit,
                year=args.year,
            )
            print(
                json.dumps(values, ensure_ascii=False, indent=2)
                if args.json
                else render_ranked_results(values, query=args.query)
            )
            return 0

        if args.command == "review":
            result = pipeline.build_literature_review(
                args.query,
                search_limit=args.search_limit,
                analyze_top=args.analyze_top,
                top_conferences=args.top_conferences,
            )
            output = (
                json.dumps(result, ensure_ascii=False, indent=2)
                if args.json
                else render_literature_review(result)
            )
            print(output)
            if result.get("status") == "completed":
                markdown_path = RUNS_DIR / f"{result['run_id']}.md"
                markdown_path.write_text(
                    render_literature_review(result),
                    encoding="utf-8",
                )
                print(f"\nSaved: {markdown_path}", file=sys.stderr)
            return 0

        if args.abstract_file:
            abstract = args.abstract_file.read_text(encoding="utf-8")
            result = pipeline.build_from_abstract(
                title=args.title,
                abstract=abstract,
                user_goal=args.goal,
                top_conferences=args.top_conferences,
            )
        elif args.paper_id:
            result = pipeline.build_from_paper_id(
                args.paper_id,
                user_goal=args.goal,
                use_pdf=not args.no_pdf,
                top_conferences=args.top_conferences,
            )
        else:
            result = pipeline.build_from_query(
                args.query,
                select=args.select,
                search_limit=args.search_limit,
                user_goal=args.goal,
                use_pdf=not args.no_pdf,
                top_conferences=args.top_conferences,
            )

        output = (
            json.dumps(result, ensure_ascii=False, indent=2)
            if args.json
            else render_brief(result)
        )
        print(output)
        if result.get("status") == "completed":
            markdown_path = RUNS_DIR / f"{result['run_id']}.md"
            markdown_path.write_text(render_brief(result), encoding="utf-8")
            print(f"\nSaved: {markdown_path}", file=sys.stderr)
        return 0
    except Exception as exc:
        print(f"ERROR {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
