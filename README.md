# hermes-agent-stack

Персональний текстовий Hermes-агент українською мовою для Telegram на Oracle Cloud Always Free.

## Статус

**PRODUCTION READY / FINAL E2E PASS.**

Канонічний поточний стан: [`PROJECT_STATE.md`](PROJECT_STATE.md)

Фінальна production acceptance:
- [`docs/L006F-FINAL-PRODUCTION-ACCEPTANCE.uk.md`](docs/L006F-FINAL-PRODUCTION-ACCEPTANCE.uk.md)
- [`reports/l006f-production-ready.json`](reports/l006f-production-ready.json)

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

- українські відповіді в Telegram;
- owner-only access;
- three-turn context continuity;
- long-term memory після service restart і real VM reboot;
- systemd autostart після reboot;
- рівно один production poller;
- real Hermes terminal tool через Telegram;
- sandbox security invariants;
- real keyed Exa search через Telegram з фактичним source URL;
- real backup + isolated restore memory/session history;
- quota-message delivery без навмисного вичерпання реальної квоти;
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

## Документація

- [`PROJECT_STATE.md`](PROJECT_STATE.md) — канонічний production state та правила подальших змін.
- [`AGENTS.md`](AGENTS.md) — правила для Codex та інших coding agents.
- [`docs/L005-EXA-QUALIFICATION.uk.md`](docs/L005-EXA-QUALIFICATION.uk.md) — Exa production qualification.
- [`docs/C002-CLOUDFLARE-PRODUCTION.uk.md`](docs/C002-CLOUDFLARE-PRODUCTION.uk.md) — Cloudflare productionization.
- [`docs/C002A-CATALOG-SIDECAR.uk.md`](docs/C002A-CATALOG-SIDECAR.uk.md) — plugin attestation correction.
- [`docs/L004C-CLOUDFLARE-WORKERS-AI-QUALIFICATION.uk.md`](docs/L004C-CLOUDFLARE-WORKERS-AI-QUALIFICATION.uk.md) — live Cloudflare qualification.
- [`docs/L003-RUNTIME-ORACLE.uk.md`](docs/L003-RUNTIME-ORACLE.uk.md) — pinned Hermes runtime + Docker sandbox on Oracle.
- [`config/upstream.json`](config/upstream.json) — pinned upstream Hermes metadata.

Активних build-gates після L-006F немає. Подальша робота — експлуатація, incident response або окремі planned upgrade/requalification tasks.
