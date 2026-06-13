# Output Format

This file defines the exact JSON schema and human-readable format for all content-quality-checker outputs.

---

## JSON Schema

```json
{
  "score": 87,
  "grade": "B",
  "language_detected": ["vi", "en"],
  "categories": {
    "spacing": {
      "score": 15,
      "max": 15,
      "issues": []
    },
    "punctuation": {
      "score": 12,
      "max": 15,
      "issues": [
        {
          "rule_id": "PU-02",
          "severity": "major",
          "position": "char 45",
          "found": "!!",
          "suggestion": "!",
          "message": "Consecutive identical punctuation marks"
        }
      ]
    },
    "typo": {
      "score": 25,
      "max": 25,
      "issues": []
    },
    "vietnamese_tone": {
      "score": 18,
      "max": 20,
      "issues": [
        {
          "rule_id": "VT-02",
          "severity": "critical",
          "position": "word 3",
          "found": "vẩn",
          "suggestion": "vẫn",
          "message": "Hỏi/Ngã confusion — likely input method error"
        }
      ]
    },
    "capitalization": {
      "score": 10,
      "max": 10,
      "issues": []
    },
    "brand_style": {
      "score": null,
      "max": null,
      "issues": [],
      "note": "Skipped — no brand context provided"
    },
    "image_text_conflict": {
      "score": null,
      "max": null,
      "issues": [],
      "note": "Skipped — no image provided"
    },
    "image_text_quality": {
      "score": null,
      "max": null,
      "issues": [],
      "note": "Skipped — no image provided"
    }
  },
  "total_issues": 2,
  "issues_by_severity": {
    "critical": 1,
    "major": 1,
    "minor": 0,
    "suggestion": 0
  },
  "original_text": "Sản phẩm vẩn đang được giảm giá!!",
  "corrected_text": "Sản phẩm vẫn đang được giảm giá!",
  "image_analysis": [
    {
      "image_index": 0,
      "extracted_text": "FLASH SALE\nGiảm gía 50%",
      "text_blocks": [
        {"text": "FLASH SALE", "region": "top banner", "confidence": "high"},
        {"text": "Giảm gía 50%", "region": "middle", "confidence": "high"}
      ],
      "has_text": true
    }
  ],
  "confidence": "high"
}
```

---

## Field definitions

| Field | Type | Description |
|-------|------|-------------|
| `score` | int 0–100 | Final weighted score |
| `grade` | string | A/B/C/D/F |
| `language_detected` | string[] | ISO codes: `vi`, `en` |
| `categories` | object | Per-category breakdown |
| `categories.*.score` | int | Points earned in this category |
| `categories.*.max` | int | Max points for this category |
| `categories.*.issues` | Issue[] | List of issues found |
| `total_issues` | int | Count of all issues |
| `issues_by_severity` | object | Count per severity level |
| `original_text` | string | Input as-received |
| `corrected_text` | string | All suggestions applied non-destructively |
| `confidence` | string | `high` / `medium` / `low` (low for very short texts) |

---

## Issue object

```json
{
  "rule_id": "SP-02",
  "severity": "major",
  "position": "char 12",
  "found": "bạn !",
  "suggestion": "bạn!",
  "message": "Space before punctuation mark"
}
```

| Field | Description |
|-------|-------------|
| `rule_id` | Rule identifier from reference files (e.g., `SP-02`, `VT-03`) |
| `severity` | `critical` / `major` / `minor` / `suggestion` |
| `position` | `char N`, `word N`, or `line N` — whichever is most helpful |
| `found` | The problematic text snippet (keep short, context window) |
| `suggestion` | The corrected form |
| `message` | Human-readable explanation (1 line) |

---

## Scoring formula

```
base_score = 100

for each issue:
  if severity == "critical":  base_score -= 10
  if severity == "major":     base_score -= 5
  if severity == "minor":     base_score -= 2
  if severity == "suggestion": base_score -= 0

# Apply category cap (never lose more than the category's max weight)
for each category:
  deduction = sum of issue deductions in category
  capped_deduction = min(deduction, category.max)

final_score = max(0, 100 - sum(capped_deductions))
```

### Category max weights

| Category | Max deduction | When evaluated |
|----------|---------------|----------------|
| `spacing` | 15 | Always |
| `punctuation` | 15 | Always |
| `typo` | 25 | Always |
| `vietnamese_tone` | 20 | When Vietnamese detected |
| `capitalization` | 10 | Always |
| `brand_style` | 15 | When brand context given |
| `image_text_quality` | 15 | When image provided |
| `image_text_conflict` | 15 | When image provided |

---

## Grade thresholds

| Grade | Score range | Label |
|-------|------------|-------|
| A | 90–100 | Excellent — ready to publish |
| B | 75–89 | Good — minor polish needed |
| C | 60–74 | Fair — several issues to fix |
| D | 40–59 | Poor — significant revision needed |
| F | 0–39 | Fail — major rework required |

---

## Human-readable summary format

Always render this alongside JSON when responding in chat:

```
📊 QUALITY SCORE: {score}/100  [{grade}]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📍 {total_issues} issue(s) found
   🔴 {critical} critical  🟠 {major} major  🟡 {minor} minor  💬 {suggestion} suggestion(s)

CATEGORY BREAKDOWN
  Spacing         {spacing.score}/{spacing.max}
  Punctuation     {punctuation.score}/{punctuation.max}
  Typo            {typo.score}/{typo.max}
  Vietnamese Tone {vietnamese_tone.score}/{vietnamese_tone.max}
  Capitalization  {capitalization.score}/{capitalization.max}

─────────────────────────────
ISSUES FOUND
[🔴/🟠/🟡/💬] [{rule_id}] "{found}" → "{suggestion}"
   {message}  ({position})

─────────────────────────────
✅ CORRECTED TEXT:
{corrected_text}
```
