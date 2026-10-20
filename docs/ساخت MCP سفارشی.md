## Metadata

- **Model:** `gpt-6`
- **Time:** 2026-10-17 09:31:02 +03:30
- **URL:** https://chatgpt.com/c/6ad30f1d-5da8-83ed-823c-af46601b4b83

## Conversation

### 🧑‍💻 User

این ریپو رو تازه پیدا کردم چطور میشه یه mcp سرور کاستوم ساخت تو توضیح بده من بعدش دقیقا بهت میگم که برای چه پلتفرمی لازمش دارم
https://github.com/sepehr071/awesome-iran-mcp
میخوام یه mcp سرور بنویسم و پول ریکوئست هم بدم بره داخل این ریپو مثلا یه چیزی مثل mcp مربوط به جاباما

### 🤖 Assistant

آره، دقیقاً متوجه چیزی که می‌خوای شدم. این ریپو اتفاقاً مثال خیلی خوبی برای فهمیدن معماریه. خود `awesome-iran-mcp` الان چندین MCP برای سرویس‌های ایرانی دارد و طبق README، برای هر سرویس یک پکیج کوچک می‌سازد که API/endpointهای واقعی سایت را به Toolهای MCP تبدیل می‌کند؛ مثلاً `jabama-mcp` و `digikala-mcp`. [1]

urlawesome-iran-mcp در GitHubhttps://github.com/sepehr071/awesome-iran-mcp

**اول یک نکته مهم: MCP خودش API نیست**

معماری را این‌طوری ببین:

```text
                    ┌─────────────────────┐
                    │   AI Agent / LLM    │
                    │ Claude / Codex /    │
                    │ OpenWebUI / OpenClaw│
                    └──────────┬──────────┘
                               │
                         MCP Protocol
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Your MCP Server   │
                    │                     │
                    │ search_hotels()     │
                    │ get_hotel()         │
                    │ get_rooms()         │
                    │ check_availability()│
                    │ create_booking()    │
                    └──────────┬──────────┘
                               │
                         HTTP requests
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Target Platform   │
                    │                     │
                    │   Jabama API/Web   │
                    │   or any service   │
                    └─────────────────────┘
```

یعنی تو یک **Adapter** می‌سازی.

LLM نمی‌داند جاباما چطور کار می‌کند. فقط می‌بیند:

```text
search_jabama_hotels
get_jabama_hotel
check_jabama_availability
...
```

و MCP Server پشت صحنه درخواست واقعی را به جاباما می‌فرستد.

---

**حالا اگر بخواهی مثلاً Jabama MCP بسازی**

فرض کنیم هدف این باشد:

> «یک MCP Server برای جاباما بسازم و بعد Pull Request بدهم به awesome-iran-mcp.»

اول باید API/رفتار سایت جاباما را Reverse Engineer کنیم.

مثلاً بفهمیم:

```text
GET /api/...
POST /api/...
```

چه requestهایی می‌فرستد، چه headerهایی لازم دارد، response چه شکلی است و authentication لازم است یا نه.

بعد آن‌ها را تبدیل می‌کنیم به MCP tools.

مثلاً:

```text
jabama-mcp/

├── pyproject.toml
├── README.md
├── src/
│   └── jabama_mcp/
│       ├── __init__.py
│       ├── server.py
│       ├── api.py
│       └── models.py
└── tests/
    └── test_jabama.py
```

و مثلاً:

```python
@mcp.tool()
async def search_stays(
    city: str,
    check_in: str,
    check_out: str,
    guests: int = 2,
):
    ...
```

Agent بعداً می‌تواند بگوید:

> Find me a villa in Kish for 3 nights under 5 million toman.

و مدل تصمیم می‌گیرد:

```text
search_stays(
    city="کیش",
    check_in="2026-10-20",
    check_out="2026-10-23",
    guests=2
)
```

MCP Server نتیجه را می‌گیرد و به شکل مناسب به Agent برمی‌گرداند.

---

**چیزی که در این ریپو جالب است**

این پروژه صرفاً یک `server.py` نیست.

ساختار فعلی ریپو نشان می‌دهد که برای هر سرویس یک package جدا دارند و همه را در marketplace/skills هم expose کرده‌اند. مثلاً:

```text
servers/
    jabama-mcp/
    digikala-mcp/
    snappfood-mcp/
    mrbilit-mcp/
    ...
```

و نصب Jabama حتی به این شکل است:

```bash
uvx jabama-mcp
```

و در MCP client:

```json
{
  "mcpServers": {
    "jabama": {
      "command": "uvx",
      "args": ["jabama-mcp"]
    }
  }
}
```

این دقیقاً همان چیزی است که تو اگر بخواهی contribution بدهی باید دنبال کنی. [1]

---

**برای ساخت MCP دو انتخاب اصلی داری**

**1. Python**

برای پروژه‌ای مثل `awesome-iran-mcp` احتمالاً انتخاب خیلی خوبی است، مخصوصاً چون packageهای موجودشان Python هستند.

معماری:

```text
Python
  ↓
MCP SDK
  ↓
Your tools
  ↓
httpx / requests
  ↓
Target API
```

**2. TypeScript**

MCP SDK رسمی TypeScript هم بسیار مناسب است و نسخه فعلی SDK امکان ساخت Server و expose کردن `tools`, `resources` و `prompts` را دارد. برای HTTP هم Streamable HTTP مسیر مدرن SDK است. [2]

مثلاً خیلی ساده:

```typescript
const server = new McpServer({
  name: "jabama",
  version: "1.0.0"
});

server.registerTool(
  "search_stays",
  {
    description: "Search accommodation on Jabama",
    inputSchema: z.object({
      city: z.string(),
      checkIn: z.string(),
      checkOut: z.string(),
      guests: z.number()
    })
  },
  async ({ city, checkIn, checkOut, guests }) => {
    // call Jabama
  }
);
```

SDK رسمی هم دقیقاً همین مدل `registerTool()` را پیشنهاد می‌کند. [3]

---

**اما نکته مهم‌تر برای چیزی که تو می‌خواهی**

تو گفتی:

> «یه MCP سرور بنویسم و پول ریکوئست هم بدم بره داخل این ریپو»

اگر منظورت **Pull Request** است، workflow تقریباً این است:

```text
awesome-iran-mcp
        │
        ▼
Fork
        │
        ▼
Create branch
        │
        ▼
servers/jabama-mcp
        │
        ├── MCP Server
        ├── API client
        ├── Tests
        ├── README
        └── package metadata
        │
        ▼
Run tests
        │
        ▼
Push
        │
        ▼
Pull Request
        │
        ▼
Maintainer review
        │
        ▼
Merge
```

و اگر package در PyPI منتشر شود، حتی می‌تواند در نهایت با:

```bash
uvx jabama-mcp
```

قابل نصب باشد؛ همان الگوی فعلی پروژه. [1]

---

**و یک تفاوت خیلی مهم**

اگر فقط برای **خود AI Lab Pro / OpenWebUI / OpenKyla / Marco Polo** بخواهی MCP بسازی، لازم نیست حتماً وارد این ریپو شوی.

می‌توانیم مثلاً:

```text
jabama-mcp.looply.one
```

یا حتی یک MCP server داخل AI Lab Pro داشته باشیم:

```text
AI Lab Pro
│
├── LiteLLM
├── OpenWebUI
├── n8n
├── OpenClaw
│
└── MCP Gateway
      ├── Jabama
      ├── Digikala
      ├── Search Console
      ├── Google Sheets
      └── ...
```

اما اگر هدفت **open-source contribution** باشد، بهتر است MCP را دقیقاً مطابق conventions همین repository بسازیم.

**پیشنهاد من**

قبل از اینکه حتی یک خط کد بنویسیم، **ساختار `jabama-mcp` فعلی همین repo را کامل بررسی کنیم** و بفهمیم:

- دقیقاً چطور MCP Server نوشته‌اند
- API جاباما را چطور پیدا کرده‌اند
- چه Toolهایی ساخته‌اند
- naming convention چیست
- تست‌ها چطورند
- package چطور publish می‌شود
- `servers.json` چطور update می‌شود
- README چه استانداردی دارد
- Pull Request چه چیزهایی باید داشته باشد

بعد می‌توانیم همان architecture را برای پلتفرمی که مدنظر توست پیاده کنیم.

اگر منظورت از «پول ریکوئست» واقعاً **Pull Request** بوده، بگو پلتفرمی که می‌خواهی MCP آن را بسازیم چیست؛ از صفر تا PR را با هم طراحی می‌کنیم.

### 🧑‍💻 User

خوب متوجه شدم ولی منظورم یه چی دیگه بود من میخوام در قدم اول یه mcp سرور کاستوم برای شرکتی که توش کار میکنم بنویسم یعنی shab.ir من بکند دولوپر شرکتم و به راحتی میتونم سرور بسازم براش پس میتونم یه ریپو برای shab-mcp بسازم و بعد لینکشو پول رک بدم به ریپوی iran mcp

### 🤖 Assistant

دقیقاً. **این کار کاملاً شدنیه** و اتفاقاً برای شروع ساخت MCP یک پروژه خیلی خوبه، چون هم به بک‌اند Shab دسترسی داری و هم می‌تونی APIهای واقعی و قابل‌اعتماد در اختیار MCP قرار بدی.

مدل پیشنهادی:

```text
GitHub
│
├── your-account/shab-mcp
│       │
│       ├── MCP Server
│       ├── Shab API Client
│       ├── Tools
│       ├── README
│       └── Tests
│
└── sepehr071/awesome-iran-mcp
        │
        └── PR
             └── Add shab-mcp
```

یعنی **لازم نیست کد Shab MCP را داخل `awesome-iran-mcp` قرار بدهی.**

تو یک repo مستقل می‌سازی:

```text
github.com/YOUR_USERNAME/shab-mcp
```

و بعد در PR به `awesome-iran-mcp` می‌گویی:

> این یک MCP مستقل برای Shab است و می‌توانید آن را به لیست/collection پروژه اضافه کنید.

---

**حتی بهتر: معماری‌ای که من برای Shab پیشنهاد می‌کنم**

چون خودت Backend Developer هستی، من MCP را مستقیماً به دیتابیس وصل نمی‌کردم.

این:

```text
MCP
 │
 └── MySQL
```

❌

بهتر است:

```text
                 ┌───────────────┐
                 │ AI Agent      │
                 │ Claude/Codex  │
                 │ OpenWebUI     │
                 │ OpenClaw      │
                 └───────┬───────┘
                         │ MCP
                         ▼
                 ┌───────────────┐
                 │   shab-mcp    │
                 │               │
                 │ Tools         │
                 └───────┬───────┘
                         │ HTTPS
                         ▼
                 ┌───────────────┐
                 │ Shab API      │
                 │ Laravel       │
                 └───────┬───────┘
                         │
                ┌────────┴────────┐
                ▼                 ▼
             MySQL             Redis
```

این معماری خیلی تمیزتر است.

---

**چه Toolهایی می‌توانی بسازی؟**

اینجاست که پروژه واقعاً جذاب می‌شود.

مثلاً اگر Shab سیستم رزرو/اقامت است، می‌توانی MCP را با Toolهای read-only شروع کنی:

```text
search_accommodations
get_accommodation
get_accommodation_details
check_availability
search_destinations
get_destination
```

مثلاً Agent می‌گوید:

> برای آخر هفته در رامسر یه اقامتگاه برای ۴ نفر پیدا کن زیر ۵ میلیون.

LLM خودش تصمیم می‌گیرد:

```text
search_accommodations(
    destination="رامسر",
    guests=4,
    max_price=5000000
)
```

و MCP:

```text
→ Shab API
→ دریافت نتایج
→ normalize
→ MCP response
→ LLM
```

---

**بعداً می‌توانی Action هم اضافه کنی**

مثلاً:

```text
get_user_bookings
get_booking
create_booking
cancel_booking
```

ولی این‌ها را من **از همان اول اضافه نمی‌کنم**.

برای نسخه اول:

```text
v0.1
├── search
├── details
├── availability
└── destinations
```

بعد:

```text
v0.2
├── user bookings
└── booking details
```

و در نهایت:

```text
v1.0
├── search
├── availability
├── booking
├── cancellation
├── user profile
└── ...
```

چون Toolهایی که عملیات واقعی انجام می‌دهند، مخصوصاً booking/cancel، نیاز به authentication، authorization، confirmation و audit دارند.

---

**یک نکته خیلی مهم برای Shab**

اگر API داخلی فعلی Shab مناسب MCP نیست، **لازم نیست MCP را مجبور کنیم مستقیماً با APIهای فعلی کار کند.**

می‌توانی یک API مخصوص integration ایجاد کنی:

```text
api.shab.ir
       │
       ├── /v1/search
       ├── /v1/accommodations/{id}
       ├── /v1/availability
       └── /v1/bookings
```

و:

```text
shab-mcp
    ↓
Shab Integration API
    ↓
Core Shab
```

این در بلندمدت خیلی بهتر است.

---

**و بله، بعداً PR می‌دهی**

مثلاً:

```text
github.com/mohamadreza/shab-mcp
```

و در `awesome-iran-mcp` چیزی شبیه:

```text
## Shab

AI tools for interacting with Shab accommodation services.

Repository:
https://github.com/mohamadreza/shab-mcp
```

قرار می‌گیرد.

پس ownership این شکلی است:

```text
                 ┌─────────────────────┐
                 │   Shab Organization │
                 │                     │
                 │   shab-mcp          │
                 └──────────┬──────────┘
                            │
                            │ referenced by
                            ▼
                 ┌─────────────────────┐
                 │   awesome-iran-mcp  │
                 │                     │
                 │   🇮🇷 Shab MCP       │
                 └─────────────────────┘
```

---

**و یک ایده حتی بهتر برای تو**

با توجه به کاری که الان روی **AI Lab Pro + OpenWebUI + OpenClaw + MCP** انجام می‌دهی، من Shab MCP را فقط به چشم یک contribution نمی‌بینم.

می‌توانی آن را تبدیل کنی به **اولین MCP واقعی production-grade خودت**.

یعنی از همان اول این موارد را رعایت کنیم:

- Type-safe input/output
- Authentication
- Authorization
- Rate limiting
- Structured errors
- Logging
- Sentry
- Tests
- Docker
- CI
- README حرفه‌ای
- MCP Inspector testing
- Security boundaries
- Read-only tools در نسخه اول
- API versioning

بعد همان تجربه را برای Looply و سرویس‌های دیگر هم استفاده کنی.

**اگر موافقی، قدم بعدی اینه که خود `shab.ir` و معماری فعلی بک‌اندش را بررسی کنیم و مشخص کنیم اولین نسخه `shab-mcp` دقیقاً چه Toolهایی باید داشته باشد و چه APIهایی را expose کنیم.**

### 🧑‍💻 User

من میخوام یه mcp شخصی در ابتدا برای خود شب بسازم که اول فرانت اند و مارکومولو در صورت نیاز ازش استفاده کنن و اگه اوکی بود توی کل شرکت پابلیشش کنیم و حالا بعدا اگه تصمیم گرفتن پابلیک میکنیم پس در قدم اول پرایویته

api های شب خوبن و نسخه بندی شدن و برای ساخت نسخه اولیه کفایت میکنه

میخوام کلا راهنماییم کنی که چطور میتونم از صفر یه mcp برای شرکت بسازم روی ai lab pro دیپلوی کنم به litellm اضافش کنم سپس به openwebui و در نهایت به مارکوپولو
یه چیزی هم توضیح بده که الان فرق mcp با mcp server چیه ما الان کدوم رو باید بسازیم و ستاپ کنیم ایا هردوتاشم لازمه؟

پس در قدم اول همانطور که خودت گفتی از tool های ریدانلی شروع کنیم میتونی از mcp مشابه جاباما کمک بگیری
https://github.com/sepehr071/jabama-mcp

اره این mcp رو باید پروداکشن گرید بزنیم ولی همون اول کار همه فیچرارو لازم ندارم

### 🤖 Assistant

بله؛ الان scope کاملاً مشخص شد. **این پروژه را باید مثل یک سرویس داخلی production-grade طراحی کنیم، ولی MVP آن کوچک و read-only باشد.** برای شروع هم لازم نیست public کنیم یا به `awesome-iran-mcp` وصلش کنیم.

> این کار از نظر فرآیند یک کار **architectural** است؛ فعلاً طراحی را مشخص می‌کنیم و بعد از تأیید تو وارد implementation plan و کدنویسی می‌شویم. [4]

من مستندات فعلی LiteLLM/Open WebUI و ساختار `jabama-mcp` را هم بررسی کردم. `jabama-mcp` برای الگوی Tool design، typed async functions، تست offline/live و جداسازی فایل‌ها الگوی خوبی است. [5]

---

**1. اول مهم‌ترین سؤال: MCP و MCP Server چه فرقی دارند؟**

اینجا یک اشتباه رایج وجود دارد.

**MCP**

**Model Context Protocol** یک **پروتکل/استاندارد** است.

مثل HTTP.

HTTP خودش یک سرور نیست.

```text
HTTP
 ↓
یک protocol برای ارتباط
```

MCP هم:

```text
MCP
 ↓
protocol برای ارتباط Agent/Host با Tool/Resource/Prompt
```

---

**MCP Server**

چیزی است که **تو می‌سازی**.

مثلاً:

```text
shab-mcp
```

این برنامه MCP Protocol را پیاده می‌کند و Toolهای Shab را در اختیار Client قرار می‌دهد.

مثلاً:

```text
shab-mcp

Tools:
  search_accommodations
  get_accommodation
  check_availability
  get_destination
```

بنابراین:

```text
MCP              = Protocol
MCP Server       = Application implementing that protocol
MCP Client       = چیزی که به Server وصل می‌شود
MCP Host         = اپلیکیشنی که Client را در خودش اجرا می‌کند
```

پس **تو الان باید MCP Server بسازی.**

لازم نیست جداگانه چیزی به اسم "MCP" بسازی.

---

**2. معماری نهایی که برای Shab پیشنهاد می‌کنم**

با توجه به AI Lab Pro فعلی شما، من این architecture را پیشنهاد می‌کنم:

```text
                         ┌──────────────────────┐
                         │       Users          │
                         └──────────┬───────────┘
                                    │
                              Open WebUI
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │       LiteLLM        │
                         │                      │
                         │ LLM Gateway          │
                         │ MCP Gateway           │
                         │ Auth / Access         │
                         │ Logging              │
                         └──────────┬───────────┘
                                    │
                              MCP Protocol
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │       shab-mcp       │
                         │                      │
                         │ MCP Server           │
                         │                      │
                         │ search_*              │
                         │ get_*                 │
                         │ availability_*        │
                         └──────────┬───────────┘
                                    │
                                  HTTPS
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │       Shab API       │
                         │       Laravel         │
                         └──────────────────────┘
```

و در سمت Agent داخلی:

```text
Marco Polo
     │
     ▼
 LiteLLM MCP Gateway
     │
     ▼
  shab-mcp
     │
     ▼
  Shab API
```

این معماری یک مزیت خیلی مهم دارد:

**هیچ Agent مستقیماً به Shab API وصل نمی‌شود.**

همه از یک Gateway رد می‌شوند.

---

**3. چرا MCP را پشت LiteLLM قرار بدهیم؟**

این قسمت برای AI Lab Pro شما خیلی مهم است.

LiteLLM الان خودش MCP Gateway دارد و می‌تواند چند MCP Server را پشت یک endpoint جمع کند و access را بر اساس Key/Team کنترل کند. [6]

یعنی بعداً:

```text
LiteLLM MCP Gateway

        │
        ├── shab
        ├── google-sheets
        ├── search-console
        ├── metabase
        ├── ...
        └── future MCPs
```

و مثلاً برای Marco Polo:

```text
Marco Polo
     │
     │ MCP
     ▼
https://litellm.looply.one/mcp
     │
     ├── shab
     ├── ...
     └── ...
```

LiteLLM هم access control و هم key/team permission دارد. [7]

بنابراین **MCP Server را به LiteLLM تبدیل نمی‌کنیم.**

دو سرویس جدا داریم:

```text
shab-mcp
   ↓
business integration

LiteLLM
   ↓
AI/MCP gateway
```

---

**4. آیا OpenWebUI باید مستقیماً به shab-mcp وصل شود؟**

از نظر فنی **می‌تواند**.

Open WebUI جدیداً MCP را به‌صورت native با Streamable HTTP پشتیبانی می‌کند. [8]

اما برای معماری شما من پیشنهاد می‌کنم:

```text
OpenWebUI
    ↓
LiteLLM MCP Gateway
    ↓
shab-mcp
```

نه:

```text
OpenWebUI
    ↓
shab-mcp
```

چرا؟

چون اگر فردا ۱۰ MCP داشته باشید، نمی‌خواهیم OpenWebUI این شکلی شود:

```text
OpenWebUI
 ├── Shab
 ├── Google Sheets
 ├── Search Console
 ├── Metabase
 ├── ...
```

بلکه:

```text
OpenWebUI
      ↓
   LiteLLM
      ↓
   MCP Gateway
      ↓
  ┌───┼────┬────┐
 Shab Sheets Search Metabase
```

مرکز کنترل MCP می‌شود LiteLLM.

---

**5. اما یک نکته مهم درباره LiteLLM**

LiteLLM دو نقش متفاوت دارد:

**نقش اول**

LLM Gateway:

```text
OpenWebUI
    ↓
LiteLLM
    ↓
GPT / Claude / Gemini / ...
```

**نقش دوم**

MCP Gateway:

```text
Agent
    ↓
LiteLLM
    ↓
MCP Servers
```

این دو تا می‌توانند همزمان وجود داشته باشند.

و اتفاقاً برای AI Lab Pro شما خیلی منطقی است.

---

**6. خود shab-mcp را چطور بسازیم؟**

من برای نسخه اول **Python + FastMCP** را پیشنهاد می‌کنم.

ساختار چیزی شبیه:

```text
shab-mcp/
│
├── src/
│   └── shab_mcp/
│       │
│       ├── server.py
│       ├── config.py
│       │
│       ├── client/
│       │   ├── __init__.py
│       │   └── shab_api.py
│       │
│       ├── tools/
│       │   ├── accommodations.py
│       │   ├── availability.py
│       │   └── destinations.py
│       │
│       ├── models/
│       │   ├── accommodation.py
│       │   └── search.py
│       │
│       └── errors.py
│
├── tests/
│   ├── fixtures/
│   ├── test_accommodations.py
│   ├── test_availability.py
│   └── test_server.py
│
├── Dockerfile
├── compose.yaml
├── pyproject.toml
├── README.md
├── .env.example
└── LICENSE
```

تقریباً همان philosophy پروژه Jabama، ولی متناسب با API واقعی Shab.

Jabama هم Toolها را به فایل‌های domain-oriented تقسیم کرده و برای توابع از typed async functions و docstringهای مشخص استفاده می‌کند. [5]

---

**7. MVP ما چه چیزهایی دارد؟**

من **اصلاً پیشنهاد نمی‌کنم از ۲۰ Tool شروع کنیم.**

نسخه اول:

**Search**

```text
search_accommodations
```

مثلاً:

```json
{
  "destination": "رامسر",
  "check_in": "2026-10-25",
  "check_out": "2026-10-27",
  "guests": 2
}
```

---

**Details**

```text
get_accommodation
```

مثلاً:

```json
{
  "accommodation_id": 12345
}
```

---

**Availability**

```text
check_availability
```

---

**Destination**

```text
search_destinations
```

یا اگر API Shab endpoint مناسب داشته باشد:

```text
get_destination
```

---

پس MVP:

```text
shab-mcp v0.1

├── search_accommodations
├── get_accommodation
├── check_availability
└── search_destinations
```

**تمام.**

هیچ:

```text
booking
payment
cancel
modify
user account
```

در v0.1 نداریم.

---

**8. ولی Production-grade یعنی چه؟**

Production-grade الزاماً به معنی "خیلی feature زیاد" نیست.

این دو را جدا کنیم:

```text
Feature scope
     ↓
Small
```

اما:

```text
Engineering quality
     ↓
Production-grade
```

یعنی همین ۴ Tool را درست بسازیم.

مثلاً:

**Type safety**

```python
async def search_accommodations(
    destination: str,
    check_in: date,
    check_out: date,
    guests: int,
) -> ...
```

---

**Validation**

مثلاً:

```text
check_out > check_in
guests >= 1
```

---

**Error handling**

نه اینکه API Shab خطا داد:

```text
500 Internal Server Error
```

به Agent برگردد.

بلکه:

```text
Shab API temporarily unavailable.
Please retry later.
```

---

**Timeout**

مثلاً:

```text
connect timeout: 5s
read timeout: 20s
```

---

**Retry**

فقط برای خطاهای مناسب.

---

**Logging**

مثلاً:

```text
tool=search_accommodations
duration=842ms
status=success
```

ولی اطلاعات حساس را log نکنیم.

---

**Observability**

در AI Lab Pro شما Sentry/monitoring دارید، پس بعداً می‌توانیم:

```text
shab-mcp
   ↓
Sentry
   ↓
Grafana / logs
```

را هم داشته باشیم.

---

**9. مهم‌ترین قسمت: API Client را از MCP جدا کنیم**

این را خیلی جدی پیشنهاد می‌کنم.

بد:

```text
MCP Tool
   ↓
requests.get(...)
   ↓
Shab
```

بهتر:

```text
MCP Tool
   ↓
ShabAPIClient
   ↓
Shab API
```

مثلاً:

```python
class ShabAPIClient:

    async def search_accommodations(...):
        ...

    async def get_accommodation(...):
        ...

    async def check_availability(...):
        ...
```

بعد Tool:

```python
@mcp.tool()
async def search_accommodations(...):

    result = await shab_api.search_accommodations(...)

    return normalize(result)
```

این separation باعث می‌شود بعداً اگر API عوض شد، MCP Toolها را دست نزنیم.

---

**10. Response را هم باید برای LLM طراحی کنیم**

این خیلی مهم است.

قرار نیست raw API Shab را به مدل بدهیم.

مثلاً اگر API برگرداند:

```json
{
  "data": {
    "items": [...],
    "meta": {...},
    "internal_x": "...",
    "tracking": "...",
    ...
  }
}
```

نباید همان را بفرستیم.

MCP باید:

```text
Shab API Response
       ↓
Normalizer
       ↓
LLM-friendly structured response
```

بسازد.

مثلاً:

```json
{
  "results": [
    {
      "id": "12345",
      "title": "ویلا استخردار رامسر",
      "location": "رامسر",
      "rating": 4.8,
      "price_per_night": 3200000,
      "currency": "IRR",
      "capacity": 6,
      "available": true
    }
  ]
}
```

این قسمت یکی از مهم‌ترین ارزش‌های MCP شما خواهد بود.

---

**11. Deployment روی AI Lab Pro**

در AI Lab Pro من یک container جدا برایش می‌گذارم:

```text
AI Lab Pro Server

├── nginx
├── litellm
├── openwebui
├── n8n
├── postgres
├── redis
├── grafana
├── minio
│
└── shab-mcp
```

مثلاً:

```text
shab-mcp:8000
```

و فقط شبکه داخلی:

```text
Docker network
       │
       ├── LiteLLM
       │
       └── shab-mcp
```

**فعلاً public expose نمی‌کنیم.**

این خیلی مهم است.

---

**12. بعد MCP Transport**

برای deployment مرکزی من **Streamable HTTP** را انتخاب می‌کنم.

نه stdio.

Jabama چون برای clientهایی مثل Claude/Cursor طراحی شده، stdio دارد:

```text
Claude
 ↓
process
 ↓
jabama-mcp
```

[5]

اما ما داریم:

```text
OpenWebUI
       ↓
       HTTP
       ↓
LiteLLM
       ↓
       HTTP
       ↓
shab-mcp
```

پس Streamable HTTP برای deployment مرکزی مناسب‌تر است.

LiteLLM هم Streamable HTTP، SSE و stdio را پشتیبانی می‌کند. [6]

---

**13. مسیر تست ما**

من این پروژه را یکباره تا Marco Polo نمی‌برم.

مرحله‌ای:

```text
PHASE 1
Local development
        ↓
MCP Inspector
        ↓
Tools work?
```

بعد:

```text
PHASE 2
Docker
        ↓
AI Lab Pro
        ↓
Internal network
```

بعد:

```text
PHASE 3
LiteLLM MCP Gateway
        ↓
shab
```

بعد:

```text
PHASE 4
OpenWebUI
        ↓
LiteLLM MCP
        ↓
Shab
```

بعد:

```text
PHASE 5
Marco Polo
        ↓
LiteLLM MCP
        ↓
Shab
```

این ترتیب خیلی مهم است.

اگر Marco Polo کار نکرد، نمی‌خواهیم ندانیم مشکل:

```text
Marco Polo
LiteLLM
OpenWebUI
MCP
Docker
Shab API
```

کجاست.

---

**14. معماری نهایی**

در نهایت:

```text
                         ┌───────────────┐
                         │   OpenWebUI   │
                         └───────┬───────┘
                                 │
                                 │ MCP
                                 ▼
                         ┌───────────────┐
                         │    LiteLLM    │
                         │               │
                         │ MCP Gateway   │
                         │ Auth          │
                         │ Permissions   │
                         │ Logging       │
                         └───────┬───────┘
                                 │
                       Streamable HTTP
                                 │
                                 ▼
                         ┌───────────────┐
                         │   shab-mcp    │
                         │               │
                         │ 4 read tools  │
                         └───────┬───────┘
                                 │
                              HTTPS
                                 │
                                 ▼
                         ┌───────────────┐
                         │   Shab API    │
                         └───────────────┘


                         ┌───────────────┐
                         │  Marco Polo   │
                         └───────┬───────┘
                                 │
                                 ▼
                         ┌───────────────┐
                         │    LiteLLM    │
                         │  MCP Gateway  │
                         └───────┬───────┘
                                 │
                                 ▼
                             shab-mcp
```

و بعداً:

```text
                    LiteLLM MCP Gateway
                            │
          ┌─────────────────┼──────────────────┐
          ▼                 ▼                  ▼
      shab-mcp         search-console      google-sheets
```

---

**15. Public شدن فعلاً کاملاً منتفی**

این هم به نظرم تصمیم درستی است.

نسخه اول:

```text
GitHub
   │
   └── private shab-mcp
```

و:

```text
AI Lab Pro
   │
   └── private MCP
```

بعد اگر تیم Shab تأیید کرد:

```text
private
   ↓
internal company
   ↓
public?
```

و اگر یک روز خواستیم public کنیم، آن موقع جداگانه درباره:

- public GitHub repo
- documentation
- authentication model
- rate limits
- legal/licensing
- MCP Registry
- `awesome-iran-mcp`

تصمیم می‌گیریم.

---

**بنابراین چیزی که الان می‌خواهیم بسازیم**

**`shab-mcp v0.1`**

```text
Language:       Python
Transport:      Streamable HTTP
Deployment:     Docker
Location:       AI Lab Pro
Access:         Private
Gateway:        LiteLLM
First client:   OpenWebUI
Second client:  Marco Polo
API:            Existing versioned Shab APIs
Capabilities:   Read-only
Tools:          ~4
Architecture:   API Client → MCP Tools
Quality:        Production-grade
Public:         No
```

این scope به نظرم **دقیقاً اندازه مناسب** برای اولین MCP واقعی Shab است؛ نه یک prototype اسباب‌بازی، نه یک پروژه‌ای که از روز اول ۳۰ feature داشته باشد.

**اگر همین معماری و scope را تأیید می‌کنی، مرحله بعدی من باید یک Spec دقیق برای `shab-mcp v0.1` بنویسم**؛ در آن مشخص می‌کنیم دقیقاً Toolها چه نامی دارند، input/output هرکدام چیست، Docker و transport چطورند، authentication کجا قرار می‌گیرد و integration با LiteLLM/OpenWebUI/Marco Polo دقیقاً چه شکلی خواهد بود. بعد از تأیید آن Spec، می‌رویم سراغ implementation plan و سپس کدنویسی.

### 🧑‍💻 User

تاییده اسپک و پلن رو بساز ولی کدنویسی نکن بزار بعدا

### 🤖 Assistant

Data analysis isn't available right now. Do you want to continue without it?

### 🧑‍💻 User

تاییده اسپک و پلن رو بساز ولی کدنویسی نکن بزار بعدا

### 🤖 Assistant

حتماً. کدنویسی را فعلاً انجام نمی‌دهم. بر اساس scope‌ای که تأیید کردی، دو خروجی می‌سازم: **Spec معماری** و **Implementation Plan**. این مرحله فقط طراحی و برنامه‌ریزی است و هیچ فایل/کدی را تغییر نمی‌دهیم. طبق فرآیند معماری، بعد از این مرحله اگر Spec و Plan را تأیید کنی، اجرای آن جداگانه شروع می‌شود. [9]

**1. Spec — `shab-mcp v0.1`**

**Shab MCP v0.1 — Technical Specification**

**1. Goal**

Build a private, production-grade MCP Server for Shab that exposes a small set of read-only Shab capabilities to AI agents.

The first consumers are:

1. Shab frontend/AI integrations where useful
2. Marco Polo
3. OpenWebUI users through the AI Lab Pro infrastructure

The MCP must initially remain private and must not depend on public distribution or the `awesome-iran-mcp` repository.

Future public release is explicitly out of scope for v0.1.

---

**2. Scope**

**In scope**

- Private MCP Server
- Python implementation
- Streamable HTTP transport
- Docker deployment
- Existing versioned Shab APIs as the backend
- Read-only tools
- Typed input validation
- Typed/structured outputs
- Error normalization
- Timeout and retry handling
- Logging
- Health/readiness endpoint where appropriate
- Unit tests
- MCP-level tests
- Docker-based local/AI Lab Pro deployment
- LiteLLM MCP Gateway integration
- OpenWebUI integration
- Marco Polo integration
- Internal authentication between infrastructure components

**Out of scope**

- Booking creation
- Booking cancellation
- Payment
- User account mutation
- Public API
- Public GitHub repository
- MCP Registry publishing
- `awesome-iran-mcp` Pull Request
- Full Shab API coverage
- Autonomous transactional actions

---

**3. Architecture**

```text
                     ┌─────────────────────┐
                     │      OpenWebUI      │
                     └──────────┬──────────┘
                                │
                                │ MCP
                                ▼
                     ┌─────────────────────┐
                     │       LiteLLM       │
                     │                     │
                     │   MCP Gateway       │
                     │   Access Control    │
                     │   Authentication    │
                     └──────────┬──────────┘
                                │
                         Streamable HTTP
                                │
                                ▼
                     ┌─────────────────────┐
                     │      shab-mcp       │
                     │                     │
                     │  MCP Server         │
                     │                     │
                     │  Read-only Tools    │
                     └──────────┬──────────┘
                                │
                               HTTPS
                                │
                                ▼
                     ┌─────────────────────┐
                     │      Shab API       │
                     │      Laravel        │
                     └─────────────────────┘
```

Marco Polo follows the same gateway path:

```text
Marco Polo
    │
    ▼
 LiteLLM MCP Gateway
    │
    ▼
 shab-mcp
    │
    ▼
 Shab API
```

The MCP Server must not access the Shab database directly.

---

**4. Architectural principles**

**4.1 API-first integration**

The MCP uses existing versioned Shab APIs.

```text
MCP Tool
   ↓
Shab API Client
   ↓
Shab API
```

The MCP must not duplicate Shab business logic unnecessarily.

---

**4.2 No direct database access**

The MCP must never depend on:

- MySQL
- Redis
- internal database tables
- Laravel Eloquent models

Its contract is the Shab API.

This keeps the MCP independently deployable and prevents tight coupling to Shab's internal persistence layer.

---

**4.3 Separation between API client and MCP tools**

The codebase must separate:

```text
MCP layer
     ↓
Domain/API client
     ↓
HTTP
     ↓
Shab API
```

This allows API implementation details to change without changing the MCP interface exposed to models.

---

**5. Technology**

**Language**

Python

**MCP**

Official Python MCP SDK / FastMCP-compatible implementation.

**HTTP client**

Async HTTP client such as `httpx`.

**Validation**

Typed models using Pydantic where appropriate.

**Packaging**

`pyproject.toml`

**Runtime**

Python 3.x

**Deployment**

Docker

**Transport**

Streamable HTTP

**Gateway**

LiteLLM MCP Gateway

---

**6. Initial tools**

The first release should contain approximately four tools.

The exact Shab endpoints will be mapped during implementation after inspecting the current API contracts.

**6.1 `search_accommodations`**

Purpose:

Search available Shab accommodations based on user criteria.

Potential input:

```json
{
  "destination": "رامسر",
  "check_in": "2026-10-25",
  "check_out": "2026-10-27",
  "guests": 2
}
```

Potential optional filters:

- price range
- accommodation type
- capacity
- rating
- amenities

Only parameters actually supported by Shab APIs should be exposed.

---

**6.2 `get_accommodation`**

Purpose:

Retrieve structured details for one accommodation.

Potential input:

```json
{
  "accommodation_id": "12345"
}
```

Expected information may include:

- title
- location
- description
- capacity
- amenities
- rating
- images where useful
- pricing information where supported
- metadata necessary for follow-up availability queries

Internal API fields that are irrelevant to an AI agent must not be exposed.

---

**6.3 `check_availability`**

Purpose:

Check whether an accommodation is available for a specific date range and guest count.

Potential input:

```json
{
  "accommodation_id": "12345",
  "check_in": "2026-10-25",
  "check_out": "2026-10-27",
  "guests": 2
}
```

This tool is read-only.

It must not create a reservation or hold inventory.

---

**6.4 `search_destinations`**

Purpose:

Resolve or search destinations supported by Shab.

Potential input:

```json
{
  "query": "رامسر"
}
```

This tool helps the LLM convert natural-language destinations into IDs or canonical Shab destinations before performing accommodation searches.

---

**7. Tool design principles**

Tool names must be:

- explicit
- action-oriented
- understandable to an LLM
- stable
- independent from internal endpoint names

Avoid exposing raw REST endpoint names such as:

```text
GET /api/v2/foo/search
```

The MCP abstraction should represent user intent instead.

---

**8. Response design**

Raw Shab API responses must not automatically be returned to the LLM.

The MCP should normalize responses.

Example:

```json
{
  "results": [
    {
      "id": "12345",
      "title": "ویلا استخردار رامسر",
      "location": "رامسر",
      "capacity": 6,
      "rating": 4.8,
      "price_per_night": 3200000,
      "currency": "IRR",
      "available": true
    }
  ]
}
```

The response should prioritize:

1. Information useful to the model
2. Stable fields
3. Small payloads
4. Human-readable values
5. IDs required for follow-up tools

Internal tracking data, unnecessary metadata and implementation-specific fields should be removed.

---

**9. Error handling**

The MCP must normalize Shab API failures.

Examples:

```text
Authentication failure
→ SHAB_AUTHENTICATION_ERROR

Validation failure
→ SHAB_VALIDATION_ERROR

Not found
→ SHAB_NOT_FOUND

Rate limited
→ SHAB_RATE_LIMITED

Upstream unavailable
→ SHAB_UPSTREAM_UNAVAILABLE

Timeout
→ SHAB_TIMEOUT

Unknown upstream error
→ SHAB_UPSTREAM_ERROR
```

The model should receive an actionable error message rather than raw HTTP responses or stack traces.

---

**10. Reliability**

The API client must define:

- connection timeout
- read timeout
- total request timeout where appropriate
- retry policy
- retryable status codes
- maximum retry count

Retries must not be used blindly.

Read-only requests are safer candidates for retry than future transactional operations.

---

**11. Security**

The initial server is private.

The following boundaries must exist:

```text
OpenWebUI
      ↓
LiteLLM
      ↓
shab-mcp
      ↓
Shab API
```

No direct public exposure is required.

Secrets must be provided through environment variables or the deployment secret mechanism.

Never hard-code:

- API keys
- tokens
- credentials
- internal URLs containing secrets

Logs must not contain credentials or sensitive user data.

---

**12. Authentication model**

For v0.1:

**MCP access**

Access to `shab-mcp` should be restricted to the AI Lab Pro/LiteLLM environment.

**Shab API access**

The MCP authenticates against the Shab API using a dedicated service credential.

The credential should represent the MCP integration rather than an individual employee.

This gives us:

```text
AI Agent
   ↓
LiteLLM identity
   ↓
MCP identity
   ↓
Shab API service identity
```

Fine-grained user authorization can be introduced later when transactional/user-specific tools are added.

---

**13. Deployment**

`shab-mcp` will run as a separate Docker container in AI Lab Pro.

Conceptually:

```text
AI Lab Pro

├── nginx
├── litellm
├── openwebui
├── n8n
├── postgres
├── redis
├── grafana
├── minio
└── shab-mcp
```

The MCP should communicate with LiteLLM over the internal Docker/network path where possible.

The Shab API connection should use HTTPS.

---

**14. Observability**

The server must support structured logs.

Useful fields include:

```text
tool
request_id
duration
status
upstream_status
error_type
```

Sensitive request/response payloads must not automatically be logged.

Sentry integration should be designed so it can be enabled without changing application behavior.

---

**15. Testing strategy**

Testing must exist at several levels.

**Unit tests**

Test:

- validation
- API client behavior
- response normalization
- error mapping
- retry behavior

**MCP tests**

Verify:

- tool registration
- tool schemas
- valid calls
- invalid calls
- structured responses

**Integration tests**

Verify communication with a real/test Shab API where practical.

Live tests should not be required for every CI run if they depend on production credentials.

---

**16. Development flow**

```text
Local
  ↓
MCP Inspector
  ↓
Unit tests
  ↓
Docker
  ↓
AI Lab Pro
  ↓
LiteLLM
  ↓
OpenWebUI
  ↓
Marco Polo
```

Each integration must be tested independently before proceeding to the next one.

---

**17. Versioning**

Initial:

```text
shab-mcp v0.1.x
```

The MCP version is independent from Shab API versions.

The server must internally target explicit Shab API versions.

Example:

```text
shab-mcp 0.1.0
      ↓
Shab API v2
```

A future Shab API version change should be handled deliberately rather than silently changing MCP behavior.

---

**18. Future scope**

After v0.1 is validated:

```text
v0.2
├── user bookings
└── booking details

v0.3
├── authenticated user context
└── additional read-only capabilities

v0.4+
├── booking creation
├── cancellation
└── other transactional actions
```

Transactional tools require a separate security/authorization design.

---

**19. Public release**

Not part of v0.1.

If Shab later decides to open-source the MCP:

```text
Private shab-mcp
       ↓
Security review
       ↓
Documentation review
       ↓
License decision
       ↓
Public GitHub
       ↓
MCP Registry / ecosystem
       ↓
awesome-iran-mcp PR
```

No public dependency should be introduced into the private implementation merely to prepare for this possibility.

---

**20. Definition of Done for v0.1**

The first release is successful when:

- shab-mcp runs locally
- all initial read-only tools work
- tools are validated and typed
- errors are normalized
- tests pass
- Docker deployment works
- the server runs privately on AI Lab Pro
- LiteLLM can reach the MCP
- OpenWebUI can use the tools through LiteLLM
- Marco Polo can use the tools through LiteLLM
- no booking/payment/mutation capability exists
- no public exposure exists
- logs and failures are observable

---

**2. Implementation Plan**

برای Plan هم عمداً آن را به چند مرحله مستقل شکستم تا اگر مثلاً MCP Server آماده شد ولی integration با LiteLLM مشکل داشت، بتوانیم همان بخش را جداگانه تست کنیم. این مطابق اصول implementation planning برای کارهای چندمرحله‌ای است. [10]

**Shab MCP v0.1 Implementation Plan**

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and deploy a private production-grade read-only MCP Server for Shab and integrate it progressively with AI Lab Pro, LiteLLM, OpenWebUI, and Marco Polo.

**Architecture:** A standalone Python MCP Server communicates with versioned Shab APIs through a dedicated async API client. The MCP is deployed as a Docker service inside AI Lab Pro and exposed to consumers through LiteLLM's MCP Gateway rather than directly exposing the Shab service to each AI client.

**Tech Stack:** Python, MCP SDK/FastMCP, Pydantic, httpx, pytest, Docker, LiteLLM, OpenWebUI, Marco Polo.

**Spec:** Shab MCP v0.1 Technical Specification

**Global Constraints**

- Keep the repository private.
- Do not modify or publish `awesome-iran-mcp`.
- Do not implement booking/payment/cancellation.
- Do not access the Shab database directly.
- Use existing versioned Shab APIs.
- Keep MCP tools separate from the Shab API client.
- Use Streamable HTTP for the deployed MCP server.
- Keep the first release to approximately four read-only tools.
- Do not expose the MCP publicly.
- Do not start implementation until this plan is explicitly approved.

---

**Phase 1 — Repository and architecture setup**

**Task 1. Create the repository**

- [ ] Create private `shab-mcp` repository.
- [ ] Add initial README.
- [ ] Add `.gitignore`.
- [ ] Add `.env.example`.
- [ ] Add Python project metadata.
- [ ] Define supported Python version.
- [ ] Add test configuration.
- [ ] Verify a clean environment can install the project.

**Verification**

The repository installs successfully and the test runner starts with zero tests failing.

---

**Task 2. Establish project structure**

Create focused modules for:

```text
src/shab_mcp/
├── server.py
├── config.py
├── client/
├── tools/
├── models/
└── errors.py
```

- [ ] Keep MCP registration in the server layer.
- [ ] Keep HTTP communication in the API client.
- [ ] Keep tool-specific orchestration in tool modules.
- [ ] Keep request/response models separate from transport code.
- [ ] Keep configuration separate from business logic.

**Verification**

Importing the application does not create network requests or require production credentials.

---

**Phase 2 — Shab API client**

**Task 3. Define Shab API configuration**

- [ ] Define base URL.
- [ ] Define API version.
- [ ] Define service authentication configuration.
- [ ] Define connect/read/request timeouts.
- [ ] Define retry settings.
- [ ] Ensure secrets come only from environment/configuration.

**Verification**

The application can load configuration with fake credentials in tests.

---

**Task 4. Implement async HTTP client**

- [ ] Implement reusable `ShabAPIClient`.
- [ ] Configure connection pooling.
- [ ] Configure timeouts.
- [ ] Implement authentication headers.
- [ ] Implement common request handling.
- [ ] Implement status/error mapping.
- [ ] Implement safe retry behavior.

**Verification**

Unit tests cover successful responses, timeout, retryable errors and non-retryable errors.

---

**Phase 3 — First Shab domain**

**Task 5. Implement accommodation search**

- [ ] Map the relevant Shab API endpoint.
- [ ] Define typed request model.
- [ ] Define normalized response model.
- [ ] Implement API client method.
- [ ] Implement `search_accommodations` MCP tool.
- [ ] Validate dates and guest count.
- [ ] Prevent raw internal API fields from leaking into the tool response.

**Verification**

A mocked API response produces the expected MCP response.

---

**Task 6. Implement accommodation details**

- [ ] Map Shab accommodation-details endpoint.
- [ ] Define request model.
- [ ] Define response model.
- [ ] Implement client method.
- [ ] Implement `get_accommodation`.
- [ ] Map not-found errors.

**Verification**

Valid IDs return normalized accommodation information and invalid IDs return a structured error.

---

**Phase 4 — Availability**

**Task 7. Implement availability**

- [ ] Map the Shab availability endpoint.
- [ ] Define request model.
- [ ] Validate date range.
- [ ] Validate guest count.
- [ ] Implement client method.
- [ ] Implement `check_availability`.
- [ ] Ensure this tool performs no mutation.

**Verification**

Availability success, unavailable inventory, invalid dates and upstream failures are covered by tests.

---

**Phase 5 — Destination resolution**

**Task 8. Implement destination search**

- [ ] Identify the appropriate Shab destination endpoint.
- [ ] Define request/response models.
- [ ] Implement client method.
- [ ] Implement `search_destinations`.
- [ ] Return canonical IDs/names where available.

**Verification**

Natural destination queries return usable canonical Shab destinations.

---

**Phase 6 — MCP server**

**Task 9. Register tools**

- [ ] Create MCP server.
- [ ] Register the four tools.
- [ ] Add concise tool descriptions.
- [ ] Add parameter descriptions.
- [ ] Ensure schemas are LLM-friendly.
- [ ] Ensure tool descriptions explain important constraints.
- [ ] Configure Streamable HTTP transport.

**Verification**

MCP Inspector can discover all four tools and their schemas.

---

**Task 10. MCP-level tests**

- [ ] Test tool discovery.
- [ ] Test valid tool invocation.
- [ ] Test invalid inputs.
- [ ] Test structured errors.
- [ ] Test normalized outputs.
- [ ] Test that tools do not unexpectedly call unrelated APIs.

**Verification**

All MCP tests pass without requiring production credentials.

---

**Phase 7 — Dockerization**

**Task 11. Build production Docker image**

- [ ] Create Dockerfile.
- [ ] Use a minimal production Python image.
- [ ] Run as a non-root user where practical.
- [ ] Install only runtime dependencies.
- [ ] Configure environment-based settings.
- [ ] Add container health/readiness behavior.
- [ ] Ensure graceful shutdown.

**Verification**

The container starts locally and exposes the MCP endpoint.

---

**Task 12. Local container integration**

- [ ] Run Shab MCP with Docker.
- [ ] Run MCP Inspector against the container.
- [ ] Verify all four tools.
- [ ] Verify logs.
- [ ] Verify configuration through environment variables.
- [ ] Verify a failed upstream request does not crash the container.

**Verification**

The complete MCP works without running it directly from the host Python environment.

---

**Phase 8 — AI Lab Pro deployment**

**Task 13. Add shab-mcp to AI Lab Pro**

- [ ] Add the MCP service to the existing AI Lab Pro deployment.
- [ ] Connect it to the appropriate internal Docker/network.
- [ ] Configure Shab API credentials securely.
- [ ] Do not expose the service publicly.
- [ ] Define internal service name/hostname.
- [ ] Verify LiteLLM can reach it over the internal network.

**Verification**

From the AI Lab Pro environment, the MCP endpoint is reachable and the MCP Inspector can discover its tools.

---

**Phase 9 — LiteLLM integration**

**Task 14. Register shab-mcp in LiteLLM**

- [ ] Add Shab MCP to LiteLLM MCP configuration.
- [ ] Configure Streamable HTTP connection.
- [ ] Configure authentication if required.
- [ ] Restrict access to the intended internal identities/teams.
- [ ] Verify LiteLLM discovers the Shab tools.
- [ ] Verify tool invocation through LiteLLM.

**Verification**

A request through LiteLLM can successfully invoke:

```text
search_accommodations
get_accommodation
check_availability
search_destinations
```

without directly connecting the client to shab-mcp.

---

**Phase 10 — OpenWebUI integration**

**Task 15. Connect OpenWebUI through LiteLLM**

- [ ] Configure the appropriate MCP/LiteLLM connection.
- [ ] Verify tool discovery.
- [ ] Verify tool permissions.
- [ ] Test a natural-language search.
- [ ] Verify the model can select the correct tool.
- [ ] Verify tool results are understandable to the model.

**Verification**

Example:

> برای دو شب در رامسر برای چهار نفر اقامتگاه مناسب پیدا کن.

The model should be able to discover and use the appropriate Shab tools.

---

**Phase 11 — Marco Polo integration**

**Task 16. Connect Marco Polo through LiteLLM**

- [ ] Provide Marco Polo access through the existing LiteLLM MCP Gateway.
- [ ] Do not expose shab-mcp directly to Marco Polo if LiteLLM is the central gateway.
- [ ] Grant only the intended MCP permissions.
- [ ] Verify tool discovery.
- [ ] Test search.
- [ ] Test details.
- [ ] Test availability.
- [ ] Test destination resolution.

**Verification**

Marco Polo can independently use Shab MCP through LiteLLM.

---

**Phase 12 — Production hardening**

**Task 17. Observability**

- [ ] Add structured logs.
- [ ] Add request/tool identifiers.
- [ ] Record duration and outcome.
- [ ] Avoid sensitive payload logging.
- [ ] Add Sentry integration if appropriate.
- [ ] Define useful failure metrics.

**Verification**

A failed Shab API request can be traced from MCP tool → API client → upstream response.

---

**Task 18. Security review**

- [ ] Verify no credentials exist in Git.
- [ ] Verify secrets are environment/deployment managed.
- [ ] Verify MCP is not publicly accessible.
- [ ] Verify only intended LiteLLM identities can invoke it.
- [ ] Verify no database credentials are required.
- [ ] Verify tool outputs do not expose internal fields.
- [ ] Verify logs do not expose sensitive information.

**Verification**

A basic internal security review passes before wider company access.

---

**Phase 13 — Documentation**

**Task 19. Developer documentation**

Document:

- [ ] Local setup.
- [ ] Environment variables.
- [ ] Running tests.
- [ ] Running MCP locally.
- [ ] Running with Docker.
- [ ] MCP Inspector usage.
- [ ] AI Lab Pro deployment.
- [ ] LiteLLM configuration.
- [ ] OpenWebUI integration.
- [ ] Marco Polo integration.
- [ ] Tool catalog.
- [ ] Error behavior.
- [ ] Security model.

---

**Phase 14 — Release v0.1**

**Task 20. Release checklist**

- [ ] All tests pass.
- [ ] Docker image builds.
- [ ] Local MCP works.
- [ ] AI Lab Pro deployment works.
- [ ] LiteLLM integration works.
- [ ] OpenWebUI integration works.
- [ ] Marco Polo integration works.
- [ ] Logs are usable.
- [ ] No secrets are committed.
- [ ] No public endpoint exists.
- [ ] README is complete.
- [ ] Version is tagged `v0.1.0`.

---

**Future plan — intentionally not part of v0.1**

After internal validation:

```text
v0.1
Read-only
   ↓
Internal feedback
   ↓
v0.2
More read capabilities
   ↓
Authentication/user context
   ↓
Transactional design
   ↓
Booking/cancellation
   ↓
Company-wide rollout
   ↓
Optional public release
   ↓
awesome-iran-mcp contribution
```

Transactional tools must receive a separate security and authorization design before implementation.

**یک تصمیم مهم که در Plan عمداً باز گذاشتم**

من **اسم دقیق endpointهای Shab را داخل Spec حدس نزدم**. چون گفتی APIهای Shab نسخه‌بندی شده و خوب هستند، مرحله اول implementation باید API contract فعلی را بررسی کند و بعد دقیقاً مشخص کند مثلاً `search_accommodations` به کدام endpoint و چه پارامترهایی map می‌شود.

این باعث می‌شود Spec ما **business-level contract** داشته باشد، نه اینکه به URLهای فعلی Shab قفل شود.

---

**ترتیب اجرای واقعی بعداً**

وقتی بخواهیم شروع کنیم، من این ترتیب را حفظ می‌کنم:

```text
1. shab-mcp repo
       ↓
2. Shab API Client
       ↓
3. 4 Read-only Tools
       ↓
4. Tests
       ↓
5. Docker
       ↓
6. AI Lab Pro
       ↓
7. LiteLLM MCP Gateway
       ↓
8. OpenWebUI
       ↓
9. Marco Polo
       ↓
10. Production hardening
```

و **فعلاً هیچ‌کدام از مراحل کدنویسی، Docker deployment یا تغییر LiteLLM را انجام نمی‌دهم.**

این Spec و Plan الان مبنای اجرای پروژه هستند؛ اگر آن‌ها را تأیید کنی، مرحله بعد می‌توانیم وارد implementation شویم و کار را از **ساخت repo و بررسی دقیق APIهای فعلی Shab** شروع کنیم.

### References

- [1] [GitHub - sepehr071/awesome-iran-mcp: 19 open-source MCP servers (308 tools) that give AI agents the Iranian web: Digikala, Snappfood, Jabama, MrBilit, Paziresh24, Taaghche and more. Prices in Toman. · GitHub](https://github.com/sepehr071/awesome-iran-mcp)
- [2] [Server | MCP TypeScript SDK (v1)](https://ts.sdk.modelcontextprotocol.io/server)
- [3] [Build your first server | MCP TypeScript SDK](https://ts.sdk.modelcontextprotocol.io/v2/get-started/first-server?trk=article-ssr-frontend-pulse_little-text-block)
- [4] unknown
- [5] [jabama-mcp by sepehr071 | Glama](https://glama.ai/mcp/servers/sepehr071/jabama-mcp)
- [6] [MCP Overview | liteLLM](https://docs.litellm.ai/docs/mcp)
- [7] [Client Setup | liteLLM](https://docs.litellm.ai/docs/proxy/client_setup/overview)
- [8] [Model Context Protocol (MCP) / Open WebUI](https://docs.openwebui.com/features/extensibility/mcp)
- [9] unknown
- [10] unknown
