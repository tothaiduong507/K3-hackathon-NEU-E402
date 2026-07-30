from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path


EVAL_DIR = Path(__file__).resolve().parent
CODEBASE_DIR = EVAL_DIR.parent / "codebase"
sys.path.insert(0, str(CODEBASE_DIR))

from paper2venue.models import Paper  # noqa: E402
from paper2venue.paper_ranking import rank_papers  # noqa: E402


def main() -> int:
    dataset = json.loads((EVAL_DIR / "ranking_cases.json").read_text(encoding="utf-8"))
    results = []
    for case in dataset["cases"]:
        ranked = rank_papers(
            case["query"],
            [Paper(**paper) for paper in case["papers"]],
        )
        actual_top = ranked[0]["paper"]["paper_id"] if ranked else None
        results.append(
            {
                "id": case["id"],
                "passed": actual_top == case["expected_top"],
                "expected_top": case["expected_top"],
                "actual_top": actual_top,
                "ranking": [
                    {
                        "paper_id": item["paper"]["paper_id"],
                        "score": item["relevance_score"],
                        "breakdown": item["score_breakdown"],
                    }
                    for item in ranked
                ],
            }
        )

    passed = sum(1 for result in results if result["passed"])
    pass_rate = passed / len(results) if results else 0.0
    output = {
        "dataset_id": dataset["dataset_id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total": len(results),
            "passed": passed,
            "pass_rate": pass_rate,
            "quality_bar": dataset["quality_bar"],
        },
        "results": results,
    }
    output_path = EVAL_DIR / "ranking_eval_results.json"
    output_path.write_text(
        json.dumps(output, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(output["summary"], ensure_ascii=False, indent=2))
    print(f"Saved: {output_path}")
    return 0 if pass_rate >= dataset["quality_bar"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

