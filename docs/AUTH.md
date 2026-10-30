# Shab MCP authentication (v0.2)

Guest booking tools need a Shab Sanctum `access_token`. The MCP does **not** store tokens server-side; the agent passes the token into each authenticated tool.

## OTP flow

1. `request_login_otp(mobile)` — SMS OTP to `09xxxxxxxxx`.
2. User reads the SMS and gives the code to the agent.
3. `verify_login_otp(mobile, code)` — returns `{ access_token, user }`.
4. Pass `access_token` to `create_booking`, `calculate_invoice`, `get_payment_link`, `list_trips`, `get_booking`, `get_booking_host`, `get_auth_status`, `logout`.

Unregistered mobiles return `status: register` — complete signup on [www.shab.ir](https://www.shab.ir) first.

## Origin / token issuance

Shab returns a Bearer token when the request `Origin` is **not** a Sanctum stateful SPA domain (`shab.ir`, etc.).

Configure:

```bash
SHAB_API_ORIGIN=https://mcp.shab.systems   # default
SHAB_API_PLATFORM=mcp
```

If `verify_login_otp` succeeds but has no `access_token`, `SHAB_API_ORIGIN` is likely treated as stateful — change it.

## Payment

`get_payment_link` returns a Shab web `payment_url`. The user completes card/IPG payment in a browser. MCP never collects card data.

## Security notes

- Treat `access_token` as a secret (chat logs may retain it).
- `create_booking` requires `confirm=true`.
- Call `logout` when done to revoke the token.
