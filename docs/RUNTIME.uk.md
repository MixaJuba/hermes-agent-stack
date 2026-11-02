# Віддалений runtime і заготовка Oracle

> Історичний NVIDIA TEST ONLY snapshot C-001. Активна production-конфігурація
> вже Cloudflare: [C-002](C002-CLOUDFLARE-PRODUCTION.uk.md), канонічний стан —
> [PROJECT_STATE.md](../PROJECT_STATE.md). NVIDIA-прив’язка нижче описує історію,
> не поточний tracked deployment. Підсумок source/runtime/ізоляції збережено.

## Межі поточного результату

У Codex Cloud штатним PM установлено Hermes **v0.22.5**, commit
`bf0203a794a07aac3ff764972ab9087baa4e4f4e`, керований **Python 3.14.9**.
Це підготовче середовище, не постійний сервер бота. Gateway не запущений.

**Блокер постійної експлуатації залишається:** NVIDIA API Trial Terms 1.2/1.4
дозволяють evaluation/internal testing, а не production без окремої підписки.
Безкоштовний production-маршрут ще не обраний і не погоджений. Конфігурація
NVIDIA нижче — лише тестова заготовка, не дозвіл на постійного бота. Платні
або сторонні резерви не підключаємо. Результат Playground не перевіряє API-ключ.

## Відтворення встановлення — тільки на віддаленому Linux

Використовувати існуючий офіційний checkout. `scripts/hermes_runtime.py`
відмовляється працювати поза Linux, при іншому HEAD або tracked-змінах upstream.
Тепер дозволений тільки точний локальний quota patch з `config/hermes-patch.json`;
довільні tracked/untracked/staged зміни відхиляються. Wrapper перевіряє HEAD,
SHA256 patch і змінених файлів. Нову чисту pinned копію готувати командою
`python3 scripts/hermes_runtime.py apply-patch`; вона не встановлює залежності
й без повторного застосування перевіряє вже patched стан.
Не запускати встановлення повторно, якщо runtime уже готовий: спочатку `cli --version`.

```bash
cd /workspace/hermes-agent-stack
python3 scripts/hermes_runtime.py cli -- --version
python3 scripts/hermes_runtime.py cli -- gateway --help
# Лише для відтворення відсутнього runtime:
python3 scripts/hermes_runtime.py install
```

Helper викликає саме `python -m pm.cli install --without agent-browser --without
cua-driver`, потім PM extras `telegram` і `exa`. Немає raw pip/uv, оновлення
lockfiles або збереження значень ключів. PM сам перевіряє артефакти й lock.
Для Oracle шляхи задаються явно: `--source /opt/hermes-agent
--home /var/lib/hermes-agent --tools /var/lib/hermes-agent/tools` перед командою.
Сам helper не встановлює системні пакети, не створює VM/користувача й не клонує код.

Не встановлені Desktop, agent-browser, Chromium, cua-driver, faster-whisper,
sounddevice, edge-tts, ElevenLabs. Штатний PM установив обов'язкові tool roots,
зокрема ffmpeg; це не ввімкнення голосу. Core Python-залежності upstream
(наприклад browser-harness) не вилучаємо всупереч lockfile; браузерні binaries
та сервіси не встановлювали і не запускали.

## Конфігурація без секретів

`deploy/hermes-config.json` — JSON, який є валідним YAML для `config.yaml` Hermes.
Поля звірено з pinned кодом; виконано нативний `validate_config_structure`.
Секретів та owner ID у файлі немає. Це не готовий профіль для запуску.

- Єдиний основний маршрут — NVIDIA. `fallback_model: []`; auxiliary маршрути
  явно NVIDIA з порожніми fallback chains. Автозаголовки та background review
  вимкнені. Не вмикати сторонні credentials/borrowed logins або auto-routing.
- Exa закріплено для search/extract. `keyless_fallback` і `keyless_rescue`
  вимкнені. Це keyed маршрут, що має працювати лише після перевірки безкоштовної
  квоти акаунта; відсутність ключа є помилкою, а не приводом змінити провайдера.
- `api_max_retries: 1`, `auto_recovery_cycles: 0`, одна concurrent session,
  8 tool-ітерацій і бюджет часу 180 секунд. Це перевірені налаштування, але
  поведінка живого API при 402/429 ще не перевірена.
- **Не додавати вигаданий `model.max_tokens`:** цей реліз описує output limits
  як provider-owned. Для контрольованих programmatic тестів існує параметр
  конструктора `AIAgent(max_tokens=...)`. Ліміти реального gateway слід окремо
  підтвердити перед експлуатацією.
- Дозволені текстові toolsets: terminal/file/memory/session_search/web/clarify.
  Голос вимкнено; TTS/vision/browser/delegation/cloud-backend toolsets не ввімкнені.

## Ізоляція інструментів

`deploy/Dockerfile.sandbox` має pinned multiarch digest офіційного Python-образу.
Штатний Docker backend використовує `docker_network: false`, окрему sandbox
папку, host UID непривілейованого сервісу й не монтує launch cwd, секрети або
Docker socket. `container_persistent: true` забезпечує штатну writable workspace;
tmpfs без UID-відповідності в початковій пробі не дозволяв запис — це виправлено.

У цій хмарі Docker daemon перевірений. Образ зібрано без мережі build-кроків:

```bash
docker build --network none -t hermes-ua-sandbox:local -f deploy/Dockerfile.sandbox deploy
```

Buildx намагався записати cache в read-only home; тут використано штатний legacy
builder (`DOCKER_BUILDKIT=0`) без зміни Docker credentials/config, TLS або sandbox.
На Oracle можна використати звичайний доступний builder. Якщо Docker-крокам
потрібна мережа в Codex Cloud, дотримуватися його proxy/CA інструкцій; не вимикати TLS.

## Власник і захищений ввід

`deploy/gateway_guard.py` відмовляє за відсутніх ключів/owner ID, wildcard чи
кількох ID, global/group grants, allow-all, додаткових policy overrides,
неперевірених fallback/Docker flags або незахищеного secret file. Перевіряє
обидва layouts pairing (`pairing` та `platforms/pairing`): сторонній approved ID
блокує запуск, **існуючий стан не видаляється**. Додаткові профілі потребують review.

Нативний Hermes справді об'єднує pairing approvals із allowlist: окремий offline
тест продемонстрував grant чужому synthetic ID та відмову нашого startup guard.

Лише після особистого підтвердження owner, на віддаленому хості:

```bash
# TELEGRAM_ALLOWED_USERS має бути заданий підтвердженим значенням, не wildcard.
python3 deploy/render_config.py --home /var/lib/hermes-agent
```

Renderer не записує ключів і не перезаписує наявні config/SOUL. `allowed_chats`
заповнюється тільки DM підтвердженого власника. Захищені реальні ключі вводити
особисто через приватний TTY/SSH; офіційний `hermes gateway setup` має маскований
Telegram prompt. Secret file має бути owner-owned `0600`, home `0700`, поза Git
і sandbox, без shell tracing/recording. Proxy placeholder Codex не переносити
як справжній серверний ключ. URL-path підстановка Telegram-токена cloud proxy
не підтверджена — її не вважати робочою інтеграцією. Gateway не запускати до
підтвердження всіх доступів і перевірки guard. Наявні state/config не видаляти.

## Systemd: лише шаблон, не активована служба

`deploy/hermes-ua.service` передбачає виділеного користувача `hermes-agent`,
приватний home, EnvironmentFile, ExecStartPre guard, Docker access, обмежений
restart та sandbox-параметри systemd. Потрібні каталог `/var/lib/hermes-agent/workspace`,
перевірена Oracle VM, системні prerequisites та встановлений pinned runtime.
Unit не встановлювали й не вмикали; reboot/autostart/реальний restart не перевірені.
Статична перевірка `systemd-analyze verify --man=no` завершилася без помилок;
вона не замінює запуск на цільовій VM.
Доступ до Docker потрібний orchestrator, але socket не надається sandbox інструментів.

## Що реально перевірено й що попереду

```bash
python3 -m unittest discover -s tests -v
python3 scripts/hermes_runtime.py python -- /workspace/hermes-agent-stack/tests/check_hermes_offline.py
python3 scripts/hermes_runtime.py python -- /workspace/hermes-agent-stack/tests/check_hermes_sandbox.py
```

Пройдено: 19 stdlib-тестів; version/help CLI; нативна config validation; вибір
лише Exa без keyless; нативні owner/outsider/missing-owner перевірки; pairing
UNION + startup block; збереження 3 synthetic messages після close/reopen БД;
нешкідлива команда через справжній DockerEnvironment Hermes з файловим round-trip,
non-root, відсутніми ключами/socket/host data й недоступними метаданими.

Це **не** реальний model -> tool -> reply цикл, не перевірка пам'яті діалогом
після reboot і не наскрізний Telegram-тест. Блокер cloud inference діагностується
окремо; успіх Playground його не скасовує. Oracle, Exa account, Telegram secret,
owner ID, E2E, autostart і зашифровані зовнішні backup/restore ще попереду.
Синтетичні native backup/restore та 402/429 перевірено на наступному етапі:
[BACKUP-QUOTA.uk.md](BACKUP-QUOTA.uk.md). Quota patch з українським overlay
перевірено в [C-001](C001-CHECKPOINT.uk.md); живу Telegram delivery не перевіряли.
Наступні дії — за окремими підтвердженими доступами; платних альтернатив немає.
