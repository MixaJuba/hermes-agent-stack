# hermes-agent-stack — канонічний стан проєкту

> Єдине джерело правди про поточний production-стан, прийняті рішення, межі доказу та правила наступних змін.

Оновлено: **12 листопада 2026 року** (отримано H-005L PARTIAL; координатор не перевіряв production повторно).

**Короткий [центр керування проєктом](docs/PROJECT-DASHBOARD.uk.md)** — таблиця завершених і незавершених задач та одна наступна дія.

> **Актуальний зріз, читати перед історичними розділами:** H-004L має статус **LIVE PARTIAL за звітом Локального Codex**. На Oracle, за цим звітом, розгорнуто H-003L (пошук з перевіркою дат) і H-004L (читання текстового PDF, створення документів, надсилання після окремої команди, одне одноразове нагадування). Автоматичне «створи й надішли» залишилося PARTIAL; точний заголовок українського PDF не підтверджений; аналіз/генерація зображень не кваліфіковані. Код H-004L прийнято в `main` через [PR №5](https://github.com/MixaJuba/hermes-agent-stack/pull/5); код H-003L — через [PR №4](https://github.com/MixaJuba/hermes-agent-stack/pull/4). Це переказ звіту Local, а не незалежний SSH-аудит координатора. H-002C прийнято в GitHub через [PR №3](https://github.com/MixaJuba/hermes-agent-stack/pull/3), **backup timers залишаються OFF**.

> **Поточний етап — H-005L: звіт отримано, PARTIAL / Очікує перевірки.** [Issue №8](https://github.com/MixaJuba/hermes-agent-stack/issues/8) не закривати до приймання. Безпечний виклад і межі доказу — у розділі H-005L нижче. **Одна наступна дія:** координаторське приймання звіту без повторного повного аудиту; потім погодження мінімального обсягу [H-004L2 / №9](https://github.com/MixaJuba/hermes-agent-stack/issues/9) щодо завершення й доставки документів одним запитом. Виправлення та нові Codex-завдання не запущені; змін production не дозволено цим оновленням. [H-002C / №10](https://github.com/MixaJuba/hermes-agent-stack/issues/10) залишається відкладеним, backup timers OFF. Усі історичні «next step» нижче підпорядковані цьому зрізу.

## 1. Загальний статус

**LIVE PRODUCTION BASELINE ACCEPTED / FINAL E2E PASS.**

`L-006F` завершив production-активацію й live E2E на Oracle. Підтверджені Telegram, systemd, reboot persistence, long-term memory, real Hermes terminal tool, real keyed Exa search, owner-only policy, quota-message transport, real backup/restore та zero-paid-fallback policy.

Це прийнята опорна точка, а не дозвіл безконтрольно змінювати систему. Подальша робота ведеться від цього baseline так, щоб не зламати вже працюючий Telegram-агент.

Sanitized evidence:
- [`docs/L006F-FINAL-PRODUCTION-ACCEPTANCE.uk.md`](docs/L006F-FINAL-PRODUCTION-ACCEPTANCE.uk.md)
- [`reports/l006f-production-ready.json`](reports/l006f-production-ready.json)
- [`docs/OPERATIONS-RUNBOOK.uk.md`](docs/OPERATIONS-RUNBOOK.uk.md)

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
- Docker sandbox: `network=none`, non-root, без Docker socket, host checkout, forwarded secrets або published ports.

Будь-яка зміна Hermes pin, Cloudflare plugin pin, production model/provider, Exa dependency/plan/web implementation, Telegram authorization model, backup/restore format або production host architecture потребує окремого qualification gate перед rollout.

## 4. Фінально підтверджений live runtime

### Telegram — CONFIRMED / PASS

- bot: `@mixa_hermes_ua_bot`;
- identity підтверджена через Bot API;
- webhook: NONE;
- native long polling;
- рівно один production poller;
- numeric owner ID підтверджений зі свіжого private update;
- owner-only access;
- foreign numeric ID denied через native authorization path до inference;
- group access denied;
- українська відповідь: PASS;
- manual gateway smoke: `HERMES_TELEGRAM_OK`;
- three-turn context continuity: `4817 → 4817 → 4822`, PASS.

Telegram token і owner configuration зберігаються тільки у protected Oracle environment; token і numeric owner ID не комітяться в Git.

### systemd / reboot — CONFIRMED / PASS

- accepted `hermes-ua.service` installed;
- service enabled + active;
- startup guard PASS;
- temporary manual gateway зупинено до systemd activation;
- VM reboot PASS;
- Docker і gateway автоматично повернулися після reboot;
- Cloudflare plugin attestation після reboot PASS;
- poller count після restart/reboot: 1;
- другого poller не створено.

### Memory — CONFIRMED / PASS

- long-term memory write через native memory tool: PASS;
- memory after service restart: PASS;
- memory after real VM reboot: PASS;
- restore memory: PASS.

### Hermes tools / sandbox — CONFIRMED / PASS

- real Hermes terminal tool через Telegram: PASS;
- контрольний stdout/result: `HERMES_FINAL_OK`;
- exit code: 0;
- test file після task видалено;
- sandbox live invariants: `network=none`, non-root, без keys, Docker socket і host checkout.

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
- dedicated production key тільки в protected Oracle `.env`;
- backend/search/extract = Exa;
- keyless fallback/rescue OFF;
- real keyed Exa search через Telegram: PASS;
- фактичне джерело: `https://github.com/nousresearch/hermes-agent/`.

### Backup / restore — CONFIRMED / PASS

- real production backup: PASS;
- location: private Oracle boot volume;
- фактичний backup: 419 files, приблизно 1.9 MB;
- backup directory mode `0700`;
- archive owner `hermes-agent`, mode `0600`;
- real native restore у separate isolated home: PASS;
- restored memory: PASS;
- restored session/history: PASS;
- restored config/state: PASS;
- restore-test home після validation видалено;
- live production home не перезаписувався;
- другого gateway/poller під час restore не створено;
- production backup archive залишено на Oracle.

Межа: це restore-capable backup на тій самій VM, а не off-site disaster-recovery copy.

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
- Telegram inbound ports не потрібні: production використовує outbound long polling.

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
- L-006F: live production activation + final E2E — **PASS / accepted baseline**.

## 7. Поточна фаза — production preservation / hardening

Build-gates для першого production baseline закриті. Проєкт переходить у режим контрольованої експлуатації та hardening.

Пріоритети:

1. **Не ламати accepted baseline.** Жодних upgrade/reinstall/model/provider changes без branch → test → evidence → coordinator acceptance.
2. **Операційна відтворюваність.** Використовувати [`docs/OPERATIONS-RUNBOOK.uk.md`](docs/OPERATIONS-RUNBOOK.uk.md) для incident/restart/reboot/backup дій.
3. **Off-site disaster recovery — ONE-TIME PASS ЗА ЗВІТОМ Local Codex H-001L3.** Повідомлено про справжній зашифрований OCI upload/download/SHA-256 та isolated native restore. Незалежний SSH/OCI тест координатор не проводив; timer OFF, повний cold recovery на новій VM не перевірено. Далі потрібні незалежний recovery key/record, контроль квот, накопичення та сповіщень.
4. **Monitoring — PLANNED.** Якщо додається автоматичний health/alerting mechanism, він має бути zero-cost, не містити secrets і не створювати другий poller.

Ці пункти не скасовують `PRODUCTION_READY`; вони визначають наступний рівень стійкості.

## 8. Прийняті технічні рішення

- GitHub `main` = accepted state.
- Oracle Always Free A1 = production host.
- Cloudflare Workers AI Free = production inference.
- Exa keyed = production web search/extract.
- Telegram = native Hermes gateway, long polling, exactly one poller.
- `openai-codex` = development only; production forbidden.
- NVIDIA = TEST ONLY.
- Voice/STT/TTS/Telethon = outside current scope.
- Secrets = target environment only.
- `l*-work/` = task-local scratch, not product source; після acceptance може бути видалений тільки після secret scan.

## 9. Evidence map

- [`docs/L006F-FINAL-PRODUCTION-ACCEPTANCE.uk.md`](docs/L006F-FINAL-PRODUCTION-ACCEPTANCE.uk.md) — detailed final live acceptance.
- [`reports/l006f-production-ready.json`](reports/l006f-production-ready.json) — sanitized machine-readable final evidence.
- [`docs/OPERATIONS-RUNBOOK.uk.md`](docs/OPERATIONS-RUNBOOK.uk.md) — safe production operations / incident rules.
- [`docs/L005-EXA-QUALIFICATION.uk.md`](docs/L005-EXA-QUALIFICATION.uk.md) / [`reports/l005-exa-qualified.json`](reports/l005-exa-qualified.json) — Exa qualification.
- [`docs/C002A-CATALOG-SIDECAR.uk.md`](docs/C002A-CATALOG-SIDECAR.uk.md) / [`reports/c002a-closeout.json`](reports/c002a-closeout.json) — Cloudflare plugin attestation correction.
- [`docs/C002-CLOUDFLARE-PRODUCTION.uk.md`](docs/C002-CLOUDFLARE-PRODUCTION.uk.md) — production config/guard/quota checks.
- [`docs/L004C-CLOUDFLARE-WORKERS-AI-QUALIFICATION.uk.md`](docs/L004C-CLOUDFLARE-WORKERS-AI-QUALIFICATION.uk.md) — Cloudflare live qualification.
- [`docs/C001-CHECKPOINT.uk.md`](docs/C001-CHECKPOINT.uk.md) — quota patch checkpoint.
- [`docs/L003-RUNTIME-ORACLE.uk.md`](docs/L003-RUNTIME-ORACLE.uk.md) — Oracle runtime + sandbox.
- [`docs/L002-ORACLE-HOST.uk.md`](docs/L002-ORACLE-HOST.uk.md) — Oracle host.
- [`config/upstream.json`](config/upstream.json) — pinned Hermes upstream metadata.
- [`reports/h001l3-operator-summary.json`](reports/h001l3-operator-summary.json) — стислий виклад H-001L3 за наданим власником звітом оператора.
- [`docs/INDEX.uk.md`](docs/INDEX.uk.md) / [`docs/ARCHITECTURE.uk.md`](docs/ARCHITECTURE.uk.md) / [`docs/ROADMAP.uk.md`](docs/ROADMAP.uk.md) — путівник для людей, архітектура й розвиток.

## 10. Правило наступних змін

Перед суттєвою production-зміною:

1. визначити один конкретний gate;
2. перевірити актуальні upstream/provider facts;
3. створити окрему branch;
4. виконати offline/synthetic tests там, де це можливо;
5. live test робити мінімальним і контрольованим;
6. зібрати sanitized evidence;
7. тільки після coordinator acceptance переносити зміну в production.

## H-001C — offline artifacts (історична точка до H-001L3)

Підготовлено native backup → mandatory age encryption → SHA256 → instance-principal OCI put/HEAD та isolated restore helpers, неактивовані daily systemd templates й offline tests. Live runtime не змінено. H-001 НЕ завершено; bucket/IAM/key custody/real remote recovery залишаються Local Codex qualification після acceptance. Деталі: [implementation](docs/H001-OFFSITE-DR-IMPLEMENTATION.uk.md).

Coordinator review виявив помилковий вкладений HEAD у helpers і старих test stubs.
H-001C correction використовує документований flat JSON / `opc-meta-*`; offline
orchestrator roundtrip перевіряє put/HEAD/get/checksum/decrypt із реальним native
backup/import. Фінальні результати — [report](reports/h001c-offline.json).
Це виправлення artifacts для review; live OCI/age qualification ще НЕ виконана.

### H-001C-FINAL — offline source ACCEPTED (7 листопада 2026)

H-001C source прийнято координатором після GitHub code review і злито через
[PR #1](https://github.com/MixaJuba/hermes-agent-stack/pull/1), GitHub merge commit
`7369dee839464e2cdf8e2f0f94d362317e6ff704`. Це GitHub/code acceptance,
**не deployment на Oracle** і не live H-001 qualification. За прийнятими L-007A/L-007S:
код export відповідав перевіреному Git tree; новий одноразовий full backup створено
7 листопада на тій самій VM, restore нового ZIP не виконувався, off-instance copy
відсутня. Повторний аудит/backup не потрібний до нового реального gate.

У прийнятому main підготовлено bounded raw rotation із захистом latest verified/legacy
copies, caps/free-space checks і lock; [recovery runbook](docs/RECOVERY-RUNBOOK.uk.md)
закриває документаційні G1–G4, включно з code-export attestation та зовнішнім
key/record custody. Це **accepted offline code**, а не live H-001. Наступний Local gate —
безкоштовність/IAM/custody preflight і після окремого дозволу один real age/OCI
upload/HEAD/get/native isolated restore без зміни
працюючого gateway. Timer до live PASS не активувати.

Offline verification H-001C-FINAL: 18 offsite + 3 recovery-readiness tests PASS;
native synthetic orchestrator PASS; один final regression 50/50 PASS.
Sanitized evidence: [h001c-final-readiness.json](reports/h001c-final-readiness.json).

**Історичний стан перед H-001L3 (не поточний):** L-007S fresh local ZIP (2026-11-07) verified by Local report, not restored; legacy local backups protected; no confirmed off-VM copy. `age`/OCI CLI/IAM and private key custody not yet qualified; billing trial discrepancy unresolved. No systemd timer activated. Coordinator reviewed code/diffs/documentation and upstream Hermes backup exclusion policy; Cloud reported 50/50 tests, coordinator did not independently run Hermes regression or live Oracle. Local next step must stop on any unclear cost, missing independent key custody or unauthorized resource creation.

## H-001L3 — один реальний off-instance backup та isolated restore (7 листопада 2026)

**Статус: PASS ЗА ЗВІТОМ ЛОКАЛЬНОГО CODEX + підтвердження власником доступності ключа.** Це новіша подія за H-001C-FINAL. Координатор отримав повідомлення оператора через власника, але не мав незалежного SSH/OCI доступу і не запускав окремий recovery-тест.

За повідомленням Local Codex створено приватний Standard OCI bucket та вузькі instance-principal IAM права; встановлено age/OCI CLI в операторському середовищі; перевірено відповідність копії коду прийнятому Git tree. Один реальний зашифрований архів завантажено до Object Storage, отримано назад, перевірено розмір/SHA-256 й відновлено пам'ять, сесії/історію, конфігурацію та плагіни у відокремленому каталозі. Сервіс Telegram не перезапускався, poller залишився один, попередні копії збережено, **таймер не активовано**.

Власник підтвердив, що відкриває два захищені записи ключа. **Незалежність від втрати одного пристрою й доступність приватного recovery record з іншого пристрою не підтверджені.** Результат тесту не доводить повне cold recovery на новій VM або роботу unattended timer. За звітом платні опції не вмикалися, але майбутні €0 не можна гарантувати без контролю тарифу/обсягу/запитів. Публічний GitHub не повинен містити реальні ключі, account/object IDs, recovery-record, архіви чи приватні журнали.

**Наступне рішення:** не повторювати H-001L3; перед scheduled backup перевірити незалежне зберігання recovery key/record, квоти та накопичення об'єктів, обробку помилок і сповіщення. Тільки після окремого контрольованого дозволу активувати timer. Наразі розробка H-001C не потребує нового Cloud Codex.

Sanitized secondary evidence: [reports/h001l3-operator-summary.json](reports/h001l3-operator-summary.json). Це виклад наданого звіту, не незалежний machine-generated OCI log.

## H-002C — safe automated backup readiness (offline proposal)

Нове доручення власника після H-001L3: підготовка bounded scheduled backup,
version-aware remote caps, короткого quota approval, durable attempt/outbox state,
owner-only outbound alerts/приватних receipts і daily heartbeat. База
`9602e0a5eb02a1a8b4f3d74f8275018344ce20f3`; код згодом прийнято в `main` через [PR №3](https://github.com/MixaJuba/hermes-agent-stack/pull/3), **не live rollout**.
H-001L3 не повторювати. Accepted native backup/restore та provider/gateway незмінні.

Реалізація не видаляє remote objects і не розширює IAM: cap/expiry/unknown
inventory → STOP. Безстрокова ротація та нові permissions потребують окремого
рішення власника. Timer OFF; Local спочатку перевіряє existing IAM/CLI, фактичну
безкоштовну квоту, незалежний key/record, права і реальну доставку сповіщень.
Деталі й умови контрольованого запуску: [H002C](docs/H002C-SCHEDULED-BACKUP.uk.md).

Offline evidence: 16 targeted schedule + 18 existing offsite tests PASS; native
synthetic roundtrip PASS; один full regression 66/66 PASS. [Sanitized report](reports/h002c-readiness.json).
Це readiness для bounded pilot, не підтвердження live IAM/квот/alerts або timer.

## H-004L — Bro Capability Pack A, 9 листопада 2026

**LIVE PARTIAL за звітом Local Codex; код уже в `main` через [PR №5](https://github.com/MixaJuba/hermes-agent-stack/pull/5).** H-003L розгорнуто на Oracle й
перевірено в Telegram. Пакет активував роботу зі штатними скілами, документами,
todo й одноразовими нагадуваннями. Вхідний PDF, пам’ять, одне нагадування та
доставка трьох реальних вкладень після явного виклику підтверджені. Звичайний
запит на створення й надсилання не гарантував виклику доставки. Точний
український заголовок у згенерованому PDF не підтвердився.

Startup guard пройшов, один poller, owner-only. Аналіз і генерацію зображень
відкладено за рішенням власника. [Докази й відтворення](docs/H004L-BRO-CAPABILITIES.uk.md).

## H-005L — діагностика Bro, 12 листопада 2026 року

**Результат: PARTIAL за наданим власником звітом Локального Codex. Статус роботи: Очікує перевірки; [Issue №8](https://github.com/MixaJuba/hermes-agent-stack/issues/8) залишається відкритим до приймання.** Повністю прочитано оригінальний звіт (151 рядок); нижче лише безпечний виклад. Координатор не повторював SSH/Oracle/Telegram перевірки.

**Межа зрізу:** оператор перевіряв `main` на `58f3cc430f9925b886b44d1bd5442861082c8425`. До поточного перед цим оновленням `cbae4a92c16328a38cdaedb90ab96c89d6680583` змінилася лише документація через [PR №7](https://github.com/MixaJuba/hermes-agent-stack/pull/7). Це звірка GitHub, а не повторний live-тест.

За звітом оператора:

- Сервіс активний, poller один, startup guard пройшов. Активні інструкції та критичні компоненти зіставлено з прийнятим кодом. Це стан на час діагностики, не безперервний моніторинг.
- Активний `SOUL.md` збігається з прийнятим шаблоном і повністю присутній у збереженому системному контексті дослідженої Telegram-сесії. Пошук із файлових інструментів відбувався в Docker, де хостовий файл недоступний; невдалий пошук не доводить відсутності інструкцій.
- Після успішного читання даних модель зайво викликала `clarify` щодо оформлення відповіді; виклик завершився скасуванням. Службова рамка `OUT-OF-BAND USER MESSAGE` була в assistant-тексті, відповідного нового user/steering-запису не знайдено. Потреби в дозволі на читання не встановлено; внутрішня причина рішення моделі невідома.
- Штатний механізм `/personality` підтверджено кодом; перемикання наживо не виконувалося. Звичайне повідомлення про роль не означає автоматичного редагування основного SOUL; життєвий цикл кешованого контексту також має значення.
- Інструменти, бібліотеки та скіли наявні, але це не підтверджує всі користувацькі сценарії. Нових Telegram E2E, inference- або Exa-запитів у H-005L не було. Попередні докази H-004L збережені: читання текстового PDF, пам’ять, одне нагадування та доставка документів після окремої команди. «Створи й надішли» залишається PARTIAL, точний український заголовок PDF не підтверджений; Telegram E2E для PPTX і окремий користувацький доказ todo відсутні, робота з зображеннями не кваліфікована.
- Виявлено застарілі неактивні серверні шаблони/метадані та один випадок примусового завершення з невстановленою причиною. Це ризик відтворюваності й окреме невирішене спостереження; вони не доводять зміну активного provider route або причину недоставки документів.
- Автоматичне резервування не активоване; активних одноразових нагадувань у перевіреному зрізі немає. Production, конфігурацію, SOUL, пам’ять і розклади оператор не змінював.

**Чому PARTIAL:** Oracle Console й Telegram Web не переглянуто; потрібну історію оператор дослідив на сервері. Поточні приватні usage/billing/subscriptions і залишки квот не підтверджені. Публічні умови провайдерів не доводять фактичну безкоштовність або доступну квоту конкретного акаунта.

**Наступне рішення:** прийняти або повернути на уточнення цей PARTIAL-звіт у №8 без повторного повного аудиту; після приймання погодити мінімальний обсяг [H-004L2 / №9](https://github.com/MixaJuba/hermes-agent-stack/issues/9). Пріоритет — завершення багатокрокового запиту й фактична доставка документа, без зайвих уточнень та плутанини між хостом і sandbox. Повторне нагадування не оголошувати несправним без окремого доказу. Роль, серверний drift і причина завершення процесу залишаються окремими питаннями, без автоматичного розширення №9. [H-002C / №10](https://github.com/MixaJuba/hermes-agent-stack/issues/10) залишається відкладеним; нових Codex-завдань не запущено.

**Публікаційна межа:** повний звіт не завантажено в GitHub. Приватні session IDs, метадані хоста, внутрішні шляхи, журнали, точні конфігураційні ліміти та дані акаунтів у цей виклад не перенесено.
