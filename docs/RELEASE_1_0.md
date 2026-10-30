# Shab MCP 1.0.0

Private FastMCP server wrapping Shab sandbox `v_1_4` APIs used by mainweb.

## Included

- Guest discovery (search, bbox/nearby, neighbourhoods, similar, count, landing)
- OTP auth + booking + order-tracking payment URL
- Guest lifecycle: cancel, chat REST, reviews, status transitions
- Guest profile: profile update, bookmarks, discounts
- Host listing wizard, calendar/pricing, host reserves
- Host dashboard, finance, host-profile, statistics

## Explicitly out of scope

- IPG/card automation
- Partner wallet settle
- Pusher realtime (REST poll only)
- Server-side image ML

## Deploy

```bash
cd /var/www/ai-lab-pro
# set SHAB_MCP_IMAGE=shab-mcp:1.0.0
make shab-mcp-rebuild
```
