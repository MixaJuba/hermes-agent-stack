# L-006F — фінальна production-активація та E2E acceptance

Дата: 2 листопада 2026 року.

## Результат

**PRODUCTION_READY / PASS.**

Фінальний Local Codex task завершив production-активацію Hermes на Oracle та повернув структурований PASS без блокерів. Цей документ є sanitized coordinator closeout; секрети, numeric owner ID, токени та приватні значення не включені.

## Підтверджено

- Telegram bot identity: `@mixa_hermes_ua_bot`.
- Numeric owner ID підтверджений; owner-only policy активна.
- Telegram webhook відсутній; production працює через native long polling.
- Telegram token зберігається лише у protected Oracle `.env`, owner `hermes-agent`, mode `0600`.
- Production config: PASS.
- Startup guard: PASS.
- Manual gateway smoke: PASS.
- systemd service: enabled + active.
- Рівно один production poller.
- Українська відповідь через Telegram: PASS.
- Три послідовні Telegram turns з context continuity: PASS.
- Long-term memory write: PASS.
- Memory після service restart: PASS.
- Реальний VM reboot: PASS.
- Автозапуск після reboot: PASS.
- Memory після reboot: PASS.
- Реальний Hermes terminal tool через Telegram: PASS; контрольний результат `HERMES_FINAL_OK`.
- Docker sandbox invariants: PASS.
- Реальний keyed Exa search через Telegram: PASS; фактичне джерело `https://github.com/nousresearch/hermes-agent/`.
- Foreign numeric user denial перевірено через native synthetic authorization path: PASS.
- Group access: DENIED.
- Accepted synthetic quota logic: PASS; реальну квоту навмисно не вичерпували.
- Accepted Ukrainian quota message доставлено через Telegram transport: PASS.
- Реальний backup на private Oracle boot volume: PASS.
- Backup directory mode `0700`, archive owner `hermes-agent`, mode `0600`.
- Реальний restore в окремий isolated home: PASS.
- Restore memory: PASS.
- Restore session/history: PASS.
- Другий poller не створено.
- Cloudflare production route незмінний: `workers-ai / @cf/zai-org/glm-4.7-flash`.
- Cloudflare plugin attestation: PASS.
- Exa backend: keyed Exa only; keyless fallback/rescue OFF.
- `openai-codex` production credential absent/forbidden.
- NVIDIA production route не використовувався.
- Paid fallback: NONE.
- Нових платних Oracle resources не додано.
- Cloudflare billing не змінювався.
- Exa PAYGO не змінювався.
- Final task-local secret scan: PASS.
- Final E2E: PASS.

## Production decision

Поточний pinned deployment вважається **PRODUCTION READY**.

Нормальний режим після цього closeout — експлуатація та моніторинг, а не продовження build-gates.

Повторна qualification потрібна перед суттєвою зміною одного з таких компонентів:

- Hermes pin;
- Cloudflare provider plugin pin;
- Cloudflare production model/provider;
- Exa plan/dependency/web implementation;
- Telegram authorization model;
- backup/restore format або production host architecture.

## Межі доказу

- Реальне Cloudflare quota exhaustion не виконувалося навмисно; quota behavior прийнято композиційно з раніше перевіреної synthetic 402/429 логіки та live Telegram delivery accepted quota text.
- Foreign-user denial виконано через native synthetic authorization path, не через створення другого реального Telegram account.
- Backup зберігається приватно на boot volume цієї Oracle VM; це перевірений restore-capable backup, але не off-site disaster-recovery copy.
