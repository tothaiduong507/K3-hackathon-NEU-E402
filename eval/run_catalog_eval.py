from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EVAL_DIR = Path(__file__).resolve().parent
CODEBASE_DIR = EVAL_DIR.parent / "codebase"
sys.path.insert(0, str(CODEBASE_DIR))

from paper2venue.conference_catalog import ConferenceCatalog  # noqa: E402
from paper2venue.guardrails import validate_request  # noqa: E402


def evaluate_case(case: dict[str, Any], catalog: ConferenceCatalog) -> dict[str, Any]:
    source = {
        "source_type": case.get("source_type", "unspecified"),
        "source_ref": case.get("source_ref", ""),
    }
    if "expected_status" in case:
        actual = validate_request(
            abstract=case.get("abstract", ""),
            user_goal=case.get("user_goal", ""),
        )
        passed = actual["status"] == case["expected_status"]
        return {
            "id": case["id"],
            "class": case["class"],
            "passed": passed,
            "expected": case["expected_status"],
            "actual": actual["status"],
            "details": actual,
            **source,
        }

    shortlist = catalog.shortlist(case["profile"], limit=3)
    actual_ids = [item["conference"]["id"] for item in shortlist]
    expected = case["expected_any"]
    passed = bool(set(actual_ids) & set(expected))
    return {
        "id": case["id"],
        "class": case["class"],
        "passed": passed,
        "expected_any": expected,
        "actual_top3": actual_ids,
        "details": shortlist,
        **source,
    }


def main() -> int:
    dataset_path = EVAL_DIR / "golden_set.json"
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    expected_counts = dataset.get("expected_counts", {})
    cases = dataset["cases"]
    actual_counts = {
        "total": len(cases),
        "real": sum(1 for case in cases if case.get("source_type") == "real"),
        "synthetic": sum(
            1 for case in cases if case.get("source_type") == "synthetic"
        ),
    }
    if expected_counts:
        for key in ("total", "real", "synthetic"):
            if actual_counts[key] != expected_counts.get(key):
                raise ValueError(
                    f"Golden-set count mismatch for {key}: "
                    f"expected {expected_counts.get(key)}, got {actual_counts[key]}"
                )
        expected_by_class = expected_counts.get("by_class", {})
        for class_name, expected in expected_by_class.items():
            actual = sum(1 for case in cases if case["class"] == class_name)
            if actual != expected:
                raise ValueError(
                    f"Golden-set class mismatch for {class_name}: "
                    f"expected {expected}, got {actual}"
                )
    catalog = ConferenceCatalog(CODEBASE_DIR / "data" / "conferences.json")
    results = [evaluate_case(case, catalog) for case in cases]
    passed = sum(1 for result in results if result["passed"])
    summary = {
        "total": len(results),
        "passed": passed,
        "pass_rate": passed / len(results) if results else 0.0,
        "quality_bar": dataset["quality_bar"],
        "source_counts": actual_counts,
        "by_class": {},
        "by_source_type": {},
    }
    classes = sorted({result["class"] for result in results})
    for class_name in classes:
        class_results = [result for result in results if result["class"] == class_name]
        class_passed = sum(1 for result in class_results if result["passed"])
        summary["by_class"][class_name] = {
            "passed": class_passed,
            "total": len(class_results),
            "pass_rate": class_passed / len(class_results),
        }
    source_types = sorted({result["source_type"] for result in results})
    for source_type in source_types:
        source_results = [
            result for result in results if result["source_type"] == source_type
        ]
        source_passed = sum(1 for result in source_results if result["passed"])
        summary["by_source_type"][source_type] = {
            "passed": source_passed,
            "total": len(source_results),
            "pass_rate": source_passed / len(source_results),
        }
    payload = {
        "dataset_id": dataset["dataset_id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "evaluation_scope": (
            "deterministic_guardrails_and_catalog_retrieval; "
            "does_not_measure_live_llm_groundedness"
        ),
        "summary": summary,
        "results": results,
    }
    output_path = EVAL_DIR / "catalog_eval_results.json"
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"Saved: {output_path}")
    return 0 if summary["pass_rate"] >= dataset["quality_bar"]["overall_pass_rate"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
