# ---- Build args ----
ARG PYTHON_VERSION=3.11-slim

# ---- Base ----
FROM python:${PYTHON_VERSION}

# Avoid Python writing .pyc files & enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# ---- System dependencies ----
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ---- Python deps ----
# Copy requirements first to leverage layer caching
COPY content-quality-agent/requirements.txt ./agent-requirements.txt
RUN pip install --no-cache-dir -r ./agent-requirements.txt

# ---- App code + skill ----
# The skill must be present at /app/content-quality-checker so the agent can read it
COPY content-quality-checker/ /app/content-quality-checker/
COPY content-quality-agent/   /app/agent/

# ---- Runtime config ----
ENV SKILL_PATH=/app/content-quality-checker \
    PORT=8000 \
    PYTHONPATH=/app/agent

WORKDIR /app/agent

# ---- Healthcheck ----
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -fsS http://localhost:${PORT}/health || exit 1

# ---- Non-root user (security best practice) ----
RUN useradd --create-home --uid 1000 agent && chown -R agent:agent /app
USER agent

EXPOSE 8000

CMD ["sh", "-c", "uvicorn agent:app --host 0.0.0.0 --port ${PORT}"]
