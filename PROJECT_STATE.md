# hermes-agent-stack — канонічний стан проєкту

> **Цей файл є єдиним джерелом правди про поточний стан, активний етап, прийняті рішення та наступні кроки.**
> Якщо README, старий handoff, звіт або чат суперечить цьому файлу, для поточного стану пріоритет має `PROJECT_STATE.md`. Технічні звіти нижче залишаються доказами того, що було перевірено на відповідному етапі.

Оновлено: **2 листопада 2026 року**.

Перевірений implementation checkpoint: `77f3b23d189d9f2f6581a266c6c38d4d614fe057`.
Документаційні коміти після нього можуть змінювати HEAD `main`, але не повинні змінювати перевірену реалізацію без окремого технічного етапу.

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
- Exa — цільовий web-search provider; keyless fallback/rescue мають бути вимкнені.

## 4. Цільова production-архітектура

```text
Telegram
   ↓
Hermes Gateway
   ↓
Hermes Agent
   ├── Cloudflare Workers AI Free / workers-ai / @cf/zai-org/glm-4.7-flash
   ├── persistent conversation + memory
   ├── Exa web search
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

- implementation checkpoint: `77f3b23d189d9f2f6581a266c6c38d4d614fe057`;
- Hermes source: `v0.22.5`, commit `bf0203a794a07aac3ff764972ab9087baa4e4f4e`;
- quota-profile patch відновлено й перевірено;
- synthetic 402/429: PASS;
- український quota text: PASS;
- одна дозволена спроба, без HTTP/model/paid fallback;
- full project regression на C-001: **20 PASS**;
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
- sandbox: non-root, `network=none`, без Docker socket, host checkout, secrets і published ports.

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
- два реальні terminal tool calls;
- sandbox security invariants збережено;
- model fallback: NONE;
- paid fallback: NONE;
- OpenAI/Codex, Gemini, Groq, NVIDIA не використовувалися;
- input tokens: 19 004 total;
- output tokens: 847 total;
- точний Dashboard Neuron counter не був доступний, тому фактичний `NEURON_DELTA` = UNKNOWN; теоретичні розрахунки не видавати за виміряний account fact.

**Production decision:** Cloudflare Workers AI Free + `workers-ai` + `@cf/zai-org/glm-4.7-flash` прийнято як production inference route для поточного pinned deployment.

Будь-який майбутній upgrade Hermes або Cloudflare plugin потребує окремої requalification.

Доказ: [`docs/L004C-CLOUDFLARE-WORKERS-AI-QUALIFICATION.uk.md`](docs/L004C-CLOUDFLARE-WORKERS-AI-QUALIFICATION.uk.md).

### 6.5 Telegram — OBSERVED / НЕ ПІДКЛЮЧЕНО

- bot існує: `@mixa_hermes_ua_bot`;
- token доступний користувачу для захищеного введення;
- Hermes gateway ще не підключений;
- owner numeric ID ще не підтверджений production E2E;
- webhook/polling state ще не перевірений live.

### 6.6 Exa — PLANNED

- Exa залишається цільовим web-search provider;
- account/key і реальна безкоштовна quota конкретного користувача ще не кваліфіковані;
- live search із фактичними URL ще не виконаний;
- keyless fallback/rescue повинні залишатися OFF.

## 7. Поточний активний gate

### C-002 — Cloudflare productionization + deployment reproducibility

**PLANNED / READY FOR CLOUD CODEX.**

Причина: live L-004C PASS уже довів production provider, але tracked deployment artifacts досі містять історичну NVIDIA production-прив'язку.

C-002 повинен:

1. привести `deploy/hermes-config.json`, `gateway_guard.py`, `.env.example` і related tests/docs до Cloudflare production route;
2. прибрати NVIDIA як production dependency, залишивши її лише як historical TEST ONLY evidence;
3. закріпити `workers-ai` + `@cf/zai-org/glm-4.7-flash` без model/provider fallback;
4. перевірити auxiliary routes, щоб вони не могли тихо піти в інший provider або paid model;
5. зробити exact Cloudflare plugin pin відтворюваним для clean restore;
6. додати synthetic Cloudflare Free quota/429 regression без live exhaustion;
7. зберегти Telegram/Exa/systemd вимкненими на цьому етапі;
8. після narrow PASS виконати full project regression один раз, diff check і secret scan.

Cloud Codex не повинен використовувати live Cloudflare credentials або торкатися Oracle.

## 8. Наступні gates після C-002

1. **L-005 Exa integration — Local Codex**: account/free quota, secure key, one real search із фактичними source URLs, no paid fallback.
2. **L-006 Telegram integration — Local Codex**: secure bot token + confirmed numeric owner ID, webhook check, native long polling, one poller, owner-only access, outsider denied.
3. **L-007 systemd + persistence — Local Codex**: install/enable service, process restart, reboot autostart, 3-message context, memory persistence, no second poller.
4. **L-008 backup/restore — Local Codex**: real target VM backup/restore, permissions, memory/history recovery, 0 грн storage path.
5. **L-009 final E2E acceptance — Local Codex**: Telegram Ukrainian response, 3-turn context, long-term memory after restart, real tool task, Exa sources, owner-only access, reboot recovery, quota failure behavior, secret isolation, zero paid routes.
6. **Coordinator final acceptance**: review evidence, update `PROJECT_STATE.md`, README і final production status.

## 9. Прийняті технічні рішення

- **D-001:** Local Codex = browser/accounts/SSH/human confirmation; Cloud Codex = Linux/Hermes/code/tests.
- **D-002:** GitHub `main` = accepted state; handoff через SHA.
- **D-003:** Oracle Always Free A1 = production host.
- **D-004:** NVIDIA = TEST ONLY.
- **D-005:** provider не призначався до live qualification; після L-004C provider decision закритий.
- **D-006:** zero paid fallback / auto-recharge / hidden paid route.
- **D-007:** Telegram native gateway, long polling, one poller; voice/Telethon поза scope.
- **D-008:** secrets не передавати через chat/Git/logs; тільки protected target environment.
- **D-009:** Hermes pin `v0.22.5` не змінювати без upgrade decision + regression.
- **D-010:** Exa = цільовий web search; keyless fallback/rescue OFF.
- **D-011:** Oracle SSH ingress лишається погодженим `/32`.
- **D-012:** `l*-work/` task-local scratch не є product source, не комітиться; після sanitized evidence і прийняття наступного milestone може бути видалений локально після secret check.
- **D-013:** `openai-codex` технічно кваліфікований, але виключений із production; Codex allowance резервується для development.
- **D-014:** Groq Free не тестувати без нової причини: documented TPM не відповідає типовому Hermes agent/tool request.
- **D-015:** Cloudflare Workers AI Free + `workers-ai` + `@cf/zai-org/glm-4.7-flash` = selected production inference route для поточного pinned deployment.
- **D-016:** Cloudflare provider plugin = community integration pinned exact commit; upgrade Hermes/plugin => mandatory requalification before production.

## 10. Що ще НЕ підтверджено

- production Exa account/quota/search;
- Telegram live delivery та owner-only denial;
- 3-turn Telegram context;
- long-term memory persistence після restart/reboot;
- production systemd autostart/recovery;
- real backup/restore на target VM;
- Telegram delivery quota message;
- повний final E2E.

Не трактувати жоден із цих пунктів як PASS до фактичного live test.

## 11. Evidence map

- [`docs/C001-CHECKPOINT.uk.md`](docs/C001-CHECKPOINT.uk.md) — quota patch recovery + 20 PASS.
- [`docs/RUNTIME.uk.md`](docs/RUNTIME.uk.md) — historical cloud runtime/deployment snapshot.
- [`docs/BACKUP-QUOTA.uk.md`](docs/BACKUP-QUOTA.uk.md) — synthetic backup/restore та quota simulations.
- [`docs/QUOTA-PATCH.uk.md`](docs/QUOTA-PATCH.uk.md) — quota overlay rationale.
- [`docs/L001-CONTROL-PLANE.uk.md`](docs/L001-CONTROL-PLANE.uk.md) — Oracle control-plane findings.
- [`docs/L002-ORACLE-HOST.uk.md`](docs/L002-ORACLE-HOST.uk.md) — provisioned Oracle A1 host evidence.
- [`docs/L003-RUNTIME-ORACLE.uk.md`](docs/L003-RUNTIME-ORACLE.uk.md) — pinned Hermes runtime + Docker sandbox on Oracle.
- [`docs/L004A-OPENAI-CODEX-QUALIFICATION.uk.md`](docs/L004A-OPENAI-CODEX-QUALIFICATION.uk.md) — openai-codex technical qualification / production rejection.
- [`docs/L004C-CLOUDFLARE-WORKERS-AI-QUALIFICATION.uk.md`](docs/L004C-CLOUDFLARE-WORKERS-AI-QUALIFICATION.uk.md) — Cloudflare Workers AI Free real qualification PASS.
- [`config/upstream.json`](config/upstream.json) — pinned Hermes upstream metadata.
- [`reports/c001-recovery.json`](reports/c001-recovery.json) — C-001 recovery evidence.

## 12. Правило оновлення цього файлу

Після кожного завершеного milestone:

1. зафіксувати sanitized evidence;
2. змінювати статус лише того, що реально перевірено;
3. завершений active task переносити в CONFIRMED;
4. визначати один наступний найменший безпечний gate;
5. не переписувати історію так, ніби plan був виконаним фактом;
6. не дублювати зайві технічні деталі — посилатися на evidence docs.
