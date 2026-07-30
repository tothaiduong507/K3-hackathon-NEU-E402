from __future__ import annotations

import html
import json
import os
from datetime import datetime, timezone
from typing import Any

import streamlit as st

from paper2venue.config import load_dotenv
from paper2venue.llm import make_provider
from paper2venue.pipeline import Paper2VenuePipeline
from paper2venue.render import render_deep_summary, render_literature_review


st.set_page_config(
    page_title="Paper2Venue · AI Research Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# The project-local .env is the source of truth for the demo. Streamlit can be
# launched from a terminal that already contains an empty or stale key; without
# override=True that inherited value would silently win over the valid file.
load_dotenv(override=True)

DEFAULT_QUERY = "Graph Neural Network for Multi-omics Classification"
PRESETS = {
    "🧬 Multi-omics GNN": DEFAULT_QUERY,
    "🤖 LLM Hallucination": "Large Language Model Hallucination Mitigation",
    "🏥 Medical Diffusion": "Diffusion Models for Medical Image Segmentation",
}

PROGRESS_MESSAGES = {
    "search_started": "Đang tìm bài báo từ Semantic Scholar, tự động chuyển sang arXiv khi cần…",
    "search_completed": "Đã nhận {result_count} bài từ nguồn {source}.",
    "filter_completed": "Bộ lọc giữ lại {kept_count} bài, loại {removed_count} bài.",
    "ranking_completed": "Đã xếp hạng {ranked_count} bài bằng điểm liên quan minh bạch.",
    "analysis_started": "AI đang đọc abstract của {selected_count} bài nổi bật…",
    "analysis_completed": "Đã tạo {summary_count} bản tóm tắt và đối chiếu chéo.",
    "conference_completed": "Đã hoàn thành {recommendation_count} gợi ý hội nghị.",
}


def esc(value: Any) -> str:
    return html.escape(str(value or ""), quote=True)


def set_query(value: str) -> None:
    st.session_state.research_query = value
    st.session_state.pop("review_result", None)


def reset_search() -> None:
    st.session_state.research_query = DEFAULT_QUERY
    st.session_state.view = "search"
    st.session_state.pop("review_result", None)
    st.session_state.pop("review_error", None)
    st.session_state.pop("deep_result", None)
    st.session_state.pop("deep_error", None)


def open_deep_summary(paper: dict[str, Any]) -> None:
    st.session_state.view = "deep"
    st.session_state.deep_paper = paper
    st.session_state.pop("deep_result", None)
    st.session_state.pop("deep_error", None)


def close_deep_summary() -> None:
    st.session_state.view = "search"
    st.session_state.pop("deep_error", None)


def joined_authors(paper: dict[str, Any], limit: int = 3) -> str:
    authors = list(paper.get("authors") or [])
    if not authors:
        return "Không rõ tác giả"
    text = ", ".join(authors[:limit])
    return f"{text} et al." if len(authors) > limit else text


def bullet_list(values: list[Any] | None, empty: str = "Chưa có dữ liệu.") -> None:
    items = [str(value).strip() for value in (values or []) if str(value).strip()]
    if not items:
        st.caption(empty)
        return
    st.markdown("\n".join(f"- {value}" for value in items))


def render_sidebar(provider_name: str) -> None:
    st.markdown(
        """
        <div class="side-brand">
          <div class="brand-mark">P2V</div>
          <div>
            <div class="brand-name">Paper2Venue</div>
            <div class="brand-subtitle">AI Research Assistant</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="side-label">LUỒNG PHÂN TÍCH</div>', unsafe_allow_html=True)
    steps = [
        ("01", "Search & Filter", "Tìm và lọc nguồn học thuật"),
        ("02", "Rule Engine", "Chấm điểm minh bạch"),
        ("03", "AI Literature Review", "Tóm tắt và so sánh"),
        ("04", "Conference Match", "Gợi ý theo phạm vi"),
    ]
    for number, title, description in steps:
        st.markdown(
            f"""
            <div class="flow-step">
              <div class="flow-number">{number}</div>
              <div><b>{esc(title)}</b><span>{esc(description)}</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown('<div class="side-label">TRẠNG THÁI DEMO</div>', unsafe_allow_html=True)
    key_name = "OPENAI_API_KEY" if provider_name == "openai" else "OPENROUTER_API_KEY"
    key_ready = bool(os.getenv(key_name))
    state_class = "ready" if key_ready else "missing"
    state_text = "Sẵn sàng gọi AI" if key_ready else f"Thiếu {key_name}"
    st.markdown(
        f"""
        <div class="system-card">
          <div><span class="status-dot {state_class}"></span>{esc(state_text)}</div>
          <span>Paper search có cơ chế Semantic Scholar → arXiv fallback.</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption(
        "Tóm tắt chỉ dùng abstract đã truy xuất. Gợi ý hội nghị là độ phù hợp chủ đề, "
        "không phải dự đoán khả năng được nhận."
    )


def render_ranked_papers(result: dict[str, Any]) -> None:
    search = result["search"]
    review = result["literature_review"]
    selected_ids = set(search["selected_paper_ids"])
    summaries = {
        item["paper_id"]: item
        for item in review["paper_summaries"]
    }

    for item in search["ranked_papers"]:
        paper = item["paper"]
        paper_id = paper["paper_id"]
        selected = paper_id in selected_ids
        score = float(item["relevance_score"])
        title = esc(paper["title"])
        url = esc(paper.get("url") or "")
        title_html = (
            f'<a href="{url}" target="_blank" rel="noopener">{title} ↗</a>'
            if url
            else title
        )
        citation = paper.get("citation_count")
        metadata = " · ".join(
            [
                esc(joined_authors(paper)),
                esc(paper.get("year") or "Không rõ năm"),
                f"{esc(citation) if citation is not None else 'N/A'} trích dẫn",
                esc(paper.get("venue") or "Chưa rõ venue"),
            ]
        )
        selected_badge = (
            '<span class="analyzed-badge">AI ANALYZED</span>' if selected else ""
        )
        st.markdown(
            f"""
            <div class="paper-card">
              <div class="paper-rank">{item["rank"]}</div>
              <div class="paper-main">
                <div class="paper-title">{title_html} {selected_badge}</div>
                <div class="paper-meta">{metadata}</div>
                <div class="match-row">Khớp từ khóa: {esc(", ".join(item["matched_query_terms"]) or "không có khớp chính xác")}</div>
              </div>
              <div class="score-pill"><b>{score:.0f}</b><span>/100</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        arxiv_id = (
            (paper.get("external_ids") or {}).get("ArXiv")
            or (paper.get("external_ids") or {}).get("ARXIV")
        )
        st.button(
            "📚 Đọc và tóm tắt toàn bài",
            key=f"deep_summary_{paper_id}",
            on_click=open_deep_summary,
            args=(paper,),
            disabled=not bool(arxiv_id),
            help=(
                "Tải PDF arXiv, đọc theo từng section và tạo bản tóm tắt chi tiết."
                if arxiv_id
                else "Paper này chưa có arXiv ID để tải toàn văn."
            ),
            use_container_width=True,
        )

        label = "AI summary & giải thích điểm" if selected else "Chi tiết cách tính điểm"
        with st.expander(label):
            breakdown = item["score_breakdown"]
            cols = st.columns(5)
            labels = [
                ("Tiêu đề", "title_overlap"),
                ("Abstract", "abstract_overlap"),
                ("Thứ hạng nguồn", "source_api_rank"),
                ("Trích dẫn", "citation_signal"),
                ("Độ mới", "recency_signal"),
            ]
            for col, (metric_label, key) in zip(cols, labels):
                col.metric(metric_label, f"{breakdown[key]:.1f}")

            summary = summaries.get(paper_id)
            if not summary:
                st.caption("Bài này nằm ngoài nhóm được AI phân tích sâu trong lượt chạy.")
                continue

            st.markdown(f"**Vì sao liên quan:** {summary['relevance_explanation']}")
            left, right = st.columns(2)
            with left:
                st.markdown("**Vấn đề nghiên cứu**")
                st.write(summary["problem"])
                st.markdown("**Kết quả chính**")
                bullet_list(summary["key_findings"])
            with right:
                st.markdown("**Phương pháp**")
                st.write(summary["method"])
                st.markdown("**Hạn chế**")
                bullet_list(summary["limitations"])
            st.caption("Nguồn bằng chứng: " + ", ".join(summary["source_refs"]))


def render_comparison(result: dict[str, Any]) -> None:
    comparison = result["literature_review"]["comparison"]
    paper_titles = {
        item["paper"]["paper_id"]: item["paper"]["title"]
        for item in result["search"]["ranked_papers"]
    }
    tabs = st.tabs(
        ["Chủ đề chung", "Khác biệt phương pháp", "Khoảng trống", "Thứ tự đọc"]
    )
    with tabs[0]:
        bullet_list(comparison["common_themes"])
    with tabs[1]:
        bullet_list(comparison["methodological_differences"])
    with tabs[2]:
        bullet_list(comparison["evidence_gaps"])
    with tabs[3]:
        order = comparison["suggested_reading_order"]
        if not order:
            st.caption("Chưa có thứ tự đọc.")
        for index, paper_id in enumerate(order, start=1):
            st.markdown(
                f'<div class="reading-item"><b>{index:02d}</b><span>{esc(paper_titles.get(paper_id, paper_id))}</span></div>',
                unsafe_allow_html=True,
            )


def render_conferences(result: dict[str, Any]) -> None:
    recommendations = result["conference_recommendations"]
    columns = st.columns(min(3, len(recommendations)))
    for index, recommendation in enumerate(recommendations):
        with columns[index % len(columns)]:
            confidence = str(recommendation["confidence"]).upper()
            st.markdown(
                f"""
                <div class="conference-card">
                  <div class="conference-top">
                    <span class="venue-rank">FIT</span>
                    <span class="confidence">{esc(confidence)}</span>
                  </div>
                  <div class="conference-acronym">{esc(recommendation["acronym"])}</div>
                  <div class="conference-name">{esc(recommendation["name"])}</div>
                  <div class="fit-score">{int(recommendation["fit_score"])}<span>/100 scope fit</span></div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown("**Vì sao phù hợp**")
            bullet_list(recommendation["reasons"])
            if recommendation["risks"]:
                with st.expander("Điểm cần kiểm tra"):
                    bullet_list(recommendation["risks"])
            st.link_button(
                f"Mở website {recommendation['acronym']} ↗",
                recommendation["official_url"],
                use_container_width=True,
            )
            st.caption(
                f"Scope kiểm chứng: {recommendation['scope_verified_at']} · "
                "Deadline không được suy đoán"
            )


def evidence_list(items: list[dict[str, Any]], text_key: str) -> None:
    if not items:
        st.caption("Không có nội dung được hỗ trợ bởi văn bản đã trích xuất.")
        return
    for item in items:
        refs = " · ".join(f"[{ref}]" for ref in item.get("source_refs") or [])
        st.markdown(f"- {item.get(text_key, '')}  \n  `{refs}`")


def render_deep_result(result: dict[str, Any]) -> None:
    if result.get("status") != "completed":
        st.error(result.get("message", "Không thể tạo bản tóm tắt toàn văn."))
        return

    summary = result["deep_summary"]
    paper = result["paper"]
    pdf = result["pdf"]
    st.success(
        "Đã tạo bản tóm tắt từ toàn văn PDF."
        + (" Kết quả được lấy từ cache." if result["cache"]["hit"] else "")
    )
    metrics = st.columns(4)
    metrics[0].metric("Trang PDF", pdf["total_pages"])
    metrics[1].metric("Trang đã đọc", pdf["extracted_pages"])
    metrics[2].metric("Độ phủ", f"{pdf['coverage_percent']}%")
    metrics[3].metric("Section chunks", summary["section_chunk_count"])

    overview_tab, method_tab, sections_tab, limits_tab, evidence_tab = st.tabs(
        [
            "Tổng quan",
            "Phương pháp & Thực nghiệm",
            "Theo từng Section",
            "Hạn chế & Thuật ngữ",
            "Evidence & Export",
        ]
    )
    with overview_tab:
        st.markdown("### Executive Summary")
        st.write(summary["executive_summary"])
        left, right = st.columns(2)
        with left:
            st.markdown("#### Research Problem")
            st.write(summary["research_problem"])
        with right:
            st.markdown("#### Motivation")
            st.write(summary["motivation"])
        st.markdown("#### Đóng góp chính")
        evidence_list(summary["contributions"], "contribution")
        st.markdown("#### Kết quả quan trọng")
        evidence_list(summary["results"], "finding")
        st.markdown("#### Key Takeaways")
        evidence_list(summary["key_takeaways"], "takeaway")

    with method_tab:
        methodology = summary["methodology"]
        st.markdown("### Methodology")
        st.write(methodology["overview"])
        left, right = st.columns(2)
        with left:
            st.markdown("#### Quy trình")
            bullet_list(methodology["steps"])
        with right:
            st.markdown("#### Thành phần")
            bullet_list(methodology["components"])
        experiments = summary["data_and_experiments"]
        exp_columns = st.columns(2)
        with exp_columns[0]:
            st.markdown("#### Datasets")
            bullet_list(experiments["datasets"])
            st.markdown("#### Metrics")
            bullet_list(experiments["metrics"])
        with exp_columns[1]:
            st.markdown("#### Experimental Setup")
            bullet_list(experiments["experimental_setup"])
            st.markdown("#### Baselines")
            bullet_list(experiments["baselines"])
        st.markdown("#### Ablation Studies")
        evidence_list(summary["ablation_studies"], "finding")

    with sections_tab:
        for section in summary["section_summaries"]:
            refs = " · ".join(f"[{ref}]" for ref in section["source_refs"])
            with st.expander(section["section"], expanded=True):
                st.write(section["summary"])
                st.caption(f"Nguồn: {refs}")

    with limits_tab:
        limitations = summary["limitations"]
        left, right = st.columns(2)
        with left:
            st.markdown("### Tác giả công bố")
            bullet_list(limitations["author_stated"])
        with right:
            st.markdown("### Nhận xét thận trọng của AI")
            bullet_list(limitations["analyst_observations"])
        st.markdown("### Glossary")
        for item in summary["glossary"]:
            refs = " · ".join(f"[{ref}]" for ref in item["source_refs"])
            st.markdown(
                f"**{item['term']}** — {item['explanation']}  \n`{refs}`"
            )

    with evidence_tab:
        st.info(result["guardrails"]["disclaimer"])
        st.markdown("**Nguồn toàn văn**")
        st.write(
            {
                "paper_id": paper["paper_id"],
                "arxiv_id": pdf["arxiv_id"],
                "source_level": summary["source_level"],
                "source_labels": summary["source_labels"],
                "model": result["model"],
                "prompt_version": summary["prompt_version"],
            }
        )
        left, right = st.columns(2)
        left.download_button(
            "⬇ Tải Deep Summary Markdown",
            render_deep_summary(result),
            file_name=f"{result['run_id']}.md",
            mime="text/markdown",
            use_container_width=True,
        )
        right.download_button(
            "⬇ Tải Deep Summary JSON",
            json.dumps(result, ensure_ascii=False, indent=2),
            file_name=f"{result['run_id']}.json",
            mime="application/json",
            use_container_width=True,
        )


def render_deep_page(provider_name: str) -> None:
    paper = st.session_state.get("deep_paper") or {}
    top_columns = st.columns([1, 5])
    top_columns[0].button(
        "← Quay lại",
        on_click=close_deep_summary,
        use_container_width=True,
    )
    with top_columns[1]:
        st.markdown(
            f"""
            <div class="result-heading" style="margin-top:0">
              <div>
                <span class="eyebrow">DEEP PAPER SUMMARY</span>
                <h2>{esc(paper.get("title") or "Paper detail")}</h2>
                <p>{esc(joined_authors(paper))} · {esc(paper.get("year") or "Không rõ năm")}</p>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.caption(
        "Hệ thống tải PDF arXiv, đọc theo từng section, tổng hợp hai lượt và "
        "gắn dẫn chứng trang cho các kết luận quan trọng."
    )

    control_columns = st.columns([2, 2, 3])
    language_label = control_columns[0].selectbox(
        "Ngôn ngữ bản tóm tắt",
        ["Tiếng Việt", "English"],
        key="deep_language",
    )
    control_columns[1].selectbox(
        "Mức độ chi tiết",
        ["Detailed · 10–15 phút đọc"],
        disabled=True,
    )
    run_deep = control_columns[2].button(
        "✨ Tạo bản tóm tắt toàn bài",
        type="primary",
        use_container_width=True,
    )

    if run_deep:
        required_key = (
            "OPENAI_API_KEY" if provider_name == "openai" else "OPENROUTER_API_KEY"
        )
        if not os.getenv(required_key):
            st.error(f"Chưa có {required_key} trong codebase/.env.")
        else:
            st.session_state.pop("deep_error", None)
            language = "vi" if language_label == "Tiếng Việt" else "en"
            with st.status("Đang đọc toàn văn paper…", expanded=True) as status:
                def deep_progress(event: str, details: dict[str, Any]) -> None:
                    if event == "paper_resolved":
                        status.write(f"✓ Đã xác định paper: {details['title']}")
                    elif event == "pdf_started":
                        status.write("• Đang tải và trích xuất PDF arXiv…")
                    elif event == "pdf_completed":
                        status.write(
                            f"✓ Đã đọc {details['extracted_pages']}/"
                            f"{details['total_pages']} trang PDF"
                        )
                    elif event == "chunk_started":
                        status.write(
                            f"• Đang tóm tắt phần {details['index']}/"
                            f"{details['total']}: {details['section']}"
                        )
                    elif event == "synthesis_started":
                        status.write("• Đang tổng hợp toàn bài và kiểm tra dẫn chứng…")
                    elif event == "cache_hit":
                        status.write("✓ Đã tìm thấy bản tóm tắt trong cache")
                    elif event == "deep_summary_completed":
                        status.write("✓ Đã hoàn thành Deep Paper Summary")

                try:
                    pipeline = Paper2VenuePipeline(provider=make_provider(provider_name))
                    deep_result = pipeline.build_deep_summary(
                        str(paper["paper_id"]),
                        language=language,
                        progress=deep_progress,
                    )
                    st.session_state.deep_result = deep_result
                    if deep_result.get("status") == "completed":
                        status.update(
                            label="Đã tóm tắt toàn bài",
                            state="complete",
                            expanded=False,
                        )
                    else:
                        status.update(
                            label="Không lấy được toàn văn",
                            state="error",
                            expanded=True,
                        )
                except Exception as exc:
                    st.session_state.pop("deep_result", None)
                    st.session_state.deep_error = f"{type(exc).__name__}: {exc}"
                    status.update(
                        label="Deep Summary gặp lỗi",
                        state="error",
                        expanded=True,
                    )

    if st.session_state.get("deep_error"):
        st.error("Không thể hoàn tất bản tóm tắt toàn bài.")
        with st.expander("Chi tiết để nhóm kiểm tra"):
            st.code(st.session_state.deep_error)
    if st.session_state.get("deep_result"):
        render_deep_result(st.session_state.deep_result)


def render_result(result: dict[str, Any]) -> None:
    if result.get("status") != "completed":
        st.error(result.get("message", "Pipeline chưa hoàn thành."))
        return

    search = result["search"]
    review = result["literature_review"]
    st.markdown(
        f"""
        <div class="result-heading">
          <div>
            <span class="eyebrow">RESULTS DASHBOARD</span>
            <h2>Smart Literature Review</h2>
            <p>{esc(result["query"])}</p>
          </div>
          <div class="run-chip">{esc(result["run_id"])}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if search["source"] == "arxiv":
        st.warning(
            "Semantic Scholar đang giới hạn truy cập nên hệ thống đã tự chuyển sang arXiv. "
            "Số lượt trích dẫn sẽ hiển thị N/A."
        )

    metrics = st.columns(4)
    metrics[0].metric("Papers fetched", search["result_count"])
    metrics[1].metric("Rule kept", search.get("filtered_count", search["result_count"]))
    metrics[2].metric("AI analyzed", len(review["paper_summaries"]))
    metrics[3].metric("Conferences", len(result["conference_recommendations"]))

    if review.get("analysis_mode") == "single_paper_brief":
        st.info(
            "Chế độ single-paper brief: hệ thống vẫn tóm tắt và gợi ý conference, "
            "nhưng không đưa ra kết luận so sánh chéo từ một nguồn duy nhất."
        )

    paper_tab, comparison_tab, conference_tab, trace_tab = st.tabs(
        ["📄 Top Papers", "🧭 So sánh & Research Gaps", "🏛️ Conferences", "🛡️ Evidence & Export"]
    )
    with paper_tab:
        render_ranked_papers(result)
    with comparison_tab:
        render_comparison(result)
    with conference_tab:
        render_conferences(result)
    with trace_tab:
        st.info(result["guardrails"]["disclaimer"])
        topic = review["topic_profile"]
        st.markdown("**Topic profile do AI trích xuất**")
        st.write(
            {
                "keywords": topic["keywords"],
                "fields": topic["fields"],
                "venue_fit_description": topic["venue_fit_description"],
                "source_level": review["source_level"],
            }
        )
        if search.get("primary_error"):
            with st.expander("Chi tiết fallback nguồn dữ liệu"):
                st.code(search["primary_error"])
        left, right = st.columns(2)
        markdown_report = render_literature_review(result)
        left.download_button(
            "⬇ Tải báo cáo Markdown",
            markdown_report,
            file_name=f"{result['run_id']}.md",
            mime="text/markdown",
            use_container_width=True,
        )
        right.download_button(
            "⬇ Tải dữ liệu JSON",
            json.dumps(result, ensure_ascii=False, indent=2),
            file_name=f"{result['run_id']}.json",
            mime="application/json",
            use_container_width=True,
        )


st.markdown(
    """
    <style>
      :root {
        --bg: #07101f;
        --panel: #0d182a;
        --panel-2: #111f34;
        --line: #20334e;
        --text: #f2f6ff;
        --muted: #91a2bd;
        --blue: #2f81f7;
        --violet: #8b5cf6;
        --green: #34d399;
      }
      .stApp {
        background:
          radial-gradient(circle at 70% -20%, rgba(47, 129, 247, .16), transparent 38%),
          linear-gradient(180deg, #07101f 0%, #091322 100%);
        color: var(--text);
      }
      [data-testid="stHeader"] { background: transparent; }
      [data-testid="stSidebar"] {
        background: #091321;
        border-right: 1px solid var(--line);
      }
      [data-testid="stSidebar"] > div { padding-top: 1.6rem; }
      .block-container { max-width: 1280px; padding: 2.2rem 2.5rem 5rem; }
      h1, h2, h3 { letter-spacing: -.03em; }
      .side-brand { display:flex; gap:12px; align-items:center; margin: 0 0 34px; }
      .brand-mark {
        width:42px; height:42px; border-radius:12px; display:grid; place-items:center;
        font-size:12px; font-weight:900; color:white;
        background:linear-gradient(135deg, var(--blue), var(--violet));
        box-shadow:0 10px 30px rgba(47,129,247,.25);
      }
      .brand-name { font-weight:800; font-size:17px; color:#fff; }
      .brand-subtitle { color:var(--muted); font-size:11px; }
      .side-label {
        color:#61738e; font-size:10px; font-weight:800; letter-spacing:.14em;
        margin:20px 0 10px;
      }
      .flow-step {
        display:flex; gap:12px; align-items:center; padding:11px 10px; margin:5px 0;
        border-radius:10px; border:1px solid transparent;
      }
      .flow-step:hover { background:#0f1d31; border-color:#1f3553; }
      .flow-number {
        width:28px; height:28px; display:grid; place-items:center; border-radius:8px;
        background:#122640; color:#66a9ff; font-size:10px; font-weight:900;
      }
      .flow-step b { display:block; color:#dce8fa; font-size:12px; }
      .flow-step span { display:block; color:#71839d; font-size:10px; margin-top:2px; }
      .system-card {
        padding:12px; border:1px solid var(--line); background:#0d1a2c;
        border-radius:12px; font-size:11px; color:#d7e1f0;
      }
      .system-card > span { display:block; color:#72839d; margin-top:8px; line-height:1.5; }
      .status-dot {
        display:inline-block; width:7px; height:7px; border-radius:99px; margin-right:8px;
      }
      .status-dot.ready { background:var(--green); box-shadow:0 0 10px var(--green); }
      .status-dot.missing { background:#fb7185; box-shadow:0 0 10px #fb7185; }
      .hero {
        position:relative; overflow:hidden; padding:34px 36px; margin-bottom:26px;
        border:1px solid #234369; border-radius:22px;
        background:linear-gradient(135deg, rgba(20,45,78,.95), rgba(15,26,48,.95));
        box-shadow:0 25px 80px rgba(0,0,0,.25);
      }
      .hero:after {
        content:""; position:absolute; width:260px; height:260px; right:-50px; top:-120px;
        border-radius:50%; background:rgba(73,120,255,.2); filter:blur(4px);
      }
      .eyebrow { color:#72aefc; font-size:10px; font-weight:900; letter-spacing:.18em; }
      .hero h1 { color:#fff; font-size:38px; margin:8px 0 10px; max-width:760px; }
      .hero p { color:#aec0d9; max-width:720px; line-height:1.6; margin:0; }
      .section-kicker {
        color:#6e84a2; font-size:10px; font-weight:800; letter-spacing:.14em;
        margin-bottom:8px;
      }
      div[data-testid="stForm"] {
        background:rgba(13,24,42,.86); border:1px solid var(--line);
        border-radius:18px; padding:10px 18px 18px;
      }
      div[data-testid="stTextInput"] input,
      div[data-testid="stNumberInput"] input {
        background:#091423; border-color:#2a3d59; color:#f5f8ff;
      }
      div[data-baseweb="select"] > div { background:#091423; border-color:#2a3d59; }
      .stButton > button, .stDownloadButton > button, .stLinkButton > a {
        border-radius:10px; border-color:#2a3d59; min-height:42px;
      }
      div[data-testid="stFormSubmitButton"] button {
        color:white; font-weight:800; border:0;
        background:linear-gradient(90deg, #246ee9, #7654df);
        box-shadow:0 12px 30px rgba(47,129,247,.25);
      }
      .result-heading {
        display:flex; align-items:end; justify-content:space-between; gap:20px;
        margin:38px 0 20px;
      }
      .result-heading h2 { color:#fff; margin:4px 0; font-size:29px; }
      .result-heading p { color:#79abed; margin:0; }
      .run-chip {
        font:10px monospace; color:#8ba0bb; background:#0d1929;
        border:1px solid var(--line); border-radius:99px; padding:7px 10px;
      }
      [data-testid="stMetric"] {
        background:#0d192a; border:1px solid var(--line); border-radius:14px; padding:13px 15px;
      }
      [data-testid="stMetricValue"] { color:#eaf3ff; font-size:26px; }
      .paper-card {
        display:flex; align-items:flex-start; gap:14px; padding:17px; margin-top:14px;
        background:linear-gradient(135deg, rgba(14,29,50,.96), rgba(11,22,39,.96));
        border:1px solid var(--line); border-radius:15px;
      }
      .paper-rank {
        flex:0 0 31px; width:31px; height:31px; display:grid; place-items:center;
        border-radius:9px; color:white; font-size:12px; font-weight:900;
        background:linear-gradient(135deg, var(--blue), var(--violet));
      }
      .paper-main { flex:1; min-width:0; }
      .paper-title { color:#f2f6ff; font-size:15px; font-weight:800; line-height:1.45; }
      .paper-title a { color:#f2f6ff; text-decoration:none; }
      .paper-title a:hover { color:#72aefc; }
      .paper-meta, .match-row { color:#8192aa; font-size:11px; margin-top:6px; }
      .match-row { color:#6995cf; }
      .analyzed-badge {
        color:#71e5bd; background:rgba(52,211,153,.1); border:1px solid rgba(52,211,153,.25);
        border-radius:99px; font-size:8px; padding:3px 6px; margin-left:7px; vertical-align:2px;
      }
      .score-pill {
        flex:0 0 auto; color:#63e6b9; background:rgba(52,211,153,.08);
        border:1px solid rgba(52,211,153,.25); border-radius:10px; padding:7px 10px;
      }
      .score-pill b { font-size:18px; }
      .score-pill span { font-size:9px; color:#83a99c; }
      .reading-item {
        display:flex; gap:15px; align-items:center; padding:12px 14px; margin:8px 0;
        background:#0d192a; border:1px solid var(--line); border-radius:11px;
      }
      .reading-item b { color:#72aefc; }
      .reading-item span { color:#dbe7f6; }
      .conference-card {
        min-height:205px; padding:18px; margin-top:12px;
        background:linear-gradient(145deg, #111e34, #0b1628);
        border:1px solid #294362; border-radius:17px;
      }
      .conference-top { display:flex; justify-content:space-between; align-items:center; }
      .venue-rank {
        color:#fff; font-size:9px; font-weight:900; padding:4px 7px; border-radius:6px;
        background:linear-gradient(135deg, #7c3aed, #5b42d2);
      }
      .confidence { color:#6eddb7; font-size:9px; font-weight:800; }
      .conference-acronym { color:#fff; font-size:27px; font-weight:900; margin-top:22px; }
      .conference-name { color:#8798b0; font-size:11px; min-height:34px; margin-top:2px; }
      .fit-score { color:#52d7a8; font-size:28px; font-weight:900; margin-top:15px; }
      .fit-score span { color:#789088; font-size:9px; font-weight:600; margin-left:4px; }
      [data-testid="stTabs"] [data-baseweb="tab-list"] { gap:7px; }
      [data-testid="stTabs"] [data-baseweb="tab"] {
        background:#0d1929; border:1px solid var(--line); border-radius:9px 9px 0 0;
        padding:8px 13px;
      }
      @media (max-width: 800px) {
        .block-container { padding:1.2rem; }
        .hero { padding:24px 20px; }
        .hero h1 { font-size:29px; }
        .result-heading { display:block; }
        .run-chip { display:inline-block; margin-top:10px; }
        .paper-meta { line-height:1.6; }
      }
    </style>
    """,
    unsafe_allow_html=True,
)

if "research_query" not in st.session_state:
    st.session_state.research_query = DEFAULT_QUERY
if "view" not in st.session_state:
    st.session_state.view = "search"

with st.sidebar:
    provider_label = st.selectbox(
        "Model provider",
        ["OpenAI", "OpenRouter"],
        help="API key được đọc từ file .env, không hiển thị trên giao diện.",
    )
    provider_name = provider_label.lower()
    render_sidebar(provider_name)
    st.button("↺ Bắt đầu tìm kiếm mới", on_click=reset_search, use_container_width=True)

if st.session_state.view == "deep":
    render_deep_page(provider_name)
    st.stop()

st.markdown(
    """
    <section class="hero">
      <span class="eyebrow">SMART LITERATURE REVIEW · LIVE DEMO</span>
      <h1>Từ câu hỏi nghiên cứu đến bản đồ tài liệu đáng tin cậy.</h1>
      <p>Tìm nguồn học thuật, xếp hạng minh bạch, tóm tắt có dấu vết bằng chứng
      và gợi ý conference phù hợp — trong một luồng duy nhất.</p>
    </section>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="section-kicker">CHỌN NHANH CHỦ ĐỀ MẪU</div>', unsafe_allow_html=True)
preset_columns = st.columns(3)
for preset_column, (label, value) in zip(preset_columns, PRESETS.items()):
    preset_column.button(
        label,
        key=f"preset_{label}",
        on_click=set_query,
        args=(value,),
        use_container_width=True,
    )

with st.form("research_form"):
    query = st.text_input(
        "Research topic query",
        key="research_query",
        placeholder="Ví dụ: Retrieval augmented generation for scientific QA",
    )
    filter_columns = st.columns([1, 1, 1, 1])
    current_year = datetime.now(timezone.utc).year
    min_year = filter_columns[0].number_input(
        "Năm tối thiểu",
        min_value=1990,
        max_value=current_year,
        value=max(1990, current_year - 4),
        step=1,
    )
    min_citations = filter_columns[1].number_input(
        "Trích dẫn tối thiểu",
        min_value=0,
        max_value=10000,
        value=0,
        step=5,
        help="Để 0 khi dùng arXiv fallback vì arXiv không trả số trích dẫn.",
    )
    search_limit = filter_columns[2].slider(
        "Số bài cần tìm",
        min_value=3,
        max_value=20,
        value=10,
    )
    analyze_top = filter_columns[3].slider(
        "Số bài AI phân tích",
        min_value=1,
        max_value=5,
        value=3,
        help=(
            "Có thể chọn 1 khi nguồn tìm kiếm hạn chế. Chế độ này vẫn tóm tắt và "
            "gợi ý conference nhưng không đưa ra so sánh chéo."
        ),
    )
    submitted = st.form_submit_button(
        "🚀 Thực thi AI Pipeline",
        use_container_width=True,
    )

if submitted:
    normalized_query = " ".join(query.split())
    if len(normalized_query) < 6:
        st.warning("Hãy nhập chủ đề nghiên cứu cụ thể hơn trước khi chạy.")
    else:
        required_key = (
            "OPENAI_API_KEY" if provider_name == "openai" else "OPENROUTER_API_KEY"
        )
        if not os.getenv(required_key):
            st.error(
                f"Chưa có {required_key}. Thêm key vào codebase/.env rồi khởi động lại app."
            )
        else:
            st.session_state.pop("review_error", None)
            with st.status("Đang thực thi pipeline…", expanded=True) as pipeline_status:
                def report(event: str, details: dict[str, Any]) -> None:
                    template = PROGRESS_MESSAGES.get(event)
                    if template:
                        pipeline_status.write("✓ " + template.format(**details))

                try:
                    pipeline = Paper2VenuePipeline(provider=make_provider(provider_name))
                    result = pipeline.build_literature_review(
                        normalized_query,
                        search_limit=search_limit,
                        analyze_top=analyze_top,
                        top_conferences=3,
                        min_year=int(min_year),
                        min_citations=int(min_citations),
                        progress=report,
                    )
                    st.session_state.review_result = result
                    if result.get("status") == "completed":
                        pipeline_status.update(
                            label="Pipeline hoàn thành",
                            state="complete",
                            expanded=False,
                        )
                    else:
                        pipeline_status.update(
                            label="Pipeline cần điều chỉnh bộ lọc",
                            state="error",
                            expanded=True,
                        )
                except Exception as exc:
                    st.session_state.pop("review_result", None)
                    st.session_state.review_error = f"{type(exc).__name__}: {exc}"
                    pipeline_status.update(
                        label="Pipeline gặp lỗi",
                        state="error",
                        expanded=True,
                    )

if st.session_state.get("review_error"):
    st.error("Không thể hoàn tất lượt phân tích.")
    with st.expander("Chi tiết để nhóm kiểm tra"):
        st.code(st.session_state.review_error)

if st.session_state.get("review_result"):
    render_result(st.session_state.review_result)
