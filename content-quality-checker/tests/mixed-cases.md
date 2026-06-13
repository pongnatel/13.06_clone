# Mixed Real-World Test Cases

These simulate actual social media post scenarios with multiple error types combined.

---

## CASE MX-T01 — Typical e-commerce post (many errors)
**Input:**
```
🔥FLASH SALE🔥 Giảm gía đến 50% tất cả sản phẩm !!
Chỉ trong hôm nay ,đừng bỏ lỡ cơ hội này!!
Shop tại Lazada,Shopee hoặc website của chúng tôi.
```
**Image:** *(none)*  
**Expected issues:**
- CA-04 (suggestion): `FLASH SALE` in all-caps (mid-text)
- VT-06 (major): `Giảm gía` → `Giảm giá`
- PU-02 (major): `!!` ×2 → `!`
- SP-02 (major): `,đừng` — missing space after comma → `, đừng`
- SP-03 (major): `Lazada,Shopee` — missing space after comma
- SP-03 (major): `Shopee hoặc` — actually fine; check `Lazada,Shopee`
**Expected score:** ~72/100  
**Expected grade:** C

---

## CASE MX-T02 — Clean professional post
**Input:**
```
Chào mừng bạn đến với BST Thu Đông 2024 của chúng tôi!
Những thiết kế tinh tế, chất liệu cao cấp — tất cả được chăm chút từng chi tiết.
Xem bộ sưu tập tại link bio hoặc liên hệ để được tư vấn miễn phí.
```
**Expected issues:** none major  
**Expected score:** 97–100/100  
**Expected grade:** A

---

## CASE MX-T03 — Post with image text conflict
**Input text:**
```
Giảm 30% toàn bộ đơn hàng từ nay đến 30/6!
```
**Image contains text:** "SALE 40% - Áp dụng đến 25/6"  
**Expected issues:**
- image_text_conflict (major): Discount % differs (30% vs 40%)
- image_text_conflict (major): End date differs (30/6 vs 25/6)
**Expected score:** ~85/100

---

## CASE MX-T04 — Mixed Vietnamese/English
**Input:**
```
New collection đã có mặt tại store! Ghé thăm chúng tôi tại 123 đường Lê lợi, Q.1.
Opening hours: thứ 2-6, 9h-21h.
```
**Expected issues:**
- CA-02 (major): `Lê lợi` → `Lê Lợi` (proper noun — each word capitalized)
- PU-03 (minor/suggestion): `thứ 2-6` → `thứ 2–6` (en dash for ranges)
**Expected score:** ~90/100  
**Expected grade:** A

---

## CASE MX-T05 — Very short post
**Input:**
```
sale hôm nay!
```
**Expected issues:**
- CA-01 (major): `sale` should be `Sale` (first word)
**Expected score:** ~95/100  
**Note in output:** Confidence = `low` (short text, limited context for tone/typo checks)

---

## CASE MX-T06 — Empty input
**Input:** *(empty string)*  
**Expected output:**
```json
{
  "score": null,
  "grade": null,
  "issues": [{ "rule_id": "EMPTY_INPUT", "severity": "critical", "message": "No text provided" }]
}
```
