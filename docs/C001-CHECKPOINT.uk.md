# C-001: відновлення перерваної перевірки

2 листопада 2026. Project HEAD до checkpoint:
`57f3b264d40a3522741b080cf537829cd01ea305`, branch `work`.
Hermes source лишився detached на `bf0203a794a07aac3ff764972ab9087baa4e4f4e`.
Знайдено лише погоджені source-зміни: `agent/turn_recovery.py` та новий
`agent/quota_profile_copy.py`. Повний project inventory збережено у recovery-звіті.

Наявний manifest, обидві копії patch та хеші source збігаються. Patch повторно
не застосовували. Старий `quota-patched-last-run.txt` містить завершений FAIL
402/українського final, а не PASS. Старий `reports/quota-check.json` був
історичним результатом до застосування patch.

Причина: CLI запускали з checkout, але зовнішній Python test script та його
дочірні процеси імпортували незмінений PM package snapshot. Wrapper тепер
ставить перевірений source першим у PYTHONPATH. Це не перевстановлення чи
зміна PM/lockfiles; subprocess тесту окремо перевіряє origins реальних модулів.

Результат мінімальних перевірок:

- Source attestation PASS: тільки exact patch, відмова за зміненого patch file,
  lockfile, додаткового source file та staged змін; Windows guard збережено.
- Native 402/429: по одній спробі, український final з overlay, нуль HTTP,
  нуль model/paid fallback, збережені reason/retryable/error metadata.
- Без overlay старі відповіді; success/auth/partial/usage-window не змінюються.
- Після вузьких PASS один повний `python3 -m unittest discover -s tests -v`:
  **20 tests PASS**. Regression suite повторно після PASS не запускали.

Відтворення на чистому pinned checkout: `scripts/hermes_runtime.py apply-patch`
з правильним `--source`. Команда перевіряє SHA256, застосовує саме збережений
patch лише за clean стану та перевіряє вже patched копію без повторної мутації.
`deploy/render_config.py` створює несекретний профіль і opt-in `locales/uk.yaml`.
Реальний runtime цього етапу не перевстановлювали, pin/залежності не змінювали.

NVIDIA — TEST ONLY. Production provider не обрано. Live Telegram delivery,
gateway persistence цього error-text та окреме відображення `billing_block`
не перевірені: ця metadata збережена й може містити штатний billing URL.
Не заявляємо готового бота або нового upstream release. Oracle/Exa/Gemini/Codex
provider та inference на цьому завданні не налаштовували й не викликали.

Checkpoint зберігається окремою branch, без merge/main update/PR.
ARM64 перевіряється лише read-only після checkpoint; факти — у recovery-звіті
й кінцевому результаті C-001, без emulator/build/deploy.
