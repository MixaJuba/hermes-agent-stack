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
- Oracle Home Region підтверджено: **Germany Central (Frankfurt), `eu-frankfurt-1`**.
- A1 Always Free конфігурація підготовлена; реальна host capacity ще перевіряється provisioning-етапом.
- Telegram bot існує: `@mixa_hermes_ua_bot`; gateway ще не запущений.
- NVIDIA = **TEST ONLY**.
- Production inference-provider навмисно **ще не обраний**: його буде визначено фактичними Hermes tool-loop і quota tests.
- Exa залишається цільовим web-search provider; production integration ще не виконана.

## Що виконується зараз

**L-002 — Oracle VM provisioning.**

Локальний Codex створює одну Always Free A1 ARM64 VM з мінімальною конфігурацією й перевіряє тільки host basics: ARM64, Ubuntu 24.04, SSH, outbound GitHub і відсутність платних ресурсів.

На цьому етапі Hermes, Docker, provider OAuth, Exa і Telegram token на VM ще не встановлюються.

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

Host: Oracle Always Free ARM64, якщо provisioning/runtime checks PASS.
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
- [`docs/C001-CHECKPOINT.uk.md`](docs/C001-CHECKPOINT.uk.md) — відновлення quota patch і 20 PASS.
- [`docs/RUNTIME.uk.md`](docs/RUNTIME.uk.md) — cloud runtime, sandbox, guard і deployment artifacts; технічний snapshot.
- [`docs/BACKUP-QUOTA.uk.md`](docs/BACKUP-QUOTA.uk.md) — synthetic backup/restore та quota simulations.
- [`docs/QUOTA-PATCH.uk.md`](docs/QUOTA-PATCH.uk.md) — rationale українського quota overlay.
- [`docs/SETUP.uk.md`](docs/SETUP.uk.md) — стабільні deployment gates, security і acceptance checklist.
- [`config/upstream.json`](config/upstream.json) — закріплений upstream Hermes.

## Коли бот вважається готовим

Тільки після реального E2E на Oracle: український Telegram-діалог, 3+ повідомлення контексту, пам'ять після restart, реальний tool call, Exa з фактичними джерелами, відмова сторонньому ID, systemd/reboot, backup/restore та контрольована quota failure без оплати.
