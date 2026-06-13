# Deployment Guide

## Local Testing First

```bash
cd content-quality-agent
cp .env.example .env
# Edit .env with at least one API key (or set ENABLE_LLM=false for code-only)

pip install -r requirements.txt
python tests/test_deterministic.py   # 21 unit tests
python agent.py                      # starts on :8000
```

In another terminal:
```bash
python tests/test_api.py             # 5 integration tests
```

## Docker Build

The Dockerfile expects the build context to be the **parent directory**
containing both `content-quality-checker/` (the skill) and
`content-quality-agent/` (this code).

```bash
# From the parent directory:
docker build -f content-quality-agent/Dockerfile -t content-quality-agent:latest .
```

Image size should be around 200 MB (Python slim + FastAPI deps).

## Docker Run

```bash
docker run -d -p 8000:8000 \
  -e MINIMAX_API_KEY=sk-your-key \
  -e GEMMA_API_KEY=sk-your-key \
  --name cqa \
  content-quality-agent:latest

# Check logs
docker logs -f cqa

# Smoke test
curl http://localhost:8000/health
```

## Docker Compose

```bash
cd content-quality-agent
cp .env.example .env  # edit with your keys
docker compose up -d --build
```

## Deploy to AgentBase (8-step flow from slide)

1. **Login Portal** — Get `Client ID`, `Client Secret`, `API Key` from AgentBase
2. **Create GitHub Repo** — `gh repo create content-quality-agent --public`
3. **Build Agent** — copy this code into the repo
4. **Import Skill** — clone the skill repo next to it:
   ```
   my-workspace/
   ├── content-quality-checker/    ← skill
   └── content-quality-agent/      ← this code
   ```
5. **Run Prompt Deploy** — use AgentBase's deploy skill
6. **Fill credentials** — in the AgentBase form:
   - `MINIMAX_API_KEY` = your Minimax key
   - `GEMMA_API_KEY` = your Gemma key
   - Runtime: Python 3.11, 1 vCPU, 2GB RAM is enough
7. **Docker Build & Push** — wait ~2-3 min for `ACTIVE` status
8. **Push GitHub** — `git push origin main`, copy URL to submit

## Verify deployment

```bash
AGENT_URL=https://your-agent.agentbase.example
curl $AGENT_URL/health
curl -X POST $AGENT_URL/check \
  -H 'Content-Type: application/json' \
  -d '{
    "text": "GreenNodeClaw-a-thon đã mở màn!!",
    "project": {"brand_exclusions": ["GreenNode"]}
  }'
```

Expected response: `score < 100`, with `SP-08` and `PU-02` issues detected.

## Cost & Latency Tuning

| Mode | Latency | Cost per check |
|------|---------|---------------|
| `enable_llm=false` | ~50 ms | $0 |
| Gemma only | ~2 s | very low |
| Gemma + Minimax (no image) | ~5–8 s | low |
| + image OCR (Minimax multimodal) | ~10–15 s | medium |

**Tips:**
- Default web traffic: `enable_llm=true`
- Batch / cron jobs reviewing thousands of posts: prefer `enable_llm=false`,
  fall back to LLM only when score < 85 (configurable in your client)
- Cache by `hash(text + project)` — same input always produces same result

## Monitoring

Endpoints exposed for ops:
- `GET /health` — liveness check (Docker HEALTHCHECK uses this)
- `GET /skill/info` — confirms which skill version is loaded
- `GET /` — agent metadata + capability flags

Suggested alerts:
- `/health` returns 503 → skill not loaded
- `llm_ready: false` in `/` after deployment → API keys missing
- p95 `/check` latency > 20s → upstream LLM degradation

## Updating the skill without rebuilding

The skill is baked into the image at build time. To update rules without a
full rebuild:

**Option A** (recommended): rebuild — the skill is the source of truth
```bash
docker build -f content-quality-agent/Dockerfile -t content-quality-agent:latest .
docker compose up -d
```

**Option B**: mount the skill as a volume (dev only)
```yaml
# docker-compose.yml override
services:
  agent:
    volumes:
      - ../content-quality-checker:/app/content-quality-checker:ro
```
