# L-001 — перевірка control plane перед Oracle deployment

Дата: **2 листопада 2026 року**.

Статус документа: **evidence snapshot**. Це санітизований підсумок перевірки Локального Codex через авторизовані браузерні сесії користувача. Він фіксує побачений стан акаунтів на момент перевірки, але не замінює реальні provisioning/E2E тести. Поточний план і активний етап див. у [`../PROJECT_STATE.md`](../PROJECT_STATE.md).

## Oracle Cloud

- Home Region: **Germany Central (Frankfurt), `eu-frankfurt-1`**; підтверджено через Tenancy Details / Region Management.
- Account status: **Free Tier / Free Trial; Always Free eligible**.
- Платний upgrade не активований.
- `VM.Standard.A1.Flex`: видимий, позначений Always Free-eligible.
- `VM.Standard.E2.1.Micro`: видимий, позначений Always Free-eligible.
- Always Free A1 allowance, який використовує проєкт як межу: **2 OCPU / 12 GB RAM**.
- Trial service limit у консолі був більшим: 16 OCPU / 96 GB; це **не** трактувати як Always Free allowance.
- Поточне використання A1 під час перевірки: 0 OCPU / 0 GB RAM.
- Block/boot volume allowance: **200 GB**, використання 0 GB.
- Backup slots: 5, використання 0/5.
- Availability domains: AD-1, AD-2, AD-3.
- У create-instance wizard A1 був доступний у всіх трьох AD; E2.1.Micro — в AD-3.
- Ubuntu 24.04 Minimal aarch64 був доступний як free image.
- Підготовлена, але не створена конфігурація майбутньої VM: A1 ARM64, **1 OCPU / 6 GB RAM / 50 GB boot volume / on-demand**.
- На момент L-001 список VM був порожній.

### Межа достовірності

Фактичну host capacity L-001 **не підтверджував**. Наявність shape у wizard не гарантує, що provisioning завершиться успішно. Це перевіряється лише створенням VM.

## Telegram

- Bot існує: `@mixa_hermes_ua_bot`.
- Bot token доступний користувачу для подальшого захищеного введення.
- Token у чат або Git не копіювався.
- Webhook state не перевірявся, щоб не переносити token через небезпечний канал.
- Poller не запускався.

## NVIDIA

- Account авторизований.
- Ключ у UI мав стан ACTIVE.
- UI показував до 40 rpm.
- Залишок trial/credits не був підтверджений.
- Новий inference не запускався.
- Роль у проєкті зафіксована як **TEST ONLY**.

## OpenAI Codex precheck

- Plan: ChatGPT Plus.
- На момент перевірки Codex usage був доступний; UI показував залишок 5-годинного й тижневого вікон.
- Credits: 0.
- Auto-recharge: вимкнено.
- Була наявна авторизація Codex CLI.
- Окремої Hermes external-app авторизації серед побачених застосунків не було.
- Hermes OAuth flow не запускався.

Це не доводить придатність ChatGPT/Codex subscription як production inference route. Такий висновок дозволений лише після окремого контрольованого Hermes OAuth + tool-loop + usage тесту.

## GitHub checkpoint

Під час L-001 локальний Codex незалежно підтвердив наявність branch `cloud/runtime-checkpoint-20261102` і commit:

`77f3b23d189d9f2f6581a266c6c38d4d614fe057`

Merge під час L-001 не виконувався. Пізніше цей checkpoint був прийнятий у `main` окремим координаторським кроком.

## Результат L-001

**PASS** для control-plane verification.

Незакриті питання після L-001:

1. Oracle host capacity — UNKNOWN до provisioning.
2. Нативний ARM64 Hermes runtime — UNKNOWN до запуску на реальній VM.
3. Production inference-provider — UNRESOLVED.
4. Telegram delivery/webhook/polling — не перевірені.
5. Exa account/key та real search — не перевірені.

Секрети, паролі, OTP, bot token, auth tokens та приватні SSH-ключі в цей документ не включені.
