# L-003 — нативний Hermes runtime на Oracle ARM64

Дата: **2 листопада 2026 року**.

Цей документ фіксує sanitized результат етапу L-003. Він не містить public IP, SSH private key, GitHub credentials, API keys, bot token, OAuth credentials або інших секретів.

## Результат

**L-003: PASS.** На перевіреній Oracle Always Free A1 ARM64 VM нативно розгорнуто закріплений Hermes runtime і перевірено ізольований Docker sandbox. Inference provider, Exa, Telegram token та production systemd service на цьому етапі не підключалися.

## Переданий project state

- Accepted project state: `5d8aea60b499e6cf3d21f800174cb18e83ffa2c2`.
- Передача на VM виконана без збереження GitHub PAT/OAuth credentials на сервері.
- Після SCP перевірено 42 project files і Git tree проти accepted commit.

Тимчасові локальні orchestration-файли `l003-work/` є робочими артефактами Local Codex, а не частиною product source. Їх не потрібно комітити в `main`.

## Hermes

- Official source pin: `v0.22.5`.
- Source commit: `bf0203a794a07aac3ff764972ab9087baa4e4f4e`.
- Reviewed local quota patch: **VERIFIED**.
- Patch застосовано через існуючий `scripts/hermes_runtime.py`, не вручну.
- PM install на `aarch64 / linux-arm64`: **PASS**.
- Hermes CLI: **v0.22.5**, реальний запуск PASS.
- `gateway --help`: PASS.
- Managed Python: **3.14.9**, реальний запуск PASS.
- Provider credentials: **не додавалися**.
- Inference requests: **0**.

## Docker sandbox

- Docker: **29.1.3**, ARM64.
- Image: `hermes-ua-sandbox:local`.
- Build з існуючого pinned `deploy/Dockerfile.sandbox`: **PASS**.
- Native `DockerEnvironment` smoke test: **PASS**.

Підтверджено:

- контейнер працює non-root;
- isolated workspace writable;
- `network=none`;
- published ports відсутні;
- metadata endpoint Oracle недоступний із sandbox;
- provider/Telegram/Exa secrets усередині відсутні;
- Docker socket усередині відсутній;
- host project checkout усередині відсутній.

## Мережа та служби

- Нових inbound ports не відкривали.
- SSH лишився обмежений погодженим `/32`.
- Telegram gateway не запускався.
- Production systemd service не активувався.
- Provider OAuth/API setup не виконувався.

## Що L-003 НЕ перевіряв

- production inference provider;
- OpenAI Codex OAuth route;
- Gemini Free route;
- Exa account/key і live web search;
- Telegram token, owner ID і real gateway delivery;
- systemd autostart/reboot persistence;
- real backup/restore на target VM;
- final Telegram E2E.

## Наступний gate

**Provider qualification.** На незмінному verified Oracle/Hermes runtime потрібно провести один контрольований Hermes agent/tool-loop тест для придатного безкоштовного candidate provider, починаючи зі штатного `openai-codex` route, якщо фактичний OAuth/usage доступ це дозволяє. Якщо кандидат не проходить acceptance criteria — перевірити наступний кандидат без paid fallback.
