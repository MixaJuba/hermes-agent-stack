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

Host: Oracle Always Free ARM64 VM, якщо provisioning і нативний runtime пройдуть перевірку.
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

- Перевірений checkpoint: `77f3b23d189d9f2f6581a266c6c38d4d614fe057`.
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

**UNKNOWN / ще не доведено**

- Нативне встановлення та виконання Hermes на реальній Oracle A1 ARM64 VM.
- Реальний model → tool → result → final-answer цикл на production-кандидаті.
- Реальна Telegram delivery quota/billing message.

Докази: [`docs/C001-CHECKPOINT.uk.md`](docs/C001-CHECKPOINT.uk.md), [`docs/RUNTIME.uk.md`](docs/RUNTIME.uk.md), [`reports/c001-recovery.json`](reports/c001-recovery.json).

### 6.2 Oracle Cloud

**CONFIRMED через авторизовану Oracle Console під час L-001**

- Home Region: **Germany Central (Frankfurt), `eu-frankfurt-1`**.
- Account: Free Tier / Free Trial; Always Free eligible; платний upgrade не активований.
- `VM.Standard.A1.Flex`: видимий і позначений Always Free-eligible.
- Always Free A1 allowance за чинними умовами, перевіреними на етапі L-001: **2 OCPU / 12 GB RAM**.
- `VM.Standard.E2.1.Micro`: видимий і Always Free-eligible.
- Block/boot volume free allowance: **200 GB**; на момент L-001 використання 0 GB.
- 5 backup slots були видимі; використання 0/5.
- Availability domains: AD-1, AD-2, AD-3.
- A1 був доступний у формі в усіх трьох AD; E2 Micro — в AD-3.
- Підготовлена конфігурація A1: 1 OCPU / 6 GB, Ubuntu 24.04 Minimal aarch64, 50 GB boot volume.

**UNKNOWN**

- Реальна host capacity. Її можна остаточно підтвердити тільки provisioning-спробою.

Доказовий snapshot: [`docs/L001-CONTROL-PLANE.uk.md`](docs/L001-CONTROL-PLANE.uk.md).

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

Кандидати для фактичної кваліфікації після готовності Oracle/Hermes runtime:

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
- Підключати лише після готовності базового runtime і вибору основного inference-provider.

## 7. Активний етап

### L-002 — Oracle VM provisioning

**IN PROGRESS у Локальному Codex.**

Мета: створити **одну** Always Free A1 VM і довести тільки базову придатність host-а.

Погоджена цільова конфігурація:

- `VM.Standard.A1.Flex`;
- 1 OCPU;
- 6 GB RAM;
- Ubuntu 24.04 Minimal ARM64/aarch64;
- 50 GB boot volume;
- on-demand;
- мінімальний inbound доступ, SSH без публікації private key;
- без Hermes, Docker, provider OAuth, Telegram token або Exa на цьому етапі.

Критерій PASS L-002:

- VM = RUNNING;
- `uname -m = aarch64`;
- Ubuntu 24.04;
- 1 CPU / близько 6 GB RAM / 50 GB root volume;
- SSH працює повторно;
- outbound GitHub HTTPS працює;
- не створено платних ресурсів або зайвих inbound ports.

**Cloud Codex на L-002 не потрібен.**

## 8. Наступні gates після L-002

Порядок може змінитися лише за фактичним блокером, але не через повторне переосмислення вже вирішеного.

1. **L-003 / Runtime on Oracle** — clone прийнятого `main`, встановити pinned Hermes штатним способом на ARM64, перевірити CLI/runtime і Docker sandbox; без секретів та без Telegram запуску.
2. **Provider qualification** — один контрольований тест кожного потрібного кандидата на незмінному Hermes checkpoint; обрати production provider за фактом.
3. **Exa integration** — перевірити акаунт/квоту, встановити key без Git, виконати реальний search із джерелами.
4. **Telegram integration** — безпечно ввести token і owner ID, перевірити webhook/polling, запустити один gateway.
5. **systemd + persistence** — автозапуск, reboot, process restart, memory persistence.
6. **backup/restore on target VM** — перевірити disaster recovery реальної інсталяції.
7. **Final E2E acceptance** — усі 8 критерії з розділу 2.

## 9. Прийняті технічні рішення

- **D-001:** Local Codex — браузер/акаунти/SSH/людські підтвердження; Cloud Codex — Linux/Hermes/code/tests.
- **D-002:** GitHub `main` — прийнятий стан; handoff через SHA.
- **D-003:** Oracle Always Free A1 — цільовий host, але придатність остаточно підтверджується тільки реальним provisioning + runtime test.
- **D-004:** NVIDIA = TEST ONLY.
- **D-005:** Production inference-provider не фіксується до фактичної кваліфікації.
- **D-006:** Нуль paid fallback / auto-recharge / прихованих платних маршрутів.
- **D-007:** Telegram long polling; Telethon і voice не потрібні.
- **D-008:** Secrets не передавати через чат/Git; вводити тільки у захищене цільове середовище.
- **D-009:** Hermes pin `v0.22.5` не змінювати без окремого upgrade-рішення і regression.
- **D-010:** Exa — цільовий web search; keyless fallback вимкнений.

## 10. Що НЕ можна вважати підтвердженим

Не перетворювати на факт:

- доступність Oracle capacity до успішного provisioning;
- придатність Gemini Free для 24/7 Hermes до реальних agent-turn tests;
- придатність ChatGPT/Codex subscription як production route до реального Hermes OAuth + usage test;
- працездатність Telegram лише з факту існування BotFather bot-а;
- production-ready статус лише з offline/unit tests;
- безкоштовність сервісу лише через signup credits або trial balance.

## 11. Evidence map

- [`docs/C001-CHECKPOINT.uk.md`](docs/C001-CHECKPOINT.uk.md) — відновлення перерваного quota patch та 20 PASS.
- [`docs/RUNTIME.uk.md`](docs/RUNTIME.uk.md) — cloud runtime, sandbox, guard, deployment artifacts; історичний технічний snapshot.
- [`docs/BACKUP-QUOTA.uk.md`](docs/BACKUP-QUOTA.uk.md) — synthetic backup/restore та quota simulations.
- [`docs/QUOTA-PATCH.uk.md`](docs/QUOTA-PATCH.uk.md) — rationale quota overlay.
- [`docs/L001-CONTROL-PLANE.uk.md`](docs/L001-CONTROL-PLANE.uk.md) — sanitized Local Codex control-plane findings.
- [`config/upstream.json`](config/upstream.json) — pinned Hermes upstream.
- [`reports/c001-recovery.json`](reports/c001-recovery.json) — recovery evidence.

## 12. Правило оновлення цього файлу

Після кожного завершеного milestone:

1. зафіксувати доказ: commit SHA, test result або sanitized control-plane snapshot;
2. змінити статус лише того, що реально перевірено;
3. перенести завершений active task у CONFIRMED;
4. визначити один наступний найменший безпечний етап;
5. не переписувати історію так, ніби план був виконаним фактом;
6. не дублювати великі технічні деталі — посилатися на evidence docs.
