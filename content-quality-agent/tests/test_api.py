"""Integration tests for the agent's HTTP API.

Run a smoke test against the running server:
    python tests/test_api.py [base_url]

Default base_url is http://localhost:8000
"""

import sys
import requests


def test_health(base_url: str) -> None:
    r = requests.get(f"{base_url}/health", timeout=5)
    r.raise_for_status()
    data = r.json()
    assert data["status"] == "ok"
    assert data["skill_loaded"] is True
    print("  ✓  /health")


def test_skill_info(base_url: str) -> None:
    r = requests.get(f"{base_url}/skill/info", timeout=5)
    r.raise_for_status()
    data = r.json()
    assert "categories" in data
    assert "spacing-rules" in data["categories"]
    print("  ✓  /skill/info")


def test_check_deterministic_only(base_url: str) -> None:
    payload = {
        "text": "GreenNodeClaw-a-thon đã mở màn  bằng buổi đào tạo!!",
        "project": {
            "brand_name": "GreenNode",
            "brand_exclusions": ["GreenNode"],
        },
        "enable_llm": False,
    }
    r = requests.post(f"{base_url}/check", json=payload, timeout=10)
    r.raise_for_status()
    data = r.json()
    assert isinstance(data["score"], int)
    assert data["score"] < 100  # has issues
    assert data["total_issues"] >= 3

    # Must detect SP-08 on GreenNodeClaw-a-thon
    rule_ids = {i["rule_id"] for i in data["issues"]}
    assert "SP-08" in rule_ids, f"Expected SP-08, got: {rule_ids}"
    assert "PU-02" in rule_ids, f"Expected PU-02, got: {rule_ids}"
    print(f"  ✓  /check deterministic — score={data['score']}, issues={data['total_issues']}")


def test_check_empty_text(base_url: str) -> None:
    payload = {"text": "", "enable_llm": False}
    r = requests.post(f"{base_url}/check", json=payload, timeout=5)
    r.raise_for_status()
    data = r.json()
    assert any(i["rule_id"] == "EMPTY_INPUT" for i in data["issues"])
    print("  ✓  /check empty input")


def test_check_clean_text(base_url: str) -> None:
    payload = {
        "text": "Chào mừng bạn đến với cửa hàng của chúng tôi. Liên hệ để được tư vấn.",
        "enable_llm": False,
    }
    r = requests.post(f"{base_url}/check", json=payload, timeout=5)
    r.raise_for_status()
    data = r.json()
    assert data["score"] >= 90, f"Clean text should score high, got {data['score']}"
    print(f"  ✓  /check clean text — score={data['score']}")


if __name__ == "__main__":
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    print(f"Testing against {base_url}")
    print()
    tests = [
        test_health,
        test_skill_info,
        test_check_deterministic_only,
        test_check_empty_text,
        test_check_clean_text,
    ]
    failed = 0
    for t in tests:
        try:
            t(base_url)
        except Exception as e:
            failed += 1
            print(f"  ✗  {t.__name__}: {type(e).__name__}: {e}")
    print()
    print(f"{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
