# PROJECT_HANDOFF.md — передача контексту ChatGPT Command Center / Hermes Agent

> **Увага (9.11.2026):** цей великий handoff містить історичні зрізи та старі наступні кроки. Для будь-якого нового завдання спершу відкрий [актуальний `PROJECT_STATE.md`](PROJECT_STATE.md): H-004L — LIVE PARTIAL за звітом Local Codex, код H-004L прийнято в `main` через [PR №5](https://github.com/MixaJuba/hermes-agent-stack/pull/5); H-002C — код у GitHub, timers OFF. Старі контрольні SHA в розділах нижче є історією, не цільовою версією для роботи.

> **Призначення:** відновити роботу головного координатора, Локального Codex і Хмарного Codex після нового чату, втрати контексту чи завершення сесії. Це **не** інструкція безумовно виконувати зміни та **не** сховище секретів.
>
> **Зріз інформації:** 7 листопада 2026 року. Канонічний GitHub main, перевірений під час створення: **247b0ccd3051a6b057951d99552d58f15aff5222**. Статус H-001C може змінитися пізніше; **перед новою дією перечитати живі GitHub refs**.
>
> **Публічна безпека:** репозиторій MixaJuba/hermes-agent-stack є **публічним**. Тому документ навмисно не містить приватної біографії власника, номерів Telegram ID, IP/OCID, адрес акаунтів, токенів, приватних ключів або резервних архівів.

## 0. Прочитати за дві хвилини: точка продовження

**Мета:** особистий, україномовний, текстовий Telegram ШІ-помічник на окремому постійно працюючому сервері, з пам'яттю, вебпошуком і безпечними інструментами, з **нулем платних production-витрат**. Надалі розвивати його можливості, не руйнуючи вже прийняту працюючу систему.

**Що прийнято:** baseline **L-006F / PRODUCTION_READY**, реально розгорнутий на Oracle Always Free. Telegram, один poller, owner-only, Cloudflare Workers AI Free, keyed Exa, пам'ять, виконання інструментів, systemd/reboot, локальний backup + isolated restore пройшли за детальним звітом Локального Codex. Прийнятий стан записано у PROJECT_STATE.md і evidence. Це доказ прийнятого тестування, **не безперервний онлайн-моніторинг стану сьогодні**.

**Актуальний напрям:** H-001L3 завершено як **один real encrypted off-instance backup + isolated restore за звітом Локального Codex**. Далі — незалежність ключа/record, контроль сховища і безпечний запуск регулярного резервування тільки після окремого gate.

**Статус під час H-001C-FINAL (історична точка, до H-001L3):** **H-001C-FINAL offline source ACCEPTED.** Координатор перевірив source, тести, runbook і ризики. Cloud Codex повідомив **21 targeted PASS, 50/50 full regression PASS, synthetic native roundtrip PASS**; сам координатор не запускав увесь тестовий набір у Hermes runtime й не робив live Oracle перевірок. [PR №1](https://github.com/MixaJuba/hermes-agent-stack/pull/1) **злито в main**: merge commit `7369dee839464e2cdf8e2f0f94d362317e6ff704`, Cloud head `a6b0b1d190b78d9e7dbdfe87f121cc75fa87a049`. Документаційні G1–G4, правила обмеження raw ZIP і зовнішній recovery-record template тепер у GitHub main.

**Історична межа після merge PR №1, до H-001L3:** GitHub merge сам по собі **НЕ ЗМІНИВ Telegram/Oracle production**. Після L-007S є один новий native local ZIP, створений 7 листопада, CRC/склад перевірені; isolated restore саме цього ZIP не виконувався. Off-VM copy відсутня, live age/OCI, free-billing, IAM, незалежні ключі й remote restore **NOT QUALIFIED**. Timer OFF. Не перевстановлювати працюючий Hermes лише через новий GitHub SHA.

**Наступний gate:** не повторювати один реальний тест H-001L3. Підтвердити відновлюваність recovery key/record незалежно від одного пристрою; окремо оцінити remote retention, quota/billing і failure alerting перед активацією timer. Таймер OFF.

**GitHub:** поточний main перевіряти live, бо після H-001C merge координатор оновлював PROJECT_STATE.md та цей handoff; попередні SHA/PR-draft згадки в історії є історичними, не чинним статусом.

## 1. Навіщо проєкт існує і як виглядає успіх

Це не разовий бот і не експериментальна демонстрація. Мета — **власний керований ШІ-агент**, доступний власнику з Telegram незалежно від ввімкненого ноутбука. Він повинен відповідати українською, пам'ятати контекст і збережені відомості, шукати джерела та використовувати ізольовані інструменти. Поступово можна додавати нові навички та автоматизації лише після окремих перевірок сумісності, користі, безпеки й ціни.

**Критерії довготривалої якості:** 24/7 у межах доступності безкоштовної інфраструктури; жодного прихованого платного шляху; контроль доступу одного власника; робоча пам'ять; безпечні інструменти; відтворюваний deployment; recovery після втрати VM; достатній monitoring; зрозумілий український UX. Поточний L-006F забезпечив **перший працюючий baseline**, а не завершив розвиток функцій.

**Поза поточним обсягом:** голос/STT/TTS, Telethon, production OpenAI/Codex, NVIDIA як production-провайдер, установка Hermes або LLM на ноутбук користувача. Не розширювати scope самостійно.

## 2. Власник і стиль співпраці

- Власник проєкту — україномовний користувач, який просить **пояснювати йому простими словами**; глибокі технічні команди та перевірки передавати агентам Codex. Не змушувати власника самостійно розбиратися з Git, Python, systemd, IAM або SSH.
- Координатор має діяти ініціативно, але не самовпевнено: **перевіряти вихідний код, історію змін, точні статуси, звіти й тести**, а не просто погоджуватися з PASS у звіті Codex.
- Власнику давати лаконічно: **що вже працює, що перевірено, який ризик, що робимо далі та що потрібно від нього**. Не показувати довгих технічних переліків без потреби.
- Готувати **один конкретний готовий промпт** відповідному Codex лише тоді, коли від нього справді потрібна дія; не перевантажувати власника вибором плагінів або десятками варіантів.
- Бюджет production — **0 грн**. Не підключати PAYGO, платні акаунти/ресурси/підписки, auto-top-up і запасні платні моделі; якщо безкоштовність не підтверджено у реальному акаунті — STOP.
- Власнику важливий **гарний і зрозумілий публічний README**, не лише DevOps-документація. Технічні докази зберігати окремо в docs/reports. Не прикрашати неперевірене.
- Власник хоче бачити бота, спілкуватися з ним, тестувати звичайні пошукові й пам'яттєві сценарії. Поки триває hardening, не доручати боту самостійно оновлюватися, змінювати systemd, провайдерів, секрети чи видаляти production-файли.
- Користувач може працювати з Windows 10, ChatGPT desktop/web, Codex, PowerShell, SSH. Це **не означає**, що новий чат безумовно має прямий доступ до цих інструментів.
- У документі навмисно немає несуттєвих приватних персональних відомостей власника: публічному репозиторію вони не потрібні.

## 3. Хто за що відповідає: тристороння координація

### Власник / людина

Визначає кінцеву потребу й бюджет, надає необхідний дозвіл на операції з реальними акаунтами, за потреби підтверджує роботу через Telegram/інтерфейс та передає результат Codex. Від нього **не вимагати** копіювання API keys, токенів, паролів чи приватних ключів у ChatGPT або Git.

### ChatGPT у ролі головного координатора

Володіє **планом, пріоритетами, інтеграційною якістю та правилами прийняття**, а не робочим середовищем Codex. Його завдання:
1. Перед кожним новим gate перечитати PROJECT_STATE.md, цей handoff, AGENTS.md, поточні GitHub main/branch refs і релевантні докази.
2. Чітко відрізнити **прийнятий main**, **незавершену branch**, **звіт виконавця**, **доказ live**, **припущення**.
3. Ставити одне перевірюване завдання одному виконавцеві, з обмеженнями й критеріями приймання.
4. Самостійно дивитися diff/source/tests через GitHub connector; перевіряти контрприклади, ризики й приховані залежності.
5. При виявленні проблеми — **CHANGES REQUESTED** у тій самій гілці/завданні; не передавати неперевірений результат у production.
6. Після приймання забезпечувати безпечний Git workflow, оновлювати PROJECT_STATE.md та цей handoff, давати Локальному точний SHA для rollout.
7. Власнику повідомляти дії й результат простими словами.

**Межа повноважень:** координатор не повинен казати «я перевірив Oracle/Telegram live», якщо справді лише переглянув GitHub і Local Codex log. Не видавати виконані offline tests за production qualification.

### Хмарний Codex = інженер коду

Працює у **своєму ізольованому cloud workspace** з GitHub-кодом: дослідження pinned source, патчі, конфігурації, скрипти, offline/synthetic tests, документація й regression. Працює у **своїй branch від актуального main**, комітить і push лише цю branch. Не запускає real Oracle/Telegram/Cloudflare/Exa, не отримує production secrets, не merge у main без review. Наприкінці повертає base SHA, branch, new SHA, change summary, test commands/results, errors/limitations, network scope.

**Важливо:** Codex Cloud може відкривати застарілий snapshot. На H-001C спочатку був BLOCKED на старій f0f8… і відсутньому H-001 design. Для repo sync/branch push **GitHub network дозволений**, попри заборону live provider/network calls. Не просити власника вручну переносити Git bundle, якщо достатньо дозволити безпечний Git fetch.

### Локальний Codex = оператор реальної інфраструктури

Працює з авторизованим браузером, SSH, Oracle Console, Telegram, Cloudflare/Exa account та захищеним введенням конфіденційних значень **у цільовому середовищі**, лише в межах прийнятого gate. Перевіряє actual plans/billing, створює потрібні ресурси, розгортає перевірений SHA, виконує реальні інтеграційні перевірки, підтверджує service/poller і повертає sanitized evidence. Не експериментує безпосередньо на live baseline; при розбіжності з прийнятим кодом — STOP і звіт координатору.

### Правило взаємодії

**Власник → координатор → один Codex → звіт + Git SHA → перевірка координатора → інший Codex лише коли необхідно → live evidence → приймання.**

Не дозволяти Local і Cloud одночасно редагувати однакові tracked files. Не запускати другий Telegram poller. Не передавати авторизацію або секрети через повідомлення. Повторювати вже завершені тести лише з поясненої причини.

## 4. Чинна архітектура (accepted L-006F)

~~~
Власник у Telegram
       ↕ native long polling (один poller; лише owner)
Hermes Agent, Oracle Always Free VM, Ubuntu ARM64
       ├─ Cloudflare Workers AI Free — inference / tools planning
       ├─ Exa (keyed) — web search та extract
       ├─ локальна persistent memory + history
       ├─ Docker non-root, network=none — terminal tools
       ├─ systemd — autostart і restart
       └─ private Hermes backup на локальному boot volume
              ↘ H-001 ПЛАН: age-encrypted off-instance OCI object
~~~

**Закріплені значення:**
- GitHub repository: https://github.com/MixaJuba/hermes-agent-stack
- Oracle host: Always Free VM.Standard.A1.Flex, 1 OCPU / 6 GB RAM, 50 GB boot volume, Ubuntu 24.04.5 Minimal, ARM64; instance **hermes-agent-prod**.
- Hermes pinned: **v0.22.5**, exact commit **bf0203a794a07aac3ff764972ab9087baa4e4f4e**.
- Cloudflare provider: **workers-ai**; model: **@cf/zai-org/glm-4.7-flash**.
- Community Cloudflare Hermes plugin pin: **f6821d058d504ee6324b0d3217564b93124c09f9**.
- Web search + extract: Exa keyed only; dependency **exa-py==2.10.2**. Keyless fallback/rescue OFF.
- Telegram bot: **@mixa_hermes_ua_bot**, webhook NONE, native long polling, один owner-only poller, group access DENIED.
- Docker sandbox: non-root, **network=none**, no Docker socket, no host checkout, no production secrets, no published inbound ports.
- Production systemd: **hermes-ua.service**, enabled + active за прийнятим acceptance.
- Production secrets: захищене середовище Oracle для service account hermes-agent, файл .env owner hermes-agent, mode 0600; не в Git, документації, чатах, логах.
- Production OpenAI/Codex credentials: ABSENT/FORBIDDEN; NVIDIA: TEST ONLY; paid/model fallback: NONE.
- На ноутбуці Windows Hermes/runtime/models **не розгортаються**. Ноутбук лише для адміністрування через Local Codex/SSH.

Будь-який upgrade pinned Hermes, plugin, provider/model, Exa dependency/plan, Telegram authorization, host architecture чи backup/restore format потребує **окремої qualification**.

## 5. Історія виконаного і докази

| Gate | Статус | Суть |
| --- | --- | --- |
| L-001 | PASS | Oracle/Telegram/control-plane precheck. |
| L-002 | PASS | Oracle Always Free ARM64 host. |
| L-003 | PASS | Pinned Hermes runtime та non-root Docker sandbox на Oracle. |
| L-004A | Технічно кваліфіковано, але **відхилено для production** | OpenAI/Codex inference route не відповідав прийнятим production умовам. |
| L-004C | PASS | Cloudflare Workers AI Free, український turn, реальний Hermes model → tool → result → final; HERMES_CF_OK. |
| C-001 | PASS | Synthetic quota 402/429 patch, bounded retries, український текст, відсутність платного fallback. |
| C-002 | PASS | Production config/guard, Cloudflare provider routes, plugin attestation і synthetic regression. |
| C-002A | PASS | Виправлення перевірки installer-created .hermes-catalog.json, без послаблення pin/metadata. |
| L-005 | PASS | Exa Free, payment absent, PAYGO disabled, keyed search + extract live. |
| L-006F | **PRODUCTION_READY / ACCEPTED** | Telegram E2E, owner-only, one poller, 3 turns, memory після restart/reboot, real terminal tool, Exa через Telegram, backup/isolated restore. |
| H-001 | **IN PROGRESS** | Off-instance encrypted disaster recovery, не введено в production. |
| H-001C | **OFFLINE SOURCE ACCEPTED; LIVE NOT QUALIFIED** | PR #1 merged до main, Cloud final a6b0b1d…; 21 targeted / 50 full PASS за Cloud report. |

**Конкретні результати L-006F:** Telegram smoke HERMES_TELEGRAM_OK; 3-turn context marker 4817 → 4817 → 4822; terminal tool HERMES_FINAL_OK; memory survives service restart and real VM reboot; один poller; web search повернув https://github.com/nousresearch/hermes-agent/; local backup 419 files, приблизно 1.9 MB, mode 0600, isolated restore підтвердив memory/session/history/config.

**Межі доказів:** foreign numeric-ID denial було **native synthetic**, не тест через чужий реальний Telegram account. Реальну Cloudflare quota не вичерпували; перевіряли synthetic logic + Telegram delivery повідомлення. Backup з L-006F лежить **на тому самому boot volume**: це не захист від повної втрати VM. Документи ґрунтуються на прийнятих Local Codex evidence і review GitHub; цей чат **не має безперервного live SSH-спостереження**.

**Корисні розбори невдач:** старий owner marker зник із Bot API queue, тому використано новий приватний marker без вгадування ID; один проміжний user-side звіт про помилку пам'яті виявився хибним після повторної перевірки; Exa extract test помилково очікував SDK-поле ids замість urls, тестовий guard виправлено до повторного запиту; Cloudflare sidecar не був внесений у первинну fixture, через що валідна install attestation спочатку давала FAIL. Це доводить потребу відокремлювати помилки **тестового harness** від помилок продукту.

## 6. Активний gate H-001: стан і наступне рішення

**Навіщо:** якщо Oracle boot volume/VM зникнуть, локальний backup також зникне. H-001 прагне забезпечити зашифровану копію поза boot volume та реальний шлях із remote backup до ізольованого restore.

**Плановий, не підтверджений live варіант:** OCI Object Storage Always Free, private Standard bucket, versioning ENABLED, без retention/lifecycle delete спочатку; VM доступ через instance principal, scoped IAM/dynamic group, без static OCI API keys; age client-side encryption до upload; сервер містить лише public recipient, **private recovery identity зберігається окремо від VM/Git/чатів**. Право доступу, реальну безкоштовну квоту і key custody перевіряє Локальний перед створенням ресурсу. OCI в цій самій tenancy не захищає від повної втрати tenancy чи втрати private decrypt key. Заявлені провайдерські free allowances не є гарантією рахунку.

**Що зроблено Хмарним до review:** у branch створено scripts/offsite_backup.py, scripts/offsite_restore.py, scripts/offsite_native.py, config/offsite-backup.example.json, deploy/hermes-backup-offsite.{service,timer}, tests/check_offsite_backup.py, tests/test_offsite_backup.py, docs/H001-OFFSITE-DR-IMPLEMENTATION.uk.md та reports/h001c-offline.json; змінено README/PROJECT_STATE **лише у branch**. Звіт Cloud: 10 вузьких тестів + real native isolated synthetic restore PASS, full regression 39 PASS після корекції runtime paths; age/OCI stubbed, real network/live не тестували; timer NOT ACTIVATED.

**Review:** Cloud H-001C-FINAL виправив OCI HEAD і зафіксував bounds для raw ZIP. PR #1 злито в main 7 листопада. Статус offline source accepted; живі Oracle/age/recovery тести не виконані. Старі 14e4da3c/42 tests — історична попередня ітерація.

**Порядок відновлення роботи:**
1. Перевірити актуальний main/PROJECT_STATE і merged PR #1; L-007S прийнято, новий ZIP тільки локальний.
2. Не повторювати Cloud H-001C/G1–G4/L-007A: підготовлений код, пояснення, тести вже в main. Не перевстановлювати працюючого Hermes.
3. Перед новими ресурсами Local Codex підтверджує actual €0 spend boundary/Always Free billing, OCI IAM/instance-principal feasibility, доступні age/OCI CLI, незалежний key custody й private recovery record. На невідомих витратах/доступах — STOP.
4. Після безпечного preflight й відповідного дозволу виконати одне реальне шифроване off-instance копіювання й ізольований restore з 1 poller, без зміни live home.
5. Лише після підтвердженого live PASS обережно активувати щоденний timer з контролем disk/quota/failure. Оновити PROJECT_STATE і handoff із доказами.

## 7. Джерела правди та навігація

**Порядок пріоритету:** фактично перевірений live-state/evidence для тверджень про інфраструктуру; **актуальний GitHub main + PROJECT_STATE.md** для прийнятих рішень і поточного gate; точні tests/log/report/commit для доказу; reviewed branch для запропонованих змін; цей PROJECT_HANDOFF — карта й контекст; старі handoff/чати — історія. Якщо суперечність, зафіксувати її й перевірити, **не зливати версії в одну вигадану історію**. Git main теж лише snapshot, не доказ того, що VM саме зараз active.

**У GitHub:**
- [PROJECT_STATE.md](PROJECT_STATE.md) — канонічний прийнятий стан, pins, active phase, constraints.
- [AGENTS.md](AGENTS.md) — сталі Codex правила, Git workflow, credentials, task reports.
- [README.md](README.md) — зрозумілий публічний огляд для звичайного читача.
- [docs/OPERATIONS-RUNBOOK.uk.md](docs/OPERATIONS-RUNBOOK.uk.md) — нормальна експлуатація, інциденти, restart/reboot, secrets, backup.
- [docs/L006F-FINAL-PRODUCTION-ACCEPTANCE.uk.md](docs/L006F-FINAL-PRODUCTION-ACCEPTANCE.uk.md) — деталізований live acceptance.
- [reports/l006f-production-ready.json](reports/l006f-production-ready.json) — структурований L-006F evidence.
- [docs/H001-OFFSITE-DR-DESIGN.uk.md](docs/H001-OFFSITE-DR-DESIGN.uk.md) — H-001 constraints, storage, encryption, recovery.
- [docs/L005-EXA-QUALIFICATION.uk.md](docs/L005-EXA-QUALIFICATION.uk.md) — Exa Free.
- [docs/L004C-CLOUDFLARE-WORKERS-AI-QUALIFICATION.uk.md](docs/L004C-CLOUDFLARE-WORKERS-AI-QUALIFICATION.uk.md) — Cloudflare live qualification.
- [docs/C002-CLOUDFLARE-PRODUCTION.uk.md](docs/C002-CLOUDFLARE-PRODUCTION.uk.md), [docs/C002A-CATALOG-SIDECAR.uk.md](docs/C002A-CATALOG-SIDECAR.uk.md) — production guard, plugin attestation.
- [docs/C001-CHECKPOINT.uk.md](docs/C001-CHECKPOINT.uk.md) — quota patch.
- [docs/L003-RUNTIME-ORACLE.uk.md](docs/L003-RUNTIME-ORACLE.uk.md), [docs/L002-ORACLE-HOST.uk.md](docs/L002-ORACLE-HOST.uk.md) — runtime/host.
- [config/upstream.json](config/upstream.json) — exact upstream pin.
- [docs/CONTINUATION.uk.md](docs/CONTINUATION.uk.md) — **legacy pointer, НЕ актуальна точка продовження**.
- Гілка [cloud/h001c-offsite-dr-artifacts](https://github.com/MixaJuba/hermes-agent-stack/tree/cloud/h001c-offsite-dr-artifacts) — новий H-001C code, непогоджені зміни й offline звіт до завершення review.

**Джерела від виконавців:** Local Codex L-006F transcript/report із sanitized live proof; Cloud Codex H-001C conversation/report + commits. Звіт без commit SHA/diff або без доказів **не прирівнювати до перевірки**. Повні приватні browser/SSH logs і вміст Oracle .env **не включати** до handoff.

**Офіційні довідки для механізму координації:**
- ChatGPT Projects: https://help.openai.com/en/articles/10169521-projects-in-chatgpt
- Memory in ChatGPT: https://help.openai.com/en/articles/8590148-memory-in-chatgpt
- Using Codex Cloud: https://help.openai.com/en/articles/20001545-using-codex-cloud
- Codex / AGENTS.md context: https://developers.openai.com/cookbook/examples/codex/iterating-development-workflows-with-codex
- OCI CLI object HEAD: https://docs.oracle.com/en-us/iaas/tools/oci-cli/latest/oci_cli_docs/cmdref/os/object/head.html

## 8. Навички, плагіни, інтеграції: не плутати рівні

- **Hermes plugin:** встановлений і pinned community **Cloudflare Workers AI provider**. Це production частина Hermes, **не** ChatGPT plugin.
- **Hermes web integration:** keyed Exa Python dependency. Це production інструмент, а не Codex skill.
- **Codex Skills:** тематика досліджувалася в ширшому проєкті ChatGPT Command Center. Конкретного підтвердженого набору власноруч інстальованих Skills для цього Hermes stack у перевіреному GitHub main немає. **Не вигадувати** встановлення чи дозволи.
- **ChatGPT GitHub connector:** у цьому чаті фактично використовувався для читання GitHub й review/комітів. Доступність у новому чаті потрібно перевірити, вона залежить від підключення/дозволів. Публічний GitHub URL лишається запасним каналом.
- **Cloud Codex environment** відокремлений від Local Codex на Windows і Oracle VM; Codex Cloud іноді має старий Git snapshot. **GitHub sync допустимий**, якщо заборонені лише live provider/production calls.
- **OpenAI/Codex:** development/review only; не платний inference route для Telegram production. Немає підтвердження, що новому чату дозволено напряму керувати Windows/Oracle, навіть якщо GitHub доступний.

## 9. Чому ChatGPT-пам'яті недостатньо і як забезпечити безперервність

ChatGPT Projects можуть використовувати файли та інші чати проєкту, якщо доступні відповідні налаштування; Memory вибірково відтворює релевантний контекст і **не гарантує повного точного технічного журналу**. Cloud Codex tasks мають окремі робочі копії; незакомічений стан одного task не гарантується у новому. Тому **чати і Memory — зручна підказка, GitHub — перевірювана довговічна база**.

Рекомендована схема:

1. **GitHub main / PROJECT_STATE.md:** тільки прийнятий стан, доказові посилання, незмінні технічні обмеження, наступний gate.
2. **PROJECT_HANDOFF.md:** ролі, широке бачення, історія, помилки, поточний незакритий task і спосіб старту після втрати контексту. Оновлювати **після прийнятого milestone** та під час критичного handoff, не на кожне повідомлення.
3. **AGENTS.md:** короткі завжди чинні правила для Codex. Не дублювати весь handoff у prompt чи AGENTS.
4. **docs/ + reports/:** незмінні для прийнятих gate evidence; нові звіти прив'язувати до SHA, не переписувати історію.
5. **Branch/PR:** усі неперевірені зміни й тести до приймання. Записи гілки не є автоматичним новим канонічним станом.
6. **ChatGPT Project:** продовжувати **в тому самому проєкті**, додати цей файл до файлів проєкту за потреби або дати лінк; не вважати, що навіть у проєкті кожен попередній turn гарантовано доступний.
7. **При переході:** новий координатор спочатку читає цей handoff і **живий main**, перевіряє Cloud branch/новий SHA, повідомляє в 3–5 реченнях встановлений стан, потім робить наступний конкретний крок.

**Оновлення після gate (короткий протокол):**
- TASK, STATUS: PLANNED / IN PROGRESS / BLOCKED / CHANGES REQUESTED / ACCEPTED.
- BASE_SHA, BRANCH, NEW_SHA, MAIN_SHA після фактичної перевірки.
- Що змінили; що протестували offline/live; які ризики й межі доказу.
- Які служби та ресурси реально змінені; що не змінювали.
- Budget/secrets/security outcome; rollback/restore.
- NEXT_ACTION: тільки один наступний відповідальний і gate.

**Git дисципліна:** branch → tests → review → controlled merge/fast-forward → verified main SHA → (за потреби) live rollout → accepted live report. НІКОЛИ не force-push main, не overwrite Oracle .env, не виконувати випадковий restart/upgrade як метод діагностики. При зміні main іншою роботою — переобчислити diff і узгодити базу.

## 10. Типові помилки, яких не повторювати

- **Вірити PASS без code review.** H-001C offline tests підставляли OCI HEAD формат; доводять поведінку stubs, а не справжній API. Відкритий coordinator blocker — доки реально не виправлено.
- **Буквально забороняти весь network.** Так Cloud Codex не міг git fetch і застряг на старому commit. Забороняти provider/live calls, але дозволяти GitHub sync + push у branch.
- **Плутати розробку й rollout.** Код у Cloud branch не означає, що Oracle bucket чи recovery вже існують.
- **Плутати локальний backup із disaster recovery.** Boot volume й локальний archive можуть зникнути разом.
- **Вважати однаковий Oracle account незалежним від усіх аварій.** OCI Object Storage поза VM захищає від boot-volume loss, але не від втрати tenancy або decrypt identity.
- **Зберігати private age recovery key на тому самому Oracle**, де є encrypted copy, або у Git/chat. Якщо окремий recovery key custody не готовий, STOP.
- **Виконувати Hermes import без контролю post-import gateway revival.** Може запустити другий poller.
- **Встановлювати “свіжіші” Hermes/plugin/dependency/model без requalification.** Pins та accepted environment захищають від регресій.
- **Змішувати документацію історії з поточним станом.** docs/CONTINUATION.uk.md — legacy; main PROJECT_STATE.md — канонічний.
- **Публікувати внутрішні секрети/особисті відомості.** GitHub repository public, а full Hermes ZIP може містити secrets.
- **Оголошувати production актуальним лише за GitHub SHA.** Реальний runtime перевіряти read-only, коли потрібна live-гарантія.
- **Робити великі повторні дослідження без причини.** Почати з relevant docs + narrow test; повний regression після суттєвих змін, а не серією однакових запусків.

## 11. Правила для нового чату / відновлення після повної втрати контексту

1. **Не починати з нуля.** Прочитати цей файл та реальні GitHub PROJECT_STATE.md + AGENTS.md. Якщо GitHub connector не підключений, працювати через публічні URL або попросити прикріпити актуальний snapshot; **не заявляти**, що GitHub перевірено, без реального доступу.
2. Знайти git main HEAD, Cloud H-001C branch HEAD, порівняти SHA, список змінених файлів, наявний review статус. Документ — snapshot, не автоматичне live-свідчення.
3. Стисло підтвердити власнику: прийнятий baseline L-006F, активний H-001C, чи виправлено HEAD/OCI blocker, яка наступна дія. Ніяких абстрактних загальних порад.
4. Якщо Cloud Codex повернув новий звіт — першочергово провести **кодове рев'ю нового commit**, а не запускати Локального без перевірки.
5. При суттєвій невідповідності між main, branch, evidence або повідомленнями — STOP, назвати суперечність, визначити потрібний мінімальний доказ.
6. При новому approved gate оновити PROJECT_STATE.md і за потреби PROJECT_HANDOFF.md **тільки на підставі справжніх результатів**. Не редагувати production без окремого дозволеного Local task.
7. Власнику пояснювати просто і коротко, технічну деталь залишати в Codex prompts або документації.

### Коротка стартова фраза для нового чату

> Продовжуємо Hermes Agent Stack. Ти головний координатор. Спочатку перечитай АКТУАЛЬНІ GitHub main/PROJECT_STATE.md, PROJECT_HANDOFF.md, AGENTS.md і H-001L3 summary. L-006F production baseline accepted; H-001C-FINAL код прийнятий і злитий; за звітом Local H-001L3 один real OCI encrypted backup/isolated restore пройшов, timer OFF. Не повторюй уже виконане. Далі — незалежний доступ до key/record, оцінка росту та безкоштовності сховища, failure alerts; лише потім дозволяти scheduled backup. Не змішуй звіт із власним live proof і не змінюй production без gate. Пояснюй власнику просто.

---

**Ключова перевірка на вході:** H-001C уже в main, H-001L3 відомий зі звіту оператора. Перевір лише нові факти, не повторюй попередній live-тест без конкретної причини. Merge GitHub не доводить поточний стан сервера.

**Оновлення документа:** після кожного прийнятого milestone або суттєвої зміни відповідальних/обмежень; публічний файл ніколи не повинен містити реальні credentials чи приватні дані.

## 12. L-007A read-only audit — прийнято 7 листопада 2026

Локальний Codex провів інвентаризацію без змін production. На момент перевірки `hermes-ua.service` active, poller=1, core config/pins/plugin/sandbox/guard PASS. Серверний `/opt/hermes-agent-stack` є **verified export без `.git`**, а не Git checkout: 56/56 blobs збігаються із деревом commit `f0f8a41857aa9b2c647638ee070900b529e11e19` (`a4d147cf3aefc322d53966f031ef5ee93df37579`). Порівняння з тогочасним main `3e89f08499279c70d833bd8f2e4d94bf679a6d5d` показало лише docs/evidence differences, production drift не виявлено в audited scope. Не синхронізувати runtime тільки заради цих документів.

Відкриті G1–G4: cold bootstrap runbook, точна isolated native restore procedure, provenance deployed export, застарілий історичний upstream/NVIDIA metadata. Cold recovery НЕ кваліфіковано; H-001C із часом було [злито через PR #1](https://github.com/MixaJuba/hermes-agent-stack/pull/1), але без live rollout. Один відомий full local ZIP (1 970 116 bytes, 2 листопада) на тому самому VM boot volume, DB/WAL має пізніший mtime; регулярний backup timer не діє, off-instance copy не підтверджена. OCI CLI та `age` на host немає; IAM/key custody/free-billing gate UNKNOWN. Oracle Free Trial має розбіжність commitment views, показане consumption/overage €0 не є гарантією відсутності майбутніх витрат. L-007A report та `inventory.sanitized.json` надані власником у чаті; докладний приватний inventory **не публікувати в GitHub**. Наступний пріоритет: контрольований **свіжий одноразовий локальний Hermes backup без зміни gateway**, після нього GitHub-only G1–G4 і off-instance DR qualification, без зайвого повторного аудиту.


## 13. L-007S — одноразовий свіжий backup (звіт Local Codex, 7 листопада 2026)

Local Codex повідомив про **PASS**: створено рівно один новий Hermes native full backup у приватному каталозі на тій самій Oracle VM, без перезапуску gateway. UTC назва `hermes-backup-l007s-20261106T235846Z-a95448b3.zip`; creation 2026-11-07 01:58:48 Europe/Kyiv, 2 256 760 bytes, 423 entries, SHA256 `62b706c76d60e4ab04c881f3f2a08080edb628b8086fe70e2b1aacb1219b44d6`; native exit 0, ZIP CRC/required members PASS за звітом, 0600/0700; попередній backup збережений. `hermes-ua.service` active, Telegram connected, pollers=1; код/config/credentials/systemd не змінювали. Новий ZIP спочатку мав ширші права, виправлені на 0600 саме для нього. **Restore цього нового архіву NOT RUN**; off-instance copy відсутня; повний H-001 NOT COMPLETE. Власник надав лише хід роботи й sanitized фінальний звіт, а не повний первинний SSH evidence. Не викликати знову L-007S без нової потреби. Наступна пріоритетна задача — **H-001 zero-cost/permissions/key custody/OCI CLI+age feasibility preflight** перед будь-яким платним або live rollout; усунути raw ZIP retention і забезпечити поза-VM recovery record до timer. G1–G4 GitHub документація залишається pending, але не повинна блокувати забезпечення off-instance recovery.


## 14. 7 листопада — coordinator offline acceptance H-001C-FINAL

GitHub PR #1 merged, merge commit `7369dee839464e2cdf8e2f0f94d362317e6ff704`, reviewed Cloud source `a6b0b1d190b78d9e7dbdfe87f121cc75fa87a049`. Закрито G1–G4 documentation, додано raw ZIP bounded retention та зовнішній record template, Cloud 50/50 regression PASS. Coordinator перевірив GitHub source/docs та upstream, але не виконав власного live OCI/age або independent Hermes test run. **Production bot unchanged; no OCI bucket, no scheduled backup timer, no confirmed off-instance copy; live H-001 pending.** L-007S new native local full backup від 7 листопада — ZIP verified, isolated restore NOT RUN. Наступний відповідальний — Local Codex, мінімальний безпечний H-001 live preflight щодо фактичних €0 витрат, ключів та доступів, потім один real encrypted backup/isolated restore за необхідних дозволів. Хмарного Codex повторно не залучати без виявленого коду-defect.

## 15. H-001L3 — завершене разове зовнішнє відновлення за звітом Local Codex (7 листопада 2026)

Після read-only H-001L/H-001L2 зі статусом BLOCKED власник надав результати H-001L3: приватний OCI Standard bucket, вузький IAM однієї VM, кваліфіковані age/OCI CLI, зіставлення source з прийнятим Git tree, один реальний encrypted upload/HEAD/get/SHA-256/isolated native restore. Оператор повідомив PASS пам'яті, історії та сесій, конфігурації й плагінів; один Telegram poller, без restart, без видалення попередніх копій, timer OFF. Власник перевірив два захищені записи ключа.

Рівень доказу: **owner-supplied operator report**, без незалежного нового SSH/OCI доступу координатора. Незалежне від одного пристрою зберігання ключа і record ще не засвідчене; повний cold recovery на новій VM не виконувався. Платні опції, за повідомленням Local, не вмикалися; доступна Free Trial/Free квота, але без гарантії майбутніх нульових списань. Не публікувати ключ, приватний record, account/object ID, деталі IAM чи архів.

Наступне завдання: за мінімальних лімітів Codex довести незалежне відновлення key/record, контроль накопичення у Object Storage і повідомлення про збої; scheduled timer тільки після окремого узгодженого рішення. H-001C та L-007A/L-007S/H-001L3 повторно не запускати без ознак регресії. Нову Cloud Codex робочу копію синхронізувати лише під нове обґрунтоване завдання. Путівник: [docs/INDEX.uk.md](docs/INDEX.uk.md), summarized evidence: [reports/h001l3-operator-summary.json](reports/h001l3-operator-summary.json).

## H-002C — нова Cloud задача, offline readiness

Власник окремо доручив підготувати safe scheduled backups після H-001L3. У новій
branch від main `9602e0a…` підготовлено bounded uploads без remote deletion/IAM
expansion, private alerts/receipts і короткий quota approval. Це не скасовує
operator-reported H-001L3 PASS і не є timer activation. Після code acceptance
потрібний контрольований Local gate; умови та залишкові ризики:
[H002C-SCHEDULED-BACKUP.uk.md](docs/H002C-SCHEDULED-BACKUP.uk.md).
