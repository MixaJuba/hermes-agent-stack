# L-004A — кваліфікація `openai-codex` на Oracle

Дата: 2 листопада 2026 року.

## Результат

**TECHNICALLY QUALIFIED / NOT FOR PRODUCTION.**

На вже перевіреному Oracle ARM64 host із pinned Hermes `v0.22.5` виконано мінімальну реальну кваліфікацію штатного provider `openai-codex` через ChatGPT/Codex subscription OAuth.

Підтверджено:

- browser OAuth PKCE через SSH local tunnel: PASS;
- OAuth credential збережено тільки на Oracle в service-account context, права `0600`;
- фактичний model slug для тесту: `gpt-6-luna`;
- коротка українська відповідь: PASS (`Готовий допомагати.`);
- реальний Hermes-native model → tool → sandbox → tool result → final response: PASS;
- контрольний результат tool-loop: `HERMES_CODEX_OK`;
- Docker sandbox залишився `network=none`, non-root, без host secrets, Docker socket і host checkout;
- Codex App-Server Runtime не використовувався;
- `OPENAI_API_KEY` не додавався;
- paid route, OpenRouter fallback, NVIDIA, Gemini, Telegram та Exa не використовувалися.

## Usage

Перед тестом UI показував приблизно 70% залишку 5-годинного allowance і 95% тижневого; після завершення — приблизно 55% і 93% відповідно, credits = 0, auto-recharge = OFF.

Цю різницю **не можна приписувати лише Hermes**, бо в тому самому інтервалі Локальний Codex виконував браузерні, SSH, діагностичні та orchestration-дії в межах того самого Codex allowance.

## Production-рішення

`openai-codex` не використовувати як production inference-provider. Користувач зарезервував ChatGPT/Codex allowance для Локального та Хмарного Codex як розробницьких виконавців.

Перед переходом до production-кандидата credential `openai-codex` на Oracle потрібно безпечно прибрати/відключити штатним Hermes auth flow, щоб виключити випадкове споживання development allowance.

## Security

OAuth callback URL/code, tokens, auth store contents, IP-адреси та інші secrets у цей evidence не включені. Task-local `l004a-work/` не є product source, не комітиться та підлягає видаленню після перевірки на відсутність потрібних артефактів/секретів.
