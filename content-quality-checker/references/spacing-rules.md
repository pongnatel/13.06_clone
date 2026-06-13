# Spacing Rules

Rule group: `SPACING`
Category weight: 15 pts (deducted from base score)

---

## Rules

### SP-01 — Double space
**Severity:** minor  
**Pattern:** Two or more consecutive spaces between words  
**Example:**
- ❌ `Sản phẩm  mới`
- ✅ `Sản phẩm mới`

### SP-02 — Space before punctuation
**Severity:** major  
**Pattern:** Whitespace immediately before `,` `.` `!` `?` `:` `;` `)`  
**Example:**
- ❌ `Cảm ơn bạn !`
- ✅ `Cảm ơn bạn!`

### SP-03 — Missing space after punctuation
**Severity:** major  
**Pattern:** No space after `,` `.` `:` `;` when followed by a letter/digit (not end of string)  
**Example:**
- ❌ `Xin chào,bạn ơi`
- ✅ `Xin chào, bạn ơi`

### SP-04 — Space after opening bracket / before closing bracket
**Severity:** minor  
**Pattern:** Space after `(` or `[`, or space before `)` or `]`  
**Example:**
- ❌ `( miễn phí )`
- ✅ `(miễn phí)`

### SP-05 — Missing space around em dash
**Severity:** minor  
**Pattern:** Em dash `—` without spaces on both sides  
**Example:**
- ❌ `Ưu đãi—giới hạn`
- ✅ `Ưu đãi — giới hạn`

### SP-06 — Trailing whitespace
**Severity:** minor  
**Pattern:** Spaces at end of a line  
**Example:**
- ❌ `Mua ngay! ` (trailing space)
- ✅ `Mua ngay!`

### SP-07 — Space between number and unit
**Severity:** minor  
**Pattern:** No space between number and unit (e.g., `100k`, `5gb`) — apply only when unit is a word, not a symbol  
**Vietnamese exception:** `100k`, `50k` is acceptable in informal Vietnamese social posts — flag as `suggestion` only  
**Example:**
- ❌ `Chỉ với 100.000VND`
- ✅ `Chỉ với 100.000 VND`

### SP-08 — Missing space between concatenated proper nouns (CamelCase collision)
**Severity:** major  
**Pattern:** Two distinct capitalized words or brand tokens written without a space between them, where each part is independently recognizable as a word or brand name.  

**Detection algorithm:**
1. Tokenize the text into space-separated tokens
2. For each token longer than 6 characters, scan for an **internal uppercase letter** that is NOT at position 0
3. When an internal uppercase is found at position `i` (i > 0), check:
   - The character before position `i` is a **lowercase letter** (not a digit, not another uppercase)
   - The substring `token[0:i]` is a known word or brand (length ≥ 2)
   - The substring `token[i:]` starts a new recognizable word or brand (length ≥ 2)
4. If all three conditions hold → flag as SP-08

**Exclusions — do NOT flag:**
- Intentional camelCase brand names: `iPhone`, `TikTok`, `YouTube`, `LinkedIn`, `VNGCampus` *(add known brands to exclusion list below)*
- Hashtags: `#GreenNodeClawathon`
- ALL-CAPS acronyms: `AIAgent` *(flag separately under SP-09)*
- Words where the uppercase is part of a known compound: `MacBook`, `WordPress`

**Known intentional CamelCase exclusions:**
`iPhone`, `iPad`, `macOS`, `TikTok`, `YouTube`, `LinkedIn`, `VNGCampus`, `WordPress`, `JavaScript`, `TypeScript`, `PowerPoint`, `OpenAI`  
*(Extend this list when brand context is provided)*

**Examples:**
- ❌ `GreenNodeClaw-a-thon` → `GreenNode Claw-a-thon`  
  *(internal uppercase `C` at position 10; `GreenNode` and `Claw` are both recognizable)*
- ❌ `DemoAI` → `Demo AI`  
  *(internal uppercase `A` at position 4; both parts are words)*
- ❌ `AIAgent` → `AI Agent`  
  *(see SP-09 for ALL-CAPS prefix pattern)*
- ✅ `iPhone` — excluded (known brand)
- ✅ `VNGCampus` — excluded (known compound brand name, added to exclusion list)

### SP-09 — Missing space after ALL-CAPS acronym before a word
**Severity:** minor  
**Pattern:** An ALL-CAPS sequence (2+ letters) immediately followed by a capitalized or lowercase word with no space.  

**Detection:** Token matches regex `^[A-Z]{2,}[A-Za-zÀ-ỹ]` AND the ALL-CAPS prefix is a known acronym or the suffix forms a valid word.

**Examples:**
- ❌ `AIAgent` → `AI Agent`
- ❌ `VNGCampus` ← *excluded* (intentional brand)
- ✅ `AI Agent` — correct

---

## Scoring

Each violation deducts points based on severity (see SKILL.md severity table).  
Max deduction from this category: 15 pts (cap — never deduct more than 15 for spacing alone).
