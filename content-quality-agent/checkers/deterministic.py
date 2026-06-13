"""Deterministic checkers — pure regex/algorithmic rules.

These never need an LLM. Fast, free, 100% reproducible.
Implements: SP-01..09, PU-02, PU-06, PU-08, CA-04
"""

import re
from typing import Optional


# CamelCase tokens that are intentional brand names — never flag as SP-08
DEFAULT_CAMELCASE_EXCLUSIONS = {
    "iPhone", "iPad", "iPod", "iMac", "macOS", "iOS", "iCloud",
    "TikTok", "YouTube", "LinkedIn", "WhatsApp", "FaceTime",
    "WordPress", "JavaScript", "TypeScript", "PowerPoint", "OneDrive",
    "OpenAI", "ChatGPT", "GitHub", "GitLab", "BitBucket",
    "AgentBase", "VNGCampus", "GreenNode", "MinIO",
    "PostgreSQL", "MongoDB", "MySQL", "MariaDB",
    "DevOps", "WiFi", "eBay", "PayPal",
}


def _make_issue(rule_id: str, severity: str, position: int, found: str,
                suggestion: str, message: str, category: str) -> dict:
    return {
        "rule_id": rule_id,
        "severity": severity,
        "category": category,
        "position": f"char {position}",
        "position_index": position,
        "found": found,
        "suggestion": suggestion,
        "message": message,
    }


def check_spacing(text: str, brand_exclusions: Optional[set] = None) -> list[dict]:
    """Run all SP-* rules. Returns list of issue dicts."""
    issues = []
    exclusions = DEFAULT_CAMELCASE_EXCLUSIONS | (brand_exclusions or set())

    # SP-01: Double space
    for m in re.finditer(r"  +", text):
        issues.append(_make_issue(
            "SP-01", "minor", m.start(),
            f"<{len(m.group())} spaces>", " ",
            "Double or multiple consecutive spaces",
            "spacing"
        ))

    # SP-02: Space before punctuation
    for m in re.finditer(r" +([,.!?:;\)])", text):
        issues.append(_make_issue(
            "SP-02", "major", m.start(),
            m.group(), m.group(1),
            "Space before punctuation mark",
            "spacing"
        ))

    # SP-03: Missing space after punctuation (comma, period, colon, semicolon)
    # Skip if next char is digit (e.g. "10.5") or if followed by close bracket
    for m in re.finditer(r"([,;:])(?=[A-Za-zÀ-ỹ])", text):
        issues.append(_make_issue(
            "SP-03", "major", m.start(),
            text[m.start():m.start()+5], m.group(1) + " ",
            "Missing space after punctuation",
            "spacing"
        ))
    # Period followed by letter (lowercase = sentence continuation typo)
    for m in re.finditer(r"\.([A-Za-zÀ-ỹ])", text):
        # Skip common abbreviations and decimals
        ctx_start = max(0, m.start() - 3)
        ctx = text[ctx_start:m.start()]
        if not re.search(r"\d$", ctx):  # not a decimal like "10.5"
            issues.append(_make_issue(
                "SP-03", "major", m.start(),
                text[m.start():m.start()+5], ". " + m.group(1),
                "Missing space after period",
                "spacing"
            ))

    # SP-04: Space inside brackets
    for m in re.finditer(r"[\(\[]\s+", text):
        issues.append(_make_issue(
            "SP-04", "minor", m.start(),
            m.group(), m.group()[0],
            "Space after opening bracket",
            "spacing"
        ))
    for m in re.finditer(r"\s+[\)\]]", text):
        issues.append(_make_issue(
            "SP-04", "minor", m.start(),
            m.group(), m.group().strip()[-1],
            "Space before closing bracket",
            "spacing"
        ))

    # SP-05: Em dash without surrounding spaces
    for m in re.finditer(r"\S—|—\S", text):
        issues.append(_make_issue(
            "SP-05", "minor", m.start(),
            m.group(),
            m.group().replace("—", " — "),
            "Em dash should have spaces on both sides",
            "spacing"
        ))

    # SP-06: Trailing whitespace at end of line
    for m in re.finditer(r" +(\n|$)", text):
        if m.group(1) == "\n" or m.end() == len(text):
            issues.append(_make_issue(
                "SP-06", "minor", m.start(),
                "<trailing space>", "",
                "Trailing whitespace at end of line",
                "spacing"
            ))

    # SP-08: CamelCase collision — two proper nouns merged
    # Algorithm: for each whitespace-separated token long enough, scan for
    # internal uppercase letters (preceded by lowercase). Each such position
    # is a candidate split point. Find the split where BOTH halves are at
    # least 3 chars and neither full-token nor either half is in exclusions.
    # Iterate splits from LARGEST first-half down — this handles cases like
    # "GreenNodeClaw-a-thon" where the meaningful split is GreenNode + Claw,
    # not Green + Node.
    for token_match in re.finditer(r"\S+", text):
        token = token_match.group()
        if len(token) < 7:
            continue
        # Only consider tokens whose first char is a letter
        if not token[0].isalpha():
            # Skip leading punctuation/symbols (e.g., emoji+word)
            # Find the first letter
            offset = 0
            while offset < len(token) and not token[offset].isalpha():
                offset += 1
            if offset >= len(token) - 6:
                continue
            inner = token[offset:]
            inner_start = token_match.start() + offset
        else:
            inner = token
            inner_start = token_match.start()

        # Find internal uppercase positions (i > 0, prev char is lowercase)
        split_points = []
        for i in range(1, len(inner)):
            if inner[i].isupper() and inner[i-1].islower():
                # Also require the next char is lowercase or end (it's a real word start)
                if i + 1 < len(inner) and inner[i+1].isupper():
                    continue  # part of ALL-CAPS run; handled by SP-09
                split_points.append(i)

        if not split_points:
            continue

        # Try splits from LARGEST first-half to smallest
        # This prefers splitting "GreenNodeClaw" into "GreenNode" + "Claw"
        # rather than "Green" + "Node" (which is excluded).
        for split_at in reversed(split_points):
            first = inner[:split_at]
            rest = inner[split_at:]
            if len(first) < 3 or len(rest) < 3:
                continue
            # Exclusion semantics: only skip if the FULL token (or full inner)
            # is in the exclusion list. Half-matches don't count — that's the
            # whole point of catching "GreenNodeClaw" even though "GreenNode"
            # is excluded as a brand.
            if token in exclusions or inner in exclusions:
                # Token IS an intentional brand — skip all splits
                break

            issues.append(_make_issue(
                "SP-08", "major", inner_start,
                inner, f"{first} {rest}",
                f"Possible missing space: '{first}' + '{rest}' merged",
                "spacing"
            ))
            break
        # If no split worked, token is fine

    # SP-09: ALL-CAPS acronym merged with following word
    # Walk each token. If it starts with 2+ uppercase letters and the next char
    # transitions to lowercase OR (capital + lowercase tail), flag it.
    # Use longest ALL-CAPS prefix for the acronym to handle "GREENnode" correctly.
    for token_match in re.finditer(r"[A-Za-zÀ-ỹ]+", text):
        tok = token_match.group()
        tok_start = token_match.start()
        if len(tok) < 5:
            continue
        if tok in exclusions:
            continue
        # Find the longest ALL-CAPS prefix (>=2 chars)
        prefix_end = 0
        while prefix_end < len(tok) and tok[prefix_end].isupper():
            prefix_end += 1
        if prefix_end < 2:
            continue  # not enough caps to be an acronym
        # Check if SP-08 already covers this token
        if any(i.get("position_index") == tok_start and i["rule_id"] == "SP-08"
               for i in issues):
            continue
        rest = tok[prefix_end:]
        if len(rest) < 2:
            continue  # whole token is uppercase — not SP-09
        # Whole ALL-CAPS prefix = acronym, rest = the merged word.
        # We deliberately keep this simple: no alt-split heuristics.
        # The PascalCase patterns like "AIAgent" → "AI"+"Agent" are caught by
        # SP-08 (CamelCase collision) instead, which handles the boundary correctly.
        acronym = tok[:prefix_end]
        word = rest

        if len(acronym) < 2 or len(word) < 2:
            continue

        full = acronym + word
        issues.append(_make_issue(
            "SP-09", "minor", tok_start,
            tok, f"{acronym} {word}",
            f"Acronym '{acronym}' merged with '{word}'",
            "spacing"
        ))

    return issues


def check_punctuation(text: str) -> list[dict]:
    """Run all PU-* rules."""
    issues = []

    # PU-02: Consecutive identical punctuation (not ellipsis)
    for m in re.finditer(r"([!?,])\1+", text):
        issues.append(_make_issue(
            "PU-02", "major", m.start(),
            m.group(), m.group(1),
            f"Repeated punctuation: '{m.group()}' should be '{m.group(1)}'",
            "punctuation"
        ))

    # 4+ dots (ellipsis is exactly 3)
    for m in re.finditer(r"\.{4,}", text):
        issues.append(_make_issue(
            "PU-02", "minor", m.start(),
            m.group(), "...",
            "Ellipsis must be exactly 3 dots",
            "punctuation"
        ))

    # PU-02b: Mixed end-of-sentence punctuation like ". !"
    for m in re.finditer(r"\.\s*[!?]", text):
        issues.append(_make_issue(
            "PU-02", "major", m.start(),
            m.group(), m.group().strip()[-1],
            "Mixed sentence-ending punctuation",
            "punctuation"
        ))

    # PU-06: Unmatched brackets
    pairs = {"(": ")", "[": "]", "{": "}"}
    closers = {v: k for k, v in pairs.items()}
    stack = []
    for i, ch in enumerate(text):
        if ch in pairs:
            stack.append((ch, i))
        elif ch in closers:
            if not stack or stack[-1][0] != closers[ch]:
                issues.append(_make_issue(
                    "PU-06", "critical", i,
                    ch, "",
                    f"Unmatched closing '{ch}'",
                    "punctuation"
                ))
            else:
                stack.pop()
    for ch, i in stack:
        issues.append(_make_issue(
            "PU-06", "critical", i,
            ch, pairs[ch],
            f"Unmatched opening '{ch}' — missing '{pairs[ch]}'",
            "punctuation"
        ))

    # PU-08: Spaced ellipsis
    for m in re.finditer(r"\. \. \.", text):
        issues.append(_make_issue(
            "PU-08", "minor", m.start(),
            m.group(), "...",
            "Spaced ellipsis should be '...'",
            "punctuation"
        ))

    return issues


def check_capitalization_basic(text: str, brand_names: Optional[list] = None) -> list[dict]:
    """CA-04 (ALL-CAPS overuse) + CA-05 brand name capitalization check."""
    issues = []

    # CA-04: More than 5 consecutive ALL-CAPS words (excluding hashtags)
    words = text.split()
    consecutive_caps = 0
    caps_start_idx = -1
    char_offset = 0
    word_starts = []
    pos = 0
    for w in words:
        # Find actual position in text
        idx = text.find(w, pos)
        word_starts.append(idx)
        pos = idx + len(w)

    for i, w in enumerate(words):
        clean = re.sub(r"[^\w]", "", w)
        if clean and clean.isupper() and len(clean) >= 2 and not w.startswith("#"):
            if consecutive_caps == 0:
                caps_start_idx = word_starts[i]
            consecutive_caps += 1
        else:
            if consecutive_caps > 5:
                issues.append(_make_issue(
                    "CA-04", "suggestion", caps_start_idx,
                    "<all-caps sequence>", "<normal case>",
                    f"{consecutive_caps} consecutive ALL-CAPS words — feels like shouting",
                    "capitalization"
                ))
            consecutive_caps = 0
    # Handle trailing
    if consecutive_caps > 5:
        issues.append(_make_issue(
            "CA-04", "suggestion", caps_start_idx,
            "<all-caps sequence>", "<normal case>",
            f"{consecutive_caps} consecutive ALL-CAPS words",
            "capitalization"
        ))

    # CA-05: Known brand capitalization
    known_brands = {
        "iphone": "iPhone", "ipad": "iPad",
        "facebook": "Facebook", "youtube": "YouTube",
        "tiktok": "TikTok", "shopee": "Shopee",
        "lazada": "Lazada", "instagram": "Instagram",
        "linkedin": "LinkedIn", "github": "GitHub",
    }
    # Add project brands
    project_brand_map = {}
    if brand_names:
        for b in brand_names:
            project_brand_map[b.lower()] = b

    combined = {**known_brands, **project_brand_map}

    for wrong, correct in combined.items():
        # Word-boundary, case-insensitive search, but skip exact matches
        for m in re.finditer(rf"\b{re.escape(wrong)}\b", text, flags=re.IGNORECASE):
            found_text = m.group()
            if found_text != correct:
                issues.append(_make_issue(
                    "CA-05", "major", m.start(),
                    found_text, correct,
                    f"Brand capitalization: '{found_text}' should be '{correct}'",
                    "capitalization"
                ))

    return issues


def check_forbidden_words(text: str, forbidden: list[str]) -> list[dict]:
    """Project-level: flag any forbidden words."""
    issues = []
    if not forbidden:
        return issues
    for word in forbidden:
        for m in re.finditer(rf"\b{re.escape(word)}\b", text, flags=re.IGNORECASE):
            issues.append(_make_issue(
                "BS-FORBIDDEN", "major", m.start(),
                m.group(), "<remove or replace>",
                f"Forbidden word in project: '{word}'",
                "brand_style"
            ))
    return issues
