# Multi-stage build for smaller image
FROM python:3.12-slim AS builder

WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY paper_search_mcp/ paper_search_mcp/

RUN pip install --no-cache-dir build \
    && python -m build --wheel \
    && pip install --no-cache-dir dist/*.whl

FROM python:3.12-slim

WORKDIR /app
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin/paper-search-mcp /usr/local/bin/paper-search-mcp

# Environment variables (override at runtime with -e)
ENV PAPER_SEARCH_MCP_UNPAYWALL_EMAIL=""
ENV PAPER_SEARCH_MCP_CORE_API_KEY=""
ENV PAPER_SEARCH_MCP_SEMANTIC_SCHOLAR_API_KEY=""
ENV PAPER_SEARCH_MCP_ZENODO_ACCESS_TOKEN=""
ENV PAPER_SEARCH_MCP_DOAJ_API_KEY=""
ENV PAPER_SEARCH_MCP_GOOGLE_SCHOLAR_PROXY_URL=""
ENV PAPER_SEARCH_MCP_IEEE_API_KEY=""
ENV PAPER_SEARCH_MCP_ACM_API_KEY=""

# --- Streamable HTTP server mode (container deployment) ---
# PAPER_SEARCH_MCP_PORT is intentionally unset so a PaaS-injected PORT is
# honoured via the legacy fallback; the server otherwise listens on 8000.
ENV PAPER_SEARCH_MCP_TRANSPORT="streamable-http"
ENV PAPER_SEARCH_MCP_HOST="0.0.0.0"
# Provide a strong token at runtime (platform secret or -e). The server
# refuses to start in streamable-http mode without one.
ENV PAPER_SEARCH_MCP_AUTH_TOKEN=""

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD-SHELL python -c "import os, urllib.request; p = os.environ.get('PAPER_SEARCH_MCP_PORT') or os.environ.get('PORT') or '8000'; urllib.request.urlopen('http://127.0.0.1:' + p + '/health', timeout=3)"

# Use the entry point script
CMD ["paper-search-mcp"]
