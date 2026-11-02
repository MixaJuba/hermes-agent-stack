# C-002A — очікуваний catalog sidecar

База: accepted C-002 `02567a3cad56dcb9d1b3140b682076d1e2a5f2cf`.
Дата: 2 листопада 2026. **Offline corrective checks PASS; live Oracle re-attestation не виконана.**

## Виявлення та причина

За sanitized повідомленням Local Codex, L-005 завершив перевірку accepted main
і sync усіх 54 tracked C-002 files на Oracle без змін `.env`/`config.yaml`.
Local перевірив і видалив свій `l004c-work/` після secret scan. Gate 2 зупинився
до будь-якої Exa account/key/API дії: `unreviewed files in Cloudflare plugin`.
Єдиний зайвий файл — `.hermes-catalog.json`; source hashes, revision, source та
pinned flag залишалися правильними. Ознак компрометації за цією діагностикою
не виявлено. Stop перед Exa був правильним.

Root cause підтверджено читанням exact Hermes
`bf0203a794a07aac3ff764972ab9087baa4e4f4e`:

- `hermes_cli/plugins_cmd_catalog.py`: `CATALOG_SIDECAR` та
  `write_catalog_sidecar_record()` створюють `.hermes-catalog.json` **у папці
  плагіна** з catalog_name/repo/sha/tier/installed_at.
- `hermes_cli/plugins_cmd_install.py` викликає writer під час catalog install.
- Writer прямо називає in-tree файл convenience copy. Авторитетні installer-owned
  дані живуть у `plugins/.install-metadata.json`, не в sidecar.

C-002 test fixture копіювала upstream files і install metadata, але пропускала
згенерований installer-ом sidecar. Через це allowlist давав false positive на
справжньому catalog install. C-002 productionization в іншому лишається чинним.

## Мінімальне виправлення

`deploy/cloudflare_plugin.py` дозволяє лише це конкретне додаткове ім'я.
Якщо sidecar присутній, це має бути regular JSON object без symlink та
невідомих полів. Чотири expected поля повинні точно збігатися з approved pin:

- catalog_name: `cloudflare-workers-ai-provider`;
- repo: approved public repository із `config/cloudflare-plugin.json`;
- sha: `f6821d058d504ee6324b0d3217564b93124c09f9`;
- tier: `community`.

`installed_at` optional, installation-specific: непорожній printable string,
без control characters; timestamp не hard-coded і не hash-pinned. Відсутність
sidecar сумісна з попереднім контрактом. Вона не послаблює mandatory install
metadata checks. Навіть правильний sidecar не компенсує відсутній або
неправильний `.install-metadata.json`.

Revision/source/pinned перевірки та всі три approved SHA256 незмінні. Інші
dotfiles/JSON/довільні файли далі відхиляються; загального ignore для них немає.
Hermes/plugin pins, provider/model, quota patch, .env/config renderer,
Exa/Telegram/systemd не змінювалися.

## Перевірки

Fixture тепер викликає **справжній pinned** `write_catalog_sidecar_record()`
через наявний PM interpreter, без install/network/credentials. Вона також
моделює installer-owned catalog block у install metadata.

- Narrow attestation: **7 PASS** — real sidecar/absence, source tampering,
  revision/source/pin/missing authoritative metadata, arbitrary extras,
  valid/dangling symlink, malformed/wrong fields/invalid timestamp/unknown fields.
- Deployment guard: **10 PASS**.
- Full `python3 -m unittest discover -s tests -v`: **29 PASS**, один запуск
  після narrow PASS; без skips на цьому Linux workspace.
- Немає live inference, private account action, Oracle доступу або запуску сервісів.

Машинний звіт: [`reports/c002a-closeout.json`](../reports/c002a-closeout.json).

## Продовження Local Codex

Після coordinator review/accept C-002A Local Codex синхронізує прийнятий fix,
зберігаючи `.env`, `config.yaml` і наявний `l005-work` state, та **RESUME L-005
FROM GATE 2**. Саме Local виконує live re-attestation. Не повторювати завершені
Phase 1/main verification/Oracle stack sync без нової причини. До Gate 2 PASS
не переходити до Exa account/key/API. Цей документ не заявляє Oracle PASS.
