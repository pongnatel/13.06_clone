"""Unit tests for deterministic checkers.

Run: cd content-quality-agent && python -m pytest tests/ -v
Or:  python tests/test_deterministic.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from checkers.deterministic import (
    check_spacing,
    check_punctuation,
    check_capitalization_basic,
    check_forbidden_words,
)


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------

def has_rule(issues, rule_id, found=None):
    """Return True if issues contains a given rule_id (and optional found text)."""
    for i in issues:
        if i["rule_id"] == rule_id:
            if found is None or i["found"] == found:
                return True
    return False


def get_issue(issues, rule_id, found=None):
    """Return first matching issue or None."""
    for i in issues:
        if i["rule_id"] == rule_id:
            if found is None or i["found"] == found:
                return i
    return None


# ---------------------------------------------------------------------------
# Spacing rules
# ---------------------------------------------------------------------------

def test_sp01_double_space():
    issues = check_spacing("Sản phẩm  mới")
    assert has_rule(issues, "SP-01"), "Should detect double space"


def test_sp02_space_before_punct():
    issues = check_spacing("Cảm ơn bạn !")
    assert has_rule(issues, "SP-02")


def test_sp03_missing_space_after_comma():
    issues = check_spacing("Xin chào,bạn ơi")
    assert has_rule(issues, "SP-03")


def test_sp04_space_inside_brackets():
    issues = check_spacing("( miễn phí )")
    assert has_rule(issues, "SP-04")


def test_sp08_camelcase_collision():
    """The original failing case — GreenNodeClaw-a-thon."""
    text = "Ngày 10/06, GreenNodeClaw-a-thon đã mở màn"
    issues = check_spacing(text, brand_exclusions={"GreenNode"})
    i = get_issue(issues, "SP-08")
    assert i is not None, "Should detect SP-08"
    assert i["found"] == "GreenNodeClaw-a-thon"
    assert i["suggestion"] == "GreenNode Claw-a-thon"


def test_sp08_respects_exclusion():
    """VNGCampus in exclusion list — must not flag."""
    issues = check_spacing("tại VNGCampus.", brand_exclusions={"VNGCampus"})
    assert not has_rule(issues, "SP-08")


def test_sp08_iphone_not_flagged():
    issues = check_spacing("iPhone 15 Pro Max")
    assert not has_rule(issues, "SP-08")


def test_sp09_acronym_lowercase():
    issues = check_spacing("GREENnode platform")
    i = get_issue(issues, "SP-09")
    assert i is not None
    assert i["suggestion"] == "GREEN node"


def test_sp09_acronym_capitalword():
    """AIAgent — gets flagged even if split point is imperfect."""
    issues = check_spacing("AIAgent platform")
    assert has_rule(issues, "SP-09"), "Should flag AIAgent"


def test_sp09_nasa_not_flagged():
    """All-caps acronyms alone should not be flagged."""
    issues = check_spacing("NASA launched a rocket")
    assert not has_rule(issues, "SP-09")


# ---------------------------------------------------------------------------
# Punctuation rules
# ---------------------------------------------------------------------------

def test_pu02_double_exclamation():
    issues = check_punctuation("Sale khủng!!")
    i = get_issue(issues, "PU-02")
    assert i is not None
    assert i["found"] == "!!"


def test_pu02_mixed_period_exclaim():
    """ '. !' should be flagged — common typing artifact."""
    issues = check_punctuation("Thành công. !")
    assert has_rule(issues, "PU-02")


def test_pu02_ellipsis_valid():
    """3 dots is valid ellipsis, should NOT flag."""
    issues = check_punctuation("Chờ chút nhé...")
    assert not has_rule(issues, "PU-02")


def test_pu02_four_dots():
    issues = check_punctuation("Chờ chút nhé....")
    assert has_rule(issues, "PU-02")


def test_pu06_unmatched_bracket():
    issues = check_punctuation("Giảm giá (50% tất cả")
    assert has_rule(issues, "PU-06")


def test_pu06_matched_brackets():
    issues = check_punctuation("Giảm giá (50% tất cả)")
    assert not has_rule(issues, "PU-06")


# ---------------------------------------------------------------------------
# Capitalization rules
# ---------------------------------------------------------------------------

def test_ca05_brand_lowercase():
    issues = check_capitalization_basic("Tải app trên tiktok và youtube")
    assert has_rule(issues, "CA-05", found="tiktok")
    assert has_rule(issues, "CA-05", found="youtube")


def test_ca05_brand_correct():
    issues = check_capitalization_basic("Tải app trên TikTok và YouTube")
    assert not has_rule(issues, "CA-05")


def test_ca04_all_caps_overuse():
    text = "MUA NGAY ĐỂ NHẬN ƯU ĐÃI ĐẶC BIỆT HÔM NAY NÀO"
    issues = check_capitalization_basic(text)
    assert has_rule(issues, "CA-04")


# ---------------------------------------------------------------------------
# Forbidden words
# ---------------------------------------------------------------------------

def test_forbidden_word():
    issues = check_forbidden_words("Đây là từ cấm", ["cấm"])
    assert has_rule(issues, "BS-FORBIDDEN")


def test_no_forbidden_words():
    issues = check_forbidden_words("Đây là text bình thường", [])
    assert len(issues) == 0


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    tests = [name for name in dir() if name.startswith("test_")]
    passed = 0
    failed = []
    for t in tests:
        try:
            globals()[t]()
            passed += 1
            print(f"  ✓  {t}")
        except AssertionError as e:
            failed.append((t, str(e)))
            print(f"  ✗  {t}: {e}")
        except Exception as e:
            failed.append((t, f"{type(e).__name__}: {e}"))
            print(f"  ✗  {t}: {type(e).__name__}: {e}")
    print()
    print(f"{passed}/{len(tests)} passed")
    if failed:
        sys.exit(1)
