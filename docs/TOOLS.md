# Shab MCP tools (v1.0) — EN + FA

**64 tools** registered with `@mcp.tool` in `src/shab_mcp/server.py` (verified). Coverage context: [SANDBOX_COVERAGE_REPORT.md](./SANDBOX_COVERAGE_REPORT.md). Auth: [AUTH.md](./AUTH.md).

- **English** — engineers (mainweb / shab-api / Lab Pro): names, auth, params, sandbox area.
- **فارسی** — محصول / پشتیبانی / عملیات: نام‌های ساده و اینکه دستیار با هر ابزار چه کاری می‌تواند بکند.

Conventions:

- Prices in tool results are **Toman**. Agent dates in are Gregorian `YYYY-MM-DD`.
- `access_token` = Shab Sanctum Bearer from OTP login; MCP does not store it.
- Destructive / write tools require `confirm=true` unless noted.
- Payment: agents return an order-tracking **URL**; users pay in the browser (no card data in MCP).

---

## English — technical catalog

### Discovery / search

| Tool | Auth | Key params / returns | Sandbox area | Description |
|------|------|----------------------|--------------|-------------|
| `search_destinations` | no | `query` → destination suggestions | house/region suggestions | Resolve a place name into Shab destinations usable by `search_accommodations`. |
| `list_search_filters` | no | filter codes | `search/filters` | List amenity/feature filter codes for `search_accommodations(amenities=[...])`. |
| `search_accommodations` | no | destination, dates, guests, price, amenities, sort, bbox/nearby | `house/search` | Search Shab accommodations. Prices in Toman. Supports map bbox and nearby. |
| `get_accommodation` | no | `accommodation_id` | `house/{id}` | Get normalized details for one Shab accommodation. |
| `get_accommodation_photos` | no | `accommodation_id` → URLs | `house/{id}/photos` | List photo URLs for an accommodation (for agent/user review). |
| `get_accommodation_reviews` | no | `accommodation_id`, `page` | `house/{id}/reviews` | Fetch guest reviews for an accommodation. |
| `list_neighbourhoods` | no | `city` | `house/neighbourhoods` | List neighbourhoods for map/area search. |
| `get_similar_accommodations` | no | `accommodation_id` | `house/{id}/similar` | List similar accommodations for a house. |
| `count_accommodations` | no | filters (no full list) | `house/count` | Count accommodations matching filters (no full result list). |
| `get_landing_tehran` | no | — | `landing/tehran` | Tehran landing preset (categories/filters used on the home/Tehran page). |
| `check_availability` | no* | dates, guests, optional `discount_code` → quote | calendar + `reserve/proforma` | Check nightly availability and return a price quote (no booking). |

\*Quote path may accept token-less proforma; booking still needs auth.

### Auth

| Tool | Auth | Key params / returns | Sandbox area | Description |
|------|------|----------------------|--------------|-------------|
| `request_login_otp` | no | `mobile` | `auth/login-otp` | Send a Shab login OTP SMS to the user. |
| `verify_login_otp` | no | `mobile`, `code` → `access_token` | `auth/verify-otp` | Verify OTP and return `access_token` for booking/trip tools. |
| `get_auth_status` | yes | `access_token` | `GET user` | Check whether `access_token` is still valid and return user summary. |
| `logout` | yes | `access_token` | `auth/logout` | Revoke the Shab `access_token`. |

### Booking & payment handoff

| Tool | Auth | Key params / returns | Sandbox area | Description |
|------|------|----------------------|--------------|-------------|
| `create_booking` | yes | house, dates, guests; **`confirm=true`** | `POST reserve` | Create a reservation request or instant booking. Requires `confirm=true`. |
| `calculate_invoice` | yes | `invoice_id`, discount/credit flags | `invoice/calculate` | Apply discount/credit to an invoice before payment. |
| `get_payment_link` | yes | `reserve_id` / `invoice_id` → order-tracking URL | invoice show + web URL | Return a Shab payment URL for the user to complete card payment in a browser. |
| `list_trips` | yes | `page` | `reserve` / trips | List the authenticated user's trips/bookings. |
| `get_booking` | yes | `reserve_id` | `reserve/{id}` | Get details/status for one booking. |
| `get_booking_host` | yes | `reserve_id` | `reserve/{id}/host` | Get host contact info for a booking (when the reservation allows it). |
| `get_host_profile` | no | `user_id` | `profile/{user}` | Get a public host profile (no auth required). |

### Guest lifecycle (cancel, chat, reviews, status)

| Tool | Auth | Key params / returns | Sandbox area | Description |
|------|------|----------------------|--------------|-------------|
| `list_cancellation_reasons` | yes | `reserve_id` | cancellation-reasons | List cancellation reasons for a booking. |
| `get_cancellation_penalty` | yes | `reserve_id`, `reason_id` | cancellation-penalty | Preview cancellation penalty before `cancel_booking`. |
| `cancel_booking` | yes | reason + **`confirm=true`** | cancel | Cancel a booking. Requires `confirm=true`. |
| `reject_booking` | yes | **`confirm=true`** | `reserve/reject` | Guest-reject a pending reservation. Requires `confirm=true`. |
| `get_eligible_transitions` | yes | `reserve_id` | eligible-transitions | List eligible status transitions for a reservation. |
| `change_booking_status` | yes | `transition` + **`confirm=true`** | change-status | Apply a reservation status transition. Requires `confirm=true`. |
| `list_chats` | yes | `page` | `GET chat` | List chat conversations (REST). |
| `get_chat_thread` | yes | `reserve_id`, `page` | reserve chat | Fetch chat messages for a reservation (poll; no Pusher). |
| `send_chat_message` | yes | `text` + **`confirm=true`** | `POST chat` | Send a TEXT chat message. Requires `confirm=true`. |
| `mark_chat_seen` | yes | `message_id` | chat seen | Mark a chat message as seen. |
| `get_review_for_reservation` | yes | `reserve_id` | user/review/reservation | Get review form/detail for a reservation. |
| `submit_review` | yes | rating/comment + **`confirm=true`** | user/review/store | Submit a guest review for a stay. Requires `confirm=true`. |
| `comment_on_review` | yes | `review_id`, comment + **`confirm=true`** | user/review/comment | Reply/comment on a review. Requires `confirm=true`. |
| `list_my_reviews` | yes | `page` | user/review/my | List reviews written by the current user. |

### Guest profile

| Tool | Auth | Key params / returns | Sandbox area | Description |
|------|------|----------------------|--------------|-------------|
| `get_user_profile` | yes | — | `GET user` | Get the authenticated guest profile. |
| `update_user_profile` | yes | profile fields + **`confirm=true`** | `POST user` | Update guest profile fields. Requires `confirm=true`. |
| `list_bookmarks` | yes | paging | profile/bookmarks | List bookmarked accommodations. |
| `toggle_bookmark` | yes | `accommodation_id` + **`confirm=true`** | house/bookmark | Toggle bookmark for an accommodation. Requires `confirm=true`. |
| `list_discounts` | yes | — | user/discount | List available discount codes for the guest. |

### Host listing

| Tool | Auth | Key params / returns | Sandbox area | Description |
|------|------|----------------------|--------------|-------------|
| `create_host_listing` | yes | `payload` + **`confirm=true`** | `house/store` | Start a host listing (`POST house/store`). Requires `confirm=true`. |
| `update_host_listing` | yes | `house_id`, `step`, `payload` + **`confirm=true`** | house update | Update one listing wizard step. Requires `confirm=true`. |
| `list_my_houses` | yes | `page` | house/my-houses | List houses owned by the authenticated host. |
| `get_my_house` | yes | `house_id` | user/house/{id} | Get host-facing details for one of the user's houses. |
| `set_house_enabled` | yes | `enabled` + **`confirm=true`** | house enable/delete | Enable or disable a host house. Requires `confirm=true`. |

### Host calendar, pricing, reserves

| Tool | Auth | Key params / returns | Sandbox area | Description |
|------|------|----------------------|--------------|-------------|
| `get_host_calendar` | yes | `house_id`, date range | host-calendar | Fetch host calendar for a house date range. |
| `update_host_calendar` | yes | calendar `payload` + **`confirm=true`** | house calendar POST | Update host calendar (block/open/price days). Requires `confirm=true`. |
| `get_house_pricing` | yes | `house_ids` | midterm/house-pricing | Get midterm/house pricing for host houses. |
| `update_house_pricing` | yes | `house_prices` + **`confirm=true`** | midterm store | Store midterm house pricing. Requires `confirm=true`. |
| `get_price_suggestion` | yes | `house_id`, `dates` | price-suggestion | Get smart price suggestion for dates. |
| `list_host_reserves` | yes | `page` | `reserve` type=host | List reservations for the authenticated host (`type=host`). |
| `get_booking_guest` | yes | `reserve_id` | reserve/{id}/guest | Get guest contact/info for a host-side reservation. |

### Host dashboard, profile, finance

| Tool | Auth | Key params / returns | Sandbox area | Description |
|------|------|----------------------|--------------|-------------|
| `get_host_dashboard` | yes | — | host-dashboard/* | Host dashboard: at-a-glance, notices, performance. |
| `list_unanswered_reviews` | yes | — | unanswered-reviews | List unanswered host reviews from the dashboard. |
| `get_my_host_profile` | yes | — | user/host-profile GET | Get the authenticated user's host-profile settings. |
| `update_my_host_profile` | yes | `payload` + **`confirm=true`** | user/host-profile POST | Update host-profile. Requires `confirm=true`. |
| `list_host_payments` | yes | `page` | profile/payments | List host profile payments. |
| `list_host_transactions` | yes | `page` | profile/transaction | List host financial transactions. |
| `list_host_checkouts` | yes | `page` | profile/checkouts | List host checkouts/settlements. |
| `list_withdraw_requests` | yes | — | withdraw-requests | List host withdraw requests. |
| `get_settlement_type` | yes | — | settlement-type | Get host settlement type settings. |
| `get_host_statistics` | yes | — | overall/sale statistics | Overall and sale statistics for the host. |
| `get_house_statistics` | yes | `house_id` | house/{id}/statistics | Statistics for one host house. |

**Tool count: 64.**

---

## فارسی — راهنمای غیرفنی ابزارها

این بخش برای مدیر محصول، پشتیبانی و عملیات است. نام‌های انگلیسی ابزار را مهندس‌ها در لاگ و LiteLLM می‌بینند؛ اینجا معنی سادهٔ هر کدام آمده است.

دستیار **شبا** با این ابزارها می‌تواند مهمان را در پیدا کردن اقامتگاه و رزرو کمک کند، یا به میزبان در مدیریت آگهی و رزرو و مالی کمک کند. **پرداخت کارت بانکی داخل چت انجام نمی‌شود** — فقط لینک پرداخت وب داده می‌شود. حذف حساب کاربری عمداً پشتیبانی نشده است.

### جستجو و انتخاب اقامتگاه

| نام دوستانه | ابزار فنی | دستیار چه می‌کند؟ |
|-------------|-----------|-------------------|
| پیدا کردن مقصد | `search_destinations` | نام شهر یا منطقه را به مقصدهای قابل جستجو تبدیل می‌کند. |
| فهرست امکانات | `list_search_filters` | کد/نام امکانات (مثل استخر) را برای فیلتر جستجو می‌دهد. |
| جستجوی اقامتگاه | `search_accommodations` | اقامتگاه‌ها را با تاریخ، نفرات، قیمت، نقشه و … جستجو می‌کند. |
| جزئیات اقامتگاه | `get_accommodation` | مشخصات یک آگهی را نشان می‌دهد. |
| گالری عکس | `get_accommodation_photos` | لینک عکس‌ها را می‌آورد تا کاربر یا مدل تصویر ببیند. |
| نظرات مهمانان | `get_accommodation_reviews` | دیدگاه‌های قبلی مهمان‌ها را می‌خواند. |
| محله‌ها | `list_neighbourhoods` | محله‌های یک شهر را برای جستجوی منطقه‌ای لیست می‌کند. |
| اقامتگاه‌های مشابه | `get_similar_accommodations` | گزینه‌های شبیه یک آگهی را پیشنهاد می‌دهد. |
| شمارش نتایج | `count_accommodations` | فقط تعداد نتیجه را می‌گوید (بدون لیست کامل). |
| صفحه تهران | `get_landing_tehran` | فیلترها/دسته‌های آماده‌شدهٔ صفحه تهران را می‌آورد. |
| بررسی موجودی و قیمت | `check_availability` | برای تاریخ مشخص می‌گوید جا هست یا نه و قیمت تقریبی می‌دهد (هنوز رزرو نمی‌کند). |

### ورود به حساب

| نام دوستانه | ابزار فنی | دستیار چه می‌کند؟ |
|-------------|-----------|-------------------|
| ارسال کد ورود | `request_login_otp` | پیامک کد یک‌بارمصرف به موبایل کاربر می‌فرستد. |
| تأیید کد ورود | `verify_login_otp` | کد را چک می‌کند و توکن ورود می‌گیرد. |
| وضعیت ورود | `get_auth_status` | می‌گوید توکن هنوز معتبر است یا نه. |
| خروج | `logout` | توکن را باطل می‌کند. |

### رزرو و پرداخت

| نام دوستانه | ابزار فنی | دستیار چه می‌کند؟ |
|-------------|-----------|-------------------|
| ثبت رزرو | `create_booking` | درخواست رزرو یا رزرو آنی می‌سازد (فقط با تأیید صریح کاربر). |
| اعمال تخفیف روی فاکتور | `calculate_invoice` | کد تخفیف یا اعتبار را روی فاکتور اعمال می‌کند. |
| لینک پرداخت | `get_payment_link` | لینک صفحهٔ پیگیری/پرداخت وب را می‌دهد؛ کاربر در مرورگر کارت می‌کشد. |
| لیست سفرها | `list_trips` | رزروها و سفرهای کاربر را نشان می‌دهد. |
| جزئیات یک رزرو | `get_booking` | وضعیت و جزئیات یک رزرو را می‌آورد. |
| اطلاعات میزبان رزرو | `get_booking_host` | در صورت مجاز بودن، راه تماس میزبان همان رزرو را می‌دهد. |
| پروفایل عمومی میزبان | `get_host_profile` | صفحهٔ عمومی یک میزبان را بدون نیاز به ورود نشان می‌دهد. |

### سفرها، لغو، چت و نظر

| نام دوستانه | ابزار فنی | دستیار چه می‌کند؟ |
|-------------|-----------|-------------------|
| دلایل لغو | `list_cancellation_reasons` | دلایل قابل انتخاب برای لغو را لیست می‌کند. |
| پیش‌نمایش جریمه لغو | `get_cancellation_penalty` | قبل از لغو، جریمه را نشان می‌دهد. |
| لغو رزرو | `cancel_booking` | رزرو را لغو می‌کند (با تأیید صریح). |
| رد رزرو در انتظار | `reject_booking` | رزرو در انتظار تأیید را از سمت مهمان رد می‌کند. |
| وضعیت‌های ممکن رزرو | `get_eligible_transitions` | می‌گوید رزرو الان به چه وضعیت‌هایی می‌تواند برود. |
| تغییر وضعیت رزرو | `change_booking_status` | وضعیت رزرو را عوض می‌کند (با تأیید). |
| لیست گفتگوها | `list_chats` | گفتگوهای چت را لیست می‌کند. |
| پیام‌های یک رزرو | `get_chat_thread` | پیام‌های چت همان رزرو را می‌خواند (بدون اعلان لحظه‌ای؛ با تازه‌سازی). |
| ارسال پیام | `send_chat_message` | پیام متنی می‌فرستد (با تأیید). |
| علامت‌زدن دیده‌شدن | `mark_chat_seen` | پیام را به‌عنوان دیده‌شده علامت می‌زند. |
| فرم نظر برای رزرو | `get_review_for_reservation` | جزئیات/فرم ثبت نظر برای یک اقامت را می‌آورد. |
| ثبت نظر | `submit_review` | نظر مهمان را ثبت می‌کند. |
| پاسخ به نظر | `comment_on_review` | روی یک نظر پاسخ می‌گذارد (مهمان یا میزبان، بسته به نقش). |
| نظرات من | `list_my_reviews` | نظرهایی که خود کاربر نوشته را لیست می‌کند. |

### پروفایل مهمان

| نام دوستانه | ابزار فنی | دستیار چه می‌کند؟ |
|-------------|-----------|-------------------|
| دیدن پروفایل | `get_user_profile` | مشخصات حساب مهمان را می‌خواند. |
| ویرایش پروفایل | `update_user_profile` | فیلدهای پروفایل را به‌روز می‌کند (با تأیید). |
| علاقه‌مندی‌ها | `list_bookmarks` | اقامتگاه‌های ذخیره‌شده را نشان می‌دهد. |
| افزودن/حذف علاقه‌مندی | `toggle_bookmark` | یک اقامتگاه را به علاقه‌مندی‌ها اضافه یا از آن کم می‌کند. |
| کدهای تخفیف من | `list_discounts` | تخفیف‌های در دسترس کاربر را لیست می‌کند. |

### میزبان — آگهی

| نام دوستانه | ابزار فنی | دستیار چه می‌کند؟ |
|-------------|-----------|-------------------|
| شروع ثبت آگهی | `create_host_listing` | ثبت آگهی جدید را شروع می‌کند. |
| به‌روزرسانی مرحله آگهی | `update_host_listing` | یک مرحله از ویزارد آگهی را ذخیره می‌کند. |
| لیست خانه‌های من | `list_my_houses` | اقامتگاه‌های میزبان را لیست می‌کند. |
| جزئیات خانه من | `get_my_house` | جزئیات یک خانه از دید میزبان را می‌آورد. |
| فعال/غیرفعال کردن آگهی | `set_house_enabled` | آگهی را روشن یا خاموش می‌کند. |

### میزبان — تقویم، قیمت، رزروها

| نام دوستانه | ابزار فنی | دستیار چه می‌کند؟ |
|-------------|-----------|-------------------|
| تقویم میزبان | `get_host_calendar` | تقویم بازهٔ تاریخی یک خانه را می‌خواند. |
| ویرایش تقویم | `update_host_calendar` | روزها را می‌بندد/باز می‌کند یا قیمت روز را عوض می‌کند. |
| قیمت‌گذاری میان‌مدت | `get_house_pricing` | قیمت‌های میان‌مدت خانه‌ها را می‌خواند. |
| ذخیره قیمت میان‌مدت | `update_house_pricing` | قیمت میان‌مدت را ذخیره می‌کند. |
| پیشنهاد قیمت | `get_price_suggestion` | پیشنهاد قیمت هوشمند برای تاریخ‌ها می‌دهد. |
| رزروهای میزبان | `list_host_reserves` | رزروهایی که برای میزبان آمده‌اند را لیست می‌کند. |
| اطلاعات مهمان رزرو | `get_booking_guest` | اطلاعات مهمان یک رزرو را برای میزبان می‌آورد. |

### میزبان — داشبورد، پروفایل، مالی

| نام دوستانه | ابزار فنی | دستیار چه می‌کند؟ |
|-------------|-----------|-------------------|
| داشبورد میزبان | `get_host_dashboard` | خلاصه عملکرد، اعلان‌ها و آمار سریع را می‌آورد. |
| نظرات بی‌پاسخ | `list_unanswered_reviews` | نظرهایی که هنوز پاسخ داده نشده‌اند را نشان می‌دهد. |
| پروفایل میزبانی | `get_my_host_profile` | تنظیمات پروفایل میزبان را می‌خواند. |
| ویرایش پروفایل میزبانی | `update_my_host_profile` | پروفایل میزبان را به‌روز می‌کند. |
| پرداخت‌های میزبان | `list_host_payments` | لیست پرداخت‌های مرتبط با میزبان را نشان می‌دهد. |
| تراکنش‌ها | `list_host_transactions` | تراکنش‌های مالی را لیست می‌کند. |
| تسویه‌ها | `list_host_checkouts` | تسویه/چک‌اوت‌ها را نشان می‌دهد. |
| درخواست‌های برداشت | `list_withdraw_requests` | درخواست‌های برداشت وجه را لیست می‌کند. |
| نوع تسویه | `get_settlement_type` | تنظیم نوع تسویه میزبان را می‌خواند. |
| آمار کلی میزبان | `get_host_statistics` | آمار فروش و عملکرد کلی میزبان را می‌آورد. |
| آمار یک خانه | `get_house_statistics` | آمار یک اقامتگاه مشخص را نشان می‌دهد. |

**جمع ابزارها: ۶۴.**
