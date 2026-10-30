# Shab MCP v1 coverage matrix

Tracks mainweb-used sandbox routes vs MCP tools. Updated each phase; finalized at **1.0.0**.

Legend: **done** | **planned** | **skip** (intentional)

## Guest discovery (v0.2–0.3)

| Upstream | Tool(s) | Status |
|----------|---------|--------|
| `GET house/suggestions`, `region/suggestions` | `search_destinations` | done |
| `GET search/filters` | `list_search_filters` | done |
| `GET house/search` | `search_accommodations` | done (bbox/nearby in 0.3) |
| `GET house/{id}` | `get_accommodation` | done |
| `GET house/{id}/photos` | `get_accommodation_photos` | done |
| `GET house/{id}/reviews` | `get_accommodation_reviews` | done |
| `GET house/{id}/calendar`, `reserve/proforma` | `check_availability` | done |
| `GET house/neighbourhoods` | `list_neighbourhoods` | planned 0.3 |
| `GET house/{id}/similar` | `get_similar_accommodations` | planned 0.3 |
| `GET house/count` | `count_accommodations` | planned 0.3 |
| `GET landing/tehran` | `get_landing_tehran` | planned 0.3 |

## Guest auth / booking (v0.2)

| Upstream | Tool(s) | Status |
|----------|---------|--------|
| `auth/login-otp`, `verify-otp`, `logout`, `GET user` | OTP tools + `get_auth_status` | done |
| `POST reserve`, `invoice/calculate`, payment handoff | `create_booking`, `calculate_invoice`, `get_payment_link` | done |
| `GET reserve` / trips | `list_trips`, `get_booking`, `get_booking_host` | done (parity 0.4) |
| `GET profile/{user}` | `get_host_profile` | done |

## Guest lifecycle (v0.4)

| Upstream | Tool(s) | Status |
|----------|---------|--------|
| cancel reasons/penalty/cancel | cancel tools | planned 0.4 |
| chat list/thread/send/seen | chat tools | planned 0.4 |
| review store/photo/comment | review tools | planned 0.4 |
| eligible-transitions / change-status / reject | `change_booking_status` | planned 0.4 |

## Guest profile (v0.5)

| Upstream | Tool(s) | Status |
|----------|---------|--------|
| `POST user`, bookmarks, discount | profile tools | planned 0.5 |
| account delete OTP | — | skip |

## Host listing / ops / finance (v0.6–0.8)

| Area | Status |
|------|--------|
| Listing wizard store/update steps | planned 0.6 |
| Calendar / pricing / host reserves | planned 0.7 |
| Dashboard / finance / host-profile | planned 0.8 |

## Intentionally skipped

| Upstream / area | Reason |
|-----------------|--------|
| `POST /payments/pay-invoice` (card/IPG) | Browser handoff only |
| Partner wallet settle (IP whitelist) | Not mainweb guest/host MCP |
| Intrack, matching/approved, career, blog, newsletter, mood-game | Marketing/SEO/webhooks |
| Pusher `broadcasting/auth` | REST poll instead |
| Server-side image ML | Agent vision + photo URLs |
