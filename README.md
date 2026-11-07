# Особистий Hermes-помічник у Telegram

Цей проєкт створений, щоб мати власного текстового ШІ-помічника українською:
написати завдання в Telegram, продовжити попередню розмову й отримати результат
із перевіреними джерелами. Доступ до бота має лише власник.

## Що вже працює

На прийнятому live baseline бот відповідає українською, тримає контекст кількох
повідомлень, пам’ятає збережені факти після перезапуску й reboot сервера.
Він виконує завдання інструментами Hermes та шукає через Exa з реальними посиланнями.
Перевірено owner-only доступ, автоматичний запуск і відновлення резерву в окрему
папку. Помилки квот обробляються без переходу на платні моделі.

```text
Власник ↔ Telegram ↔ Hermes
                      ├─ Cloudflare Workers AI Free — відповіді й виклики інструментів
                      ├─ пам’ять та історія розмов
                      ├─ Exa — пошук джерел
                      └─ Docker — ізольоване виконання команд
Сервер: Oracle Always Free ARM64; ноутбук не потрібний для роботи бота.
```

## Що покращується зараз

Production бюджет — 0 грн, без платних резервних маршрутів або автоматичних списань.
Працюючі компоненти закріплені на перевірених версіях. Зараз готуємо зашифровану
копію резервів поза сервером: поточний перевірений backup лежить на тій самій VM
і не захистить від повної втрати її диска. Новий remote recovery ще **не пройшов
live qualification**; H-001C готує лише код, offline-тести та неактивовані шаблони.

[Поточний стан і докази](PROJECT_STATE.md) · [Операційний runbook](docs/OPERATIONS-RUNBOOK.uk.md) · [Безпечне розгортання та відновлення](docs/RECOVERY-RUNBOOK.uk.md) · [DR implementation](docs/H001-OFFSITE-DR-IMPLEMENTATION.uk.md)

## Документація

- [`PROJECT_STATE.md`](PROJECT_STATE.md) — канонічний production state, межі доказу та правила наступних змін.
- [`docs/OPERATIONS-RUNBOOK.uk.md`](docs/OPERATIONS-RUNBOOK.uk.md) — safe operations / incident handling.
- [`AGENTS.md`](AGENTS.md) — правила для Codex та інших coding agents.
- [`docs/L006F-FINAL-PRODUCTION-ACCEPTANCE.uk.md`](docs/L006F-FINAL-PRODUCTION-ACCEPTANCE.uk.md) — фінальна live acceptance.
- [`reports/l006f-production-ready.json`](reports/l006f-production-ready.json) — sanitized machine evidence.
- [`docs/L005-EXA-QUALIFICATION.uk.md`](docs/L005-EXA-QUALIFICATION.uk.md) — Exa production qualification.
- [`docs/C002-CLOUDFLARE-PRODUCTION.uk.md`](docs/C002-CLOUDFLARE-PRODUCTION.uk.md) — Cloudflare productionization.
- [`docs/C002A-CATALOG-SIDECAR.uk.md`](docs/C002A-CATALOG-SIDECAR.uk.md) — plugin attestation correction.
- [`docs/L004C-CLOUDFLARE-WORKERS-AI-QUALIFICATION.uk.md`](docs/L004C-CLOUDFLARE-WORKERS-AI-QUALIFICATION.uk.md) — live Cloudflare qualification.
- [`docs/L003-RUNTIME-ORACLE.uk.md`](docs/L003-RUNTIME-ORACLE.uk.md) — pinned Hermes runtime + Docker sandbox on Oracle.
- [`config/upstream.json`](config/upstream.json) — pinned upstream Hermes metadata.
