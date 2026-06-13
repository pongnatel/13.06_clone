# Spacing Test Cases

---

## CASE SP-T01 — Double space
**Input:**
```
Sản phẩm  mới của chúng tôi đã có mặt!
```
**Expected issues:** SP-01 (minor) at char 9  
**Expected score:** 98/100

---

## CASE SP-T02 — Space before punctuation
**Input:**
```
Cảm ơn bạn đã ủng hộ !
```
**Expected issues:** SP-02 (major) — space before `!`  
**Expected score:** 95/100

---

## CASE SP-T03 — Missing space after comma
**Input:**
```
Giảm giá áo,quần,túi xách tất cả chỉ từ 99k.
```
**Expected issues:** SP-03 (major) ×2 — missing space after `,` ×2  
**Expected score:** 90/100

---

## CASE SP-T04 — Space inside brackets
**Input:**
```
Ưu đãi đặc biệt ( chỉ hôm nay ) — đừng bỏ lỡ!
```
**Expected issues:** SP-04 (minor) ×2 — space after `(` and before `)`  
**Expected score:** 96/100

---

## CASE SP-T05 — Multiple spacing errors
**Input:**
```
Flash Sale !  Giảm đến 50%  cho tất cả sản phẩm ( trong hôm nay ) .
```
**Expected issues:**
- SP-02 (major): space before `!`
- SP-01 (minor): double space after `!`
- SP-01 (minor): double space after `50%`
- SP-04 (minor) ×2: space inside brackets
- SP-02 (major): space before `.`
**Expected score:** ~82/100

---

## CASE SP-T07 — CamelCase collision (SP-08)
**Input:**
```
Ngày 10/06 vừa qua, GreenNodeClaw-a-thon đã mở màn bằng buổi đào tạo trực tiếp diễn ra tại VNGCampus.
```
**Expected issues:**
- SP-08 (major): `GreenNodeClaw-a-thon` → `GreenNode Claw-a-thon`
- NO issue for `VNGCampus` (in exclusion list)
**Expected score:** 95/100

---

## CASE SP-T08 — ALL-CAPS acronym merge (SP-09)
**Input:**
```
Chương trình AIAgent đang được triển khai mạnh mẽ.
```
**Expected issues:**
- SP-09 (minor): `AIAgent` → `AI Agent`
**Expected score:** 98/100
**Input:**
```
Sản phẩm mới đã có mặt! Đặt hàng ngay để nhận ưu đãi.
```
**Expected issues:** none  
**Expected score:** 100/100 (spacing category full marks)
