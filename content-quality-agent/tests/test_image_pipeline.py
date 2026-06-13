"""Tests for the image pipeline with mocked Minimax responses.

Verifies that:
1. OCR extracted text gets run through deterministic + tone checks
2. Each image issue is tagged with source=image_<idx> and category=image_text_quality
3. Caption-vs-image conflicts are tagged with category=image_text_conflict
4. Both kinds of issues are separately scored
"""

import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock

sys.path.insert(0, str(Path(__file__).parent.parent))


class MockProject:
    brand_name = "GreenNode"
    brand_exclusions = ["GreenNode"]
    forbidden_words: list = []
    preferred_terms: dict = {}
    tone = "casual"
    is_social_media = True


async def test_image_pipeline_quality_check():
    """Image with typos should produce image_text_quality issues."""
    from agent import _check_image_full

    # Mock the Minimax client
    minimax = AsyncMock()
    # OCR returns text WITH typos faithfully preserved
    minimax.extract_image_text.return_value = {
        "extracted_text": "FLASH SALE!!\nGiảm gía toàn bộ  sản phẩm",
        "text_blocks": [
            {"text": "FLASH SALE!!", "region": "top", "confidence": "high"},
            {"text": "Giảm gía toàn bộ  sản phẩm", "region": "middle", "confidence": "high"},
        ],
        "has_text": True,
    }
    # Tone check finds "gía" → "giá"
    minimax.check_vietnamese_tone.return_value = [{
        "rule_id": "VT-06",
        "severity": "major",
        "category": "vietnamese_tone",
        "found": "gía",
        "suggestion": "giá",
        "position": "char 18",
        "position_index": 18,
        "message": "Common Vietnamese tone error: gía → giá",
        "confidence": "high",
    }]
    # No caption conflicts (caption matches image)
    minimax.check_image_conflicts.return_value = []

    caption = "FLASH SALE! Giảm giá toàn bộ sản phẩm"
    quality, conflicts, ocr = await _check_image_full(
        minimax, caption, "fake_b64", 0, MockProject(), set()
    )

    # Verify OCR info captured
    assert ocr["has_text"] is True
    assert "Giảm gía" in ocr["extracted_text"]

    # Verify quality issues exist
    assert len(quality) > 0, "Should detect typos / spacing in image text"

    # All quality issues should be tagged
    for issue in quality:
        assert issue["category"] == "image_text_quality"
        assert issue["source"] == "image_0"
        assert "[Image 0]" in issue["message"]
        assert issue["position"].startswith("image 0 ·")

    # Should detect double space (SP-01)
    rule_ids = {i["rule_id"] for i in quality}
    assert "SP-01" in rule_ids, f"Should detect double space, got: {rule_ids}"

    # Should detect double exclamation (PU-02)
    assert "PU-02" in rule_ids, f"Should detect !!, got: {rule_ids}"

    # Should detect VT-06 from tone checker
    assert "VT-06" in rule_ids, f"Should detect Vietnamese tone, got: {rule_ids}"

    # No conflicts
    assert len(conflicts) == 0

    print("  ✓  test_image_pipeline_quality_check")


async def test_image_pipeline_conflict_only():
    """Image text is clean but conflicts with caption — only conflict issues."""
    from agent import _check_image_full

    minimax = AsyncMock()
    minimax.extract_image_text.return_value = {
        "extracted_text": "Giảm 50% toàn bộ sản phẩm",
        "text_blocks": [],
        "has_text": True,
    }
    minimax.check_vietnamese_tone.return_value = []  # no tone issues
    minimax.check_image_conflicts.return_value = [{
        "rule_id": "IMG-CONFLICT-PERCENT",
        "severity": "critical",
        "category": "image_text_conflict",
        "found": "Giảm 30%",
        "image_text": "Giảm 50%",
        "suggestion": "Choose one: 30% or 50%",
        "position": "char 0",
        "position_index": 0,
        "message": "Discount % mismatch",
        "confidence": "high",
    }]

    caption = "Giảm 30% toàn bộ sản phẩm"
    quality, conflicts, ocr = await _check_image_full(
        minimax, caption, "fake_b64", 0, MockProject(), set()
    )

    assert len(quality) == 0, "Clean image text — should have no quality issues"
    assert len(conflicts) == 1
    assert conflicts[0]["category"] == "image_text_conflict"
    assert conflicts[0]["source"] == "image_0"
    print("  ✓  test_image_pipeline_conflict_only")


async def test_image_pipeline_empty_image():
    """Image with no extractable text — pipeline returns gracefully."""
    from agent import _check_image_full

    minimax = AsyncMock()
    minimax.extract_image_text.return_value = {
        "extracted_text": "",
        "text_blocks": [],
        "has_text": False,
    }

    quality, conflicts, ocr = await _check_image_full(
        minimax, "caption text", "fake_b64", 0, MockProject(), set()
    )

    assert ocr["has_text"] is False
    assert len(quality) == 0
    assert len(conflicts) == 0
    # Should not have called tone or conflict checkers
    minimax.check_vietnamese_tone.assert_not_called()
    minimax.check_image_conflicts.assert_not_called()
    print("  ✓  test_image_pipeline_empty_image")


async def test_image_quality_and_conflict_combined():
    """Image has BOTH typos AND conflicts with caption."""
    from agent import _check_image_full

    minimax = AsyncMock()
    minimax.extract_image_text.return_value = {
        "extracted_text": "Sãn phẩm mới!! Giảm 50%",
        "text_blocks": [],
        "has_text": True,
    }
    minimax.check_vietnamese_tone.return_value = [{
        "rule_id": "VT-06",
        "severity": "major",
        "category": "vietnamese_tone",
        "found": "Sãn phẩm",
        "suggestion": "Sản phẩm",
        "position": "char 0",
        "position_index": 0,
        "message": "Tone error",
        "confidence": "high",
    }]
    minimax.check_image_conflicts.return_value = [{
        "rule_id": "IMG-CONFLICT-PERCENT",
        "severity": "critical",
        "category": "image_text_conflict",
        "found": "Giảm 30%",
        "image_text": "Giảm 50%",
        "suggestion": "...",
        "message": "Mismatch",
        "confidence": "high",
    }]

    caption = "Sản phẩm mới! Giảm 30%"
    quality, conflicts, ocr = await _check_image_full(
        minimax, caption, "fake_b64", 0, MockProject(), set()
    )

    # Quality issues from image (typo + PU-02)
    assert len(quality) >= 2
    quality_rule_ids = {i["rule_id"] for i in quality}
    assert "VT-06" in quality_rule_ids
    assert "PU-02" in quality_rule_ids  # !! from "phẩm mới!!"

    # Conflicts
    assert len(conflicts) == 1
    assert conflicts[0]["rule_id"] == "IMG-CONFLICT-PERCENT"

    # Both kinds tagged with image_0 source
    for issue in quality + conflicts:
        assert issue["source"] == "image_0"

    print("  ✓  test_image_quality_and_conflict_combined")


if __name__ == "__main__":
    tests = [
        test_image_pipeline_quality_check,
        test_image_pipeline_conflict_only,
        test_image_pipeline_empty_image,
        test_image_quality_and_conflict_combined,
    ]
    passed = 0
    failed = []
    loop = asyncio.new_event_loop()
    for t in tests:
        try:
            loop.run_until_complete(t())
            passed += 1
        except AssertionError as e:
            failed.append((t.__name__, str(e)))
            print(f"  ✗  {t.__name__}: {e}")
        except Exception as e:
            failed.append((t.__name__, f"{type(e).__name__}: {e}"))
            print(f"  ✗  {t.__name__}: {type(e).__name__}: {e}")
    loop.close()
    print()
    print(f"{passed}/{len(tests)} passed")
    if failed:
        sys.exit(1)
