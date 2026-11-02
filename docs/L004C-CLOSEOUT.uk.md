# L-004C — sanitized closeout

**CONFIRMED/PASS**, за фактичним sanitized handoff Local Codex; Cloud Codex не
повторював live test. База live qualification: `7d061f844093f8012fb072c0e778989ef311fe81`.
Початковий [qualification evidence](L004C-CLOUDFLARE-WORKERS-AI-QUALIFICATION.uk.md)
збережено без переписування історії.

- Workers plan **FREE**, payment method **ABSENT**, payment required **NO**.
- Hermes `v0.22.5 / bf0203a794a07aac3ff764972ab9087baa4e4f4e`.
- Community plugin `cloudflare-workers-ai-provider`, exact commit
  `f6821d058d504ee6324b0d3217564b93124c09f9`, provider `workers-ai`.
- Model `@cf/zai-org/glm-4.7-flash`; Ukrainian turn **PASS**.
- Справжній Hermes-native model → terminal → Docker sandbox → tool result →
  final loop **PASS**. Два terminal calls реально виконані. Tool і final:
  `HERMES_CF_OK`.
- Sandbox: non-root, network none, без provider secrets, Docker socket, host checkout.
- OpenAI/Codex credential **ABSENT**. Model/paid fallback **NONE**; OpenAI/Codex,
  NVIDIA, Gemini та Groq не використовувалися.
- Фактичні totals: **19 004 input tokens**, **847 output tokens**.
- Точний Neuron counter Dashboard недоступний; measured delta **UNKNOWN**.
  Це не qualification failure. Оцінки використання не видаємо за вимірювання;
  у цьому closeout оцінку не додаємо.
- Telegram не запускався; Exa не використовувався.

Машинний sanitized запис: [`reports/l004c-qualified.json`](../reports/l004c-qualified.json).
Account ID, token, account URL, Oracle IP, browser/SSH data і деталі передавання
секретів тут не записані. `l004c-work/` не читається, не реконструюється й не додається.

Production inference decision закрито на користь цього Free route. Community
ProviderProfile прийнятий тільки для exact pin разом із exact Hermes; це не
first-party Cloudflare чи native Hermes core. Upgrade потребує requalification.
