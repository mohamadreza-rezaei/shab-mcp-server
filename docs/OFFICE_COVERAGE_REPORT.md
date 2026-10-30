# Shab MCP — Office (backoffice) coverage report

Audience: **frontend (shab-admin)** and **backend (shab-api)** engineers, plus Call Center / Host & Guest leads.

Related: [OFFICE_ROADMAP.md](./OFFICE_ROADMAP.md), [OFFICE_COVERAGE.md](./OFFICE_COVERAGE.md), [OFFICE_TOOLS.md](./OFFICE_TOOLS.md), [AUTH.md](./AUTH.md). Sandbox twin: [SANDBOX_COVERAGE_REPORT.md](./SANDBOX_COVERAGE_REPORT.md).

---

## 1. Executive summary

| Metric | Value | Source |
|--------|------:|--------|
| Backoffice `v_1_4` active routes | **~162** | `Route::get/post/any` in `backoffice_v_1_4.php` (82 GET + 79 POST + 1 ANY), non-commented |
| Admin SPA path templates | **~166** | `shab-admin` `APIClient.js` |
| Office MCP tools (v2.0) | **~37** | `@mcp.tool` `office_*` in `server.py` |
| Product scope | Call Center + Host & Guest | Not 100% of backoffice |
| Public exposure | **Separate allowlist** | `shab_office_mcp` ≠ `shab_mcp` |

**Product takeaway:** Staff agents do support work via backoffice tools under staff ACL. Acting as a user (mainweb/host-panel shaped actions) is a **v2** capability behind permissions, confirm, and audit — not available to website chatbots.

**v2.0 wrap:** ~37 office tools covering Call Center + HG workflows (~23% of 162 backoffice routes by intent; not every admin SPA path).

---

## 2. How counting works

### 2.1 Backoffice routes (~162)

**Source:** `/var/www/shab-api/shab/Api/src/routes/backoffice_v_1_4.php`  
**Prefix:** `api/{lang}/v_1_4/backoffice`

### 2.2 Admin usage (~166)

**Source:** `/var/www/shab-admin/src/services/APIClient.js`

### 2.3 MCP tools

Each `@mcp.tool` named `office_*` in `src/shab_mcp/server.py`.

### 2.4 Why not 100%

Same philosophy as sandbox ~37%: wrap **workflows teams need**, document skips.

---

## 3. Covered by phase

| Phase | Area |
|-------|------|
| 1.2 | Staff login / bootstrap |
| 1.3 | User / reserve / house / chat / notes reads |
| 1.4 | Reserve mutations, refunds, notifications, notes write |
| 1.5 | Followups, support-status, easy-login link |
| 1.6 | Reviews, financial edit, withdraw review |
| 2.0 | Impersonation token + audit + dual allowlists |

---

## 4. Why we skipped

### 4.1 System-prompt-only hiding

Website chatbots must not reach admin tools via prompt tricks. **Control = separate LiteLLM `allowed_tools` + staff credentials.**

### 4.2 Card / IPG automation

Refunds use existing backoffice payment refund APIs. MCP never collects card data.

### 4.3 Easy-login browser redirect until v2

`easy/login` returns browser `redirect_url`. Agents need Bearer tokens. v1.5 = login-link handoff; v2 = explicit MCP token endpoint.

### 4.4 RBAC / company / commands / OKR / promotions

Not day-to-day CC/HG work — keep in admin SPA.

### 4.5 Tickets commented out

Do not invent tools until upstream re-enables routes.

### 4.6 Private IP middleware

Backoffice uses `private` IP allowlist. MCP host must reach API from allowed network (same as admin).

---

## 5. Act-on-behalf security (v2)

1. `office_login` → `staff_token`
2. `office_impersonate_user(..., confirm=true)` + Spatie easy-login perms
3. Short-lived user `access_token` with `agentId`
4. User token → sandbox guest/host tools only; office tools keep `staff_token`
5. Audit + public allowlist never lists `office_*`

---

## 6. Source index

| Artifact | Path |
|----------|------|
| Routes | `shab-api/.../routes/backoffice_v_1_4.php` |
| Admin client | `shab-admin/src/services/APIClient.js` |
| Matrix | [OFFICE_COVERAGE.md](./OFFICE_COVERAGE.md) |
