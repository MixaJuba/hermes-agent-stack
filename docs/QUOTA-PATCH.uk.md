# Вузький блокер локалізації quota-відповідей

Перевірено на pinned Hermes v0.22.5 / `bf0203a794a07aac3ff764972ab9087baa4e4f4e`.
Оновлення C-001, 2 листопада 2026: погоджений локальний patch **уже застосовано
та перевірено**. Canonical patch: `patches/quota-profile-copy.patch`, точний
base commit і SHA256: `config/hermes-patch.json`. Це pinned Hermes + local patch,
не новий upstream release. `proposals/` збережено як історію погодження.

Native 402/429 дають український final з `deploy/locales/uk.yaml`, одну спробу,
нуль HTTP/fallback та збережені failure metadata. Без overlay поведінка стара;
success/auth/partial/usage-window не змінюються. Повний project regression:
20 тестів PASS. Подробиці recovery: [C001-CHECKPOINT.uk.md](C001-CHECKPOINT.uk.md).

Нижче — історичне обґрунтування пропозиції до її застосування; твердження
«не застосовано» в цьому історичному розділі вже застарілі.

## Чому профільний plugin не виправив би цей шлях

`tests/fixtures/quota-hook-probe` — лише тестовий observer, не deploy plugin.
Він завантажений штатним `discover_plugins` із тимчасового профілю та явного
`plugins.enabled`. Контрольний `transform_llm_output` викликав callback.
Далі справжні 402/429 у `AIAgent` дали по одному `api_request_error`, із
структурованими `billing` / `rate_limit`, але **нуль** `transform_llm_output`.
Observer не повертає переклад, не змінює error/result і не підміняє відповідь.

У `agent/conversation_loop.py` `_run_api_retry_loop` повертає `_ae.result`, а
зовнішній loop повертає цей early result до `finalize_turn`. Тому існуючий
output transform у `agent/turn_finalizer.py` оминається. `api_request_error`
є observer, не API заміни кінцевого result. Classification transform може
змінити verdict, але не є перекладом кінцевої відповіді; категорію помилки
для обходу billing copy не змінюємо. Gateway `agent:end` також не є
підтвердженою точкою заміни доставленого тексту.

`display.language: uk` реально розпізнається; штатні user locale overlays
існують. Проте жоден із них не перехоплює ці hardcoded early-result відповіді.
Підтримуваного профільного розширення, достатнього для цих двох шляхів, не знайдено.

## Мінімальна пропозиція upstream

Файл `proposals/quota-profile-copy.patch` підготовлено проти точного pin.
`git apply --check` пройшов; patch **не застосовувався**.

- Малий sibling `agent/quota_profile_copy.py` змінює лише `final_response`
  для `failed=true` з категоріями `billing` / `rate_limit`. Не аналізує довільний
  текст, не змінює retries, credentials, fallback, model або transport.
- Викликається у двох конкретних місцях `agent/turn_recovery.py`: після
  `_billing_failure_result` у nonretryable branch і перед поверненням
  `max_retries_exhausted_result`, після partial/reset stamping.
- Partial-відповіді та usage-window повідомлення з точним reset не замінюються.
  Усі інші помилки та успішні відповіді не змінюються.
- Текст береться через наявний `agent.i18n.t`; без доданого перекладу поведінка
  попередня. Метадані помилки зберігаються, зокрема діагностичний `error`.

**Нові ключі нижче запропоновані patch-ем, не підтримуються поточним runtime.**
Після окремо погодженого й перевіреного upstream-виправлення профільний
`$HERMES_HOME/locales/uk.yaml` міг би містити:

```yaml
profile:
  quota:
    billing: "Сервіс повідомив про вичерпання квоти або обмеження доступу. Запит зупинено. Потрібно перевірити безкоштовний ліміт."
    rate_limit: "Сервіс тимчасово обмежив частоту запитів. Цю спробу зупинено. Зачекайте й надішліть повідомлення ще раз."
```

Цей файл перекладу не встановлено: без patch він не виправляє нічого.
Поточний deployment і pin не змінені. Пропозиція не є обходом заборони
редагування upstream й не виконує довільний monkeypatch на старті.

Перед прийняттям patch потрібні тести на застосованій погодженій версії:
ті самі native 402/429 з українським final, одна спроба й порожній fallback;
збереження failure metadata; negative cases success/auth/partial/reset-window;
відповідність доставленого тексту збереженій історії; реальна Telegram delivery.
`billing_block` може містити штатні billing links для інших UI — цю окрему
поведінку пропозиція не маскує. Жодного з цих post-patch результатів не заявляємо.
