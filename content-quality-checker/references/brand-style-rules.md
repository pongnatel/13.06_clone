# Brand & Style Rules

Rule group: `BRAND_STYLE`
Category weight: 15 pts
**Only run this checker when brand context is provided by the user.**

---

## Overview

This checker validates brand-specific rules: tone of voice, forbidden words, preferred terminology, and product name formatting. Because rules vary per brand, this file provides a **template structure** — the user should supply their brand's specifics.

---

## How to use

When the user provides brand context (e.g., "check this against our brand guidelines"), ask for:
1. Brand name and product names
2. Tone of voice (formal / casual / playful / authoritative)
3. Forbidden words or phrases
4. Preferred terminology (e.g., "customers" not "users")
5. Required disclaimers or CTAs

If no brand context is given, skip this checker entirely.

---

## Default rules (apply universally unless overridden)

### BS-01 — Superlative claims without evidence
**Severity:** suggestion  
**Pattern:** Unsubstantiated superlatives: `số 1`, `tốt nhất`, `duy nhất`, `hàng đầu`, `best`, `#1`  
**Suggestion:** Add qualifier (e.g., "top-rated by customers") or remove  

### BS-02 — Urgency language overuse
**Severity:** suggestion  
**Pattern:** More than 2 urgency phrases in one post (`ngay`, `hôm nay`, `cuối cùng`, `giới hạn`, `hurry`, `last chance`, `limited`)  
**Suggestion:** Reduce to 1 urgency signal — overuse reduces credibility  

### BS-03 — Price formatting consistency
**Severity:** minor  
**Pattern:** Inconsistent price formats within the same post  
**Examples:**
- ❌ Mix of `100.000đ` and `100,000 VND` in same post
- ✅ Pick one format and be consistent

### BS-04 — Emoji overuse
**Severity:** suggestion  
**Pattern:** More than 5 emojis in a short post (< 100 words), or emojis interrupting mid-sentence logic  
**Suggestion:** Use emojis at line breaks or sentence ends, max 1 per thought

### BS-05 — Hashtag formatting
**Severity:** minor  
**Pattern:** Hashtags with spaces (`# sale`) or inconsistent case (`#FlashSale` mixed with `#flashsale`)  
**Correction:** `#FlashSale` or `#flashsale` — be consistent within the post

### BS-06 — Call-to-action missing
**Severity:** suggestion  
**Pattern:** Post has promotional content but no CTA (no `mua ngay`, `liên hệ`, `đặt hàng`, `click link`, `shop now`, etc.)  
**Suggestion:** Add a clear action instruction

---

## Brand-specific rule template

When user provides brand rules, insert them here:

```
BRAND: [brand name]
TONE: [formal / casual / playful]

FORBIDDEN WORDS:
- [word 1] → use [alternative] instead
- [word 2] → use [alternative] instead

PRODUCT NAMES (exact spelling):
- [Product A]
- [Product B]

REQUIRED ELEMENTS:
- [disclaimer text or CTA]
```

---

## Scoring

Max deduction from this category: 15 pts.
