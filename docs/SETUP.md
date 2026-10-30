# Setup, LiteLLM MCP, and testing

End-to-end guide: put **shab-mcp-server** on the host, wire it into **AI Lab Pro**, register it in **LiteLLM**, then verify tools.

## Architecture

| Layer | Role |
|-------|------|
| Agent / IDE | MCP client (Cursor, Claude Code, OpenClaw, OpenWebUI, …) |
| LiteLLM | Public MCP gateway + auth + tool allowlist |
| `shab-mcp` container | FastMCP Streamable HTTP, read-only Shab tools |
| `api.shab.ir` | Shab sandbox v1.4 public consumer API |

`shab-mcp` stays **internal** (no public port). Clients never call it directly in production.

---

## 1. Prerequisites

- Docker + Docker Compose (Lab Pro already uses these)
- Git access to `shab-mcp-server` and Lab Pro (`ai-lab`)
- A LiteLLM **virtual key** (or master key) that can use MCP server `shab_mcp`
- Sibling directory layout (build context is relative)

Recommended paths on the Lab Pro host:

```text
/home/mrezaei/
├── ai-lab/                 # Lab Pro repo (compose + litellm/)
└── shab-mcp-server/        # this MCP repo
```

Local/dev mirror often uses `/var/www/ai-lab-pro` + `/var/www/shab-mcp-server` with the same relative `../../shab-mcp-server` context.

---

## 2. Put the code on the server

### 2.1 Clone (or pull) the MCP repo

```bash
cd /home/mrezaei
git clone <your-git-url>/shab-mcp-server.git
# or, if already cloned:
cd /home/mrezaei/shab-mcp-server && git pull
```

Confirm build inputs exist:

```bash
ls /home/mrezaei/shab-mcp-server/Dockerfile
ls /home/mrezaei/shab-mcp-server/pyproject.toml
ls /home/mrezaei/shab-mcp-server/src/shab_mcp
```

### 2.2 What you do **not** need on the server

For Docker / Lab Pro deploy:

| Step | Needed? |
|------|---------|
| `cp .env.example .env` inside `shab-mcp-server` | **No** — env comes from Lab Pro `.env` |
| `uv sync` / `pip install` on the host | **No** — image build installs deps |
| Publishing port `8000` on the host | **No** — LiteLLM reaches `http://shab-mcp:8000` on the Docker network |

Use `.env` + `uv` only for **local host** runs (stdio / Inspector), not for production compose.

---

## 3. Lab Pro: compose service

Lab Pro already includes the service (when your branch has these files):

- `services/shab-mcp.yml` — build + env + healthcheck
- `docker-compose.yml` — `include: ./services/shab-mcp.yml`

### 3.1 Build context

In `services/shab-mcp.yml`, context defaults to:

```yaml
context: ${SHAB_MCP_BUILD_CONTEXT:-../../shab-mcp-server}
```

Resolved from `services/`, so `../../shab-mcp-server` is the **sibling** of the Lab Pro repo root.

If your clone path differs, set an absolute path in Lab Pro `.env`:

```bash
SHAB_MCP_BUILD_CONTEXT=/home/mrezaei/shab-mcp-server
```

### 3.2 Lab Pro `.env` variables

Add (or copy from Lab Pro `.env.example`):

```bash
# Build / resource
SHAB_MCP_BUILD_CONTEXT=../../shab-mcp-server
SHAB_MCP_IMAGE=shab-mcp:0.1.0
SHAB_MCP_MEMORY=256M
SHAB_MCP_CPUS=0.5

# Upstream Shab API (injected into the container)
SHAB_API_BASE_URL=https://api.shab.ir
SHAB_API_LANG=fa
SHAB_API_VERSION=v_1_4
SHAB_CONNECT_TIMEOUT=5.0
SHAB_READ_TIMEOUT=20.0
SHAB_MAX_RETRIES=2
```

### 3.3 Build and start

```bash
cd /home/mrezaei/ai-lab

# Full stack (or at least MCP + LiteLLM)
make up
# or:
docker compose up -d --build shab-mcp
docker compose restart litellm
```

### 3.4 Container health

```bash
docker compose ps shab-mcp
docker compose logs --tail=80 shab-mcp

docker compose exec shab-mcp \
  python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8000/health').read())"
```

Expect healthy status and a JSON/health payload from `/health`.

From LiteLLM’s network (same compose project):

```bash
docker compose exec litellm \
  python -c "import urllib.request; print(urllib.request.urlopen('http://shab-mcp:8000/health').read())"
```

---

## 4. LiteLLM MCP registration

### 4.1 `litellm/config.yaml`

Ensure this block exists (Lab Pro ships it):

```yaml
general_settings:
  # … other settings …
  mcp_internal_ip_ranges:
    - "10.55.0.0/24"
    - "10.0.0.0/8"
    - "172.16.0.0/12"
    - "192.168.0.0/16"

mcp_servers:
  shab_mcp:
    url: http://shab-mcp:8000/mcp
    transport: http
    auth_type: none
    available_on_public_internet: true
    allowed_tools:
      - search_destinations
      - list_search_filters
      - search_accommodations
      - get_accommodation
      - get_accommodation_photos
      - get_accommodation_reviews
      - check_availability
      - request_login_otp
      - verify_login_otp
      - get_auth_status
      - logout
      - create_booking
      - calculate_invoice
      - get_payment_link
      - list_trips
      - get_booking
      - get_booking_host
      - get_host_profile
```

Notes:

- `url` uses **Docker DNS** name `shab-mcp`, not `localhost`. The container stays internal; only LiteLLM is public.
- `available_on_public_internet: true` — external clients can use Shab MCP through the gateway. Auth is still required: virtual key with grant for `shab_mcp`.
- `auth_type: none` — Shab MCP has no upstream API key; LiteLLM authenticates **clients**.
- `mcp_internal_ip_ranges` must allow the Lab Pro Docker subnet so LiteLLM can reach the upstream container.
- After editing `config.yaml`, **restart LiteLLM** so it reloads.

```bash
docker compose restart litellm
docker compose logs --tail=50 litellm | grep -i mcp || true
```

### 4.2 Virtual key access

In LiteLLM Admin UI:

1. Create or open a **virtual key** (or team).
2. Grant access to MCP server **`shab_mcp`** (and any models you need).
3. Copy the key (`sk-…`). Clients send it as:

```http
x-litellm-api-key: Bearer sk-…
```

Prefer `x-litellm-api-key` over putting the LiteLLM key in `Authorization` for MCP traffic.

### 4.3 Public URLs

| Scope | URL |
|-------|-----|
| Shab only | `https://litellm.shab.systems/shab_mcp/mcp` |
| All MCPs the key can use | `https://litellm.shab.systems/mcp` |

Replace the host if your Lab Pro LiteLLM domain differs. Local tunnel/debug: `http://127.0.0.1:4000/shab_mcp/mcp`.

---

## 5. Test the project

### 5.1 Unit tests (dev machine or CI)

```bash
cd /path/to/shab-mcp-server
uv sync --extra dev
uv run pytest
```

Optional live calls against production Shab API:

```bash
uv run pytest -m live
```

### 5.2 Direct container MCP (internal)

Only useful for debugging from inside the Docker network:

```bash
docker compose exec litellm wget -qO- http://shab-mcp:8000/health
```

### 5.3 LiteLLM `tools/list`

```bash
export LITELLM_URL=https://litellm.shab.systems   # or http://127.0.0.1:4000
export LITELLM_API_KEY=sk-<your-virtual-key>

curl -sS "$LITELLM_URL/shab_mcp/mcp" \
  -H "x-litellm-api-key: Bearer $LITELLM_API_KEY" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"curl","version":"0"}}}'
```

Then list tools (session headers may be required depending on LiteLLM/MCP version; Admin UI → MCP → Tools is the easy check):

```bash
curl -sS "$LITELLM_URL/shab_mcp/mcp" \
  -H "x-litellm-api-key: Bearer $LITELLM_API_KEY" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
```

Expect tools (names may be prefixed with `shab_mcp-` at the gateway):

- `search_destinations`
- `search_accommodations`
- `get_accommodation`
- `check_availability`

### 5.4 OpenWebUI

1. OpenWebUI → Connections / MCP (or Tools) → LiteLLM MCP.
2. URL: `http://litellm:4000/mcp` or your public gateway URL.
3. Header / key: LiteLLM virtual key.
4. Ask: “Search destinations for اصفهان” and confirm a tool call.

### 5.5 Smoke tool semantics

| Tool | Minimal check |
|------|----------------|
| `search_destinations` | Query a Persian city name → destination ids |
| `search_accommodations` | City + date range → listing cards |
| `get_accommodation` | Known house id → detail |
| `check_availability` | House id + check-in/out (Gregorian `YYYY-MM-DD`) → calendar + Toman quote |

v0.2 adds OTP auth + booking up to payment URL handoff (no card/IPG in MCP). See AUTH.md.

---

## 6. Local development (optional)

Host process without Docker:

```bash
cd /path/to/shab-mcp-server
cp .env.example .env
uv sync --extra dev
uv run shab-mcp
# health: http://127.0.0.1:8000/health
# mcp:    http://127.0.0.1:8000/mcp
```

Stdio (MCP Inspector / Cursor local):

```bash
SHAB_MCP_TRANSPORT=stdio uv run shab-mcp
```

To point LiteLLM at a host-run MCP, register a URL reachable from the LiteLLM container (Docker bridge IP), e.g. `http://10.55.0.1:8765/mcp`, in Admin → MCP Servers or `config.yaml`. Prefer the compose service for production.

---

## 7. Upgrade / redeploy

```bash
cd /home/mrezaei/shab-mcp-server && git pull
cd /home/mrezaei/ai-lab
docker compose up -d --build shab-mcp
docker compose restart litellm
```

If tools disappear after restart, check: dead upstream MCP entries in LiteLLM Admin (LiteLLM can fail aggregation if any registered MCP is down), `mcp_internal_ip_ranges`, and key permissions for `shab_mcp`.

---

## 8. Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Build context not found | Wrong `SHAB_MCP_BUILD_CONTEXT` | Point at sibling `shab-mcp-server` path |
| `shab-mcp` unhealthy | App crash / API unreachable | `docker compose logs shab-mcp` |
| LiteLLM can’t reach MCP | Missing internal IP ranges / wrong URL | Use `http://shab-mcp:8000/mcp` + `mcp_internal_ip_ranges` |
| OpenWebUI “Failed to connect” | Stale MCP entry pointing at dead host port | Delete old Admin MCP entries; keep only compose `shab_mcp` |
| Key not allowed | Virtual key missing MCP grant | Grant `shab_mcp` on the key/team |
| Wrong dates / prices | Client sent Jalali or assumed Rial | Agents use Gregorian `YYYY-MM-DD`; prices are Toman |

---

## 9. Related

- Short index: [README.md](./README.md)
- Wire agents (Cursor, Claude, OpenClaw, …): [CLIENTS.md](./CLIENTS.md)
- Repo overview: [../README.md](../README.md)
- Env template: [../.env.example](../.env.example)
