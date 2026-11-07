# Як розвивати проєкт без ризику для Hermes

Проєкт має приватний працюючий Telegram-агент. GitHub public **не означає** публічний сервіс.

Перед роботою читайте [PROJECT_STATE.md](PROJECT_STATE.md), [AGENTS.md](AGENTS.md) і потрібний [evidence](docs/INDEX.uk.md). Звірте актуальний main, створіть гілку і визначте один вимірюваний результат. Не дублюйте прийняті тести.

**Робочий процес:** branch → точкові перевірки → secret scan / `git diff --check` → PR → review → контрольоване приймання. Merge у GitHub **не є** розгортанням на Oracle. Не оновлюйте pinned Hermes/модель/плагін, Telegram owner access, IAM, billing чи systemd без окремого дозволеного gate.

У PR обов'язково пояснюйте, що змінилось, base/new SHA, реальні тести та їхні межі, вплив на production, ризики й наступну залежність. Імітацію age/OCI **не** називайте live Oracle-верифікацією.

| Вміст | Файл |
| --- | --- |
| Огляд для людей | [README.md](README.md) |
| Канонічний стан | [PROJECT_STATE.md](PROJECT_STATE.md) |
| Контекст агента | [PROJECT_HANDOFF.md](PROJECT_HANDOFF.md) |
| Сталі правила Codex | [AGENTS.md](AGENTS.md) |
| Пояснення й навігація | [docs/INDEX.uk.md](docs/INDEX.uk.md) |
| Докази без секретів | [reports/](reports/) |

У GitHub **не публікувати** токени, приватні ключі, повні резервні архіви, приватні операційні записи чи браузерні/SSH журнали. Див. [SECURITY.md](SECURITY.md).

Окремої LICENSE на момент оформлення не зафіксовано: публічний доступ до коду сам по собі не надає необмежених прав на перевикористання. Автоматичних запусків GitHub Actions у прийнятій історії немає; не створюйте дорогі CI-процеси без оцінки.
