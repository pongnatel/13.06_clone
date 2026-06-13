# Punctuation Rules

Rule group: `PUNCTUATION`
Category weight: 15 pts

---

## Rules

### PU-01 — Missing sentence-ending punctuation
**Severity:** minor  
**Pattern:** Final sentence in post ends without `.` `!` `?` or emoji  
**Note:** Social media posts often omit final period intentionally — flag as `suggestion` unless it's a formal brand tone.  
**Example:**
- ⚠️ `Hãy liên hệ chúng tôi ngay` (no ending punctuation)

### PU-02 — Consecutive punctuation
**Severity:** major  
**Pattern:** `,,` `..` `!!` `??` (unintentional duplicates — NOT `...` ellipsis)  
**Exception:** `...` (3 dots) is valid ellipsis. `....` (4+) is an error.  
**Example:**
- ❌ `Ưu đãi khủng!!` → `Ưu đãi khủng!`
- ✅ `Chờ chút nhé...` (valid)
- ❌ `Chờ chút nhé....` (4 dots)

### PU-03 — Wrong dash type
**Severity:** minor  
**Pattern:** Hyphen `-` used where en dash `–` or em dash `—` is appropriate (between ranges or as a break)  
**Example:**
- ❌ `Thứ 2-6: 8h-17h`
- ✅ `Thứ 2–6: 8h–17h`
- **Note:** In casual Vietnamese social posts, `-` for time ranges is widely accepted; flag as `suggestion`.

### PU-04 — Missing comma before conjunction in compound sentence
**Severity:** minor  
**Pattern:** No comma before `nhưng`, `tuy nhiên`, `mà`, `và` when joining two independent clauses  
**Example:**
- ❌ `Sản phẩm tốt nhưng giá hơi cao`
- ✅ `Sản phẩm tốt, nhưng giá hơi cao`

### PU-05 — Comma splice
**Severity:** major  
**Pattern:** Two complete sentences joined only by a comma (no conjunction)  
**Example:**
- ❌ `Đây là sản phẩm mới, mua ngay đi bạn.`
- ✅ `Đây là sản phẩm mới. Mua ngay đi bạn!`

### PU-06 — Unmatched brackets or quotes
**Severity:** critical  
**Pattern:** Opening `(` `[` `"` `'` without matching close, or vice versa  
**Example:**
- ❌ `Giảm giá (50% tất cả sản phẩm`
- ✅ `Giảm giá (50% tất cả sản phẩm)`

### PU-07 — Wrong quotation mark style
**Severity:** suggestion  
**Pattern:** Straight quotes `"text"` used — prefer curly `"text"` in polished copy  
**Note:** In Vietnamese, guillemets `«text»` are also acceptable.

### PU-08 — Ellipsis formatting
**Severity:** minor  
**Pattern:** Spaced ellipsis `. . .` instead of `...`  
**Example:**
- ❌ `Đang chờ . . .`
- ✅ `Đang chờ...`

---

## Scoring

Max deduction from this category: 15 pts.
