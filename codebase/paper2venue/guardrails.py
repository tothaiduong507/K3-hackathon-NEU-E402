from __future__ import annotations

from typing import Any


OUT_OF_SCOPE_MARKERS = {
    "guarantee acceptance",
    "guarantee accepted",
    "đảm bảo được nhận",
    "chắc chắn được nhận",
    "submit automatically",
    "auto submit",
    "tự động nộp",
    "fabricate citation",
    "fake citation",
    "bịa trích dẫn",
}


def validate_request(
    *,
    abstract: str,
    user_goal: str = "",
) -> dict[str, Any]:
    goal = " ".join((user_goal or "").lower().split())
    matched = sorted(marker for marker in OUT_OF_SCOPE_MARKERS if marker in goal)
    if matched:
        return {
            "status": "out_of_scope",
            "message": (
                "Paper2Venue can create an evidence-based venue shortlist, "
                "but cannot guarantee acceptance, submit a paper, or fabricate citations."
            ),
            "matched_boundaries": matched,
        }

    compact_abstract = " ".join((abstract or "").split())
    if len(compact_abstract) < 80:
        return {
            "status": "needs_clarification",
            "message": "Provide an abstract or research description of at least 80 characters.",
            "questions": [
                "What problem does the work address?",
                "What method or technical approach does it use?",
                "What application domain or data does it target?",
            ],
        }
    return {"status": "ready"}

