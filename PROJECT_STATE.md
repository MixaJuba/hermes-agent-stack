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
- Provider credentials не додавалися.
- Inference requests: **0**.
- Telegram gateway і production systemd service не запускалися.
- Нових inbound ports не відкривали.

**UNKNOWN / ще не доведено**

- Реальний model → tool → result → final-answer цикл на production-кандидаті.
- Реальна Telegram delivery quota/billing message.

Докази: [`docs/C001-CHECKPOINT.uk.md`](docs/C001-CHECKPOINT.uk.md), [`docs/RUNTIME.uk.md`](docs/RUNTIME.uk.md), [`docs/L003-RUNTIME-ORACLE.uk.md`](docs/L003-RUNTIME-ORACLE.uk.md), [`reports/c001-recovery.json`](reports/c001-recovery.json).

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

У L-003 додано тільки необхідні prerequisites і Docker/runtime; нових inbound ports або paid resources не додано.

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

**UNRESOLVED — це навмисний стан.**

Кандидати для фактичної кваліфікації на вже готовому Oracle/Hermes runtime:

- штатний Hermes `openai-codex` через наявний ChatGPT/Codex доступ, якщо OAuth і usage-модель реально придатні;
- native Gemini provider у межах доступного Free Tier, якщо реальні Hermes agent turns вкладаються у квоти;
- інші безкоштовні provider-и лише якщо перші кандидати не проходять критерії.

Критерії вибору однакові для кожного кандидата:

1. успішна авторизація без платного API-балансу;
2. українська відповідь;
3. реальний Hermes tool call;
4. tool result → final response;
5. достатні context/tool-schema limits;
6. контрольована поведінка при 429/quota;
7. відсутність автоматичного paid fallback;
8. придатність для постійного персонального агента за умовами сервісу.

### 6.6 Exa

**PLANNED**

- Exa залишається цільовим web-search provider.
- У конфігурації keyless fallback/rescue мають бути вимкнені.
- Account/key та реальна квота цього користувача ще не є підтвердженим production-фактом.
- Підключати після вибору основного inference-provider.

## 7. Наступний активний gate

### Provider qualification

**PLANNED / READY TO START у Локальному Codex.**

Мета: на вже перевіреному Oracle ARM64 host і незмінному pinned Hermes runtime виконати один мінімальний реальний agent/tool-loop test для придатного безкоштовного candidate provider і зафіксувати фактичну usage/quota поведінку.

Перший кандидат для перевірки — штатний Hermes `openai-codex`, але тільки якщо реальний OAuth flow доступний і не вимагає окремого платного API-балансу або automatic credit spending.

Ключові вимоги:

- не змінювати Hermes pin, quota patch або Docker sandbox;
- не підключати кілька provider-ів одночасно;
- не вмикати paid fallback або auto-recharge;
- виконати один український turn і один реальний Hermes tool call;
- перевірити tool result → final answer;
- зафіксувати фактичну usage/quota поведінку;
- при непридатності кандидата зупинитися і перейти до наступного окремим контрольованим тестом.

**Cloud Codex не потрібен на старті provider qualification.** Залучати його лише при конкретному кодовому/runtime блокері.

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
- **D-012:** `l003-work/` та аналогічні task-local orchestration/scratch файли не є product source і не комітяться в `main`; після фіксації sanitized evidence їх можна видалити локально.

## 10. Що НЕ можна вважати підтвердженим

Не перетворювати на факт:

- придатність Gemini Free для 24/7 Hermes до реальних agent-turn tests;
- придатність ChatGPT/Codex subscription як production route до реального Hermes OAuth + usage test;
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
