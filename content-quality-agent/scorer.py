"""Score aggregation and corrected_text builder.

Implements the scoring rules from references/output-format.md:
- Base score 100
- critical -10, major -5, minor -2, suggestion 0
- Per-category cap (never lose more than the category's max weight)
"""

from typing import Optional


SEVERITY_POINTS = {
    "critical": 10,
    "major": 5,
    "minor": 2,
    "suggestion": 0,
}

# Category max weights (from references/output-format.md)
CATEGORY_MAX = {
    "spacing": 15,
    "punctuation": 15,
    "typo": 25,
    "vietnamese_tone": 20,
    "capitalization": 10,
    "brand_style": 15,
    "image_text_conflict": 15,
    "image_text_quality": 15,  # quality of text on the image itself
}


def deduplicate_issues(issues: list[dict]) -> list[dict]:
    """Remove duplicate issues — same rule_id + position + found.

    Multiple checkers may flag the same problem (e.g., deterministic SP-08
    catches `GreenNodeClaw` while LLM also flags it). Keep first occurrence.
    """
    seen = set()
    out = []
    for issue in issues:
        key = (
            issue.get("rule_id", ""),
            issue.get("position_index", -1),
            issue.get("found", ""),
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(issue)
    return out


def compute_score(issues: list[dict]) -> dict:
    """Compute final score + per-category breakdown.

    Returns:
        {
          "score": int (0-100),
          "grade": str (A/B/C/D/F),
          "categories": { name: {score, max, issues_count} },
          "issues_by_severity": {critical, major, minor, suggestion},
        }
    """
    # Group by category
    by_category: dict[str, list] = {}
    for issue in issues:
        cat = issue.get("category", "uncategorized")
        by_category.setdefault(cat, []).append(issue)

    categories = {}
    total_deduction = 0

    for cat, max_pts in CATEGORY_MAX.items():
        cat_issues = by_category.get(cat, [])
        raw_deduction = sum(
            SEVERITY_POINTS.get(i.get("severity", "minor"), 0)
            for i in cat_issues
        )
        capped = min(raw_deduction, max_pts)
        categories[cat] = {
            "score": max_pts - capped,
            "max": max_pts,
            "raw_deduction": raw_deduction,
            "applied_deduction": capped,
            "issues_count": len(cat_issues),
        }
        total_deduction += capped

    # Catch-all for any uncategorized issues — full deduction, no cap
    for cat, cat_issues in by_category.items():
        if cat not in CATEGORY_MAX:
            extra = sum(
                SEVERITY_POINTS.get(i.get("severity", "minor"), 0)
                for i in cat_issues
            )
            total_deduction += extra
            categories[cat] = {
                "score": None,
                "max": None,
                "raw_deduction": extra,
                "applied_deduction": extra,
                "issues_count": len(cat_issues),
            }

    final_score = max(0, 100 - total_deduction)

    by_severity = {"critical": 0, "major": 0, "minor": 0, "suggestion": 0}
    for issue in issues:
        s = issue.get("severity", "minor")
        if s in by_severity:
            by_severity[s] += 1

    return {
        "score": final_score,
        "grade": grade_from_score(final_score),
        "categories": categories,
        "issues_by_severity": by_severity,
        "total_issues": len(issues),
    }


def grade_from_score(score: int) -> str:
    if score >= 90:
        return "A"
    if score >= 75:
        return "B"
    if score >= 60:
        return "C"
    if score >= 40:
        return "D"
    return "F"


def build_corrected_text(original: str, issues: list[dict]) -> str:
    """Apply non-overlapping suggestions to original text.

    Strategy:
    - Only apply issues with both `found` and `suggestion` and known position.
    - Sort by position descending so replacements don't shift earlier indices.
    - Skip issues that overlap an already-applied range.
    - Skip suggestions with empty `found` or position_index < 0.
    """
    applicable = [
        i for i in issues
        if i.get("found")
        and i.get("suggestion") is not None
        and i.get("position_index", -1) >= 0
        and i.get("severity") != "suggestion"  # don't auto-apply optional improvements
    ]

    # Sort by position descending
    applicable.sort(key=lambda i: i["position_index"], reverse=True)

    applied_ranges: list[tuple[int, int]] = []
    result = original

    for issue in applicable:
        start = issue["position_index"]
        found = issue["found"]
        sugg = issue["suggestion"]

        # Verify the snippet at this position still matches (text may have shifted)
        # Since we apply in reverse order, earlier text is untouched.
        if result[start:start + len(found)] != found:
            # Try a nearby search (within a small window) to recover
            nearby = result.find(found, max(0, start - 5), start + len(found) + 5)
            if nearby < 0:
                continue
            start = nearby

        end = start + len(found)

        # Check overlap with already-applied range
        if any(not (end <= a_start or start >= a_end)
               for a_start, a_end in applied_ranges):
            continue

        # Apply the replacement
        result = result[:start] + sugg + result[end:]
        # Track in terms of new offsets after replacement
        applied_ranges.append((start, start + len(sugg)))

    return result


def sort_issues_for_display(issues: list[dict]) -> list[dict]:
    """Sort issues: severity descending, then position ascending."""
    severity_order = {"critical": 0, "major": 1, "minor": 2, "suggestion": 3}
    return sorted(
        issues,
        key=lambda i: (
            severity_order.get(i.get("severity", "minor"), 99),
            i.get("position_index", 0),
        ),
    )
