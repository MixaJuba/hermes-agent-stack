# Путівник по Hermes Agent Stack

**Почніть із [README](../README.md).** Тут посилання для різних ролей, без дублювання канонічного стану.

## Перший погляд

[Архітектура](ARCHITECTURE.uk.md) пояснює шлях повідомлення та межі безпеки. [Дорожня карта](ROADMAP.uk.md) відрізняє готове від запланованого. [Історія](CHANGELOG.uk.md) показує, як проєкт розвивався.

## Для розробника та Codex

[PROJECT_STATE.md](../PROJECT_STATE.md) — **джерело прийнятого стану**, обмежень і наступного gate. [AGENTS.md](../AGENTS.md) — сталі правила. [PROJECT_HANDOFF.md](../PROJECT_HANDOFF.md) — передавання контексту. [CONTRIBUTING.md](../CONTRIBUTING.md) — правила змін. [scripts/](../scripts/) — код, [tests/](../tests/) — перевірки, [config/](../config/) — приклади налаштувань без секретів.

## Для оператора

[OPERATIONS-RUNBOOK.uk.md](OPERATIONS-RUNBOOK.uk.md) — чинні операційні процедури. [RECOVERY-RUNBOOK.uk.md](RECOVERY-RUNBOOK.uk.md) — контрольоване відновлення; **не доказ повного cold recovery** на новій VM. [H-001 implementation](H001-OFFSITE-DR-IMPLEMENTATION.uk.md) та [design](H001-OFFSITE-DR-DESIGN.uk.md) — технічні межі резервування. [SECURITY.md](../SECURITY.md) — чого ніколи не публікувати.

## Рівні доказів

[H-002C: контрольоване scheduled резервування](H002C-SCHEDULED-BACKUP.uk.md) —
offline proposal після H-001L3: ліміти/alerts підготовлені, timer не ввімкнений,
live права/квоти й доставку сповіщень ще перевірятиме Local.

| Етап | Джерело | Що саме доведено |
| --- | --- | --- |
| L-006F | [Acceptance](L006F-FINAL-PRODUCTION-ACCEPTANCE.uk.md), [звіт](../reports/l006f-production-ready.json) | Реальні інтеграційні тести на дату звіту, не live-моніторинг |
| L-007A / L-007S | [Handoff](../PROJECT_HANDOFF.md) | Результати Локального Codex, без публічних приватних SSH-журналів |
| H-001C-FINAL | [Офлайн-звіт](../reports/h001c-final-readiness.json), [PR №1](https://github.com/MixaJuba/hermes-agent-stack/pull/1) | Код злито; age/OCI у тестах імітувалися |
| H-001L3 | [Переказ звіту оператора](../reports/h001l3-operator-summary.json) | Один реальний зашифрований upload/download/restore **зі слів Local Codex**, без незалежного SSH-підтвердження |

**Тлумачення статусів:** «ACCEPTED» означає приймання в межах доказів; «OPERATOR-REPORTED» — наданий звіт без незалежного повтору; «OFFLINE» — тестування без production; «PLANNED» — ще не реалізовано; «BLOCKED» — відома невиконана передумова. Якщо джерела суперечать, звіряйте актуальний main, [PROJECT_STATE.md](../PROJECT_STATE.md) і свіжі докази; старі звіти зберігайте як історію.
