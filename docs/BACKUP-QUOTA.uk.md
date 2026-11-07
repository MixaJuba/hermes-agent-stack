# Штатний резерв і симуляції квоти

Це історичний Cloud snapshot. L-006F пізніше підтвердив реальний local restore;
L-007S — новий локальний full backup, але не його restore. Поточна керована
процедура, контроль gateway revival та off-instance gate:
[RECOVERY-RUNBOOK.uk.md](RECOVERY-RUNBOOK.uk.md). Згадки нижче «ще не перевірено»
і NVIDIA описують саме первинний етап, не поточну production-чергу.

Оновлення C-001: погоджений локальний quota patch уже застосований і native
402/429 з українським overlay перевірені. Нижче опис початкового етапу;
його текст про невиправлений quota UX застарів. Актуально:
[C001-CHECKPOINT.uk.md](C001-CHECKPOINT.uk.md), `reports/quota-check.json`.

Виконано лише в Codex Cloud на синтетичних даних. Робочі data/source,
credentials та pairing не змінювалися. Нових запитів до NVIDIA, установлень,
gateway або ресурсів Oracle не було.

## Резерв і відновлення

Використано справжній `tools.memory_tool.memory_tool` / `MemoryStore`,
`SessionDB` та entry points команд `hermes backup` / `hermes import`
(`run_backup` / `run_import`). Власного формату резервів не додано.

Три окремі процеси створили дані, відновили їх в іншу порожню папку й прочитали
відновлене. Перевірено довготривалий факт, три повідомлення, несекретну
конфігурацію, належність поточному користувачу й відсутність доступу group/other
до home, config, бази та MEMORY.md. SQLite копіювався штатним WAL-safe шляхом.
Архів містив лише синтетичні дані, SOUL та службові lock-файли; `.env`, auth,
credentials, pairing і зовнішніх memory-provider даних у ньому не було.

Тимчасові папки створює сам тест. Перед видаленням перевіряються точний parent,
префікс, відсутність symlink та маркер належності тесту.

**Штатна особливість:** `run_import` викликає `_revive_gateway_after_import`,
який може встановити/активувати службу. У тесті підставлено тільки цей
post-restore callback; сам restore справжній. Службу не запускали.

Для майбутнього Oracle:

1. Використовувати повний штатний `hermes backup -o <private-path> --keep 0`.
   Quick snapshot не замінює повного резерву файлів пам'яті.
2. Працювати від сервісного користувача з `umask 077`, приватною папкою 0700
   та архівом 0600. Успіх backup — exit 0, не саме існування ZIP.
3. Повний ZIP **може містити `.env`, auth і pairing**. У parser цього релізу
   немає `--exclude-secrets` чи шифрування. Не надсилати сирий ZIP у чат, Git
   або публічне сховище. Синтетичний тест резервує лише власну fixture й не
   призначений для очищення секретів живого профілю.
4. Зашифровану зовнішню копію та retention налаштовувати після підтвердження
   безкоштовної квоти сховища. Цього ще не зроблено.
5. Спочатку відновлювати в окремий порожній home. Не запускати довільно
   `hermes import` на сервері без контролю автоматичної активації gateway.
   Перед живим відновленням потрібні перевірка owner/pairing, зупинка єдиного
   poller та review цільової служби. Серверну процедуру ще не перевірено.

## Симуляція 402 та 429

Використано справжній `AIAgent` із pinned runtime. Підставлено OpenAI client
та порожній набір інструментів за test seams upstream. Native turn,
classifier, error/retry/fallback logic виконувалися без заміни. Socket connect
заблоковано tripwire; жодного виклику connect не зафіксовано.

Для кожного статусу: одна спроба клієнта, `failed=true`, `completed=false`,
непорожня кінцева відповідь, причина `billing` або `rate_limit`. Нативний код
перевірив порожній fallback chain, але нічого не активував. Провайдер/модель
залишилися NVIDIA / DeepSeek. `api_max_retries: 1` означає одну загальну
спробу; `auto_recovery_cycles: 0` вимикає наступну драбину.

**Невиконана вимога:** кінцеві quota-відповіді pinned релізу англійською
та радять оплату/резерв. Жодної такої дії тест не виконав, але текст не
відповідає нашому UX і бюджету. Підтримуваний `display.language: uk` додано
до шаблону й нативно перевірено (`get_language() == 'uk'`). Це не перекладає
hardcoded copy у `agent/turn_failure_copy.py` та billing error path.
Штатні overlays `$HERMES_HOME/locales/uk.yaml` застосовуються до рядків через
`agent.i18n.t`, але ці кінцеві відповіді їх не використовують. SOUL або overlay
не вважаємо виправленням цього шляху. Upstream не змінювали.

Профільний output hook також реально перевірено: він не викликається для цих
early results. [Точна причина та незастосована вузька patch-пропозиція](QUOTA-PATCH.uk.md).
Потрібне окремо перевірене рішення текстового обмеження перед готовністю бота.
Telegram delivery, retry наступного повідомлення, restart VM, systemd та зовнішній
backup/restore E2E не перевірені. NVIDIA дозволено лише для тестового прототипу;
іншого провайдера не погоджено.

## Відтворення

```bash
python3 scripts/hermes_runtime.py python -- /workspace/hermes-agent-stack/tests/check_hermes_backup.py
python3 scripts/hermes_runtime.py python -- /workspace/hermes-agent-stack/tests/check_hermes_quota.py
```

Звіти: `reports/backup-check.json`, `reports/quota-check.json`. Лише синтетичні
дані й безпечні результати. Скрипти не призначені для живого профілю. Після
цього етапу нових напрямів у межах перевірки локалізації не починали.
