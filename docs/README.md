# Shab MCP docs

Private MCP for [Shab](https://shab.ir) accommodation APIs (discovery + guest booking). Agents talk to **LiteLLM**, LiteLLM talks to **shab-mcp** (Docker), shab-mcp talks to **api.shab.ir**.

```
Cursor / Claude / OpenClaw / OpenWebUI / …
              │  HTTPS + virtual key
              ▼
     LiteLLM MCP gateway
     /shab_mcp/mcp
              │  Docker DNS (internal)
              ▼
         shab-mcp:8000
              │
              ▼
         api.shab.ir
```

## Guides

| Doc | When to use |
|-----|-------------|
| [SETUP.md](./SETUP.md) | Clone on server, Lab Pro compose, LiteLLM config, health checks, pytest |
| [CLIENTS.md](./CLIENTS.md) | Add Shab MCP to Cursor, Claude Code, OpenClaw, VS Code Copilot, Hermes |
| [AUTH.md](./AUTH.md) | OTP auth + access_token + payment handoff |
| [ROADMAP.md](./ROADMAP.md) | Version plan 0.2 → 1.0 |
| [V1_COVERAGE.md](./V1_COVERAGE.md) | Compact sandbox vs MCP done/skip matrix |
| [SANDBOX_COVERAGE_REPORT.md](./SANDBOX_COVERAGE_REPORT.md) | Detailed coverage report for mainweb + shab-api teammates |
| [TOOLS.md](./TOOLS.md) | All 64 tools — English (engineers) + فارسی (PM/support) |
| [OFFICE_ROADMAP.md](./OFFICE_ROADMAP.md) | Staff / Call Center Office plan 1.1 → 2.0 |
| [OFFICE_COVERAGE.md](./OFFICE_COVERAGE.md) | Backoffice route → tool matrix |
| [OFFICE_COVERAGE_REPORT.md](./OFFICE_COVERAGE_REPORT.md) | Office coverage report for admin + API teammates |
| [OFFICE_TOOLS.md](./OFFICE_TOOLS.md) | Office tools — EN + FA |
| [office-mindmap.excalidraw](./office-mindmap.excalidraw) | Office roadmap mind map |
| [ساخت MCP سفارشی.md](./ساخت%20MCP%20سفارشی.md) | Design notes / architecture (Persian) |

## Quick cheatsheet

**Server layout (sibling repos):**

```text
/home/mrezaei/
├── ai-lab/              # Lab Pro (LiteLLM + compose)
└── shab-mcp-server/     # this repo (Docker build context)
```

**Do not** copy `.env.example` or `uv sync` on the server for Docker deploy. Compose builds the image; Lab Pro `.env` supplies `SHAB_*`.

**Endpoints:**

| What | URL |
|------|-----|
| Container health | `http://shab-mcp:8000/health` (internal) |
| Container MCP | `http://shab-mcp:8000/mcp` (internal) |
| Public via LiteLLM | `https://litellm.shab.systems/shab_mcp/mcp` |
| All MCPs via LiteLLM | `https://litellm.shab.systems/mcp` |

**Auth (clients → LiteLLM):**

```http
x-litellm-api-key: Bearer sk-<virtual-key>
```

**Tools (v1.0):** **64** tools — see [TOOLS.md](./TOOLS.md); coverage [SANDBOX_COVERAGE_REPORT.md](./SANDBOX_COVERAGE_REPORT.md)

**Dates:** Gregorian `YYYY-MM-DD` in · Jalali / unix day out to Shab API · prices in **Toman**.

## One-liner verify

```bash
export LITELLM_URL=https://litellm.shab.systems
export LITELLM_API_KEY=sk-<your-virtual-key>

curl -sS "$LITELLM_URL/shab_mcp/mcp" \
  -H "x-litellm-api-key: Bearer $LITELLM_API_KEY" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
```

You should see the Shab MCP tools (64 in v1.0). Full steps → [SETUP.md](./SETUP.md).
