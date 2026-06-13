# Typo Rules

Rule group: `TYPO`
Category weight: 25 pts (highest weight — typos hurt credibility most)

---

## Rules

### TY-01 — Common word substitution errors (English)
**Severity:** major  
Common confusable pairs to check:
- `your` / `you're`
- `its` / `it's`
- `their` / `there` / `they're`
- `then` / `than`
- `affect` / `effect`
- `loose` / `lose`
- `complement` / `compliment`

### TY-02 — Keyboard proximity typo
**Severity:** major  
**Pattern:** A word that is one key away from the intended word and produces a non-word or wrong word  
**Approach:** Flag words that do not exist in a standard dictionary and have a high-probability substitution one key away  
**Example:**
- ❌ `prodcut` → `product`
- ❌ `recieve` → `receive`

### TY-03 — Common Vietnamese word errors
**Severity:** major  
Check for frequently confused Vietnamese word pairs:
- `không` vs `hông` (informal but not always wrong — context-dependent)
- `với` vs `vơi` (with vs. diminished)
- `được` vs `đươc` (missing stroke)
- `người` vs `ngươi`
- `của` vs `cũa`
- `những` vs `nhưng` (plural marker vs. but)
- `mình` vs `minh`
- `giúp` vs `giúp` (check tone mark completeness)
- `thông tin` vs `thông tín` (wrong tone)
- `tiếp theo` vs `tiếp đến` (stylistic — flag as suggestion)

### TY-04 — Missing or extra letter
**Severity:** major  
**Pattern:** Word with an obvious dropped or doubled letter  
**Example:**
- ❌ `reccommend` → `recommend`
- ❌ `occured` → `occurred`

### TY-05 — Number/letter confusion
**Severity:** minor  
**Pattern:** Using `0` for `O`, `1` for `I`/`l`, `3` for `E` outside of stylized brand names  
**Example:**
- ❌ `L00k at this` (non-intentional)

### TY-06 — Homophone confusion (Vietnamese)
**Severity:** critical  
Vietnamese homophones that change meaning entirely:
- `sữa` (milk) vs `sửa` (fix/repair) vs `sứa` (jellyfish)
- `bổ` (nourishing) vs `bộ` (set/ministry) vs `bỗ` (suddenly)
- `cá` (fish) vs `cả` (all) vs `ca` (sing)
- `má` (mom/cheek) vs `ma` (ghost) vs `mà` (but/so)
- Flag any instance where context does not match the word used.

### TY-07 — Brand name misspelling
**Severity:** major  
**Pattern:** Misspelling of widely known brand names  
**Common cases:**
- `Facebook` not `Facbook`, `Facebok`
- `Instagram` not `Instragram`
- `YouTube` not `Youtube`, `you tube`
- `TikTok` not `Tiktok`, `tik tok`
- `Shopee` not `Shopie`, `Shope`
- `Lazada` not `Lasada`

---

## Approach for typo detection

1. Tokenize text into words
2. For each word: check against rule patterns above in order TY-01 → TY-07
3. For unknown words (not in common dictionary): compute edit-distance to nearest valid word
4. Flag edit-distance-1 substitutions as `major`, distance-2 as `minor`
5. Never flag proper nouns, hashtags (#word), or @mentions as typos

---

## Scoring

Max deduction from this category: 25 pts.
