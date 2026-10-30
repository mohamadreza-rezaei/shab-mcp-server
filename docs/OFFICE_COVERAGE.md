# Office coverage matrix (Call Center + Host & Guest)

Upstream: `api/{lang}/v_1_4/backoffice` (~162 active routes).
Scope: admin flows used by Call Center and Host & Guest — **not** every backoffice route.

Status values: `planned` | `done` | `skip`.

## Staff auth (1.2)

| Upstream | Tool | Status |
|----------|------|--------|
| `POST auth/login` | `office_login` | done |
| `POST auth/logout` | `office_logout` | done |
| `GET bootstrap` | `office_bootstrap` | done |
| — | `office_auth_status` | done |

## Reads (1.3)

| Upstream | Tool | Status |
|----------|------|--------|
| `GET user` | `office_search_users` | done |
| `GET user/{id}` | `office_get_user` | done |
| `GET user/{id}/statistic` | `office_get_user_stats` | done |
| `GET reserve` | `office_search_reserves` | done |
| `GET reserve/{id}` | `office_get_reserve` | done |
| `GET reserve/{id}/chat` | `office_get_reserve_chat` | done |
| `GET reserve/{id}/eligible-transitions` | `office_get_reserve_transitions` | done |
| `GET house` | `office_search_houses` | done |
| `GET house/{id}` | `office_get_house` | done |
| `GET chat` | `office_list_chats` | done |
| `GET notes` / `GET notes/{type}/{id}` | `office_list_notes` / `office_get_notes` | done |

## Writes (1.4)

| Upstream | Tool | Status |
|----------|------|--------|
| `POST reserve/change-status` | `office_change_reserve_status` | done |
| `POST reserve/{id}/cancel` | `office_cancel_reserve` | done |
| `POST reserve/{reservation}/tag` | `office_tag_reserve` | done |
| `GET payment` / `POST payment/{id}/refund` | `office_search_payments` / `office_refund_payment` | done |
| `GET notification/message-templates` | `office_list_message_templates` | done |
| `POST notification` | `office_send_notification` | done |
| `POST notes` | `office_add_note` | done |

## Followups + handoff (1.5)

| Upstream | Tool | Status |
|----------|------|--------|
| `GET/POST followup/reservations/checkin…` | `office_list_checkin_followups` / `office_update_checkin_followup` | planned |
| `GET/POST followup/reservations/cancellation…` | `office_list_cancellation_followups` | planned |
| `GET/POST followup/reservations/review…` | `office_list_review_followups` | planned |
| `POST house/{id}/support-status/change` | `office_set_house_support_status` | planned |
| `POST user/{id}/easy/login-link` | `office_generate_easy_login_link` | planned |

## Host & Guest extras (1.6)

| Upstream | Tool | Status |
|----------|------|--------|
| `GET/POST review…` | `office_list_reviews` / `office_update_review` | planned |
| `POST financial/edit-host-and-guest-records` | `office_edit_host_guest_financials` | planned |
| `GET user/withdraw-requests` / review | `office_list_withdraw_requests` / `office_review_withdraw` | planned |

## Act-as-user (2.0)

| Upstream | Tool | Status |
|----------|------|--------|
| `POST user/{id}/easy/login-token` (MCP) | `office_impersonate_user` | planned |
| — | `office_end_impersonation` | planned |

## Intentionally skipped

| Area | Reason |
|------|--------|
| RBAC role admin UI | Internal IAM; not day-to-day CC/HG |
| Company / B2B / contracts | Separate product surface |
| Commands runner | Ops break-glass in admin SPA |
| OKR | Different API prefix |
| Promotions / shortlinks | Marketing |
| Tickets (commented out) | Disabled upstream |
| Blind “ignore office tools” prompt | Not a security control |

Update status to `done` as each phase ships. See [OFFICE_COVERAGE_REPORT.md](./OFFICE_COVERAGE_REPORT.md).
