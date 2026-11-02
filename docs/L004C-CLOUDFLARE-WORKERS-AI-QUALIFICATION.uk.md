# L-004C — кваліфікація Cloudflare Workers AI Free на Oracle

Дата: 2 листопада 2026 року.

## Результат

**PASS / TECHNICALLY QUALIFIED FREE.**

На вже перевіреному Oracle ARM64 host із pinned Hermes `v0.22.5` виконано мінімальну реальну кваліфікацію Cloudflare Workers AI Free через provider `workers-ai` з моделлю `@cf/zai-org/glm-4.7-flash`.

Підтверджено:

- GitHub base перед тестом: `7d061f844093f8012fb072c0e778989ef311fe81`;
- `openai-codex` credential на Oracle видалено і перевірено як відсутній;
- Workers plan: **FREE** до і після тесту;
- payment method: відсутній; окрема оплата для тесту не вимагалася;
- встановлено plugin `cloudflare-workers-ai-provider` із точним commit `f6821d058d504ee6324b0d3217564b93124c09f9`;
- Cloudflare credential збережено тільки на Oracle у service-account environment; `.env` має режим `0600`;
- короткий український turn: **PASS** (`Готовий допомагати!`);
- реальний Hermes-native model → tool → sandbox → tool result → final-answer цикл: **PASS**;
- модель ініціювала два реальні виклики terminal tool;
- контрольний результат tool-loop: `HERMES_CF_OK`;
- фінальна відповідь після tool result: `HERMES_CF_OK`;
- Docker sandbox залишився `network=none`, non-root, без provider secrets, Docker socket та host checkout;
- тестовий sandbox-стан після перевірки прибрано;
- model fallback: **NONE**;
- paid fallback: **NONE**;
- OpenAI/Codex, Gemini, Groq, NVIDIA, Telegram та Exa під час L-004C не використовувалися.

## Фактичне використання

За результатом двох дозволених turns Hermes зафіксував:

- input tokens: **19 004** (`4 196` + `14 808`);
- output tokens: **847** (`80` + `767`).

Cloudflare Dashboard під час контрольної перевірки не показав точного лічильника Neurons, тому `NEURONS_BEFORE`, `NEURONS_AFTER` і фактичний `NEURON_DELTA` залишаються **UNKNOWN**. Будь-який розрахунок Neurons за публічною тарифікацією слід позначати лише як оцінку, а не як виміряний account fact.

## Важливе уточнення ходу тесту

Під час L-004C Локальний Codex спочатку передчасно повідомив, що token нібито вже збережено на Oracle. Наступна перевірка встановила, що Cloudflare variables у `.env` ще були відсутні. Після цього стан було виправлено: існуючий dedicated token без публікації значення передано на Oracle через захищений SSH-процес, а вже після фактичного підтвердження `.env` були виконані обидва inference turns. Отже, PASS базується лише на фінальному виправленому стані.

## Інтеграційний механізм

Використано не plain `custom` provider. У pinned Hermes plugin catalog наявний `cloudflare-workers-ai-provider`, який реєструє окремий provider `workers-ai` і використовує стандартний OpenAI-compatible transport Hermes із provider-specific metadata/configuration. Plugin має статус community, тому для production приймається тільки в зафіксованій версії `f6821d058d504ee6324b0d3217564b93124c09f9` разом із поточним pinned Hermes. Майбутній upgrade Hermes або plugin потребує окремої requalification.

## Security

У цей evidence не включені API token, Account ID, account-specific base URL, Oracle IP, SSH credentials, browser URLs або інші secrets.

Каталог `l004c-work/` є task-local scratch Локального Codex, не є product source, уже покривається правилом `.gitignore` `l*-work/` і не повинен комітитися. До завершення C-002 його можна тимчасово залишити локально для діагностики; після прийняття відтворюваної production-конфігурації його слід перевірити на secrets і видалити.

## Наступний gate

Перед Exa/Telegram потрібно привести tracked production deployment у відповідність із фактично кваліфікованим Cloudflare route: прибрати історичну NVIDIA production-прив'язку, зафіксувати `workers-ai` + `@cf/zai-org/glm-4.7-flash`, перевірити auxiliary routes, fallback policy, startup guard і synthetic quota behavior. Це окремий Cloud Codex етап C-002.
