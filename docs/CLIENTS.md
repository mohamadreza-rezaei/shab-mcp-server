# Connect agents to Shab MCP (via LiteLLM)

Use the **LiteLLM MCP gateway**, not the raw `shab-mcp` container.

## Shared values

| Piece | Value |
|--------|--------|
| Shab only | `https://litellm.shab.systems/shab_mcp/mcp` |
| All allowed MCPs | `https://litellm.shab.systems/mcp` |
| Auth header | `x-litellm-api-key: Bearer sk-<virtual-key>` |

Prefer `/shab_mcp/mcp` so the agent only sees Shab tools. The virtual key must be allowed to use MCP server `shab_mcp`.

Replace `litellm.shab.systems` if your Lab Pro domain differs.

---

## Cursor

Settings → **MCP** → New server, or edit `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "shab": {
      "url": "https://litellm.shab.systems/shab_mcp/mcp",
      "headers": {
        "x-litellm-api-key": "Bearer sk-<your-virtual-key>"
      }
    }
  }
}
```

Confirm tools: `search_destinations`, `search_accommodations`, `get_accommodation`, `check_availability` (gateway may prefix with `shab_mcp-`).

---

## Claude Code

```bash
export LITELLM_API_KEY="sk-<your-virtual-key>"

claude mcp add --transport http shab \
  https://litellm.shab.systems/shab_mcp/mcp \
  --header "x-litellm-api-key: Bearer $LITELLM_API_KEY"
```

Inside Claude Code: `/mcp` to verify.

Optional LLM routing through the same gateway (separate from MCP):

```bash
export ANTHROPIC_BASE_URL="https://litellm.shab.systems"
export ANTHROPIC_AUTH_TOKEN="$LITELLM_API_KEY"
```

---

## OpenClaw

CLI:

```bash
openclaw mcp add shab \
  --url https://litellm.shab.systems/shab_mcp/mcp \
  --transport streamable-http

# Add header in Settings → MCP → shab:
# x-litellm-api-key: Bearer sk-<your-virtual-key>

openclaw mcp doctor shab --probe
```

Config:

```json5
{
  mcp: {
    servers: {
      shab: {
        url: "https://litellm.shab.systems/shab_mcp/mcp",
        transport: "streamable-http",
        headers: {
          "x-litellm-api-key": "Bearer sk-<your-virtual-key>"
        }
      }
    }
  }
}
```

---

## VS Code / GitHub Copilot

`.vscode/mcp.json`:

```json
{
  "servers": {
    "shab": {
      "type": "http",
      "url": "https://litellm.shab.systems/shab_mcp/mcp",
      "headers": {
        "x-litellm-api-key": "Bearer sk-<your-virtual-key>"
      }
    }
  }
}
```

Use **Agent** mode in Copilot Chat so MCP tools are available.

---

## Claude Desktop / generic MCP hosts

Same remote HTTP pattern as Cursor:

```json
{
  "mcpServers": {
    "shab": {
      "url": "https://litellm.shab.systems/shab_mcp/mcp",
      "headers": {
        "x-litellm-api-key": "Bearer sk-<your-virtual-key>"
      }
    }
  }
}
```

---

## Hermes

LiteLLM’s Hermes docs cover **model routing** (`/v1/chat/completions`), not MCP.

1. Point Hermes at LiteLLM for models (`~/.hermes/config.yaml` + `LITELLM_API_KEY`).
2. For Shab tools: add the same Streamable HTTP MCP URL in OpenClaw (if Hermes runs under it), or in Hermes’ native MCP config if your build supports HTTP MCP with custom headers.

---

## OpenWebUI

Inside Lab Pro Docker network:

- MCP / Tools URL: `http://litellm:4000/mcp` or `http://litellm:4000/shab_mcp/mcp`
- Auth: LiteLLM virtual key (`Authorization` or LiteLLM-specific header, per your OpenWebUI version)

Public: same as Cursor (`https://litellm.shab.systems/shab_mcp/mcp` + key).

---

## Quick verify

```bash
export LITELLM_URL=https://litellm.shab.systems
export LITELLM_API_KEY=sk-<your-virtual-key>

curl -sS "$LITELLM_URL/shab_mcp/mcp" \
  -H "x-litellm-api-key: Bearer $LITELLM_API_KEY" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
```

Server deploy + LiteLLM config: [SETUP.md](./SETUP.md).
