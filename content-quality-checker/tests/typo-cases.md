# Typo Test Cases

---

## CASE TY-T01 — Vietnamese homophone (critical)
**Input:**
```
Sữa xe máy chỉ 150k — uy tín, nhanh chóng!
```
**Expected issues:** TY-06 (critical) — `Sữa` (milk) should be `Sửa` (repair) given context  
**Expected score:** 90/100

---

## CASE TY-T02 — Wrong Vietnamese word
**Input:**
```
Nhưng sản phẩm này rất được ưa chuộng.
```
**Expected issues:** TY-03 (major) — `Nhưng` (but) should likely be `Những` (these/those) given context  
**Expected score:** 95/100

---

## CASE TY-T03 — Brand name typo
**Input:**
```
Follow chúng tôi trên Instragram và Tiktok nhé!
```
**Expected issues:**
- TY-07 (major): `Instragram` → `Instagram`
- TY-07 (major) or CA-05 (major): `Tiktok` → `TikTok`
**Expected score:** 90/100

---

## CASE TY-T04 — English typo
**Input:**
```
Recieve your order within 3 days!
```
**Expected issues:** TY-02 (major) — `Recieve` → `Receive`  
**Expected score:** 95/100

---

## CASE TY-T05 — Multiple typos mixed
**Input:**
```
Sữa xe, thay nhớt, bơm bánh xe giá chỉ 50k!! Follow Instragram để cập nhật ưu đải mới nhất.
```
**Expected issues:**
- TY-06 (critical): `Sữa` → `Sửa`
- PU-02 (major): `!!` → `!`
- TY-07 (major): `Instragram` → `Instagram`
- VT-06 (major): `ưu đải` → `ưu đãi`
**Expected score:** ~72/100

---

## CASE TY-T06 — Hashtags not flagged
**Input:**
```
#FlashSale #MuaNgay Sản phẩm chất lượng cao!
```
**Expected issues:** none — hashtags should not be flagged as typos  
**Expected score:** 100/100
