# hermes-agent-stack — канонічний стан проєкту

> Єдине джерело правди про поточний production-стан, прийняті рішення та подальші правила експлуатації.

Оновлено: **2 листопада 2026 року**.

## 1. Загальний статус

**PRODUCTION READY / FINAL E2E PASS.**

Фінальний Local Codex task `L-006F` завершив production-активацію й перевірив Telegram, systemd, reboot persistence, long-term memory, real Hermes tool call, real Exa search, owner-only policy, quota-message delivery, real backup/restore та zero-paid-fallback policy.

Sanitized evidence:
- [`docs/L006F-FINAL-PRODUCTION-ACCEPTANCE.uk.md`](docs/L006F-FINAL-PRODUCTION-ACCEPTANCE.uk.md)
- [`reports/l006f-production-ready.json`](reports/l006f-production-ready.json)

## 2. Production-архітектура

```text
Telegram
   ↓ native long polling / one poller / owner-only
Hermes Gateway
   ↓
Hermes Agent
   ├── Cloudflare Workers AI Free
   │   provider: workers-ai
   │   model: @cf/zai-org/glm-4.7-flash
   ├── persistent conversation + memory
   ├── keyed Exa search/extract only
   └── isolated Docker terminal tools

Host: Oracle Always Free A1 ARM64
Source of truth: GitHub MixaJuba/hermes-agent-stack
```

## 3. Закріплені компоненти

- Hermes: `v0.22.5` / `bf0203a794a07aac3ff764972ab9087baa4e4f4e`.
- Cloudflare plugin: `f6821d058d504ee6324b0d3217564b93124c09f9`.
- Production inference: `workers-ai / @cf/zai-org/glm-4.7-flash`.
- Production web: keyed Exa only.
- Exa dependency: `exa-py==2.10.2`.
- Oracle VM: `VM.Standard.A1.Flex`, 1 OCPU / 6 GB RAM, ARM64, Ubuntu 24.04.5 Minimal, 50 GB boot volume.
- Docker: ARM64 sandbox, `network=none`, non-root, без Docker socket, host checkout, forwarded secrets або published ports.

Будь-яка зміна Hermes pin, Cloudflare plugin pin, production model/provider, Exa dependency/plan/web implementation або Telegram authorization model потребує окремої requalification перед production rollout.

## 4. Фінально підтверджений runtime

### Telegram — CONFIRMED / PASS

- bot: `@mixa_hermes_ua_bot`;
- webhook: NONE;
- native long polling;
- рівно один production poller;
- numeric owner ID confirmed;
- owner-only access;
- foreign numeric ID denied через native authorization path;
- group access denied;
- українська відповідь: PASS;
- three-turn context continuity: PASS.

Telegram token і owner configuration зберігаються тільки у protected Oracle environment; numeric owner ID і token не комітяться в Git.

### systemd / reboot — CONFIRMED / PASS

- `hermes-ua.service` enabled;
- service active;
- startup guard PASS;
- manual gateway smoke PASS до systemd activation;
- VM reboot PASS;
- gateway автоматично повертається після reboot;
- другого poller не створено.

### Memory — CONFIRMED / PASS

- long-term memory write PASS;
- memory after service restart PASS;
- memory after real VM reboot PASS;
- restore memory PASS.

### Hermes tools / sandbox — CONFIRMED / PASS

- real Hermes terminal tool через Telegram: PASS;
- контрольний результат: `HERMES_FINAL_OK`;
- sandbox security invariants після live tool execution: PASS.

### Cloudflare — CONFIRMED / PASS

- provider: `workers-ai`;
- model: `@cf/zai-org/glm-4.7-flash`;
- plugin exact pin attestation: PASS;
- model/provider/paid fallback: NONE;
- OpenAI/Codex production credential: ABSENT / FORBIDDEN;
- NVIDIA production route: NOT USED / TEST ONLY.

### Exa — CONFIRMED / PASS

- account qualified FREE;
- payment method absent;
- PAYGO disabled;
- dedicated production key встановлено тільки в protected Oracle `.env`;
- backend/search/extract = Exa;
- keyless fallback/rescue OFF;
- real keyed Exa search через Telegram: PASS;
- фактичне джерело: `https://github.com/nousresearch/hermes-agent/`.

### Backup / restore — CONFIRMED / PASS

- real production backup: PASS;
- location: private Oracle boot volume;
- backup directory mode `0700`;
- archive owner `hermes-agent`, mode `0600`;
- real restore у separate isolated home: PASS;
- restored memory: PASS;
- restored session/history: PASS;
- другого gateway/poller під час restore не створено.

Примітка: це restore-capable backup на тій самій VM, а не off-site disaster-recovery copy.

### Quota behavior — ACCEPTED / PASS

- synthetic Cloudflare 402/429 logic previously verified;
- bounded retries;
- український quota text;
- no provider/model/paid fallback;
- accepted quota message live-delivered через Telegram transport;
- реальну Cloudflare quota навмисно не вичерпували.

## 5. Безпека та бюджет

- Production budget: **0 грн**.
- Auto-recharge / paid fallback / hidden paid route: заборонені.
- Нових paid Oracle resources у L-006F не додано.
- Cloudflare billing у L-006F не змінювався.
- Exa PAYGO у L-006F не змінювався.
- Production `.env`: regular file, owner `hermes-agent`, mode `0600`.
- Secrets не повинні потрапляти у Git, chat, task artifacts, logs або sandbox.
- Final task-local secret scan: PASS.
- Telegram ingress ports не потрібні: production використовує outbound long polling.

## 6. Історичні milestones

- L-001: Oracle/Telegram/control-plane precheck — PASS.
- L-002: Oracle Always Free A1 host — PASS.
- L-003: pinned Hermes runtime + Docker sandbox on Oracle ARM64 — PASS.
- L-004A: OpenAI/Codex technically qualified, rejected for production.
- L-004C: Cloudflare Workers AI Free production inference qualification — PASS.
- C-001: quota patch / synthetic 402/429 regression — PASS.
- C-002: Cloudflare productionization — PASS.
- C-002A: `.hermes-catalog.json` attestation correction — PASS.
- L-005: Exa Free production qualification — PASS.
- L-006F: final production activation + E2E — **PASS / PRODUCTION READY**.

## 7. Прийняті технічні рішення

- GitHub `main` = accepted state.
- Oracle Always Free A1 = production host.
- Cloudflare Workers AI Free = production inference.
- Exa keyed = production web search/extract.
- Telegram = native Hermes gateway, long polling, exactly one poller.
- `openai-codex` = development only; production forbidden.
- NVIDIA = TEST ONLY.
- Voice/STT/TTS/Telethon = outside current scope.
- Secrets = target environment only.
- `l*-work/` = task-local scratch, not product source; після acceptance може бути видалений лише після secret scan.

## 8. Evidence map

- [`docs/L006F-FINAL-PRODUCTION-ACCEPTANCE.uk.md`](docs/L006F-FINAL-PRODUCTION-ACCEPTANCE.uk.md) — final live production acceptance.
- [`reports/l006f-production-ready.json`](reports/l006f-production-ready.json) — sanitized final machine-readable status.
- [`docs/L005-EXA-QUALIFICATION.uk.md`](docs/L005-EXA-QUALIFICATION.uk.md) / [`reports/l005-exa-qualified.json`](reports/l005-exa-qualified.json) — Exa qualification.
- [`docs/C002A-CATALOG-SIDECAR.uk.md`](docs/C002A-CATALOG-SIDECAR.uk.md) / [`reports/c002a-closeout.json`](reports/c002a-closeout.json) — Cloudflare plugin attestation correction.
- [`docs/C002-CLOUDFLARE-PRODUCTION.uk.md`](docs/C002-CLOUDFLARE-PRODUCTION.uk.md) — production config/guard/quota checks.
- [`docs/L004C-CLOUDFLARE-WORKERS-AI-QUALIFICATION.uk.md`](docs/L004C-CLOUDFLARE-WORKERS-AI-QUALIFICATION.uk.md) — Cloudflare live qualification.
- [`docs/C001-CHECKPOINT.uk.md`](docs/C001-CHECKPOINT.uk.md) — quota patch checkpoint.
- [`docs/L003-RUNTIME-ORACLE.uk.md`](docs/L003-RUNTIME-ORACLE.uk.md) — Oracle runtime + sandbox.
- [`docs/L002-ORACLE-HOST.uk.md`](docs/L002-ORACLE-HOST.uk.md) — Oracle host.
- [`config/upstream.json`](config/upstream.json) — pinned Hermes upstream metadata.

## 9. Наступний режим роботи

Активних build-gates більше немає.

Подальша робота — лише:
- нормальна експлуатація;
- перевірка при фактичному incident;
- planned upgrade через окремий qualification gate;
- за потреби окремо додати off-site encrypted backup, але це не блокує поточний production-ready status.
