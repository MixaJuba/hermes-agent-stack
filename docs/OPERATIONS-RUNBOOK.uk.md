# Hermes production — операційний runbook

Дата: 2 листопада 2026 року.

Цей документ описує безпечну експлуатацію вже прийнятого production baseline після `L-006F`. Він не є інструкцією для повторного розгортання з нуля і не змінює закріплені production pins.

Початкове розгортання, provenance export і контрольоване native restore описані
окремо: [RECOVERY-RUNBOOK.uk.md](RECOVERY-RUNBOOK.uk.md). Це процедура наступного
Local gate, не виконаний cold recovery. L-007A/L-007S не повторювати: за прийнятим
handoff 7 листопада створено новий локальний full ZIP; його restore ще не перевірено,
захищеної копії поза VM ще немає. Архіви L-006F/L-007S не видаляти.

## 1. Нормальний стан

Очікуваний production-стан:

- Oracle VM: одна Always Free A1 ARM64 instance;
- `hermes-ua.service`: enabled + active;
- Telegram: native long polling, webhook absent;
- production pollers: рівно один;
- owner-only access, group access disabled;
- inference: `workers-ai / @cf/zai-org/glm-4.7-flash`;
- Cloudflare plugin pin: `f6821d058d504ee6324b0d3217564b93124c09f9`;
- Hermes pin: `v0.22.5 / bf0203a794a07aac3ff764972ab9087baa4e4f4e`;
- web: keyed Exa only, keyless fallback/rescue off;
- production `.env`: regular file, owner `hermes-agent`, mode `0600`;
- sandbox: `network=none`, non-root, без Docker socket, host checkout, forwarded secrets або published ports.

## 2. Що вважати incident

Incident — це будь-який із таких станів:

- Telegram перестав відповідати;
- `hermes-ua.service` inactive/failed або crash-loop;
- більше одного gateway/poller;
- з'явився Telegram webhook;
- startup guard або Cloudflare plugin attestation FAIL;
- production provider/model/web route відрізняється від канонічного;
- `.env` має неправильного owner/mode;
- з'явився paid route, payment method, PAYGO або auto-recharge;
- пам'ять не переживає service restart/reboot;
- backup/restore більше не проходить;
- secret знайдено у Git, task-artifacts, звичайних logs або sandbox.

## 3. Безпечний порядок діагностики

При incident спочатку нічого не оновлювати і не перевстановлювати.

1. Перевірити VM і SSH.
2. Перевірити `systemctl status hermes-ua.service`.
3. Перевірити кількість gateway/poller процесів.
4. Перевірити startup guard.
5. Перевірити Cloudflare plugin attestation.
6. Перевірити sanitized journal/service logs без друку `.env` або токенів.
7. Визначити конкретну причину до restart/reinstall/upgrade.

Restart дозволений як діагностичний крок лише після перевірки, що другого poller немає. Upgrade Hermes, plugin, model, Exa dependency або Telegram authorization policy не є incident fix без окремої requalification.

## 4. Заборонені швидкі "виправлення"

Без окремого coordinator decision не робити:

- `pip install --upgrade ...` у production runtime;
- Hermes update;
- Cloudflare plugin update;
- зміну model/provider;
- увімкнення fallback provider/model;
- keyless web fallback/rescue;
- додавання payment method/PAYGO/auto-recharge;
- відкриття нового inbound port для Telegram;
- запуск другого manual gateway паралельно з systemd;
- ручне редагування `.env` із виведенням secrets у terminal history/log;
- restore поверх live production home без окремого плану.

## 5. Backup / restore

Прийнятий L-006F baseline підтвердив реальний Hermes backup на private Oracle boot volume та native restore в окремий isolated home.

Операційні правила:

- backup directory: private, mode `0700`;
- archive: owner `hermes-agent`, mode `0600`;
- raw archive не надсилати у chat/Git і не завантажувати в публічне сховище;
- restore спочатку виконувати лише в окремий isolated home;
- не допускати автоматичного створення другого gateway/poller під час restore;
- після restore перевірити memory, session/history, config і permissions;
- production backup не видаляти як частину звичайного cleanup.

Поточний backup на boot volume є restore-capable, але не є off-site disaster-recovery copy. Off-site encrypted copy може бути окремим future hardening task після перевірки zero-cost storage і моделі шифрування.

## 6. Secrets

Production secrets існують тільки в target environment.

Не друкувати й не копіювати в Git/chat/logs:

- Telegram bot token;
- numeric owner ID, якщо він не потрібен для конкретної локальної перевірки;
- Cloudflare token/base URL account identifier;
- Exa key;
- будь-які auth/session credentials.

Після task-local роботи scratch можна видаляти тільки після secret scan і coordinator acceptance.

## 7. Upgrade policy

Перед будь-якою зміною одного з цих компонентів потрібен окремий qualification gate:

- Hermes pin;
- Cloudflare plugin pin;
- Cloudflare model/provider;
- Exa plan/dependency/web implementation;
- Telegram authorization model;
- backup/restore format;
- production host architecture.

Спочатку test/branch/evidence, потім coordinator acceptance, і лише після цього production rollout.

## 8. Контроль після планового restart/reboot

Після планового service restart або VM reboot мінімально підтвердити:

- `hermes-ua.service` active;
- poller count = 1;
- startup guard PASS;
- Cloudflare plugin attestation PASS;
- Telegram відповідає owner;
- long-term memory читається;
- provider/model/web routing незмінні.

## 9. Source of truth

Поточний стан і закріплені рішення: `PROJECT_STATE.md`.

Фінальний live evidence: `docs/L006F-FINAL-PRODUCTION-ACCEPTANCE.uk.md` та `reports/l006f-production-ready.json`.
