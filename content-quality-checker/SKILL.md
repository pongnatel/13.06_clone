---
name: content-quality-checker
description: >
  Use this skill whenever the user wants to proofread, score, or validate social media posts, captions, or marketing copy — especially Vietnamese content. Triggers include: "check my post", "proofread this", "score this caption", "kiểm tra bài đăng", "chấm điểm post", "review nội dung", or any request to validate text quality before publishing. Also triggers when the user provides text + images together for a quality review. Always use this skill when the user wants a structured quality score with issue breakdown, not just a casual proofread.
---

# Content Quality Checker

A structured proofreading and scoring skill for social media posts. Accepts text and/or images as input, validates across multiple error categories, and returns a scored report.

---

## Input

- **text**: The post body (required)
- **image(s)**: Optional — scan for text in image that may conflict with caption, check visual-text consistency

---

## Execution Pipeline

Run checks in this exact order. Each step feeds into the final score.

```
Input
 → [0] Normalize text
 → [1] Check spacing          (ref: references/spacing-rules.md)
 → [2] Check punctuation      (ref: references/punctuation-rules.md)
 → [3] Check typos            (ref: references/typo-rules.md)
 → [4] Check Vietnamese tones (ref: references/vietnamese-tone-rules.md)  ← only if Vietnamese detected
 → [5] Check capitalization   (ref: references/capitalization-rules.md)
 → [6] Check brand/style      (ref: references/brand-style-rules.md)      ← only if brand context provided
 → [7] Aggregate score + output (ref: references/output-format.md)
```

**Step [0] — Normalize:**
- Strip leading/trailing whitespace
- Detect language(s): Vietnamese, English, or mixed
- Flag if input is empty or image-only (no extractable text)

**Steps [1]–[6] — Run each checker:**
- Read the relevant reference file before running each check
- Collect all `Issue` objects with: `{ rule_id, severity, position, found, suggestion }`
- Do NOT stop early on errors — run all checks and aggregate

**⚠️ Special attention — SP-08 CamelCase collision:**  
Standard space-checking only catches spaces *around* punctuation. It will NOT catch two proper nouns concatenated without a space (e.g., `GreenNodeClaw-a-thon`). For every token longer than 6 chars, explicitly scan for an internal uppercase letter that signals two words merged. See SP-08 in `references/spacing-rules.md` for the full algorithm and exclusion list.

**Step [7] — Score and output:**
- Read `references/output-format.md` for the exact JSON schema
- Compute per-category scores and total score
- Emit `corrected_text` with all suggestions applied (non-destructively)

---

## When to read reference files

| Step | Read this file | When |
|------|---------------|------|
| 1 | `references/spacing-rules.md` | Always |
| 2 | `references/punctuation-rules.md` | Always |
| 3 | `references/typo-rules.md` | Always |
| 4 | `references/vietnamese-tone-rules.md` | Vietnamese detected |
| 5 | `references/capitalization-rules.md` | Always |
| 6 | `references/brand-style-rules.md` | Only if brand context given |
| 7 | `references/output-format.md` | Always |

---

## Severity levels

| Level | Meaning | Score impact |
|-------|---------|-------------|
| `critical` | Meaning changed, completely wrong | −10 pts each |
| `major` | Clearly visible error, affects credibility | −5 pts each |
| `minor` | Subtle, stylistic, easy to miss | −2 pts each |
| `suggestion` | Optional improvement, not an error | −0 pts |

**Base score: 100.** Final score cannot go below 0.

---

## Image handling

If image(s) are provided, run a **3-step image pipeline** for each image:

**Step A — OCR extraction (pure):**
- Extract all visible text from the image VERBATIM — do NOT correct typos during OCR
- If image shows "Giảm gía" (misspelled), record it as "Giảm gía", not "Giảm giá"
- This faithfulness is critical so Step B can flag the actual error

**Step B — Image text QUALITY check:**
- Run the EXTRACTED text through the full quality pipeline:
  spacing → punctuation → typo → vietnamese tone → capitalization
- Use the SAME rule IDs (SP-01, VT-02, etc.) so issues are diagnosable
- Tag all issues with `category: image_text_quality` and `source: image_<idx>`
- This catches designer mistakes — typos baked into the image design itself

**Step C — Caption vs Image cross-check:**
- Compare caption text against extracted image text
- Flag only QUANTITATIVE / DEFINITIVE conflicts:
  prices, percentages, dates, product names, quantities
- Category: `image_text_conflict`
- Normalize before comparing: "100k" == "100.000đ" == "100,000 VND"

**Important:** Steps B and C are independent. An image can have:
- Quality issues (typos on the image) BUT match the caption perfectly
- Match in quality (clean text) BUT conflict with caption values
- Both kinds of issues simultaneously

Both contribute separate categories in the final score (each capped at 15 pts).

Do NOT score image aesthetics — only text accuracy and consistency.

---

## Output

Always return structured output as defined in `references/output-format.md`.

In addition to JSON, render a **human-readable summary** in this format:

```
📊 QUALITY SCORE: {score}/100  [{grade}]

📍 Issues found: {total_issues} ({critical} critical, {major} major, {minor} minor)

🔴 CRITICAL
  [C1] {rule_id} — "{found}" → "{suggestion}"
       Position: {position}

🟠 MAJOR
  ...

🟡 MINOR
  ...

✅ CORRECTED TEXT:
{corrected_text}
```

Grades: A (90–100), B (75–89), C (60–74), D (40–59), F (<40)

---

## Edge cases

- **Empty text**: Return score = null, single issue: `{ rule_id: "EMPTY_INPUT", severity: "critical" }`
- **Image only, no text**: Extract image text if possible; otherwise return `INSUFFICIENT_INPUT`
- **Mixed Vietnamese/English**: Run both language checks; flag cross-language issues under `mixed_language`
- **Very short text** (< 5 words): Run all checks but note in output that scoring confidence is low

---

## Test cases

See `tests/` for ready-made cases:
- `tests/spacing-cases.md` — double spaces, missing spaces, space around punctuation
- `tests/punctuation-cases.md` — missing periods, wrong dash type, bracket errors
- `tests/typo-cases.md` — common Vietnamese/English typos
- `tests/mixed-cases.md` — combined real-world post examples with image descriptions
