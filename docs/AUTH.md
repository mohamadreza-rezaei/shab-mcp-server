# Shab MCP authentication

The MCP does **not** store tokens server-side. Agents pass tokens into each authenticated tool.

| Surface | Who | Credential | LiteLLM entry |
|---------|-----|------------|---------------|
| Guest / host (sandbox) | End users | OTP → `access_token` | `shab_mcp` |
| Office (backoffice) | Call Center / Host & Guest staff | Mobile + password → `staff_token` | `shab_office_mcp` |

Never put `office_*` tools on the public `shab_mcp` allowlist. System prompts alone are **not** a security boundary.

## Guest / host — OTP flow

1. `request_login_otp(mobile)` — SMS OTP to `09xxxxxxxxx`.
2. User reads the SMS and gives the code to the agent.
3. `verify_login_otp(mobile, code)` — returns `{ access_token, user }`.
4. Pass `access_token` to `create_booking`, `calculate_invoice`, `get_payment_link`, `list_trips`, `get_booking`, `get_booking_host`, `get_auth_status`, `logout`.

Unregistered mobiles return `status: register` — complete signup on [www.shab.ir](https://www.shab.ir) first.

## Origin / token issuance

`SHAB_API_ORIGIN` is **only an HTTP `Origin` request header** sent to `api.shab.ir` so Sanctum returns a Bearer `access_token` instead of a browser cookie session. It is **not** a real hostname, DNS record, or public MCP URL. Agents reach Shab MCP via **LiteLLM** (e.g. `https://litellm.shab.systems/shab_mcp/mcp` or Docker `http://litellm:4000/shab_mcp/mcp`). The `shab-mcp` container stays internal (`http://shab-mcp:8000/mcp`).

Shab returns a Bearer token when the request `Origin` is **not** a Sanctum stateful SPA domain (`shab.ir`, etc.).

Configure:

```bash
SHAB_API_ORIGIN=https://shab-mcp.internal   # default
SHAB_API_PLATFORM=mcp
```

If `verify_login_otp` succeeds but has no `access_token`, `SHAB_API_ORIGIN` is likely treated as stateful — change it.

## Payment

`get_payment_link` returns `{SHAB_WEB_BASE_URL}/order-tracking/{invoice_id}/show` (same as mainweb after reserve). The user completes card/IPG payment in a browser. MCP never collects card data.

## Guest / host — security notes

- Treat `access_token` as a secret (chat logs may retain it).
- `create_booking` requires `confirm=true`.
- Call `logout` when done to revoke the token.

---

## Office — staff password flow (from 1.2)

Staff tools talk to `api/{lang}/v_1_4/backoffice` (same API as [shab-admin](https://admin.shab.ir)).

1. `office_login(mobile, password)` — returns `{ staff_token, user, … }`.
2. Pass `staff_token` to every `office_*` tool.
3. `office_bootstrap(staff_token)` — permissions / panel user_info (Spatie ACL still enforced upstream).
4. `office_logout(staff_token)` when done.

Configure (in addition to sandbox settings):

```bash
SHAB_API_BASE_URL=https://api.shab.ir   # shared host
SHAB_API_LANG=fa
SHAB_API_VERSION=v_1_4
SHAB_API_ORIGIN=https://shab-mcp.internal
SHAB_BACKOFFICE_CLIENT_ID=78fse4gc-q2ed-8fnh-sewq-bgnc8rtwjaer  # admin SPA client-id
```

Backoffice routes often require **private IP** allowlisting — run MCP where admin already can reach the API.

### Easy login link (1.5)

`office_generate_easy_login_link(user_id, agent_mobile, confirm=true)` → browser/SMS handoff URL (token embedded). For humans opening the site as the user — not for chaining sandbox MCP tools.

### Act-as-user / impersonation (2.0)

1. Staff must already hold `staff_token` and Spatie `easy login` / `generate easy login link`.
2. `office_impersonate_user(user_id, confirm=true)` returns a short-lived **user** `access_token` (API stamps `agentId`).
3. Pass that token only into **sandbox** guest/host tools (`create_booking`, host calendar, etc.).
4. Keep using `staff_token` for backoffice tools (refunds, followups, …).
5. Prefer short sessions; call logout/end-impersonation when finished.

Destructive office tools always require `confirm=true`.
