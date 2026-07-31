from __future__ import annotations

import csv
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
EVAL_DIR = ROOT / "eval"
CODEBASE_DIR = ROOT / "codebase"
RUNS_DIR = CODEBASE_DIR / "runs"
QUALITY_BAR = 0.80


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def run_command(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        args,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def run_unit_tests() -> dict[str, Any]:
    command = [
        sys.executable,
        "-m",
        "unittest",
        "discover",
        "-s",
        "tests",
        "-v",
    ]
    result = run_command(command, CODEBASE_DIR)
    combined = "\n".join(
        [
            f"Executed at: {utc_now()}",
            f"Command: {' '.join(command)}",
            f"Exit code: {result.returncode}",
            "",
            "=== STDOUT ===",
            result.stdout.rstrip(),
            "",
            "=== STDERR ===",
            result.stderr.rstrip(),
            "",
        ]
    )
    (EVAL_DIR / "unit_test_results.txt").write_text(combined, encoding="utf-8")

    match = re.search(r"Ran\s+(\d+)\s+tests?", result.stdout + result.stderr)
    total = int(match.group(1)) if match else 0
    passed = total if result.returncode == 0 else 0
    return {
        "total": total,
        "passed": passed,
        "failed": total - passed if total else None,
        "status": "PASS" if result.returncode == 0 else "FAIL",
        "exit_code": result.returncode,
        "artifact": "eval/unit_test_results.txt",
    }


def run_eval_script(filename: str) -> subprocess.CompletedProcess[str]:
    return run_command([sys.executable, str(EVAL_DIR / filename)], ROOT)


def as_rate(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def normalize_refs(value: Any) -> str:
    if isinstance(value, list):
        return "; ".join(str(item) for item in value)
    if value is None:
        return ""
    return str(value)


def claim_text(item: Any, preferred_key: str) -> tuple[str, str]:
    if isinstance(item, str):
        return item, ""
    if not isinstance(item, dict):
        return str(item), ""
    text = item.get(preferred_key)
    if not text:
        for key in ("claim", "text", "summary", "description"):
            if item.get(key):
                text = item[key]
                break
    return str(text or ""), normalize_refs(item.get("source_refs"))


def generate_groundedness_sheet() -> dict[str, Any]:
    output_path = EVAL_DIR / "groundedness_review.csv"
    previous: dict[tuple[str, str, str], dict[str, str]] = {}
    if output_path.exists():
        with output_path.open("r", encoding="utf-8-sig", newline="") as stream:
            for old_row in csv.DictReader(stream):
                key = (
                    old_row.get("run_id", ""),
                    old_row.get("claim_type", ""),
                    old_row.get("claim", ""),
                )
                previous[key] = old_row

    rows: list[dict[str, str]] = []
    deep_runs: list[dict[str, Any]] = []
    section_plan = (
        ("contribution", "contributions", "contribution", 2),
        ("result", "results", "finding", 2),
        ("takeaway", "key_takeaways", "takeaway", 1),
    )

    for path in sorted(RUNS_DIR.glob("deep_*.json")):
        payload = load_json(path)
        paper = payload.get("paper") or {}
        summary = payload.get("deep_summary") or {}
        pdf = payload.get("pdf") or {}
        run_id = str(payload.get("run_id") or path.stem)
        title = str(paper.get("title") or "")

        selected = 0
        for claim_type, section_key, text_key, limit in section_plan:
            for item in list(summary.get(section_key) or [])[:limit]:
                text, refs = claim_text(item, text_key)
                if not text:
                    continue
                selected += 1
                old_row = previous.get((run_id, claim_type, text), {})
                rows.append(
                    {
                        "run_id": run_id,
                        "paper_title": title,
                        "claim_type": claim_type,
                        "claim": text,
                        "source_refs_from_model": refs,
                        "rater_1": old_row.get("rater_1", ""),
                        "rater_2": old_row.get("rater_2", ""),
                        "final_status": old_row.get(
                            "final_status",
                            "NOT_REVIEWED",
                        ),
                    }
                )

        deep_runs.append(
            {
                "run_id": run_id,
                "paper_title": title,
                "status": payload.get("status"),
                "model": payload.get("model"),
                "pdf_pages_extracted": pdf.get("extracted_pages"),
                "pdf_pages_total": pdf.get("total_pages"),
                "claims_selected_for_review": selected,
                "source_file": f"codebase/runs/{path.name}",
            }
        )

    columns = [
        "run_id",
        "paper_title",
        "claim_type",
        "claim",
        "source_refs_from_model",
        "rater_1",
        "rater_2",
        "final_status",
    ]
    with output_path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)

    completed = sum(1 for item in deep_runs if item["status"] == "completed")
    valid_labels = {"SUPPORTED", "PARTIAL", "UNSUPPORTED"}
    label_counts = {
        label: sum(
            1 for row in rows if row["final_status"].strip().upper() == label
        )
        for label in sorted(valid_labels)
    }
    reviewed = sum(label_counts.values())
    agreements = sum(
        1
        for row in rows
        if row["rater_1"].strip()
        and row["rater_1"].strip().upper() == row["rater_2"].strip().upper()
    )
    review_complete = bool(rows) and reviewed == len(rows)
    return {
        "total_runs": len(deep_runs),
        "completed_runs": completed,
        "claims_prepared": len(rows),
        "claims_reviewed": reviewed,
        "groundedness_status": "COMPLETED" if review_complete else "NOT_REVIEWED",
        "label_counts": label_counts,
        "strict_groundedness_rate": (
            label_counts["SUPPORTED"] / reviewed if reviewed else None
        ),
        "supported_or_partial_rate": (
            (label_counts["SUPPORTED"] + label_counts["PARTIAL"]) / reviewed
            if reviewed
            else None
        ),
        "rater_agreements": agreements,
        "rater_disagreements": len(rows) - agreements,
        "rater_agreement_rate": agreements / len(rows) if rows else None,
        "artifact": "eval/groundedness_review.csv",
        "runs": deep_runs,
    }


def format_percent(value: Any) -> str:
    return f"{as_rate(value) * 100:.2f}%"


def markdown_breakdown(title: str, values: dict[str, Any]) -> list[str]:
    lines = [
        f"### {title}",
        "",
        "| Nhóm | Đạt | Tổng | Tỷ lệ |",
        "|---|---:|---:|---:|",
    ]
    for name, metric in values.items():
        lines.append(
            f"| {name} | {metric['passed']} | {metric['total']} | "
            f"{format_percent(metric['pass_rate'])} |"
        )
    lines.append("")
    return lines


def write_report(summary: dict[str, Any], catalog: dict[str, Any]) -> None:
    golden = summary["golden_eval"]
    ranking = summary["ranking_eval"]
    unit = summary["unit_tests"]
    live = summary["live_deep_runs"]
    failed_cases = [item for item in catalog.get("results", []) if not item.get("passed")]
    if live["groundedness_status"] == "COMPLETED":
        groundedness_result = (
            f"{live['label_counts']['SUPPORTED']}/{live['claims_reviewed']} SUPPORTED "
            f"({format_percent(live['strict_groundedness_rate'])}); "
            f"SUPPORTED + PARTIAL: "
            f"{format_percent(live['supported_or_partial_rate'])}"
        )
        groundedness_conclusion = "**COMPLETED**"
    else:
        groundedness_result = (
            f"{live['completed_runs']}/{live['total_runs']} runs; "
            f"{live['claims_prepared']} claim đã lấy mẫu"
        )
        groundedness_conclusion = "**NOT_REVIEWED**"

    lines = [
        "# Báo cáo đánh giá Paper2Venue",
        "",
        f"- Thời điểm chạy (UTC): `{summary['created_at']}`",
        f"- Trạng thái: **{summary['overall_status']}**",
        f"- Ngưỡng đạt cho golden/ranking: **{QUALITY_BAR:.0%}**",
        "",
        "## Kết quả chính",
        "",
        "| Hạng mục | Kết quả | Ngưỡng / trạng thái | Kết luận |",
        "|---|---:|---:|---|",
        (
            f"| Golden set | {golden['passed']}/{golden['total']} "
            f"({format_percent(golden['pass_rate'])}) | ≥ {QUALITY_BAR:.0%} | "
            f"{golden['status']} |"
        ),
        (
            f"| Ranking | {ranking['passed']}/{ranking['total']} "
            f"({format_percent(ranking['pass_rate'])}) | ≥ {QUALITY_BAR:.0%} | "
            f"{ranking['status']} |"
        ),
        (
            f"| Unit tests | {unit['passed']}/{unit['total']} | Không có test lỗi | "
            f"{unit['status']} |"
        ),
        (
            f"| Groundedness | {groundedness_result} | Hai người chấm | "
            f"{groundedness_conclusion} |"
        ),
        "",
        "## Phạm vi đánh giá",
        "",
        "- Golden set đo guardrail và khả năng truy xuất conference từ catalog cục bộ.",
        "- Ranking eval đo việc paper phù hợp có đứng đầu danh sách trong các case cố định.",
        "- Unit tests kiểm tra logic backend bằng mock; không gọi API trực tiếp.",
        (
            "- Ba log deep-summary thật được dùng để chấm groundedness. "
            f"Trạng thái review hiện tại: `{live['groundedness_status']}`."
        ),
        "",
    ]
    lines.extend(markdown_breakdown("Golden set theo loại case", golden["by_class"]))
    lines.extend(markdown_breakdown("Golden set theo nguồn", golden["by_source_type"]))

    lines.extend(
        [
            "## Case chưa đạt",
            "",
        ]
    )
    if failed_cases:
        for case in failed_cases:
            lines.extend(
                [
                    f"- `{case.get('id')}`: expected `{case.get('expected')}`, "
                    f"actual `{case.get('actual')}`.",
                    "  Nguyên nhân: guardrail hiện chỉ kiểm tra độ dài chuỗi nên metadata dài nhưng thiếu nội dung nghiên cứu vẫn được xem là đủ. Case được giữ nguyên để thể hiện giới hạn thật của hệ thống.",
                ]
            )
    else:
        lines.append("- Không có case thất bại trong lần chạy này.")

    lines.extend(
        [
            "",
            "## Cách chấm groundedness",
            "",
            "1. Mở `eval/groundedness_review.csv`; mỗi người chấm độc lập từng claim bằng `SUPPORTED`, `PARTIAL` hoặc `UNSUPPORTED`.",
            "2. Đối chiếu `source_refs_from_model` với đúng trang PDF trong log tương ứng. Không bắt buộc ghi rater note.",
            "3. Nếu hai người bất đồng, cùng kiểm tra lại và ghi nhãn thống nhất vào `final_status`.",
            "4. Chỉ báo cáo tỷ lệ groundedness sau khi mọi dòng không còn `NOT_REVIEWED`.",
            "",
            "Công thức: `groundedness = số claim SUPPORTED / tổng số claim đã chấm`. Có thể báo cáo thêm tỷ lệ `SUPPORTED + PARTIAL`, nhưng phải ghi rõ cách tính.",
            "",
            "## Cách chạy lại",
            "",
            "Từ thư mục gốc dự án:",
            "",
            "```powershell",
            "codebase\\.venv\\Scripts\\python.exe eval\\run_all_eval.py",
            "```",
            "",
            "Bộ chạy không gọi mạng. Nó chạy unit tests, golden eval, ranking eval và tái tạo toàn bộ artifact tổng hợp.",
            "",
            "## Giới hạn cần công bố",
            "",
            "- Golden set có 26 case, gồm 11 case lấy từ log chạy thật và 15 case do nhóm thiết kế; đây không phải nhãn do chuyên gia bên ngoài cung cấp.",
            "- Catalog conference là tập cục bộ giới hạn, vì vậy điểm cao không chứng minh độ bao phủ mọi hội nghị.",
            "- Unit/golden/ranking đều là deterministic; chúng không chứng minh bản tóm tắt LLM đúng với toàn văn.",
            (
                "- Groundedness được báo cáo theo hai cách: strict chỉ tính "
                "`SUPPORTED`; tỷ lệ mở rộng tính cả `PARTIAL` phải được ghi rõ."
            ),
            "",
            "## Artifact",
            "",
            "- `eval/evaluation_summary.json`: số liệu tổng hợp máy đọc được.",
            "- `eval/catalog_eval_results.json`: kết quả chi tiết 26 golden cases.",
            "- `eval/ranking_eval_results.json`: kết quả chi tiết 8 ranking cases.",
            "- `eval/unit_test_results.txt`: log unit test.",
            "- `eval/groundedness_review.csv`: 15 claim và nhãn của hai người chấm.",
            "- `eval/REAL_SOURCE_INDEX.md`: ánh xạ 11 case thật về log nguồn.",
            "",
        ]
    )
    (EVAL_DIR / "EVALUATION_REPORT.md").write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


def main() -> int:
    EVAL_DIR.mkdir(parents=True, exist_ok=True)

    unit = run_unit_tests()
    catalog_process = run_eval_script("run_catalog_eval.py")
    ranking_process = run_eval_script("run_ranking_eval.py")

    catalog = load_json(EVAL_DIR / "catalog_eval_results.json")
    ranking = load_json(EVAL_DIR / "ranking_eval_results.json")
    groundedness = generate_groundedness_sheet()

    catalog_summary = catalog["summary"]
    ranking_summary = ranking["summary"]
    golden_rate = as_rate(catalog_summary["pass_rate"])
    ranking_rate = as_rate(ranking_summary["pass_rate"])

    golden = {
        "dataset_id": catalog.get("dataset_id"),
        "total": catalog_summary["total"],
        "passed": catalog_summary["passed"],
        "failed": catalog_summary["total"] - catalog_summary["passed"],
        "pass_rate": golden_rate,
        "quality_bar": QUALITY_BAR,
        "status": "PASS"
        if catalog_process.returncode == 0 and golden_rate >= QUALITY_BAR
        else "FAIL",
        "real_source_cases": catalog_summary["source_counts"]["real"],
        "synthetic_cases": catalog_summary["source_counts"]["synthetic"],
        "by_class": catalog_summary["by_class"],
        "by_source_type": catalog_summary["by_source_type"],
        "artifact": "eval/catalog_eval_results.json",
    }
    rank_metric = {
        "dataset_id": ranking.get("dataset_id"),
        "total": ranking_summary["total"],
        "passed": ranking_summary["passed"],
        "failed": ranking_summary["total"] - ranking_summary["passed"],
        "pass_rate": ranking_rate,
        "quality_bar": QUALITY_BAR,
        "status": "PASS"
        if ranking_process.returncode == 0 and ranking_rate >= QUALITY_BAR
        else "FAIL",
        "artifact": "eval/ranking_eval_results.json",
    }

    deterministic_pass = (
        unit["status"] == "PASS"
        and golden["status"] == "PASS"
        and rank_metric["status"] == "PASS"
    )
    review_completed = groundedness["groundedness_status"] == "COMPLETED"
    summary = {
        "created_at": utc_now(),
        "evaluation_scope": (
            "deterministic unit, catalog guardrail, ranking; "
            "manual groundedness is prepared but not yet reviewed"
        ),
        "quality_bar": QUALITY_BAR,
        "unit_tests": unit,
        "golden_eval": golden,
        "ranking_eval": rank_metric,
        "live_deep_runs": groundedness,
        "overall_status": (
            "PASS_DETERMINISTIC_REVIEW_COMPLETED"
            if deterministic_pass and review_completed
            else "PASS_DETERMINISTIC_ONLY"
            if deterministic_pass
            else "FAIL_DETERMINISTIC"
        ),
        "limitations": [
            "Golden and ranking evaluation do not measure live LLM groundedness.",
            "Golden set includes team-authored synthetic cases.",
            "Conference coverage is limited to the local catalog.",
            (
                "Strict groundedness counts only SUPPORTED; "
                "PARTIAL is reported separately."
            ),
        ],
    }
    (EVAL_DIR / "evaluation_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_report(summary, catalog)

    print(
        json.dumps(
            {
                "overall_status": summary["overall_status"],
                "unit_tests": f"{unit['passed']}/{unit['total']}",
                "golden_eval": (
                    f"{golden['passed']}/{golden['total']} "
                    f"({format_percent(golden['pass_rate'])})"
                ),
                "ranking_eval": (
                    f"{rank_metric['passed']}/{rank_metric['total']} "
                    f"({format_percent(rank_metric['pass_rate'])})"
                ),
                "groundedness": groundedness["groundedness_status"],
                "claims_prepared": groundedness["claims_prepared"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    print(f"Saved: {EVAL_DIR / 'EVALUATION_REPORT.md'}")
    print(f"Saved: {EVAL_DIR / 'evaluation_summary.json'}")
    print(f"Saved: {EVAL_DIR / 'groundedness_review.csv'}")
    return 0 if deterministic_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
