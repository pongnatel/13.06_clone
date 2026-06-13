# Content Quality Checker Agent

A FastAPI agent that proofreads and scores social media posts using the
`content-quality-checker` Claude skill plus two LLMs (Minimax 2.5 + Gemma 4).

## Architecture

```
my-workspace/
├── content-quality-checker/      ← The skill (rules + tests)
│   ├── SKILL.md
│   ├── references/
│   └── tests/
└── content-quality-agent/        ← This agent
    ├── agent.py                  ← FastAPI entrypoint
    ├── skill_loader.py
    ├── scorer.py
    ├── checkers/
    │   ├── deterministic.py      ← Pure regex (free, fast)
    │   ├── gemma_checker.py      ← Gemma 4 — typos, diacritics
    │   ├── minimax_checker.py    ← Minimax 2.5 — semantic + images
    │   └── llm_base.py
    ├── prompts/
    │   ├── vietnamese_tone.txt
    │   ├── homophone_context.txt
    │   ├── basic_typo.txt
    │   └── image_check.txt
    ├── Dockerfile
    ├── docker-compose.yml
    ├── requirements.txt
    └── .env.example
```

The agent reads the skill at startup and injects relevant rule sections into
LLM prompts. Deterministic rules run as regex; semantic rules go to LLMs.

## Pipeline

```
POST /check
  → 1. Deterministic checks (SP-01..09, PU-*, CA-04, CA-05)
  → 2. Gemma 4 — basic typos, diacritics, brand spelling
  → 3. Minimax 2.5 — Vietnamese tones, homophones, missing words
  → 4. Minimax 2.5 (multimodal) — OCR image, cross-check vs caption
  → 5. Deduplicate, sort, score
  → JSON response
```

Phases 2/3/4 run **in parallel** (`asyncio.gather`).

## Run locally

```bash
# 1. From the parent directory (containing both skill and agent folders)
cd content-quality-agent

# 2. Copy env template and fill in API keys
cp .env.example .env
# Edit .env with your MINIMAX_API_KEY and GEMMA_API_KEY

# 3. Install deps
pip install -r requirements.txt

# 4. Run
python agent.py
# or: uvicorn agent:app --reload --port 8000
```

## Run with Docker

```bash
# From the parent directory containing both skill and agent
cd <parent-dir>

# Build (uses content-quality-agent/Dockerfile, context = parent)
docker build -f content-quality-agent/Dockerfile -t content-quality-agent:latest .

# Run
docker run -p 8000:8000 \
  -e MINIMAX_API_KEY=sk-xxx \
  -e GEMMA_API_KEY=sk-yyy \
  content-quality-agent:latest
```

Or with compose:

```bash
cd content-quality-agent
docker compose up --build
```

## API

### `POST /check`

```bash
curl -X POST http://localhost:8000/check \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Ngày 10/06 vừa qua, GreenNodeClaw-a-thon đã mở màn...",
    "project": {
      "brand_name": "GreenNode",
      "brand_exclusions": ["GreenNode", "AgentBase", "VNGCampus"],
      "tone": "casual"
    }
  }'
```

### Response

```json
{
  "score": 72,
  "grade": "C",
  "total_issues": 5,
  "issues_by_severity": { "critical": 2, "major": 2, "minor": 1, "suggestion": 0 },
  "categories": { ... },
  "issues": [
    {
      "rule_id": "SP-08",
      "severity": "major",
      "category": "spacing",
      "position": "char 20",
      "found": "GreenNodeClaw",
      "suggestion": "GreenNode Claw",
      "message": "Possible missing space: 'GreenNode' + 'Claw' merged"
    }
  ],
  "original_text": "...",
  "corrected_text": "..."
}
```

### Fast mode (no LLM)

Set `enable_llm: false` in the request to skip LLM calls — runs only the
deterministic checks. Returns in ~50ms instead of ~5-10s.

## Environment variables

| Var | Required | Default |
|-----|----------|---------|
| `MINIMAX_API_KEY` | for semantic checks | — |
| `MINIMAX_ENDPOINT` | no | `https://api.minimax.chat/v1/chat/completions` |
| `MINIMAX_MODEL` | no | `minimax-2.5` |
| `GEMMA_API_KEY` | for fast typo pass | — |
| `GEMMA_ENDPOINT` | no | (set in `.env.example`) |
| `GEMMA_MODEL` | no | `gemma-4` |
| `SKILL_PATH` | no | `../content-quality-checker` |
| `PORT` | no | `8000` |
| `ENABLE_LLM` | no | `true` |
| `LOG_LEVEL` | no | `INFO` |

## Testing

```bash
# Health check
curl http://localhost:8000/health

# Skill info
curl http://localhost:8000/skill/info

# Deterministic-only check (no LLM keys needed)
curl -X POST http://localhost:8000/check \
  -H "Content-Type: application/json" \
  -d '{ "text": "Test  text!! ", "enable_llm": false }'
```
