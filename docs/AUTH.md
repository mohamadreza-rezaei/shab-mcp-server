# Shab MCP authentication (v0.2)

Guest booking tools need a Shab Sanctum `access_token`. The MCP does **not** store tokens server-side; the agent passes the token into each authenticated tool.

## OTP flow

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

## Security notes

- Treat `access_token` as a secret (chat logs may retain it).
- `create_booking` requires `confirm=true`.
- Call `logout` when done to revoke the token.
