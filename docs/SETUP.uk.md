# SETUP — стабільні deployment gates і критерії приймання

Поточний стан, активний етап і наступну дію завжди див. у [`../PROJECT_STATE.md`](../PROJECT_STATE.md).
Цей файл **не визначає поточну чергу робіт**. Він містить стабільні технічні та безпекові умови, які мають бути виконані до фінального приймання системи.

Відтворювана послідовність для нового Linux host, isolated restore і provenance:
[RECOVERY-RUNBOOK.uk.md](RECOVERY-RUNBOOK.uk.md). Gates нижче — вимоги; їхня
наявність не скасовує вже прийняті L-006F/L-007A/L-007S і не наказує повторний rollout.

## 1. Загальні правила

- Production-бюджет: **0 грн**.
- Не активувати auto-recharge, автоматичну покупку credits або платні fallback-маршрути.
- Не встановлювати Hermes/runtime/models на Windows-ноутбук користувача.
- Не зберігати API keys, bot tokens, OAuth credentials, cookies, passwords, OTP або SSH private keys у Git, чатах чи звичайних логах.
- Не змінювати pinned Hermes release без окремого upgrade-рішення і повного regression.
- Не називати компонент готовим до production лише через unit/offline test.

## 2. Gate A — Oracle host

Перед переходом до runtime deployment має бути фактично підтверджено:

- Always Free-eligible VM створюється без платного upgrade;
- цільова architecture = ARM64/aarch64;
- ОС відповідає погодженій Ubuntu 24.04;
- SSH працює повторно;
- outbound HTTPS/GitHub працює;
- немає зайвих inbound ports;
- фактичні CPU/RAM/disk відповідають погодженій безкоштовній конфігурації;
- не створено зайвих або платних Oracle resources.

Наявність shape у Console не дорівнює доступній host capacity. Capacity підтверджується тільки успішним provisioning.

## 3. Gate B — Hermes runtime на цільовій VM

На Oracle VM потрібно:

1. отримати прийнятий `main` з GitHub;
2. використовувати pinned upstream Hermes `v0.22.5` / `bf0203a794a07aac3ff764972ab9087baa4e4f4e`;
3. встановлювати штатним PM/runtime workflow, а не випадковими `pip/uv` змінами;
4. застосувати тільки перевірений quota patch через project wrapper;
5. підтвердити CLI/version/help;
6. підтвердити нативний ARM64 dependency resolution;
7. побудувати/перевірити Docker sandbox;
8. підтвердити, що sandbox не бачить секретів, Docker socket, host checkout або Oracle metadata;
9. не вводити provider/Telegram secrets до завершення базового runtime smoke-test.

Технічний snapshot і команди: [`RUNTIME.uk.md`](RUNTIME.uk.md).

## 4. Gate C — inference-provider qualification

Поточний production provider після L-004C — Cloudflare Workers AI Free,
`workers-ai / @cf/zai-org/glm-4.7-flash`. Повторно його не кваліфікувати без нової
причини. Активний deployment: [C002-CLOUDFLARE-PRODUCTION.uk.md](C002-CLOUDFLARE-PRODUCTION.uk.md).
Новий provider або upgrade потребує окремої кваліфікації; нижче стабільні критерії.

Кожен реальний кандидат проходить однаковий мінімальний тест:

1. авторизація без платного API-балансу або автоматичної оплати;
2. український user turn;
3. реальний Hermes tool call;
4. виконання tool;
5. tool result → фінальна відповідь;
6. достатній context/tool-schema budget;
7. контрольована quota/429 поведінка;
8. відсутність automatic paid/model fallback;
9. умови сервісу дозволяють цільовий режим використання.

Провайдер обирається за результатом цього тесту, а не за marketing/free-credit описом.

NVIDIA у цьому проєкті має статус **TEST ONLY**.

## 5. Gate D — Exa web search

Перед production запуском:

- account/key мають бути підтверджені для конкретного користувача;
- реальна доступна безкоштовна квота має бути перевірена;
- `keyless_fallback` і `keyless_rescue` мають бути вимкнені;
- один реальний пошук повинен повернути фактичні результати та URL;
- агент повинен цитувати саме отримані джерела, а не вигадані посилання;
- при вичерпанні квоти не повинен автоматично переходити на платний search provider.

## 6. Gate E — Telegram

Перед запуском gateway:

- підтвердити bot `@mixa_hermes_ua_bot`;
- token ввести тільки безпосередньо в захищене server environment;
- підтвердити числовий Telegram ID власника;
- не використовувати wildcard або allow-all;
- перевірити webhook state перед long polling;
- запустити тільки один poller;
- перевірити відмову сторонньому Telegram ID.

Token не повинен з'являтися в Git, shell history, chat transcript або test fixture.

## 7. Gate F — systemd, persistence, restart

На цільовій VM потрібно фактично перевірити:

- окремого непривілейованого service user;
- захищений home і secret file permissions;
- systemd unit install/enable/start;
- restart після process failure;
- автоматичний старт після reboot;
- conversation/history persistence після restart;
- довготривалу memory після restart;
- відсутність другого gateway/poller.

Статична `systemd-analyze verify` перевірка не замінює реальний boot/restart test.

## 8. Gate G — backup/restore

Synthetic backup/restore уже перевірявся в cloud environment, але production readiness потребує окремого test на Oracle:

- створити backup реальних persistent data/config без секретів у репозиторії;
- відновити в контрольоване чисте розташування або test instance;
- підтвердити читання memory/history після restore;
- підтвердити permissions;
- використовувати лише безкоштовне storage/backup рішення, якщо воно входить у погоджений бюджет.

Попередні synthetic результати: [`BACKUP-QUOTA.uk.md`](BACKUP-QUOTA.uk.md).

## 9. Gate H — quota/error behavior

Перевірений cloud quota patch має бути відтворений на target runtime.

Необхідно підтвердити:

- 402/429 не запускають нескінченний retry loop;
- немає paid/model fallback;
- user-facing повідомлення зрозуміле українською;
- failure metadata не губиться;
- Telegram delivery цього повідомлення працює;
- можливий billing URL не перетворюється на рекомендацію автоматично оплатити сервіс.

Evidence cloud-етапу: [`C001-CHECKPOINT.uk.md`](C001-CHECKPOINT.uk.md).

## 10. Фінальний E2E acceptance

Система вважається готовою лише якщо на реальній Oracle VM пройдені всі пункти:

1. Telegram-бот відповідає українською.
2. Тримає контекст мінімум 3 послідовних повідомлень.
3. Записує тестовий факт у довготривалу пам'ять і відтворює його після restart.
4. Виконує реальне завдання інструментом через Hermes.
5. Виконує Exa search і повертає посилання на фактично отримані джерела.
6. Приймає запити лише від підтвердженого owner ID; outsider отримує відмову.
7. Автоматично стартує після reboot; backup/restore перевірений.
8. Quota exhaustion обробляється без нескінченних повторів, оплати або платного fallback.
9. Secret isolation перевірена.
10. Усі використані production-сервіси відповідають погодженій умові 0 грн.

Якщо хоча б один критичний пункт не підтверджений, статус проєкту — **не готовий**, а невідоме має залишатися `UNKNOWN`, а не трактуватися як PASS.
