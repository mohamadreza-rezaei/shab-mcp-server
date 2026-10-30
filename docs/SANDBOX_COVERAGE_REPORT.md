# Shab MCP — sandbox coverage report (v1.0)

Audience: **frontend (mainweb)** and **backend (shab-api)** engineers who need a shared, numbered picture of what the MCP wraps, what it deliberately skips, and what remains optional after 1.0.

Related: [V1_COVERAGE.md](./V1_COVERAGE.md) (compact matrix), [ROADMAP.md](./ROADMAP.md), [RELEASE_1_0.md](./RELEASE_1_0.md), [TOOLS.md](./TOOLS.md), [AUTH.md](./AUTH.md).

---

## 1. Executive summary

| Metric | Value | How we got it |
|--------|------:|---------------|
| Sandbox `v_1_4` routes | **188** | `Route::get` + `Route::post` in `sandbox_v_1_4.php` (106 GET + 82 POST) |
| MCP tools | **64** | `@mcp.tool` functions in `src/shab_mcp/server.py` |
| Wrapped client endpoints | **70** | `self._request(...)` calls in `client/shab_api.py` |
| Share of full sandbox | **~37%** | 70 ÷ 188 ≈ 37.2% |
| Mainweb guest + host agent scope | **Treated complete for v1** | Discovery → book → pay-link → trips/lifecycle → profile + host listing/ops/finance |

**Product takeaway for mainweb:** an agent can run the same guest journey the site cares about (search → availability → OTP → reserve → order-tracking payment URL → trips, cancel, chat poll, reviews) and the host journey (listing wizard, calendar/pricing, host reserves, dashboard/finance). It does **not** automate card/IPG, partner wallets, marketing/SEO surfaces, Pusher, or multipart CV uploads.

Some tools call more than one upstream path (e.g. `search_destinations` hits both `house/suggestions` and `region/suggestions`; `get_host_dashboard` aggregates several dashboard GETs). That is why tools (64) ≠ `_request` call sites (70).

---

## 2. How counting works

### 2.1 Sandbox routes (188)

**Source of truth:**

`/var/www/shab-api/shab/Api/src/routes/sandbox_v_1_4.php`

Mainweb talks to `https://api.shab.ir/api/fa/sandbox/v_1_4` (see [ROADMAP.md](./ROADMAP.md)). Every `Route::get(...)` / `Route::post(...)` in that file is one route for this report. Nested `Route::prefix` groups do not change the count; commented-out routes still appear in the file as `Route::` lines and are included in the 188 (same as a greppable inventory).

Verify:

```bash
rg -c 'Route::(get|post)\(' /var/www/shab-api/shab/Api/src/routes/sandbox_v_1_4.php
# → 188
```

### 2.2 MCP tools (64)

**Source of truth:**

`src/shab_mcp/server.py` — each `@mcp.tool` async function is one tool exposed to LiteLLM / MCP clients.

Verify:

```bash
rg -c '@mcp\.tool' src/shab_mcp/server.py
# → 64
```

Full catalog (names, auth, params, FA journey copy): [TOOLS.md](./TOOLS.md).

### 2.3 Wrapped endpoints (70)

**Source of truth:**

`src/shab_mcp/client/shab_api.py` — each `self._request("METHOD", "path...", ...)` is one upstream call shape the client knows how to make.

Verify:

```bash
rg -c 'self\._request\(' src/shab_mcp/client/shab_api.py
# → 70
```

Paths are relative to the sandbox prefix (e.g. `house/search`, `auth/login-otp`, `user/host-dashboard/at-a-glance`). F-string IDs (`house/{house_id}`) count as one endpoint shape each.

### 2.4 Why ~37% is the right “coverage” number

We report **endpoint wrap rate** (70/188), not “tools/routes”. Tools are agent-facing product surfaces; routes are the API inventory. A tool may wrap 1–N routes. Claiming “64/188 tools” would understate wrap depth; claiming “every mainweb button has a tool” would overstate. For teammates: **~37% of sandbox routes have a client wrapper; guest/host mainweb agent flows for v1 are intentionally complete.**

---

## 3. What’s covered by phase / product area

Mapped to flows mainweb and agents actually care about. Status mirrors [V1_COVERAGE.md](./V1_COVERAGE.md).

### 3.1 Discovery (phases 0.2–0.3) — search & browse

| Mainweb-ish flow | MCP tools | Upstream (examples) |
|------------------|-----------|---------------------|
| Place name → destination | `search_destinations` | `GET house/suggestions`, `GET region/suggestions` |
| Amenity codes | `list_search_filters` | `GET search/filters` |
| Listing search (incl. map bbox / nearby) | `search_accommodations` | `GET house/search` |
| Listing detail / photos / reviews | `get_accommodation`, `get_accommodation_photos`, `get_accommodation_reviews` | `GET house/{id}`, `…/photos`, `…/reviews` |
| Availability + quote | `check_availability` | `GET house/{id}/calendar`, `GET reserve/proforma` |
| Neighbourhoods, similar, count, Tehran landing | `list_neighbourhoods`, `get_similar_accommodations`, `count_accommodations`, `get_landing_tehran` | matching house/landing routes |

### 3.2 Auth + booking + payment handoff (0.2)

| Flow | MCP tools | Notes |
|------|-----------|--------|
| OTP login | `request_login_otp`, `verify_login_otp`, `get_auth_status`, `logout` | Token passed per tool; not stored in MCP ([AUTH.md](./AUTH.md)) |
| Create reservation | `create_booking` (`confirm=true`) | `POST reserve` |
| Discount / credit on invoice | `calculate_invoice` | `POST invoice/calculate` |
| Pay in browser | `get_payment_link` | Builds `/order-tracking/{invoice_id}/show` — **no card fields** |
| Trips / booking detail / host contact | `list_trips`, `get_booking`, `get_booking_host`, `get_host_profile` | Guest trips prefer `GET /reserve?type=guest&new=1` shape |

### 3.3 Guest lifecycle (0.4) — after the booking exists

| Flow | MCP tools |
|------|-----------|
| Cancel (reasons → penalty preview → cancel) | `list_cancellation_reasons`, `get_cancellation_penalty`, `cancel_booking` |
| Reject pending / status transitions | `reject_booking`, `get_eligible_transitions`, `change_booking_status` |
| Chat via REST poll (not Pusher) | `list_chats`, `get_chat_thread`, `send_chat_message`, `mark_chat_seen` |
| Reviews | `get_review_for_reservation`, `submit_review`, `comment_on_review`, `list_my_reviews` |

### 3.4 Guest profile (0.5)

| Flow | MCP tools |
|------|-----------|
| Profile read/update | `get_user_profile`, `update_user_profile` |
| Bookmarks | `list_bookmarks`, `toggle_bookmark` |
| Discounts | `list_discounts` |
| Account delete OTP | **skipped** (see §4) |

### 3.5 Host listing / ops / finance (0.6–0.8)

| Area | MCP tools (representative) |
|------|----------------------------|
| Listing wizard | `create_host_listing`, `update_host_listing`, `list_my_houses`, `get_my_house`, `set_house_enabled` |
| Calendar / pricing | `get_host_calendar`, `update_host_calendar`, `get_house_pricing`, `update_house_pricing`, `get_price_suggestion` |
| Host-side reserves | `list_host_reserves`, `get_booking_guest` (+ shared transition/cancel tools where applicable) |
| Dashboard / reviews backlog | `get_host_dashboard`, `list_unanswered_reviews` |
| Host profile | `get_my_host_profile`, `update_my_host_profile` |
| Finance | `list_host_payments`, `list_host_transactions`, `list_host_checkouts`, `list_withdraw_requests`, `get_settlement_type`, `get_host_statistics`, `get_house_statistics` |

---

## 4. Why we skipped major buckets

These are **product/security decisions**, not “forgot to implement.” Compact rows live in [V1_COVERAGE.md](./V1_COVERAGE.md) and [RELEASE_1_0.md](./RELEASE_1_0.md); rationale below is for design reviews.

### 4.1 Card / IPG / pay-invoice → browser order-tracking only

**What exists upstream:** payment gateway eligibility (DigiPay, Snapp Pay, Ewano, Crouse, ZeeCard), payment tokens, reserve gateway lists, wallet request/settle/refund style partner flows, and related finance POSTs.

**What MCP does:** `get_payment_link` returns the same style of **order-tracking URL** mainweb uses after reserve (`{SHAB_WEB_BASE_URL}/order-tracking/{invoice_id}/show`). The human completes card / IPG in a browser.

**Why skip automation:**

- MCP sessions and LLM chat logs are a terrible place for PAN, CVV, OTP-to-bank, or redirect cookie jars.
- PCI / fraud / 3DS flows belong in Shab’s web payment surface, not in tool arguments.
- Agents still help through booking and “here is your pay link”; they do not become a second checkout page.

See [AUTH.md](./AUTH.md) § Payment.

### 4.2 Partner wallet settle → IP whitelist / not guest–host agent surface

**What exists upstream:** `wallet/*` (`request-payment`, `settle-payment`, `refund-payment`, tracker/invoice helpers) and related partner settle paths. Several marketing/ops integrations also sit behind IP middleware (`intrack-ip-whitelist`, `allow-marmulak-ip`).

**Why skip:**

- These are **B2B / partner** or server-to-server surfaces, not what a guest or host does in mainweb chat with an assistant.
- IP-whitelisted callers are expected to be Shab infra or named partners — not arbitrary MCP clients behind LiteLLM.
- Host-facing finance that *is* mainweb-relevant (payments list, transactions, checkouts, withdraw *requests* list, settlement *type* read, statistics) **is** wrapped; partner settle POSTs are not.

### 4.3 Marketing / SEO / blog / newsletter / mood-game / Intrack / matching

**Examples in sandbox:** `blog/*`, `newsletter/subscribe`, campaign `mood-game`, `intrack/*` (IP whitelist), `matching/approved` (Marmulak IP), NPS tips/store, invitation prize/SMS campaigns, retention lucky-prize, company volunteer, weather forecast, photography package pay, visit-request, etc.

**Why skip:**

- Not required for “find a place → book → manage trip” or “manage my listings/money.”
- SEO/footer/region marketing pages are website concerns; agents already search via `house/search` + suggestions.
- Webhook / IP-locked marketing channels would add auth complexity without helping OpenWebUI/Cursor guests.

### 4.4 Pusher broadcasting → REST chat poll instead

Docs and roadmap call out `broadcasting/auth` / realtime Pusher as out of scope through v1.0.

**Why skip:**

- MCP tools are request/response; long-lived websocket auth for Pusher does not fit the LiteLLM tool model cleanly.
- Mainweb already has REST chat list/thread/send/seen; agents **poll** with `list_chats` / `get_chat_thread` instead of subscribing to channels.
- Realtime UX is a browser concern; agents tolerate slightly stale threads.

### 4.5 Server CV / multipart photo upload → agent vision + URLs

**What exists upstream:** temp photo upload (`photo/upload`), profile photo change, review photo add (`user/review/photo/add`), photography package flows, listing photo update paths that expect multipart binaries.

**What MCP does:**

- Returns **photo URLs** via `get_accommodation_photos` (and listing payloads) so the *client* model / OpenWebUI vision can judge courtyards, pools, etc.
- Listing create/update tools accept structured JSON steps where the API allows; they are not a binary upload proxy.

**Why skip multipart/CV on the MCP server:**

- Shipping image bytes through an LLM tool gateway is large, slow, and awkward to authorize.
- Server-side image ML was explicitly out of v1 ([ROADMAP.md](./ROADMAP.md), [RELEASE_1_0.md](./RELEASE_1_0.md)).
- Review photo attach and profile avatar change remain “do it on mainweb” for binary safety.

### 4.6 Account delete OTP → explicit skip

Upstream: `POST send-delete-account-otp`, `POST delete-account`.

**Why skip:**

- Irreversible account destruction via an agent is an abuse and support nightmare (prompt injection → “delete my account”).
- OTP-to-destroy is a deliberate, high-friction mainweb flow; v1 keeps destructive guest actions limited to booking cancel/reject (with `confirm=true`) and logout.
- Listed as skip in [V1_COVERAGE.md](./V1_COVERAGE.md) guest profile section.

### 4.7 Other skip / non-goals clusters (from coverage, AUTH, release notes)

| Cluster | Why not in MCP v1 |
|---------|-------------------|
| Password change / legacy login & refresh | OTP + Sanctum Bearer is the agent path ([AUTH.md](./AUTH.md)); password tools invite credential paste into chats |
| Quick-register / activation / invite-code / external-app auth | Signup and partner SSO belong on www.shab.ir; unregistered OTP returns `status: register` |
| Deep BNPL / gateway eligibility UX | Eligibility endpoints exist; agents hand off to order-tracking rather than reimplement BNPL UI |
| Host house replicate, referral, feedback, best-feature, income prediction, 2D first-page houses, photography host-houses | Niche host helpers — optional post-1.0, not blocking mainweb host ops |
| Reserve notes/tags/help call-me, midterm confirm-only extras | Edge host/ops helpers; core calendar/pricing/reserves covered |
| Review complaint / about-me alternate review surfaces | Core store/comment/my + unanswered covered |
| Bootstrap, local-storage, user-devices, check-ip health | App bootstrap / device telemetry / ops probes — not agent product |
| Device / crouse / zeecard eligibility alone | Same payment philosophy as §4.1 |

---

## 5. Post-1.0 gaps (~60 routes) — optional, not open bugs

After subtracting wrapped endpoints and the intentional skip buckets above, on the order of **~60** sandbox routes remain as **optional backlog**, not release blockers or defect tickets.

Labeled **optional** on purpose:

| Theme | Examples | When it might matter |
|-------|----------|----------------------|
| Companions | Reserve companions + invoice companion CRUD | Agents that must manage guest companion lists on invoices |
| Region SEO / marketing geography | `region/` index, with-province, footer-links, most-visited, show, search/tag (suggestions already wrapped) | SEO-style region pages; agents usually use search suggestions instead |
| Niche host helpers | Replicate listing, referral, income prediction, photography packages, host chat discount actions, automatic withdraw *mutation*, settlement-type *POST*, etc. | Power-host tooling beyond dashboard/calendar/finance reads |
| Misc guest extras | Weather, visit-request, NPS surveys, invitations | Campaign / engagement features |

Shipping any of these later should follow the same rules: wrap mainweb-shaped paths, slim payloads, `confirm=true` on writes, update LiteLLM `allowed_tools`, and extend [V1_COVERAGE.md](./V1_COVERAGE.md).

---

## 6. Cross-check notes (docs that may be stale)

| Location | Issue | Guidance |
|----------|-------|----------|
| [SETUP.md](./SETUP.md) §4.1 `allowed_tools` example | Lists only the **early v0.2** tool set (~18 names: discovery + OTP + booking + trips). **Does not list all 64 tools.** | Treat as a *shape* example for `config.yaml`. For production LiteLLM, sync allowlist to the full tool list in [TOOLS.md](./TOOLS.md) (or omit `allowed_tools` if you intentionally expose the whole server). ROADMAP says allowlist was synced for 1.0 — verify Lab Pro’s live `config.yaml`, not only this repo’s SETUP snippet. |
| [docs/README.md](./README.md) cheatsheet “Tools (v0.2)” | Still describes the v0.2 subset in prose | Prefer [TOOLS.md](./TOOLS.md) / this report for current inventory |
| Root [README.md](../README.md) tools table | Same early subset | Linked docs below are authoritative for 1.0 |
| Image tags in SETUP / ROADMAP | May mention `0.x` vs `1.0.0` | Deploy uses Lab Pro `SHAB_MCP_IMAGE` (see [RELEASE_1_0.md](./RELEASE_1_0.md)) |

If counts in this report disagree with a future sandbox edit, re-run the three greps in §2 and update the executive table.

---

## 7. Source index

| Artifact | Path |
|----------|------|
| Sandbox routes | `/var/www/shab-api/shab/Api/src/routes/sandbox_v_1_4.php` |
| MCP tool surface | `src/shab_mcp/server.py` |
| HTTP client wrappers | `src/shab_mcp/client/shab_api.py` |
| Compact done/skip matrix | `docs/V1_COVERAGE.md` |
| Phase plan / out-of-scope | `docs/ROADMAP.md` |
| Release boundaries | `docs/RELEASE_1_0.md` |
| Auth + payment handoff | `docs/AUTH.md` |
| Per-tool EN + FA catalog | `docs/TOOLS.md` |

**Verified locally while writing this report:** 188 routes, 64 `@mcp.tool`, 70 `self._request` → **~37%** wrap rate; v1 guest/host mainweb agent scope treated complete.
