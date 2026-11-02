# hermes-agent-stack

Персональний текстовий Hermes-агент українською мовою для Telegram, який має працювати на придатній безкоштовній Oracle Cloud інфраструктурі, мати довготривалу пам'ять, інструменти та вебпошук без непередбачених платних маршрутів.

## Почати звідси

**Актуальний стан, активний етап, рішення і наступні кроки:** [`PROJECT_STATE.md`](PROJECT_STATE.md)

Це головний документ для користувача, Codex та інших AI. Якщо старий handoff або технічний звіт суперечить йому щодо поточного стану, використовуй `PROJECT_STATE.md`.

Для Codex та інших coding agents діють сталі правила з [`AGENTS.md`](AGENTS.md).

## Поточний стан коротко

- Прийнятий implementation checkpoint: `77f3b23d189d9f2f6581a266c6c38d4d614fe057`.
- Hermes pinned: `v0.22.5` / `bf0203a794a07aac3ff764972ab9087baa4e4f4e`.
- Cloud runtime і quota patch відновлені та перевірені.
- Повний project regression: **20 PASS**.
- Secret scan: PASS.
- Oracle Home Region: **Germany Central (Frankfurt), `eu-frankfurt-1`**.
- Oracle host реально створений: одна Always Free `VM.Standard.A1.Flex`, **1 OCPU / 6 GB**, ARM64, Ubuntu 24.04.5 LTS Minimal, 50 GB boot volume.
- VM = `RUNNING`; SSH і повторне SSH-підключення PASS; outbound GitHub HTTPS/TLS PASS.
- Мережа VM: public subnet, ephemeral public IPv4, Internet Gateway, ingress тільки TCP/22 з погодженого `/32`.
- L-003 PASS: pinned Hermes **v0.22.5** нативно встановлений на Oracle ARM64 через PM; managed Python **3.14.9** і CLI реально запускаються.
- Docker **29.1.3** ARM64 і `hermes-ua-sandbox:local` перевірені; native DockerEnvironment smoke test PASS, `network=none`, non-root, без secrets/socket/host checkout.
- Нових inbound ports не відкривали; provider credentials не додавали; inference requests = 0.
- Telegram bot існує: `@mixa_hermes_ua_bot`; gateway ще не запущений.
- NVIDIA = **TEST ONLY**.
- Production inference-provider навмисно **ще не обраний**: його буде визначено фактичними Hermes tool-loop і quota tests.
- Exa залишається цільовим web-search provider; production integration ще не виконана.

## Наступний етап

**Provider qualification.**

На вже перевіреному Oracle/Hermes runtime потрібно провести один контрольований agent/tool-loop тест для придатного безкоштовного candidate provider і вибрати production route за фактом, без платного fallback.

Перший кандидат для перевірки — штатний Hermes `openai-codex`, якщо фактичний OAuth/usage route доступний і не вимагає окремого платного API-балансу. Якщо він не проходить критерії — перевіряється наступний безкоштовний кандидат.

## Цільова схема

```text
Telegram
   ↓
Hermes Gateway
   ↓
Hermes Agent
   ├── production inference provider (після фактичної кваліфікації)
   ├── persistent memory/history
   ├── Exa web search
   └── isolated Docker tools

Host: перевірена Oracle Always Free A1 ARM64 VM з нативним Hermes runtime.
```

## Важливі правила

- Бюджет production: **0 грн**.
- Немає auto-recharge, платних fallback-моделей або прихованих paid routes.
- Hermes/runtime/models не встановлюються на Windows-ноутбук.
- NVIDIA використовується лише для тестування.
- Telethon і голос зараз поза scope.
- Секрети не зберігаються у Git, чатах або звичайних логах.
- GitHub `main` — прийнятий перевірений стан; handoff між агентами робиться через commit SHA.

## Документація та докази

- [`PROJECT_STATE.md`](PROJECT_STATE.md) — канонічний поточний стан, рішення, active task, roadmap і Definition of Done.
- [`AGENTS.md`](AGENTS.md) — сталі інструкції для Codex та інших AI-агентів.
- [`docs/L001-CONTROL-PLANE.uk.md`](docs/L001-CONTROL-PLANE.uk.md) — sanitized Oracle/Telegram/NVIDIA/Codex account precheck.
- [`docs/L002-ORACLE-HOST.uk.md`](docs/L002-ORACLE-HOST.uk.md) — підтверджений Oracle A1 host, SSH і мережеві перевірки.
- [`docs/L003-RUNTIME-ORACLE.uk.md`](docs/L003-RUNTIME-ORACLE.uk.md) — нативний Hermes runtime і Docker sandbox на Oracle ARM64.
- [`docs/C001-CHECKPOINT.uk.md`](docs/C001-CHECKPOINT.uk.md) — відновлення quota patch і 20 PASS.
- [`docs/RUNTIME.uk.md`](docs/RUNTIME.uk.md) — cloud runtime, sandbox, guard і deployment artifacts; технічний snapshot.
- [`docs/BACKUP-QUOTA.uk.md`](docs/BACKUP-QUOTA.uk.md) — synthetic backup/restore та quota simulations.
- [`docs/QUOTA-PATCH.uk.md`](docs/QUOTA-PATCH.uk.md) — rationale українського quota overlay.
- [`docs/SETUP.uk.md`](docs/SETUP.uk.md) — стабільні deployment gates, security і acceptance checklist.
- [`config/upstream.json`](config/upstream.json) — закріплений upstream Hermes.

## Коли бот вважається готовим

Тільки після реального E2E на Oracle: український Telegram-діалог, 3+ повідомлення контексту, пам'ять після restart, реальний tool call, Exa з фактичними джерелами, відмова сторонньому ID, systemd/reboot, backup/restore та контрольована quota failure без оплати.
