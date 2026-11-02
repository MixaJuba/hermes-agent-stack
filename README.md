# hermes-agent-stack

Персональний текстовий Hermes-агент українською мовою для Telegram на Oracle Cloud Always Free.

## Статус

**LIVE PRODUCTION BASELINE ACCEPTED / FINAL E2E PASS.**

Канонічний поточний стан: [`PROJECT_STATE.md`](PROJECT_STATE.md)

Фінальна live acceptance:
- [`docs/L006F-FINAL-PRODUCTION-ACCEPTANCE.uk.md`](docs/L006F-FINAL-PRODUCTION-ACCEPTANCE.uk.md)
- [`reports/l006f-production-ready.json`](reports/l006f-production-ready.json)

Операційний runbook:
- [`docs/OPERATIONS-RUNBOOK.uk.md`](docs/OPERATIONS-RUNBOOK.uk.md)

## Production stack

```text
Telegram
   ↓ native long polling / owner-only / one poller
Hermes Gateway
   ↓
Hermes Agent
   ├── Cloudflare Workers AI Free
   │   workers-ai / @cf/zai-org/glm-4.7-flash
   ├── persistent memory/history
   ├── keyed Exa web search/extract
   └── isolated Docker terminal tools

Host: Oracle Always Free A1 ARM64
```

## Підтверджено live

- правильний Telegram bot identity;
- webhook відсутній;
- owner-only access;
- group access denied;
- рівно один production poller;
- українські відповіді в Telegram;
- manual smoke `HERMES_TELEGRAM_OK`;
- three-turn context continuity `4817 → 4817 → 4822`;
- long-term memory після service restart і real VM reboot;
- systemd autostart після reboot;
- real Hermes terminal tool через Telegram з результатом `HERMES_FINAL_OK`;
- sandbox `network=none`, non-root, без Docker socket/host checkout/secrets;
- real keyed Exa search через Telegram з фактичним source URL;
- native foreign-ID denial до inference;
- quota-message delivery без навмисного вичерпання реальної квоти;
- real production backup + isolated native restore memory/session/history/config;
- backup: 419 files, приблизно 1.9 MB, private Oracle boot volume;
- no OpenAI/Codex production route;
- no NVIDIA production route;
- no provider/model/paid fallback;
- final secret scan PASS.

## Закріплені версії

- Hermes: `v0.22.5` / `bf0203a794a07aac3ff764972ab9087baa4e4f4e`.
- Cloudflare provider plugin: `f6821d058d504ee6324b0d3217564b93124c09f9`.
- Exa dependency: `exa-py==2.10.2`.

Зміна цих production pins потребує окремої requalification.

## Основні правила

- Production budget: **0 грн**.
- Без auto-recharge, paid fallback або hidden paid routes.
- Secrets не зберігаються у Git, чатах або звичайних логах.
- NVIDIA = TEST ONLY.
- OpenAI/Codex = development only, не production inference.
- Telegram = native Hermes long polling; inbound public port не потрібен.
- Voice/STT/TTS/Telethon зараз поза scope.
- Accepted live baseline не змінювати напряму: спочатку branch/test/evidence/acceptance.

## Поточна фаза

Перший повний production baseline уже працює й прийнятий. Далі проєкт переходить у режим **production preservation / hardening**, а не хаотичного продовження build.

Наступні напрямки не повинні ламати живу систему:

- operational monitoring без другого poller і без paid services;
- окремий future gate для encrypted off-site disaster-recovery backup;
- planned upgrades тільки після requalification.

Поточний backup перевірено реальним restore на тій самій Oracle VM, але він ще не є off-site DR copy.

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
