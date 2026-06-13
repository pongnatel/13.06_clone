# Punctuation Test Cases

---

## CASE PU-T01 — Consecutive punctuation
**Input:**
```
Sale khủng!! Giảm giá đến 70%!! Mua ngay!!
```
**Expected issues:** PU-02 (major) ×3 — `!!` should be `!`  
**Expected score:** 85/100

---

## CASE PU-T02 — Unmatched bracket
**Input:**
```
Ưu đãi giảm giá (50% tất cả sản phẩm mùa hè.
```
**Expected issues:** PU-06 (critical) — unclosed `(`  
**Expected score:** 90/100

---

## CASE PU-T03 — Valid ellipsis vs. invalid
**Input:**
```
Đang cập nhật.... Vui lòng chờ...
```
**Expected issues:**
- PU-02 (minor): `....` (4 dots) → `...`
- No issue for the second `...` (valid)
**Expected score:** 98/100

---

## CASE PU-T04 — Spaced ellipsis
**Input:**
```
Chờ mình chút . . . sắp có thông báo mới!
```
**Expected issues:** PU-08 (minor) — `. . .` → `...`  
**Expected score:** 98/100

---

## CASE PU-T05 — No issues
**Input:**
```
Chào mừng bạn đến với cửa hàng của chúng tôi! Liên hệ ngay để nhận tư vấn miễn phí.
```
**Expected issues:** none  
**Expected score:** 100/100 (punctuation category)
