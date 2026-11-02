# hermes-agent-stack — канонічний стан проєкту

> **Цей файл є єдиним джерелом правди про поточний стан, активний етап, прийняті рішення та наступні кроки.**
> Якщо README, старий handoff, звіт або чат суперечить цьому файлу, для поточного стану пріоритет має `PROJECT_STATE.md`. Технічні звіти нижче залишаються доказами того, що було перевірено на відповідному етапі.

Оновлено: **2 листопада 2026 року**.

Перевірений implementation checkpoint: `77f3b23d189d9f2f6581a266c6c38d4d614fe057`.
Документаційні коміти після нього можуть змінювати HEAD `main`, але не повинні змінювати перевірену реалізацію без окремого технічного етапу.

## 1. Як читати статуси

- **CONFIRMED** — є фактична перевірка, тест, Git-артефакт або контрольована перевірка в авторизованій консолі.
- **OBSERVED** — побачено в акаунті/інтерфейсі, але не підтверджено робочим E2E-тестом.
- **IN PROGRESS** — активна задача зараз виконується.
- **PLANNED** — погоджений наступний крок, ще не виконаний.
- **UNKNOWN** — даних недостатньо; не вважати ні успіхом, ні помилкою.
- **BLOCKED** — є конкретний блокер, який перешкоджає переходу далі.

## 2. Кінцева мета

Побудувати персонального текстового Hermes-агента українською мовою, який постійно працює на придатній **безкоштовній** інфраструктурі Oracle Cloud та доступний через Telegram.

Фінальна система повинна:

1. відповідати українською у Telegram і правильно використовувати контекст щонайменше трьох послідовних повідомлень;
2. зберігати довготривалу пам'ять і відтворювати тестовий факт після перезапуску;
3. виконувати реальне завдання через інструмент Hermes;
4. виконувати вебпошук через Exa та повертати посилання на фактично отримані джерела;
5. приймати запити лише від підтвердженого Telegram ID власника та відмовляти сторонньому ID;
6. автоматично запускатися після reboot і мати перевірене відновлення з резервної копії;
7. при вичерпанні квоти завершуватися контрольовано, без нескінченних повторів і без переходу на оплату;
8. не мати непередбачених платних маршрутів, а секрети не повинні потрапляти в Git, чати, логи чи sandbox.

## 3. Незмінні обмеження

- Бюджет: **0 грн** для постійної роботи.
- Не використовувати автопоповнення, автоматичну покупку credits або платні fallback-маршрути.
- ChatGPT/Codex allowance зарезервований для Локального та Хмарного Codex як розробницьких виконавців; production Hermes не повинен його споживати.
- Hermes, його runtime і моделі не встановлювати на Windows-ноутбук користувача.
- Голос, STT/TTS і Telethon зараз **не входять** у погоджену ціль.
- Telegram — штатний gateway Hermes, long polling.
- Один production poller.
- Production inference-provider **не призначати наперед**: обрати лише після фактичної кваліфікації.
- NVIDIA Build/NIM — **TEST ONLY**, не production-основа.
- Upstream Hermes закріплений на `v0.22.5` / `bf0203a794a07aac3ff764972ab9087baa4e4f4e` до окремо погодженого upgrade-етапу.

## 4. Цільова архітектура

```text
Telegram
   ↓
Hermes Gateway
   ↓
Hermes Agent
   ├── inference provider (ще не обраний)
   ├── persistent conversation + memory
   ├── Exa web search
   └── isolated Docker tool environment

Host: перевірена Oracle Always Free A1 ARM64 VM з нативним pinned Hermes runtime.
Source of truth: GitHub repository `MixaJuba/hermes-agent-stack`.
```

## 5. Ролі середовищ

### Локальний Codex

Відповідає за:

- браузер і авторизовані акаунти;
- Oracle Console, Telegram/BotFather, provider OAuth/login;
- локальний SSH до Oracle;
- дії, що потребують присутності користувача;
- безпечне введення секретів без публікації в чаті або Git;
- перевірку результатів Cloud Codex у GitHub.

### Хмарний Codex

Відповідає за:

- Linux/cloud workspace;
- Hermes runtime, код, патчі та тести;
- статичні та інтеграційні перевірки, які не потребують приватного браузера;
- підготовку deployment-артефактів;
- Git checkpoint після завершеної перевіреної фази.

### GitHub

- `main` — прийнятий перевірений стан.
- Великі або ризикові зміни робити в окремій branch.
- Не дозволяти Local і Cloud одночасно редагувати ті самі файли.
- Handoff між середовищами передавати через commit SHA, а не переказом усієї історії.

## 6. Поточний підтверджений стан

### 6.1 Git і Hermes

**CONFIRMED**

Cloud / implementation checkpoint:

- Перевірений implementation checkpoint: `77f3b23d189d9f2f6581a266c6c38d4d614fe057`.
- Hermes source: `v0.22.5`, commit `bf0203a794a07aac3ff764972ab9087baa4e4f4e`.
- У Codex Cloud Hermes runtime було встановлено штатним PM.
- Managed Python: `3.14.9`.
- Quota-profile patch відновлено після перерваного 5-годинним лімітом turn і перевірено.
- Вузькі 402/429 тести: PASS.
- Український user-facing quota text: PASS.
- Одна дозволена спроба; HTTP/model/paid fallback у синтетичній перевірці: 0.
- Повний project regression suite: **20 PASS**, один запуск після вузьких PASS.
- Secret scan: PASS.
- PM містить Linux ARM64-артефакти; pinned Docker base image має `arm64/v8` manifest.

Oracle target / L-003:

- Accepted project state `5d8aea60b499e6cf3d21f800174cb18e83ffa2c2` передано на VM без GitHub credentials; 42 project files і Git tree повторно перевірені.
- Official Hermes source на VM закріплено на `bf0203a794a07aac3ff764972ab9087baa4e4f4e`.
- Reviewed local quota patch: **VERIFIED** через `scripts/hermes_runtime.py`.
- PM install на `aarch64 / linux-arm64`: **PASS**.
- Hermes CLI: **v0.22.5**, реальний запуск PASS.
- `gateway --help`: PASS.
- Managed Python **3.14.9**, реальний запуск PASS.
- Docker **29.1.3**, ARM64.
- `hermes-ua-sandbox:local` build: PASS.
- Native `DockerEnvironment` smoke test: PASS.
- Sandbox: non-root, writable isolated workspace, `network=none`, metadata route недоступний, published ports відсутні, secrets/Docker socket/host checkout відсутні.
- На завершенні L-003 provider credentials не додавалися, inference requests = 0, Telegram gateway і production systemd service не запускалися, нових inbound ports не відкривали.

Oracle target / L-004A:

- Штатний Hermes `openai-codex` OAuth через browser PKCE + SSH local tunnel: **PASS**.
- Credential збережено на Oracle у service-account context з правами `0600`.
- Реальний model slug: `gpt-6-luna`.
- Короткий український turn: **PASS**.
- Реальний Hermes-native model → tool → sandbox → tool result → final-answer цикл: **PASS**; контрольний результат `HERMES_CODEX_OK`.
- Sandbox security properties під час tool-loop збережено.
- `OPENAI_API_KEY` не використовувався; paid route, OpenRouter fallback, NVIDIA, Gemini, Telegram та Exa не використовувалися.
- Usage delta між BEFORE/AFTER не атрибутується лише Hermes, бо в тому самому allowance працював Локальний Codex.
- Production decision: `openai-codex` **НЕ використовувати в production**; Codex allowance зарезервовано для розробки.

**UNKNOWN / ще не доведено**

- Реальний model → tool → result → final-answer цикл на фактичному production-кандидаті.
- Реальна Telegram delivery quota/billing message.

Докази: [`docs/C001-CHECKPOINT.uk.md`](docs/C001-CHECKPOINT.uk.md), [`docs/RUNTIME.uk.md`](docs/RUNTIME.uk.md), [`docs/L003-RUNTIME-ORACLE.uk.md`](docs/L003-RUNTIME-ORACLE.uk.md), [`docs/L004A-OPENAI-CODEX-QUALIFICATION.uk.md`](docs/L004A-OPENAI-CODEX-QUALIFICATION.uk.md), [`reports/c001-recovery.json`](reports/c001-recovery.json).

### 6.2 Oracle Cloud

**CONFIRMED**

Control plane / L-001:

- Home Region: **Germany Central (Frankfurt), `eu-frankfurt-1`**.
- Account: Free Tier / Free Trial; Always Free eligible; платний upgrade не активований.
- Always Free A1 allowance, перевірений на етапі L-001: **2 OCPU / 12 GB RAM**.
- Block/boot volume free allowance: **200 GB**.
- Availability domains: AD-1, AD-2, AD-3.

Provisioned host / L-002:

- Створено рівно одну VM `hermes-agent-prod`.
- Lifecycle: `RUNNING`.
- Shape: `VM.Standard.A1.Flex`.
- Placement: `EU-FRANKFURT-1-AD-1`.
- Реально на VM: **1 OCPU, ~6 GB RAM, `aarch64`, Ubuntu 24.04.5 LTS Minimal**.
- Boot volume: **50 GB**, root filesystem приблизно 48G.
- Always Free usage після provisioning: **1/2 OCPU, 6/12 GB RAM, 50/200 GB storage**.
- Capacity: підтверджена успішним provisioning з першої спроби; capacity errors не було.
- SSH: працює; повторне підключення PASS.
- Public subnet: YES; ephemeral public IPv4 assigned.
- Default route: `0.0.0.0/0 -> Internet Gateway`.
- Ingress: лише `TCP/22` з погодженого `/32`; зайвих ingress rules не додано.
- Outbound GitHub HTTPS: PASS, HTTP 200 на public endpoint, TLS verification PASS.
- Платних ресурсів у межах L-002 не створено.

У L-003/L-004A нових inbound ports або paid resources не додано; OAuth callback працював через локальний SSH tunnel.

Докази: [`docs/L001-CONTROL-PLANE.uk.md`](docs/L001-CONTROL-PLANE.uk.md), [`docs/L002-ORACLE-HOST.uk.md`](docs/L002-ORACLE-HOST.uk.md), [`docs/L003-RUNTIME-ORACLE.uk.md`](docs/L003-RUNTIME-ORACLE.uk.md).

### 6.3 Telegram

**CONFIRMED / OBSERVED**

- Bot існує: `@mixa_hermes_ua_bot`.
- Token доступний користувачу для подальшого захищеного введення.
- Token не повинен зберігатися в Git або чаті.

**UNKNOWN**

- Webhook state не перевірявся, щоб не копіювати token у небезпечний канал.
- Hermes gateway ще не підключений.
- Owner ID production-конфігурації ще не підтверджений E2E.

### 6.4 NVIDIA

**DECISION: TEST ONLY**

- Account авторизований.
- Ключ був активний; UI показував до 40 rpm.
- Playground раніше відповідав успішно.
- Hosted trial не використовувати як production foundation.
- Нових NVIDIA inference-тестів без конкретної діагностичної причини не робити.

### 6.5 Production inference-provider

**UNRESOLVED — фактичний production-provider ще не призначений.**

Вже перевірені/відсіяні варіанти:

- `openai-codex`: **QUALIFIED TECHNICALLY**, але **REJECTED FOR PRODUCTION** — споживає ChatGPT/Codex allowance, який зарезервовано для Локального/Хмарного Codex.
- Gemini Free: **НЕ ПЕРШИЙ КАНДИДАТ** — pinned Hermes підтримує native Gemini і tool calling, але власна документація Hermes попереджає, що Free Tier замалий для довготривалих agent sessions через кілька model calls на turn. Практичний тест відкладено, доки немає причини повертатися до цього варіанта.
- Groq Free: **REJECTED WITHOUT LIVE TEST** — documented Free TPM ліміт недостатній для типового Hermes agent request із tool schemas; live test не виправданий.
- Local LLM на поточній Oracle VM: **REJECTED AS PRIMARY ROUTE** — 1 OCPU / 6 GB ARM64 не дає прийнятної якості/швидкості для цільового agent workload.

**Поточний найкраще обґрунтований кандидат для мінімальної фактичної кваліфікації: Cloudflare Workers AI Free.**

Підстави до live test:

- Free план має окрему щоденну безкоштовну allocation і не переходить автоматично на paid usage; після вичерпання free limits операції мають завершуватися помилкою.
- Для text generation на free-compatible models немає Groq-подібного 8K TPM blocker; default rate limit значно вищий за наш персональний workload.
- Cloudflare заявляє zero-data-retention для standard inference та no training on Customer Content.
- У pinned Hermes `v0.22.5` офіційний plugin catalog містить `cloudflare-workers-ai-provider`, pinned на `f6821d058d504ee6324b0d3217564b93124c09f9`, сумісний з Hermes >=0.21.5.
- Plugin лише реєструє provider/metadata, не додає tools/hooks/background processes; підтримує function-calling models, коректні context windows і free-plan entitlement errors.
- Перший model candidate: `@cf/zai-org/glm-4.7-flash` — Free-compatible, multilingual, function calling, multi-turn tool calling, context 131072; обраний для першого тесту через низьку neuron-вартість серед придатних моделей.

Production-рішення приймається тільки після одного мінімального реального test на акаунті користувача.

Критерії кваліфікації:

1. Workers Free без payment method/Workers Paid/AI Gateway credits;
2. успішна авторизація dedicated token;
3. `@cf/zai-org/glm-4.7-flash` реально доступний на Free;
4. українська відповідь;
5. реальний Hermes tool call → tool result → final response;
6. фактичний neuron usage після мінімального test;
7. контрольована відмова при вичерпанні квоти без paid fallback;
8. OpenAI/Codex route відключений і не використовується.

### 6.6 Exa

**PLANNED**

- Exa залишається цільовим web-search provider.
- У конфігурації keyless fallback/rescue мають бути вимкнені.
- Account/key та реальна квота цього користувача ще не є підтвердженим production-фактом.
- Підключати після вибору основного inference-provider.

## 7. Наступний активний gate

### L-004C — Cloudflare Workers AI Free qualification

**PLANNED / READY TO START у Локальному Codex.**

Мета: на незмінному Oracle ARM64 + pinned Hermes runtime виконати один мінімальний реальний test Cloudflare Workers AI Free з `@cf/zai-org/glm-4.7-flash`, достатній для підтвердження account entitlement, реального Hermes tool-loop і фактичної neuron-витрати.

Перед тестом:

- прибрати/відключити `openai-codex` credential на Oracle штатним Hermes auth flow, щоб production route не міг випадково споживати Codex development allowance;
- видалити `l004a-work/` після secret check; task-local scratch не комітити;
- не змінювати Hermes pin, quota patch, Docker sandbox, Oracle network або systemd;
- встановити тільки pinned Cloudflare provider із official Hermes plugin catalog;
- не вмикати Workers Paid, payment method, prepaid AI Gateway credits, unified billing або будь-який fallback.

Test scope:

- один короткий український turn;
- один контрольований Hermes-native tool-loop у sandbox;
- один BEFORE/AFTER neuron usage check;
- після цього STOP.

**Cloud Codex не потрібен на старті L-004C.** Залучати лише при конкретному code/runtime blocker.

## 8. Наступні gates після provider qualification

Порядок може змінитися лише за фактичним блокером, але не через повторне переосмислення вже вирішеного.

1. **Exa integration** — перевірити акаунт/квоту, встановити key без Git, виконати реальний search із джерелами.
2. **Telegram integration** — безпечно ввести token і owner ID, перевірити webhook/polling, запустити один gateway.
3. **systemd + persistence** — автозапуск, reboot, process restart, memory persistence.
4. **backup/restore on target VM** — перевірити disaster recovery реальної інсталяції.
5. **Final E2E acceptance** — усі 8 критерії з розділу 2.

## 9. Прийняті технічні рішення

- **D-001:** Local Codex — браузер/акаунти/SSH/людські підтвердження; Cloud Codex — Linux/Hermes/code/tests.
- **D-002:** GitHub `main` — прийнятий стан; handoff через SHA.
- **D-003:** Oracle Always Free A1 підтверджений як реальний host; L-003 підтвердив нативний pinned Hermes runtime і Docker sandbox на ARM64.
- **D-004:** NVIDIA = TEST ONLY.
- **D-005:** Production inference-provider не фіксується до фактичної кваліфікації.
- **D-006:** Нуль paid fallback / auto-recharge / прихованих платних маршрутів.
- **D-007:** Telegram long polling; Telethon і voice не потрібні.
- **D-008:** Secrets не передавати через чат/Git; вводити тільки у захищене цільове середовище.
- **D-009:** Hermes pin `v0.22.5` не змінювати без окремого upgrade-рішення і regression.
- **D-010:** Exa — цільовий web search; keyless fallback вимкнений.
- **D-011:** SSH до Oracle лишається обмеженим погодженим `/32`; не розширювати до `0.0.0.0/0` без конкретної потреби й review.
- **D-012:** `l*-work/` та аналогічні task-local orchestration/scratch файли не є product source і не комітяться в `main`; після фіксації sanitized evidence їх можна видалити локально.
- **D-013:** ChatGPT/Codex subscription route технічно перевірений, але виключений із production; allowance резервується для розробницьких Codex.
- **D-014:** Groq Free не тестувати: documented TPM limits несумісні з типовим Hermes agent/tool request.
- **D-015:** Cloudflare Workers AI Free — наступний контрольований production-candidate test; `@cf/zai-org/glm-4.7-flash` — перша модель для кваліфікації, але не production-рішення до PASS.

## 10. Що НЕ можна вважати підтвердженим

Не перетворювати на факт:

- придатність Cloudflare Workers AI Free для нашого production до L-004C real account/tool-loop/neuron test;
- фактичну кількість Hermes turns/day лише з теоретичного neuron розрахунку;
- придатність Gemini Free для 24/7 Hermes без окремої причини повертатися до його practical test;
- працездатність Telegram лише з факту існування BotFather bot-а;
- production-ready статус лише з runtime/sandbox tests;
- безкоштовність сервісу лише через signup credits або trial balance.

## 11. Evidence map

- [`docs/C001-CHECKPOINT.uk.md`](docs/C001-CHECKPOINT.uk.md) — відновлення перерваного quota patch та 20 PASS.
- [`docs/RUNTIME.uk.md`](docs/RUNTIME.uk.md) — cloud runtime, sandbox, guard, deployment artifacts; історичний технічний snapshot.
- [`docs/BACKUP-QUOTA.uk.md`](docs/BACKUP-QUOTA.uk.md) — synthetic backup/restore та quota simulations.
- [`docs/QUOTA-PATCH.uk.md`](docs/QUOTA-PATCH.uk.md) — rationale quota overlay.
- [`docs/L001-CONTROL-PLANE.uk.md`](docs/L001-CONTROL-PLANE.uk.md) — sanitized Local Codex control-plane findings.
- [`docs/L002-ORACLE-HOST.uk.md`](docs/L002-ORACLE-HOST.uk.md) — sanitized proof of the provisioned Oracle A1 host, SSH and network checks.
- [`docs/L003-RUNTIME-ORACLE.uk.md`](docs/L003-RUNTIME-ORACLE.uk.md) — sanitized proof of native pinned Hermes runtime and Docker sandbox on Oracle ARM64.
- [`docs/L004A-OPENAI-CODEX-QUALIFICATION.uk.md`](docs/L004A-OPENAI-CODEX-QUALIFICATION.uk.md) — sanitized proof that `openai-codex` works technically but is excluded from production.
- [`config/upstream.json`](config/upstream.json) — pinned Hermes upstream metadata; current provider decision is governed by this file's pin fields plus `PROJECT_STATE.md`, not by historical model notes.
- [`reports/c001-recovery.json`](reports/c001-recovery.json) — recovery evidence.

## 12. Правило оновлення цього файлу

Після кожного завершеного milestone:

1. зафіксувати доказ: commit SHA, test result або sanitized control-plane snapshot;
2. змінити статус лише того, що реально перевірено;
3. перенести завершений active task у CONFIRMED;
4. визначити один наступний найменший безпечний етап;
5. не переписувати історію так, ніби план був виконаним фактом;
6. не дублювати великі технічні деталі — посилатися на evidence docs.
