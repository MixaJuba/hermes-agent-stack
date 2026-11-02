# L-006F — фінальна production-активація та E2E acceptance

Дата: 2 листопада 2026 року.

## Результат

**PRODUCTION_READY / PASS.**

Фінальний Local Codex task завершив production-активацію Hermes на Oracle та повернув структурований PASS без блокерів. Цей документ є sanitized coordinator closeout: секрети, numeric owner ID, токени, приватні account identifiers і raw logs не включені.

## Підтверджено live

### Telegram / authorization

- bot identity перевірено через Telegram Bot API `getMe`: `@mixa_hermes_ua_bot`;
- webhook: NONE;
- numeric owner ID підтверджений зі свіжого private `L006-OWNER` update;
- owner marker після підтвердження прибрано з update queue;
- owner-only policy активна;
- group access disabled;
- foreign numeric user denial перевірено через native synthetic authorization path: PASS;
- denial відбувається до inference/tool activity; у synthetic authorization test мережевих provider calls не було.

Перший старий `L006-OWNER` уже не був доступний у Bot API queue, тому Local Codex коректно не вгадав ID і запросив один свіжий marker. Після нового update owner ID був підтверджений і production config встановлено.

### Production config / gateway

- canonical production config встановлено атомарно;
- startup guard: PASS;
- Cloudflare plugin attestation: PASS;
- manual gateway smoke: PASS;
- під час manual smoke був рівно один poller;
- через native history підтверджено Cloudflare model call через `workers-ai` та Telegram reply `HERMES_TELEGRAM_OK`;
- temporary gateway після smoke зупинено; перед systemd activation було 0 poller;
- accepted `hermes-ua.service` встановлено, enabled + active;
- production poller count після systemd activation: 1.

### Context / long-term memory

Три послідовні Telegram turns реально перевірено:

1. контрольне число `4817` прийнято;
2. наступний turn повернув `4817`;
3. наступний turn повернув `4822` після додавання 5.

Long-term marker було записано через native memory tool і перевірено у реальному memory store.

- long-term memory write: PASS;
- після `systemctl restart hermes-ua` service повернувся з одним poller;
- memory після service restart: PASS;
- один проміжний user-side confirmation був помилково позначений як "інша відповідь/немає відповіді"; production service при цьому залишався active, marker був на диску, а повторна фактична перевірка повернула правильний marker;
- реальний VM reboot: PASS;
- Docker і `hermes-ua.service` автоматично повернулися;
- startup guard + Cloudflare attestation після reboot: PASS;
- poller після reboot: 1;
- memory після reboot: PASS.

### Real Hermes terminal tool / sandbox

Через Telegram виконано real Hermes terminal tool task.

- bot створив, прочитав і видалив `/workspace/final-e2e.txt`;
- реальний terminal invocation підтверджено;
- stdout/result: `HERMES_FINAL_OK`;
- exit code: 0;
- контрольний файл після task видалено;
- sandbox: `network=none`;
- non-root;
- без production keys;
- без Docker socket;
- без host checkout mount;
- accepted resource/sandbox invariants збережені.

### Exa через Telegram

- реальний keyed Exa `web_search` викликаний через production Hermes/Telegram flow;
- Telegram отримав фактичний source URL;
- підтверджене джерело: `https://github.com/nousresearch/hermes-agent/`;
- keyless fallback/rescue: OFF;
- інший web provider не використовувався.

### Quota transport

- accepted synthetic Cloudflare 402/429 logic: PASS з попереднього C-001/C-002 evidence;
- accepted Ukrainian quota message live-delivered через Telegram transport: PASS;
- inference quota навмисно не вичерпувалася;
- `REAL_QUOTA_EXHAUSTED=NO`;
- no provider/model/paid fallback.

### Backup / restore

- real production Hermes backup: PASS;
- backup збережено тільки на private Oracle boot volume;
- backup містив 419 files, приблизно 1.9 MB за фактичним Local Codex evidence;
- backup directory mode `0700`;
- archive owner `hermes-agent`, mode `0600`;
- production home не перезаписувався;
- restore виконано native Hermes restore/import path у separate isolated test home;
- restore harness коригував лише test setup/post-import behavior, коли новий Hermes home створював службові файли; production runtime не змінювався;
- restored long-term memory marker: PASS;
- restored session/history: PASS;
- restored config/state: PASS;
- permissions: private;
- isolated restore-test home після PASS видалено;
- другого poller/service не створено;
- production backup archive залишено на Oracle.

## Production routes / security

- Cloudflare provider: `workers-ai`;
- model: `@cf/zai-org/glm-4.7-flash`;
- Cloudflare plugin exact pin attestation: PASS;
- Exa backend: keyed Exa only;
- `openai-codex` production credential: ABSENT / production forbidden;
- NVIDIA production route: NOT USED;
- paid fallback: NONE;
- нових paid Oracle resources не додано;
- Cloudflare billing не змінювався;
- Exa PAYGO не змінювався;
- Telegram token / provider credentials залишаються тільки у protected Oracle `.env`, owner `hermes-agent`, mode `0600`;
- task-local secret scan: PASS.

## Coordinator decision

Поточний pinned deployment прийнятий як **PRODUCTION READY baseline**.

Це не означає, що проєкт більше ніколи не змінюється. Це означає, що від цієї точки працююча production-система є захищеним baseline: наступні зміни не повинні ламати її без окремого test → evidence → acceptance циклу.

Повторна qualification потрібна перед суттєвою зміною одного з таких компонентів:

- Hermes pin;
- Cloudflare provider plugin pin;
- Cloudflare production model/provider;
- Exa plan/dependency/web implementation;
- Telegram authorization model;
- backup/restore format;
- production host architecture.

## Межі доказу

- Реальне Cloudflare quota exhaustion не виконувалося навмисно; quota behavior прийнято композиційно з synthetic 402/429 логіки та live Telegram delivery accepted quota text.
- Foreign-user denial виконано через native synthetic authorization path, не через створення другого реального Telegram account.
- Поточний backup зберігається на boot volume цієї Oracle VM: restore capability підтверджена, але це ще не off-site disaster-recovery copy.
- L-006F доводить працездатність і recovery поточного pinned deployment; повне відтворення після повної втрати VM з окремого off-site носія не перевірялося.
