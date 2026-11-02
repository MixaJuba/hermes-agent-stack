# hermes-agent-stack — канонічний стан проєкту

> **Цей файл є єдиним джерелом правди про поточний стан, активний етап, прийняті рішення та наступні кроки.**
> Якщо README, старий handoff, звіт або чат суперечить цьому файлу, для поточного стану пріоритет має `PROJECT_STATE.md`. Технічні звіти нижче залишаються доказами того, що було перевірено на відповідному етапі.

Оновлено: **2 листопада 2026 року**.

Прийнятий implementation C-002A: `f0f8a41857aa9b2c647638ee070900b529e11e19`.
Історичний C-002 implementation: `02567a3cad56dcb9d1b3140b682076d1e2a5f2cf`.
Історичний C-001 checkpoint: `77f3b23d189d9f2f6581a266c6c38d4d614fe057`.
Документаційні коміти після implementation checkpoint можуть змінювати HEAD `main`, але не повинні змінювати перевірену реалізацію без окремого технічного етапу.

## 1. Статуси

- **CONFIRMED** — є фактична перевірка, test, Git-артефакт або контрольована перевірка в авторизованій консолі.
- **OBSERVED** — побачено в UI/account, але не E2E.
- **IN PROGRESS** — активна задача зараз виконується.
- **PLANNED** — погоджений наступний крок, ще не виконаний.
- **UNKNOWN** — даних недостатньо.
- **BLOCKED** — є конкретний блокер.

## 2. Кінцева мета

Побудувати персонального текстового Hermes-агента українською мовою, який постійно працює на безкоштовній Oracle Cloud інфраструктурі та доступний через Telegram.

Фінальна система повинна:

1. відповідати українською в Telegram і тримати контекст щонайменше трьох послідовних повідомлень;
2. зберігати довготривалу пам'ять і відтворювати тестовий факт після restart/reboot;
3. виконувати реальне завдання через інструмент Hermes;
4. виконувати вебпошук через Exa і повертати посилання на фактично отримані джерела;
5. приймати запити лише від підтвердженого numeric Telegram owner ID;
6. автоматично запускатися після reboot і мати перевірене backup/restore;
7. при вичерпанні квоти завершуватися контрольовано, без нескінченних retry і без переходу на оплату;
8. не мати непередбачених paid routes, а secrets не повинні потрапляти в Git, чати, логи чи sandbox.

## 3. Незмінні обмеження

- Production-бюджет: **0 грн**.
- Заборонені auto-recharge, automatic credit purchase і paid fallback.
- ChatGPT/Codex allowance зарезервований тільки для Локального та Хмарного Codex як розробницьких виконавців.
- Hermes/runtime/models не встановлювати на Windows-ноутбук користувача.
- Голос, STT/TTS і Telethon зараз поза scope.
- Telegram — штатний Hermes gateway, long polling, один production poller.
- NVIDIA Build/NIM — **TEST ONLY**.
- Hermes pinned на `v0.22.5` / `bf0203a794a07aac3ff764972ab9087baa4e4f4e` до окремого upgrade-рішення.
- Exa — єдиний production web-search/content-extraction provider; keyless fallback/rescue вимкнені.

## 4. Цільова production-архітектура

```text
Telegram
   ↓
Hermes Gateway
   ↓
Hermes Agent
   ├── Cloudflare Workers AI Free / workers-ai / @cf/zai-org/glm-4.7-flash
   ├── persistent conversation + memory
   ├── Exa keyed web search/extract
   └── isolated Docker tool environment

Host: Oracle Always Free A1 ARM64.
Source of truth: GitHub repository MixaJuba/hermes-agent-stack.
```

## 5. Ролі середовищ

### Локальний Codex

Використовувати для браузера, приватних акаунтів, Oracle Console, Telegram/BotFather, provider login/token creation, локального SSH, безпечного введення secrets і live E2E на реальному Oracle.

### Хмарний Codex

Використовувати для Linux/cloud workspace, Hermes source/runtime, code, patches, tests, deployment artifacts і автономних задач без приватного браузера.

### GitHub

- `main` = прийнятий перевірений стан.
- Технічні зміни — через окрему branch.
- Local і Cloud не редагують ті самі tracked files одночасно.
- Handoff між середовищами — commit SHA + коротка delta.

## 6. Поточний підтверджений стан

### 6.1 Cloud implementation checkpoint — CONFIRMED

- implementation checkpoint C-002A: `f0f8a41857aa9b2c647638ee070900b529e11e19`;
- Hermes source: `v0.22.5`, commit `bf0203a794a07aac3ff764972ab9087baa4e4f4e`;
- quota-profile patch відновлено й перевірено;
- synthetic 402/429: PASS;
- український quota text: PASS;
- bounded retry, без model/provider/paid fallback;
- C-002A full regression: **29 PASS**;
- secret scan: PASS;
- ARM64 artifacts / Docker base image manifest підтверджені.

### 6.2 Oracle host/runtime — CONFIRMED

- одна VM `hermes-agent-prod`;
- `VM.Standard.A1.Flex`, 1 OCPU / 6 GB RAM, ARM64, Ubuntu 24.04.5 Minimal;
- 50 GB boot volume;
- Oracle Always Free usage у перевірених межах;
- SSH PASS;
- ingress лише TCP/22 з погодженого `/32`;
- outbound HTTPS PASS;
- pinned Hermes source і reviewed quota patch на Oracle: PASS;
- PM install / managed Python 3.14.9 / Hermes CLI v0.22.5: PASS;
- Docker 29.1.3 ARM64;
- `hermes-ua-sandbox:local`: build + native smoke PASS;
- sandbox: non-root, `network=none`, без Docker socket, host checkout, secrets і published ports;
- C-002A delta синхронізований на Oracle, real Cloudflare plugin attestation: PASS.

### 6.3 L-004A openai-codex — CONFIRMED TECHNICALLY / REJECTED FOR PRODUCTION

- browser OAuth PKCE через SSH tunnel: PASS;
- український turn: PASS;
- real Hermes model → tool → result → final-answer loop: PASS;
- production decision: `openai-codex` **не використовувати**, бо він споживає development Codex allowance;
- L-004C підтвердив, що credential `openai-codex` на Oracle видалено.

### 6.4 L-004C Cloudflare Workers AI Free — CONFIRMED / PASS

Production inference route обраний після реального test:

- provider: `workers-ai`;
- model: `@cf/zai-org/glm-4.7-flash`;
- Workers plan: FREE до і після test;
- payment method: відсутній;
- plugin: `cloudflare-workers-ai-provider`;
- exact plugin commit: `f6821d058d504ee6324b0d3217564b93124c09f9`;
- plugin має статус community, але exact commit pinned у official Hermes plugin catalog і пройшов live test на нашому pinned Hermes;
- Ukrainian turn: PASS;
- real Hermes-native model → terminal tool → sandbox → tool result → final response: PASS;
- контрольний результат: `HERMES_CF_OK`;
- sandbox security invariants збережено;
- model fallback: NONE;
- paid fallback: NONE;
- OpenAI/Codex, Gemini, Groq, NVIDIA не використовувалися;
- точний Dashboard Neuron counter не був доступний; фактичний `NEURON_DELTA` не заявляється.

**Production decision:** Cloudflare Workers AI Free + `workers-ai` + `@cf/zai-org/glm-4.7-flash` — production inference route для поточного pinned deployment.

Будь-який майбутній upgrade Hermes або Cloudflare plugin потребує окремої requalification.

Докази: [`docs/L004C-CLOUDFLARE-WORKERS-AI-QUALIFICATION.uk.md`](docs/L004C-CLOUDFLARE-WORKERS-AI-QUALIFICATION.uk.md), [`docs/L004C-CLOSEOUT.uk.md`](docs/L004C-CLOSEOUT.uk.md), [`reports/l004c-qualified.json`](reports/l004c-qualified.json).

### 6.5 Telegram — OBSERVED / НЕ ПІДКЛЮЧЕНО

- bot існує: `@mixa_hermes_ua_bot`;
- token доступний користувачу для захищеного введення;
- Hermes gateway ще не підключений;
- owner numeric ID ще не підтверджений production E2E;
- webhook/polling state ще не перевірений live.

### 6.6 Exa / L-005 — CONFIRMED / PASS

- account: ACTIVE;
- plan: FREE; dashboard показав `$10 credits/month`;
- payment method: ABSENT;
- PAYGO: NO;
- paid subscription: NO;
- balance before controlled test: `$20.00`;
- створено один dedicated key `hermes-agent-prod`; UI не надав scopes;
- `EXA_API_KEY` встановлено тільки у protected Oracle `.env`; owner `hermes-agent`, mode `0600`;
- existing Cloudflare variables збережені;
- dependency: `exa-py==2.10.2`, уже була встановлена, без reinstall;
- web routing: `backend=exa`, `search_backend=exa`, `extract_backend=exa`;
- keyless fallback/rescue: OFF;
- один real keyed Exa `web_search`: PASS, три source URLs;
- один real keyed Exa `web_extract`: PASS, content отримано;
- інший web provider не використовувався;
- balance after: `$19.99`; точний call cost не заявляти через UI rounding/reporting;
- secret scan: PASS; task-local exact-key scan — 0 збігів;
- paid route: NONE.

Докази: [`docs/L005-EXA-QUALIFICATION.uk.md`](docs/L005-EXA-QUALIFICATION.uk.md), [`reports/l005-exa-qualified.json`](reports/l005-exa-qualified.json).

### 6.7 C-002 / C-002A productionization — ACCEPTED

- tracked production route: `workers-ai / @cf/zai-org/glm-4.7-flash`;
- NVIDIA прибрано з production required secrets і main/auxiliary config; TEST ONLY history збережена;
- main/auxiliary fallback chains порожні;
- exact community plugin commit + source hashes + installer-owned provenance attestation;
- `.hermes-catalog.json` дозволений лише як inert installer sidecar і не використовується як provenance;
- startup guard fail-closed для inference/web/Telegram/sandbox/retry policy;
- synthetic Cloudflare 429: bounded, без provider/model/paid switch;
- full regression після C-002A: 29 PASS.

## 7. Поточний активний gate

### L-006F — final production activation, Local Codex

**PLANNED.**

Щоб не створювати зайві handoff-и, завершальні етапи виконуються одним Local Codex task із внутрішніми gates. Перехід до наступної фази дозволений лише після PASS попередньої; при новому blocker Local Codex STOP і повертає точну причину.

Послідовність:

1. Telegram production integration: secure bot token, confirmed numeric owner ID, webhook/polling check, native long polling, рівно один poller, owner-only policy, foreign-ID denial test.
2. Production config + startup guard PASS, після чого один manual gateway smoke через Telegram.
3. systemd install/enable; process restart і VM reboot; gateway автоматично повертається без другого poller.
4. Три послідовні Telegram turns із context continuity.
5. Long-term memory fact записується та відтворюється після restart/reboot.
6. Real Hermes tool task через Telegram із збереженням sandbox invariants.
7. Real Exa search через Telegram із фактичними source URLs.
8. Real backup/restore на target VM у безкоштовному storage path; перевірка permissions та memory/history recovery.
9. Final E2E: owner-only, Ukrainian response, Cloudflare+Exa routes, reboot recovery, quota-message path, secret isolation, zero paid fallback.

## 8. Залишкові gates

- **L-006 Telegram** — ще не виконано live.
- **L-007 systemd + persistence** — ще не виконано live.
- **L-008 backup/restore** — ще не виконано real target restore.
- **L-009 final E2E** — ще не виконано.
- **Coordinator final acceptance** — після sanitized evidence L-006F оновити `PROJECT_STATE.md`, README і production status.

## 9. Прийняті технічні рішення

- **D-001:** Local Codex = browser/accounts/SSH/human confirmation; Cloud Codex = Linux/Hermes/code/tests.
- **D-002:** GitHub `main` = accepted state; handoff через SHA.
- **D-003:** Oracle Always Free A1 = production host.
- **D-004:** NVIDIA = TEST ONLY.
- **D-005:** Cloudflare Workers AI Free / `workers-ai` / `@cf/zai-org/glm-4.7-flash` = production inference route.
- **D-006:** zero paid fallback / auto-recharge / hidden paid route.
- **D-007:** Telegram native gateway, long polling, one poller; voice/Telethon поза scope.
- **D-008:** secrets не передавати через chat/Git/logs; тільки protected target environment.
- **D-009:** Hermes pin `v0.22.5` не змінювати без upgrade decision + regression.
- **D-010:** Exa keyed = production web search/extract; keyless fallback/rescue OFF.
- **D-011:** Oracle SSH ingress лишається погодженим `/32`.
- **D-012:** `l*-work/` task-local scratch не є product source і не комітиться; після sanitized evidence + acceptance може бути видалений після secret scan.
- **D-013:** `openai-codex` технічно кваліфікований, але виключений із production; Codex allowance резервується для development.
- **D-014:** Groq Free не тестувати без нової причини.
- **D-015:** Cloudflare provider plugin = community integration pinned exact commit; upgrade Hermes/plugin => mandatory requalification.
- **D-016:** C-002A sidecar policy: installer-owned `.install-metadata.json` є authoritative provenance; in-tree `.hermes-catalog.json` — лише validated inert sidecar.
- **D-017:** Exa Free qualification L-005 прийнята; зміна plan/dependency/web implementation потребує requalification перед policy change.

## 10. Що ще НЕ підтверджено

- Telegram live delivery та owner-only denial;
- 3-turn Telegram context;
- long-term memory persistence після restart/reboot;
- production systemd autostart/recovery;
- real backup/restore на target VM;
- Telegram delivery quota message;
- повний final E2E.

Не трактувати жоден із цих пунктів як PASS до фактичного live test.

## 11. Evidence map

- [`docs/L005-EXA-QUALIFICATION.uk.md`](docs/L005-EXA-QUALIFICATION.uk.md) — Exa Free account/key/native Hermes search+extract qualification.
- [`reports/l005-exa-qualified.json`](reports/l005-exa-qualified.json) — sanitized machine-readable L-005 evidence.
- [`docs/C002A-CATALOG-SIDECAR.uk.md`](docs/C002A-CATALOG-SIDECAR.uk.md) — corrective attestation policy.
- [`reports/c002a-closeout.json`](reports/c002a-closeout.json) — C-002A machine evidence.
- [`docs/C002-CLOUDFLARE-PRODUCTION.uk.md`](docs/C002-CLOUDFLARE-PRODUCTION.uk.md) — Cloudflare production artifacts/offline proofs.
- [`docs/L004C-CLOSEOUT.uk.md`](docs/L004C-CLOSEOUT.uk.md) — Cloudflare sanitized closeout.
- [`docs/C001-CHECKPOINT.uk.md`](docs/C001-CHECKPOINT.uk.md) — quota patch recovery.
- [`docs/RUNTIME.uk.md`](docs/RUNTIME.uk.md) — historical cloud runtime/deployment snapshot.
- [`docs/BACKUP-QUOTA.uk.md`](docs/BACKUP-QUOTA.uk.md) — synthetic backup/restore та quota simulations.
- [`docs/QUOTA-PATCH.uk.md`](docs/QUOTA-PATCH.uk.md) — quota overlay rationale.
- [`docs/L001-CONTROL-PLANE.uk.md`](docs/L001-CONTROL-PLANE.uk.md) — Oracle control-plane findings.
- [`docs/L002-ORACLE-HOST.uk.md`](docs/L002-ORACLE-HOST.uk.md) — provisioned Oracle A1 host evidence.
- [`docs/L003-RUNTIME-ORACLE.uk.md`](docs/L003-RUNTIME-ORACLE.uk.md) — pinned Hermes runtime + Docker sandbox on Oracle.
- [`docs/L004A-OPENAI-CODEX-QUALIFICATION.uk.md`](docs/L004A-OPENAI-CODEX-QUALIFICATION.uk.md) — openai-codex technical qualification / production rejection.
- [`docs/L004C-CLOUDFLARE-WORKERS-AI-QUALIFICATION.uk.md`](docs/L004C-CLOUDFLARE-WORKERS-AI-QUALIFICATION.uk.md) — Cloudflare live qualification.
- [`config/upstream.json`](config/upstream.json) — pinned Hermes upstream metadata.

## 12. Правило оновлення цього файлу

Після кожного завершеного milestone:

1. зафіксувати sanitized evidence;
2. змінювати статус лише того, що реально перевірено;
3. завершений active task переносити в CONFIRMED;
4. визначати один наступний найменший безпечний gate;
5. не переписувати історію так, ніби plan був виконаним фактом;
6. не дублювати зайві технічні деталі — посилатися на evidence docs.
