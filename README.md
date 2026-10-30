# shab-mcp

Private [Model Context Protocol](https://modelcontextprotocol.io/) server for [Shab](https://shab.ir) accommodation APIs (`sandbox` v1.4) — discovery + guest booking assistant.

Designed to run inside **AI Lab Pro** and be consumed through **LiteLLM’s MCP gateway**.

## Documentation

| Doc | Contents |
|-----|----------|
| [docs/README.md](docs/README.md) | Short cheatsheet (URLs, auth, layout) |
| [docs/SETUP.md](docs/SETUP.md) | Server deploy, Lab Pro compose, LiteLLM MCP, testing |
| [docs/CLIENTS.md](docs/CLIENTS.md) | Cursor, Claude Code, OpenClaw, Copilot, Hermes, OpenWebUI |
| [docs/SANDBOX_COVERAGE_REPORT.md](docs/SANDBOX_COVERAGE_REPORT.md) | Full coverage report (188 routes, 64 tools, skips) |
| [docs/TOOLS.md](docs/TOOLS.md) | All 64 tools — EN (tech) + FA (PM/ops) |

## Tools (v1.0)

**64 tools** — guest discovery → booking → lifecycle → profile + host listing/ops/finance. Full bilingual catalog: [docs/TOOLS.md](docs/TOOLS.md). Coverage numbers and skip rationale: [docs/SANDBOX_COVERAGE_REPORT.md](docs/SANDBOX_COVERAGE_REPORT.md).

Auth details: [docs/AUTH.md](docs/AUTH.md). Card/IPG entry is out of scope (`get_payment_link` → browser order-tracking only).

## Quick start (local)

```bash
cd /var/www/shab-mcp-server
uv sync --extra dev
cp .env.example .env

# Streamable HTTP (Docker / LiteLLM)
uv run shab-mcp

# stdio (MCP Inspector / Cursor)
SHAB_MCP_TRANSPORT=stdio uv run shab-mcp
```

Health: `GET http://127.0.0.1:8000/health`  
MCP: `http://127.0.0.1:8000/mcp`

## Docker

```bash
docker build -t shab-mcp:0.2.0 .
docker run --rm -p 8000:8000 \
  -e SHAB_API_BASE_URL=https://api.shab.ir \
  shab-mcp:0.2.0
```

## AI Lab Pro + LiteLLM

1. LabPro compose service: `services/shab-mcp.yml` (internal network, no public ports).
2. LiteLLM `config.yaml`:

```yaml
mcp_servers:
  shab_mcp:
    url: http://shab-mcp:8000/mcp
    transport: http
    auth_type: none
    available_on_public_internet: true
```

3. From LabPro: `make up` (or recreate `shab-mcp` + restart `litellm` so it reloads `config.yaml`).
4. Call tools via LiteLLM: `https://litellm.shab.systems/shab_mcp/mcp` with a virtual key that grants `shab_mcp`.

Local host testing without Docker: run `SHAB_MCP_PORT=8765 uv run shab-mcp`, then register that URL in LiteLLM Admin → MCP Servers (use the Docker-bridge host IP, e.g. `http://10.55.0.1:8765/mcp`).

## Tests

```bash
make sync          # uv sync --extra dev
make test          # mocked unit tests (default)
make test-live     # include @pytest.mark.live (hits api.shab.ir)
# or:
uv run pytest
uv run pytest -m live
```

## Configuration

See [`.env.example`](.env.example). Important defaults:

- `SHAB_API_BASE_URL=https://api.shab.ir`
- Prices exposed to agents are in **Toman**
- Agent dates are Gregorian `YYYY-MM-DD` (converted to Shab Jalali `YYYY-MM-DD` / unix day timestamps)

## Notes

- Shab’s `sandbox` prefix is the public first-party consumer API, not a separate test environment.
- Upstream OpenAPI: `/var/www/shab/docs/openapi/sandbox/`
