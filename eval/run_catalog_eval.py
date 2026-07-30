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
    }


def main() -> int:
    dataset_path = EVAL_DIR / "golden_set.json"
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    catalog = ConferenceCatalog(CODEBASE_DIR / "data" / "conferences.json")
    results = [evaluate_case(case, catalog) for case in dataset["cases"]]
    passed = sum(1 for result in results if result["passed"])
    summary = {
        "total": len(results),
        "passed": passed,
        "pass_rate": passed / len(results) if results else 0.0,
        "quality_bar": dataset["quality_bar"],
        "by_class": {},
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
    payload = {
        "dataset_id": dataset["dataset_id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "evaluation_scope": "deterministic_guardrails_and_catalog_retrieval",
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

