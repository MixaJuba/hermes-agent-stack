# L-005 — Exa Free production qualification

Дата: 2 листопада 2026 року.

## Результат

**QUALIFIED_FREE / PASS.**

L-005 завершено Local Codex на production Oracle host після прийняття C-002A.

## Підтверджено

- GitHub main на старті continuation: `f0f8a41857aa9b2c647638ee070900b529e11e19`.
- C-002A delta синхронізовано на Oracle; новий tracked tree перевірено.
- Реальна Oracle attestation Cloudflare plugin: **PASS**.
- Exa account: ACTIVE.
- Exa plan: **FREE**; dashboard показав `$10 credits/month`.
- Payment method: **ABSENT**.
- PAYGO: **NO**.
- Paid subscription: **NO**.
- Credits before test: `$20.00`.
- Створено один dedicated production API key `hermes-agent-prod`.
- UI не запропонував окремих scopes.
- `EXA_API_KEY` безпечно встановлено тільки в protected Oracle environment; `.env` залишився regular file, owner `hermes-agent`, mode `0600`.
- Existing Cloudflare variables збережені.
- Pinned dependency уже була на host: `exa-py==2.10.2`; перевстановлення не виконувалося.
- Production web routing: `backend=exa`, `search_backend=exa`, `extract_backend=exa`.
- `keyless_fallback=false`, `keyless_rescue=false`.
- Реальний Hermes `web_search` через keyed Exa: **PASS**, один Exa `/search` request, три результати.
- Source URLs з фактичної Exa response:
  - `https://github.com/nousresearch/hermes-agent/`
  - `https://github.com/NousResearch/hermes-agent/tree/main`
  - `https://hermes-agent.nousresearch.com/`
- Реальний Hermes `web_extract` через keyed Exa: **PASS**, один Exa `/contents` request, content отримано для першого URL.
- Інший web provider не використовувався.
- Cloudflare inference route не змінювався.
- Telegram та systemd не запускалися.
- OpenAI/Codex і NVIDIA не використовувалися.
- Paid route: **NONE**.
- Credits after test: `$19.99`; UI округлює, тому точна вартість двох Exa calls не встановлена і не заявляється.
- Secret scan: PASS; exact-key scan task-local artifacts не знайшов production key, clipboard/transient values очищені.

## Важлива діагностика під час тесту

Після успішного search перший extract fixture зупинився локально до HTTP-запиту через помилкове очікування test guard щодо назви SDK-поля (`ids` замість фактичного `urls`). Trace підтвердив один `/search` і нуль `/contents`. Guard було виправлено; search не повторювався; після цього виконано рівно один `/contents`, який пройшов PASS. Production source/config через це не змінювалися.

## Безпековий висновок

Exa прийнято як production web-search/content-extraction route для поточного pinned deployment. Keyless rescue/fallback та всі інші web providers мають залишатися вимкненими. Будь-яка майбутня зміна Exa plan, Hermes web implementation або dependency pin потребує повторної перевірки перед зміною production policy.

## Наступний етап

Після coordinator acceptance наступна робота виконується Local Codex на Oracle: Telegram integration → systemd/persistence → real backup/restore → final E2E acceptance.
