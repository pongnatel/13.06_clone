# Vietnamese Tone Rules

Rule group: `VIETNAMESE_TONE`
Category weight: 20 pts
**Only run this checker when Vietnamese language is detected in the input.**

---

## Background

Vietnamese uses 6 tones marked by diacritics. Missing or wrong tone marks are among the most common errors in social media posts — often caused by fast typing, autocorrect, or Telex/VNI input method errors.

The 6 tones:
| Tone | Mark | Example |
|------|------|---------|
| Ngang (flat) | none | `ma` |
| Huyền (falling) | ` ̀` | `mà` |
| Sắc (rising) | ` ́` | `má` |
| Hỏi (questioning) | ` ̉` | `mả` |
| Ngã (broken) | ` ̃` | `mã` |
| Nặng (heavy) | ` ̣` | `mạ` |

---

## Rules

### VT-01 — Missing tone mark entirely
**Severity:** major  
**Pattern:** A Vietnamese word written without any tone mark that has a standard marked form  
**Common causes:** Fast mobile typing, Telex input misfire  
**Example:**
- ❌ `san pham` → `sản phẩm`
- ❌ `cam on` → `cảm ơn`

### VT-02 — Hỏi / Ngã confusion
**Severity:** critical  
**Description:** `hỏi` (?) and `ngã` (~) are the two tones most often swapped — especially in Southern Vietnamese dialect writing  
**Common error pairs:**
- `vẫn` (still) vs `vẩn` (turbid) — often confused
- `sẽ` (will) vs `sẻ` (sparrow/share)
- `cũng` (also) vs `củng` (consolidate)
- `lẽ` (reason) vs `lẻ` (odd/small change)
- `mẫu` (sample/mother) vs `mẩu` (small piece)
- `nghĩ` (think) vs `nghỉ` (rest)
- `bẽ` vs `bẻ`

### VT-03 — Sắc / Huyền confusion
**Severity:** critical  
**Common error pairs:**
- `bán` (sell) vs `bàn` (table/discuss)
- `cá` (fish) vs `cà` (eggplant)
- `mẹ` (mom) vs `mè` (sesame)
- `tiến` (advance) vs `tiền` (money)
- `sắc` (sharp/bright) vs `sằc` (not a word)

### VT-04 — Nặng / Sắc confusion
**Severity:** major  
**Common error pairs:**
- `lập` (establish) vs `lắp` (assemble/install)
- `nhập` (import/enter) vs `nhắp` (sip)
- `cập` (update) vs `cắp` (steal)

### VT-05 — Base vowel + wrong/missing secondary diacritic
**Severity:** major  
**Description:** Vietnamese has compound vowels with both a vowel modifier (ă, â, ô, ơ, ê, ư) AND a tone mark. Errors occur when one is dropped.  
**Example:**
- ❌ `đươc` (missing secondary diacritic on ơ) → `được`
- ❌ `nguoi` → `người`
- ❌ `tôi` written as `toi`

### VT-06 — Common single-word tone errors (lookup list)
**Severity:** major  
Frequently misspelled words in Vietnamese social media:
| Wrong | Correct |
|-------|---------|
| `thông tín` | `thông tin` |
| `dịch vụ` | ✅ (correct) |
| `đặc biệt` | ✅ |
| `khuyến mãi` | `khuyến mãi` ✅ |
| `ưu đải` | `ưu đãi` |
| `giảm gía` | `giảm giá` |
| `sãn phẩm` | `sản phẩm` |
| `đia chỉ` | `địa chỉ` |
| `liên lạc` | ✅ |
| `phản hồi` | ✅ |
| `tư vấn` | ✅ |
| `khuyen mai` | `khuyến mãi` |

---

## Detection approach

1. Tokenize Vietnamese text into syllables (Vietnamese is monosyllabic — each syllable is a token)
2. For each syllable: validate against a Vietnamese syllable dictionary
3. If syllable is invalid: find nearest valid Vietnamese syllable (edit-distance on tone marks)
4. Apply VT-02 and VT-03 detection using known confusion pairs first (highest precision)
5. Flag uncertain cases as `suggestion` rather than `major`

---

## Scoring

Max deduction from this category: 20 pts.
