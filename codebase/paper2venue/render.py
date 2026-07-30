from __future__ import annotations

from typing import Any


def render_deep_summary(payload: dict[str, Any]) -> str:
    if payload.get("status") != "completed":
        return "\n".join(
            [
                "# Deep Paper Summary",
                "",
                f"Status: **{payload.get('status', 'unknown')}**",
                "",
                payload.get("message", ""),
            ]
        )

    paper = payload["paper"]
    summary = payload["deep_summary"]
    lines = [
        f"# Deep Paper Summary — {paper['title']}",
        "",
        f"- Authors: {', '.join(paper.get('authors') or []) or 'Unknown'}",
        f"- Year: {paper.get('year') or 'Unknown'}",
        f"- Paper URL: {paper.get('url') or 'Unavailable'}",
        f"- Source level: `{summary['source_level']}`",
        f"- PDF coverage: {payload['pdf']['coverage_percent']}%",
        "",
        "## Executive summary",
        "",
        summary["executive_summary"],
        "",
        "## Research problem",
        "",
        summary["research_problem"],
        "",
        "## Motivation",
        "",
        summary["motivation"],
        "",
        "## Contributions",
        "",
    ]
    for item in summary["contributions"]:
        refs = ", ".join(f"`[{ref}]`" for ref in item["source_refs"])
        lines.append(f"- {item['contribution']} — {refs}")

    methodology = summary["methodology"]
    lines.extend(["", "## Methodology", "", methodology["overview"], ""])
    lines.extend(f"- Step: {value}" for value in methodology["steps"])
    lines.extend(f"- Component: {value}" for value in methodology["components"])

    experiments = summary["data_and_experiments"]
    lines.extend(["", "## Data and experiments", ""])
    for label, key in [
        ("Dataset", "datasets"),
        ("Setup", "experimental_setup"),
        ("Metric", "metrics"),
        ("Baseline", "baselines"),
    ]:
        lines.extend(f"- {label}: {value}" for value in experiments[key])

    lines.extend(["", "## Results", ""])
    for item in summary["results"]:
        refs = ", ".join(f"`[{ref}]`" for ref in item["source_refs"])
        lines.append(f"- {item['finding']} — {refs}")

    lines.extend(["", "## Ablation studies", ""])
    for item in summary["ablation_studies"]:
        refs = ", ".join(f"`[{ref}]`" for ref in item["source_refs"])
        lines.append(f"- {item['finding']} — {refs}")

    limitations = summary["limitations"]
    lines.extend(["", "## Limitations stated by the authors", ""])
    lines.extend(f"- {value}" for value in limitations["author_stated"])
    lines.extend(["", "## Analyst observations", ""])
    lines.extend(f"- {value}" for value in limitations["analyst_observations"])

    lines.extend(["", "## Section summaries", ""])
    for item in summary["section_summaries"]:
        refs = ", ".join(f"`[{ref}]`" for ref in item["source_refs"])
        lines.extend([f"### {item['section']}", "", item["summary"], "", f"Sources: {refs}", ""])

    lines.extend(["## Key takeaways", ""])
    for item in summary["key_takeaways"]:
        refs = ", ".join(f"`[{ref}]`" for ref in item["source_refs"])
        lines.append(f"- {item['takeaway']} — {refs}")

    lines.extend(["", "## Glossary", ""])
    for item in summary["glossary"]:
        refs = ", ".join(f"`[{ref}]`" for ref in item["source_refs"])
        lines.append(f"- **{item['term']}**: {item['explanation']} — {refs}")

    lines.extend(["", "## Important boundary", "", payload["guardrails"]["disclaimer"]])
    return "\n".join(lines)


def render_search_results(items: list[dict[str, Any]]) -> str:
    lines = ["# Paper search results", ""]
    for index, paper in enumerate(items, start=1):
        authors = ", ".join(paper.get("authors") or []) or "Unknown authors"
        lines.extend(
            [
                f"## {index}. {paper.get('title', 'Untitled')}",
                f"- Authors: {authors}",
                f"- Year: {paper.get('year') or 'Unknown'}",
                f"- Venue: {paper.get('venue') or 'Unknown'}",
                f"- Citations: {paper.get('citation_count') if paper.get('citation_count') is not None else 'Unknown'}",
                f"- URL: {paper.get('url') or 'Unavailable'}",
                "",
            ]
        )
    return "\n".join(lines)


def render_ranked_results(items: list[dict[str, Any]], *, query: str) -> str:
    lines = [f"# Ranked papers — {query}", ""]
    for item in items:
        paper = item["paper"]
        authors = ", ".join(paper.get("authors") or []) or "Unknown authors"
        matched = ", ".join(item["matched_query_terms"]) or "No exact query-term overlap"
        lines.extend(
            [
                f"## {item['rank']}. {paper['title']}",
                f"- Relevance score: {item['relevance_score']}/100",
                f"- Source API rank: {item['source_rank']}",
                f"- Matched terms: {matched}",
                f"- Authors: {authors}",
                f"- Year: {paper.get('year') or 'Unknown'}",
                f"- Citations: {paper.get('citation_count') if paper.get('citation_count') is not None else 'Unknown'}",
                f"- URL: {paper.get('url') or 'Unavailable'}",
                "",
            ]
        )
    return "\n".join(lines)


def render_brief(payload: dict[str, Any]) -> str:
    status = payload.get("status")
    if status != "completed":
        lines = [
            "# Paper2Venue result",
            "",
            f"Status: **{status}**",
            "",
            payload.get("message", ""),
        ]
        for question in payload.get("questions") or []:
            lines.append(f"- {question}")
        return "\n".join(lines)

    paper = payload["paper"]
    summary = payload["summary"]
    lines = [
        f"# Research brief — {paper['title']}",
        "",
        f"- Source level: `{summary['source_level']}`",
        f"- Paper URL: {paper.get('url') or 'Unavailable'}",
        "",
        "## Problem",
        "",
        summary["problem"],
        "",
        "## Method",
        "",
        summary["method"],
        "",
        "## Data / experiments",
        "",
        summary["data_or_experiments"],
        "",
        "## Key findings",
        "",
    ]
    lines.extend(f"- {item}" for item in summary["key_findings"])
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- {item}" for item in summary["limitations"])
    lines.extend(["", "## Evidence map", ""])
    for item in summary["evidence"]:
        refs = ", ".join(f"`[{ref}]`" for ref in item["source_refs"])
        lines.append(f"- {item['claim']} — {refs}")

    lines.extend(["", "## Conference shortlist", ""])
    for index, item in enumerate(payload["conference_recommendations"], start=1):
        lines.extend(
            [
                f"### {index}. {item['acronym']} — fit {item['fit_score']}/100",
                f"- Confidence: {item['confidence']}",
                f"- Official site: {item['official_url']}",
                f"- Scope source: {item['scope_source_url']}",
                f"- Scope verified: {item['scope_verified_at']}",
            ]
        )
        lines.extend(f"- Fit: {reason}" for reason in item["reasons"])
        lines.extend(f"- Risk: {risk}" for risk in item["risks"])
        lines.append("")

    lines.extend(["## Important boundary", "", payload["guardrails"]["disclaimer"]])
    return "\n".join(lines)


def render_literature_review(payload: dict[str, Any]) -> str:
    status = payload.get("status")
    if status != "completed":
        return "\n".join(
            [
                "# Smart Literature Review",
                "",
                f"Status: **{status}**",
                "",
                payload.get("message", ""),
            ]
        )

    review = payload["literature_review"]
    ranked_by_id = {
        item["paper"]["paper_id"]: item
        for item in payload["search"]["ranked_papers"]
    }
    lines = [
        f"# Smart Literature Review — {payload['query']}",
        "",
        f"- Papers found: {payload['search']['result_count']}",
        f"- Papers compared: {len(review['paper_summaries'])}",
        "- Evidence level: `abstract_only`",
        "",
        "## Ranked reading list",
        "",
    ]
    for item in payload["search"]["ranked_papers"]:
        paper = item["paper"]
        selected = " — **analyzed**" if paper["paper_id"] in payload["search"]["selected_paper_ids"] else ""
        lines.append(
            f"{item['rank']}. [{paper['title']}]({paper.get('url') or '#'}) "
            f"— relevance {item['relevance_score']}/100{selected}"
        )

    lines.extend(["", "## Paper summaries", ""])
    for summary in review["paper_summaries"]:
        ranked = ranked_by_id[summary["paper_id"]]
        paper = ranked["paper"]
        lines.extend(
            [
                f"### {paper['title']}",
                f"- Why relevant: {summary['relevance_explanation']}",
                f"- Problem: {summary['problem']}",
                f"- Method: {summary['method']}",
            ]
        )
        lines.extend(f"- Finding: {value}" for value in summary["key_findings"])
        lines.extend(f"- Limitation: {value}" for value in summary["limitations"])
        refs = ", ".join(f"`[{ref}]`" for ref in summary["source_refs"])
        lines.extend([f"- Sources: {refs}", ""])

    comparison = review["comparison"]
    lines.extend(["## Cross-paper comparison", "", "### Common themes", ""])
    lines.extend(f"- {value}" for value in comparison["common_themes"])
    lines.extend(["", "### Methodological differences", ""])
    lines.extend(f"- {value}" for value in comparison["methodological_differences"])
    lines.extend(["", "### Research gaps", ""])
    lines.extend(f"- {value}" for value in comparison["evidence_gaps"])
    lines.extend(["", "### Suggested reading order", ""])
    lines.extend(
        f"{index}. {paper_id}"
        for index, paper_id in enumerate(comparison["suggested_reading_order"], start=1)
    )

    lines.extend(["", "## Conference shortlist", ""])
    for item in payload["conference_recommendations"]:
        lines.extend(
            [
                f"### {item['acronym']} — fit {item['fit_score']}/100",
                f"- Official site: {item['official_url']}",
                f"- Confidence: {item['confidence']}",
            ]
        )
        lines.extend(f"- Fit: {reason}" for reason in item["reasons"])
        lines.extend(f"- Risk: {risk}" for risk in item["risks"])
        lines.append("")

    lines.extend(["## Boundary", "", payload["guardrails"]["disclaimer"]])
    return "\n".join(lines)
