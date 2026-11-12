# AGENTS.md — hermes-agent-stack

Цей файл містить сталі правила роботи для Codex та інших AI-агентів у цьому репозиторії.

**Навігація:** [путівник](docs/INDEX.uk.md) · [архітектура](docs/ARCHITECTURE.uk.md) · [дорожня карта](docs/ROADMAP.uk.md). Вони не замінюють канонічний `PROJECT_STATE.md`. H-001L3 — одноразовий live PASS **за звітом оператора**, не незалежне SSH-підтвердження координатора.

**Оперативна точка продовження:** [центр керування](docs/PROJECT-DASHBOARD.uk.md) показує коротку чергу задач і відповідні докази; канонічним джерелом підтвердженого стану залишається [PROJECT_STATE.md](PROJECT_STATE.md). Після прийняття milestone оновлюй обидва посилання/статуси разом.

## 1. Початок будь-якої роботи

Перед змінами обов'язково прочитай:

1. `PROJECT_STATE.md` — **канонічний поточний стан, активний етап і рішення**.
2. Документ evidence, на який посилається відповідний розділ `PROJECT_STATE.md`.
3. `git status`, поточну branch і актуальний `main`.

Не відновлюй контекст із пам'яті чату, якщо він суперечить репозиторію.
Не повторюй завершене дослідження або тест без конкретної причини.

## 2. Пріоритет джерел

Для **поточного стану і наступної дії**:

`PROJECT_STATE.md` > `README.md` > старі handoff/setup документи > попередні чати.

Для **доказу того, що реально перевірялося**:

фактичний test/log/report/commit > evidence docs > план/опис.

Якщо джерела суперечать одне одному — зупинись, назви суперечність і не вигадуй розв'язання.

## 3. Статуси

Не змішуй:

- `CONFIRMED` — фактична перевірка;
- `OBSERVED` — побачено в UI/account, але не E2E;
- `IN PROGRESS` — виконується зараз;
- `PLANNED` — ще не виконано;
- `UNKNOWN` — даних недостатньо;
- `BLOCKED` — є конкретний блокер.

План ніколи не записуй як виконаний результат.

## 4. Ролі середовищ

### Local Codex

Використовувати для:

- браузера й авторизованих акаунтів;
- Oracle Console;
- Telegram/BotFather;
- provider OAuth/login;
- локального SSH до Oracle;
- безпечного введення секретів;
- дій, що потребують користувача.

Не встановлювати Hermes/runtime/models на Windows-ноутбук.

### Cloud Codex

Використовувати для:

- Linux/cloud workspace;
- Hermes runtime/source;
- коду, патчів і тестів;
- deployment artifacts;
- автономних задач без приватного браузера.

Не дублювати браузерні/акаунтні дії Local Codex.

## 5. Git workflow

- `main` = прийнятий перевірений стан.
- Для технічних змін створюй окрему branch від актуального `main`.
- Не force-push без окремого явного дозволу.
- Local і Cloud не повинні одночасно редагувати ті самі файли.
- Handoff між агентами передавай через commit SHA + коротку delta, не через повторення всієї історії.
- Перед commit: `git diff --check`, релевантні тести, secret scan.
- Не merge/fast-forward неперевірену реалізацію в `main`.

Після завершеного milestone онови `PROJECT_STATE.md` так, щоб він відображав лише підтверджений результат.

## 6. Незмінні product constraints

- Кінцева система: персональний текстовий Hermes-агент українською в Telegram.
- Постійний host: придатна безкоштовна Oracle Cloud інфраструктура, якщо фактично проходить provisioning/runtime checks.
- Бюджет production: 0 грн.
- Заборонені auto-recharge, платні fallback-и та приховані paid routes.
- NVIDIA = `TEST ONLY`.
- Поточний production inference — `workers-ai / @cf/zai-org/glm-4.7-flash` після L-004C/L-006F. Не змінювати без окремого qualification gate.
- Hermes pin: `v0.22.5` / `bf0203a794a07aac3ff764972ab9087baa4e4f4e` до окремого upgrade-рішення.
- Telegram: штатний Hermes gateway, long polling, один poller.
- Telethon, voice/STT/TTS зараз поза scope.
- Exa — цільовий web-search provider; keyless fallback/rescue мають бути вимкнені.

## 7. Секрети

Ніколи не записуй у chat, Git, issue, report, test fixture або звичайний log:

- API keys;
- Telegram bot token;
- OAuth access/refresh tokens;
- cookies;
- passwords/OTP;
- SSH private keys;
- `~/.hermes/.env`;
- `~/.hermes/auth.json`;
- `~/.codex/auth.json`.

Секрети вводити тільки безпосередньо в захищене цільове середовище.
У Git дозволені лише placeholders без реальних значень.

## 8. Provider policy

Не переключай model/provider автоматично.
Не додавай fallback provider без окремого рішення.
Не трактуй signup credits/trial як постійний Free Tier.

Для provider qualification потрібен мінімум:

1. auth без платного балансу;
2. український turn;
3. реальний Hermes tool call;
4. tool result → final answer;
5. перевірка context/tool-schema limits;
6. контрольована quota/429 поведінка;
7. відсутність paid/model fallback;
8. придатність за умовами сервісу для цільового режиму.

## 9. Економія Codex-лімітів

- Не перечитуй увесь repo, якщо `PROJECT_STATE.md` і конкретний evidence doc достатні.
- Спочатку запускай вузький тест; повний regression — один раз після вузького PASS.
- Не запускай однаковий test suite повторно після PASS без нової зміни.
- Не повторюй web research, якщо рішення вже зафіксоване і факти не змінилися.
- Не припускай, що Cloud Codex workspace автоматично оновився з GitHub; перед новою роботою перевір локальні незбережені зміни та актуальний SHA без їхнього стирання.
- Не делегуй Cloud задачу, яку Local може виконати одним read-only браузерним кроком, і навпаки.

## 10. Handoff format

Наприкінці завершеної задачі повертай стисло:

```text
TASK=
OWNER=
BASE_SHA=
RESULT=PASS/FAIL/BLOCKED
CHANGES=
TESTS=
EVIDENCE=
NEW_SHA=
BLOCKERS=
NEXT_RECOMMENDED_GATE=
```

Не переказуй всю історію проєкту, якщо вона вже є в `PROJECT_STATE.md`.

## 11. Публічна документація без перебільшень

- `README.md` описує продукт для відвідувача, а не всі робочі журнали. Деталі Codex/оператора — через `docs/INDEX.uk.md`, `PROJECT_STATE.md`, `AGENTS.md`, `PROJECT_HANDOFF.md`.
- Розрізняй: встановлений пакет; код, прийнятий GitHub; ізольований тест; Telegram E2E за звітом оператора; незалежне повторне live підтвердження. Не підвищуй статус без нових доказів.
- Після кожної зміни можливостей або deployment перевіряй, чи не застаріли публічні README, roadmap, changelog і перші рядки `PROJECT_STATE.md`. Не переписуй минулі звіти як нові.
- Дійсні технічні й recovery-артефакти не видаляй заради вигляду репозиторію; не зливай документаційні гілки без дозволу власника.
