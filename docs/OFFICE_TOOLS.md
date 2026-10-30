# Office MCP tools catalog

Staff tools for Call Center and Host & Guest. All names start with `office_`.
Guest/host sandbox tools stay in [TOOLS.md](./TOOLS.md) and must **not** share the public LiteLLM allowlist with these.

Importers/callers: README.md, docs/README.md, OFFICE_ROADMAP.md. Affected API: backoffice `v_1_4`. No data files.

This catalog fills in as phases ship (1.2 → 2.0). Until a tool is marked **done** in [OFFICE_COVERAGE.md](./OFFICE_COVERAGE.md), treat the row as the planned contract.

User instruction: "Implement the plan as specified, it is attached for your reference. Do NOT edit the plan file itself."

---

## English (engineers)

### Auth (1.2)

| Tool | Auth | Description |
|------|------|-------------|
| `office_login` | none | `POST auth/login` with staff mobile + password; returns `staff_token` + user summary |
| `office_logout` | staff_token | `POST auth/logout` |
| `office_bootstrap` | staff_token | `GET bootstrap` — permissions / user_info |
| `office_auth_status` | staff_token | Confirms token still valid via bootstrap or slim user check |

### Reads (1.3)

| Tool | Auth | Description |
|------|------|-------------|
| `office_search_users` | staff_token | `GET user` grid search |
| `office_get_user` | staff_token | `GET user/{id}` |
| `office_get_user_stats` | staff_token | `GET user/{id}/statistic` |
| `office_search_reserves` | staff_token | `GET reserve` |
| `office_get_reserve` | staff_token | `GET reserve/{id}` |
| `office_get_reserve_chat` | staff_token | `GET reserve/{id}/chat` |
| `office_get_reserve_transitions` | staff_token | `GET reserve/{id}/eligible-transitions` |
| `office_search_houses` | staff_token | `GET house` |
| `office_get_house` | staff_token | `GET house/{id}` |
| `office_list_chats` | staff_token | `GET chat` |
| `office_list_notes` / `office_get_notes` | staff_token | Notes list / by model |

### Writes (1.4)

| Tool | Auth | Description |
|------|------|-------------|
| `office_change_reserve_status` | staff_token + confirm | `POST reserve/change-status` |
| `office_cancel_reserve` | staff_token + confirm | `POST reserve/{id}/cancel` |
| `office_tag_reserve` | staff_token | `POST reserve/{id}/tag` |
| `office_search_payments` | staff_token | `GET payment` |
| `office_refund_payment` | staff_token + confirm | `POST payment/{id}/refund` |
| `office_list_message_templates` | staff_token | Notification templates |
| `office_send_notification` | staff_token + confirm | `POST notification` |
| `office_add_note` | staff_token | `POST notes` |

### Followups + handoff (1.5)

| Tool | Auth | Description |
|------|------|-------------|
| `office_list_checkin_followups` / `office_update_checkin_followup` | staff_token | Check-in followup |
| `office_list_cancellation_followups` | staff_token | Cancellation followup |
| `office_list_review_followups` | staff_token | Review followup |
| `office_set_house_support_status` | staff_token + confirm | House support-status change |
| `office_generate_easy_login_link` | staff_token + confirm | `POST user/{id}/easy/login-link` — browser/SMS handoff |

### Host & Guest (1.6)

| Tool | Auth | Description |
|------|------|-------------|
| `office_list_reviews` / `office_update_review` | staff_token | Review moderation |
| `office_edit_host_guest_financials` | staff_token + confirm | Financial host/guest record edit |
| `office_list_withdraw_requests` / `office_review_withdraw` | staff_token + confirm | Withdraw review |

### Act-as-user (2.0)

| Tool | Auth | Description |
|------|------|-------------|
| `office_impersonate_user` | staff_token + confirm + perm | Returns short-lived **user** `access_token` for sandbox tools |
| `office_end_impersonation` | staff_token / user token | Revoke / clear delegated session guidance |

---

## فارسی (غیر فنی / پشتیبانی)

### ورود کارمند

| ابزار | معنی ساده |
|-------|-----------|
| `office_login` | ورود کارمند با موبایل و رمز؛ توکن کارمندی می‌دهد |
| `office_logout` | خروج |
| `office_bootstrap` | دسترسی‌ها و اطلاعات پنل |
| `office_auth_status` | آیا هنوز وارد هستید؟ |

### جستجو و مشاهده

| ابزار | معنی ساده |
|-------|-----------|
| `office_search_users` / `office_get_user` | پیدا کردن و دیدن کاربر |
| `office_search_reserves` / `office_get_reserve` | پیدا کردن و دیدن رزرو |
| `office_get_reserve_chat` | چت همان رزرو |
| `office_search_houses` / `office_get_house` | پیدا کردن و دیدن اقامتگاه |
| `office_list_notes` | یادداشت‌های داخلی |

### عملیات پشتیبانی

| ابزار | معنی ساده |
|-------|-----------|
| `office_change_reserve_status` | تغییر وضعیت رزرو |
| `office_cancel_reserve` | لغو رزرو |
| `office_refund_payment` | استرداد پرداخت |
| `office_send_notification` | ارسال پیامک/اعلان |
| `office_add_note` | ثبت یادداشت |

### پیگیری و ورود به حساب کاربر

| ابزار | معنی ساده |
|-------|-----------|
| followup tools | پیگیری چک‌این / لغو / نظر |
| `office_generate_easy_login_link` | لینک ورود به حساب کاربر (برای مرورگر) |
| `office_impersonate_user` | گرفتن دسترسی موقت برای انجام کار **به‌جای کاربر** در ابزارهای مهمان/میزبان (نسخه ۲) |

**امنیت:** ابزارهای `office_*` فقط برای تیم داخلی و با لاگین کارمندی هستند؛ در چت‌بات عمومی سایت فعال نمی‌شوند.
