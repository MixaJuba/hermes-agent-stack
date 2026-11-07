# H-002C — контрольоване регулярне резервування

**Підготовлено offline для review; не ввімкнено.** База
`9602e0a5eb02a1a8b4f3d74f8275018344ce20f3`. H-001C-FINAL прийнятий, H-001L3 —
one-time live PASS за звітом Local, timer OFF. Тут не повторювали H-001L3,
не зверталися до Oracle/Telegram та не змінювали billing, IAM або credentials.

## Що вирішує реалізація

`scheduled_backup.py` обгортає прийнятий `offsite_backup.py`; native backup/restore,
Hermes/provider/web/gateway pins незмінні. Без нових dependencies або storage agent.

1. **Локальні копії.** Збережені H-001C caps: raw 2 × 64 MiB, 512 MiB local budget,
   reserve 256 MiB, flock, CRC/native success, latest verified raw і legacy copies.
   Raw старих невдалих спроб, local ciphertext і receipts не видаляються навмання:
   за межею backup STOP, власник отримує alert. Нативні temporary SQLite snapshots
   не є filesystem quota; фактичний VM disk monitoring залишається потрібним.
2. **Віддалені копії.** До кожної спроби читаються **всі версії всього bucket**, а
   не тільки поточні імена нашого prefix. `list-object-versions --fields
   name,size,storageTier --limit <cap>`; при досягненні cap, continuation/unknown
   shape, відсутньому size/tier, Archive/InfrequentAccess або IAM error — STOP до PUT.
   Delete markers теж враховані в count; усі старі versions — у bytes.
   Резервується worst-case `max_archive_bytes + 1 MiB` для нового ciphertext.
   Default remote budget: 14 versions / 256 MiB, не Oracle account allowance.
3. **Дозвіл на обмежений період.** Protected `scheduled-backup.example.json` після
   Local preflight: до 7 діб, до 7 спроб, одна спроба на UTC-добу. Чотири explicit
   confirmations за замовчуванням false: €0, independent recovery, exclusive bucket
   writer та згода на приватну доставку recovery receipts власнику. Expiry, clock
   rollback або змінений policy hash блокують запуск. Approval перечитується перед PUT.
4. **Durable accounting.** Private `job.json` прив'язаний до точного policy SHA256.
   Спроба резервується з fsync **до першого network call**; timeout/lost PUT ack
   не повертає бюджет і не повторюється сліпо. Немає state — немає auto-init/upload.
   Missing/ambiguous/corrupt state вимагає Local reconciliation. Окремий flock
   захищає job; accepted helper додатково захищає raw rotation.
5. **Безпечний upload.** Перед новою копією HEAD звіряє останній known verified
   object із private reference. Scheduled PUT має `--no-multipart`, no-overwrite,
   no CLI retry; oversized ciphertext відхиляється до upload. Немає remote DELETE,
   lifecycle mutation або fallback. Невдала нова спроба не прибирає попередню.

Це **bounded unattended pilot**, а не безстрокова autonomous retention. Коли
remote/local cap або approval budget досягнутий, відбудеться безпечна зупинка зі
сповіщенням. Нові uploads не можуть рости необмежено за незмінних policy/state та
підтвердженого exclusive writer. Зміни сторонніми actors/іншими buckets потребують
нового account review; цей код не керує рахунком Oracle.

## OCI contract та фактичний IAM

Public SDK [ObjectVersionCollection](https://github.com/oracle/oci-python-sdk/blob/master/src/oci/object_storage/models/object_version_collection.py)
має `items/prefixes`; public generated
[CLI](https://github.com/oracle/oci-cli/blob/master/services/object_storage/src/oci_cli_object_storage/generated/objectstorage_cli.py)
вимагає explicit `size`, і `--limit` використовує bounded up-to-limit paginator.
Це GitHub source review, не запуск установленого на Oracle CLI. Flat HEAD
залишається прийнятим H-001C contract; list response — окремий `data.items`.

H-001L3 повідомляє «вузький IAM», але не містить фактичного policy тексту/доказу
`list-object-versions`. Відомі put/HEAD/get не доводять право inspection усіх versions.
Local перевіряє **наявний** instance principal доступ до цього read-only API.
IAM denial/непідтримуваний response → STOP; код не додає permissions.
Базова модель для object inspection — `OBJECT_INSPECT`, але реальна authorization
залежить від існуючих conditions/policy. Не вважати її підтвердженою за source docs.

Не автоматизовано remote pruning. Для безстрокового rolling storage знадобиться
окреме рішення власника: retention/RPO, перелік protected versions і scoped
`OBJECT_DELETE` для **конкретних старих version IDs** або переглянутий lifecycle.
Delete без version ID у versioned bucket може лишити попередні payloads і створити
marker — це не звільнення місця. Тут не додаються ні DELETE-права, ні lifecycle,
ні bucket management. Versioning не поєднувати з retention rule за старим дизайном.
Перед будь-яким майбутнім видаленням потрібні незалежний recovery record/key,
перевірена інша копія та окремий дозвіл; H-001L3 anchor/legacy не прибирати.

## Сповіщення без другого poller

`backup_notify.py` використовує тільки outbound HTTPS **sendMessage** існуючого
бота й одного positive numeric owner. Не викликає getUpdates, gateway, model/Exa,
не відкриває inbound port. Fixed host, redirects OFF, timeout 10 s, response cap
16 KiB, owner chat ID acknowledgement. Raw errors/URLs/bodies не логуються.

Backup oneshot має OnFailure і OnSuccess → `hermes-backup-watch.service`.
На Ubuntu 24.04/systemd 255 monitor context `MONITOR_SERVICE_RESULT` дозволяє
відрізнити невдалий unit (включно з timeout/ExecStart failure) від normal watch.
Окремий hourly watch timer перевіряє: failed job, незавершений job >1 год,
копію >36 год, clock/approval/state errors і наближення renewal. Persistent backup
timer дає один catch-up, не чергу всіх пропущених днів; ledger додатково блокує
другу спробу в одну UTC-добу. Restart=no, немає retry/crash loop.

Protected `notify.json` — coalesced outbox/ack, fsync до send. Максимум **3 спроби
на UTC-добу**, між ними не менше години; невдале повідомлення лишається pending
і буде перевірене пізніше. При lost acknowledgement можлива дубльована доставка,
але немає unbounded retry або обіцянки exactly-once. Invalid credentials/state
дають generic failure у journal, не «повідомлення доставлено».

На healthy state — щоденний heartbeat; після нового backup — private receipt
`object/SHA256/bytes/verified_at` навіть якщо heartbeat сьогодні вже був.
Це **не секретний ключ**, але приватні metadata: доставка дозволена лише після
explicit `owner_receipt_delivery_confirmed=true`, тільки в підтверджений owner DM.
Не включаються namespace/account/bucket IDs, токени, приватні файли чи logs.
Receipt доповнює незалежний private recovery record зі сховищем/кодом; key
ніколи не відправляється Telegram. Ack доводить прийняття Telegram для owner chat,
а не прочитання людиною чи незалежний доступ з другого пристрою.
Telegram bot DM не має наскрізного шифрування; це погоджений канал лише metadata,
не сховище private key і не єдина copy повного recovery record. За неприйнятної
конфіденційності metadata цей opt-in не давати: інший канал потребує окремого gate.

Якщо мережа зникла, pending переживає reboot; при відновленні зв'язку повтори
обмежені. **Повністю вимкнений host або зникла VM не може надіслати alert сама.**
Власник має очікувати daily heartbeat: за відсутності понад 36 год звернутися до
Local Codex для незалежної перевірки. Без окремого зовнішнього zero-cost monitor
не заявляти автоматичне виявлення total host outage. Telegram outage теж спільний
ризик каналу; після вичерпання трьох спроб наступна — нової UTC-доби.

## Permissions і секрети

- `/etc/hermes-backup-schedule.json` і `/etc/hermes-offsite.json`: root-owned 0640,
  group hermes-agent, без group write/other access. Або protected owner file 0600
  для контрольованого операторського запуску; policy не містить API credentials.
- `/var/lib/hermes-backup-automation`: StateDirectory 0700 owner hermes-agent;
  файли 0600. Не входить у native archive; після втрати state потрібний explicit
  init з remote reconciliation, не копіювати старий лічильник для обходу cap.
- Local створює `/etc/hermes-backup-notify.env`, root 0600: **лише два вже наявні**
  значення TELEGRAM_BOT_TOKEN / TELEGRAM_ALLOWED_USERS з protected production
  source, без shell literals, export, echo чи chat. Це не нові облікові дані.
  LoadCredential надає watcher private `%d/telegram`; немає EnvironmentFile.
  Парсер відхиляє extras/duplicates/wildcards/multiple owners/unsafe file modes.
- Watcher не бачить `/var/lib/hermes-agent` і Docker socket. Backup не отримує
  notifier credentials або provider environment (native archive за дизайном може
  містити opaque secrets, upload тільки зашифрований).

Не включати real policy, state, credentials, receipts чи private records у Git
або ChatGPT. Tracked sample має placeholders/false, не активує automation сам.

## Local gate після coordinator acceptance

1. Не повторювати H-001L3/повний аудит. Прочитати точний accepted commit і targeted
   diff; актуальний gateway unit/config/providers не переписувати. Timers OFF.
2. Підтвердити independent key/record access з іншого пристрою/носія та зберегти
   trusted H-001L3 anchor metadata. Узгодити приватну Telegram receipt delivery.
3. Перевірити actual aggregate Free storage/request allowance, усі versions,
   інші buckets/workloads і резерв headroom; payment/upgrade/lifecycle не змінювати.
   За невідомої ціни чи shared uncontrolled writer — STOP. Policy expires ≤7 діб;
   max_remote_bytes — виділений консервативний бюджет, а не загальна Free квота.
4. Read-only перевірити installed CLI `list-object-versions`/fields/limit і наявний
   IAM. Не додавати дозволи без власника. CLI paginator/instance authentication
   можуть зробити більше одного HTTP call: max_runs обмежує application attempts,
   **не є точним лічильником billed API requests**. Local враховує фактичний overhead.
5. Розмістити protected config/credential files і units без enable/start timer;
   static verify, перевірити права саме service UID. Не копіювати всю `.env`
   у notifier. Заповнити last_verified реальним часом backup, не часом preflight.
6. Один explicit init, тільки коли job.json ще немає; read-only inventory/HEAD,
   без нового archive. Запустити watch і підтвердити owner receipt; fake failure
   notification та network failure/recovery перевірити контрольовано, без gateway
   restart/другого poller. Окремо підтвердити MONITOR_SERVICE_RESULT для failure.

```bash
# Future Local gate only, as hermes-agent; do not run in Cloud / on existing timers.
python3 /opt/hermes-agent-stack/scripts/scheduled_backup.py init \
  --policy /etc/hermes-backup-schedule.json
```

7. Після окремого дозволу на один scheduled-path manual attempt перевірити
   encrypted-only PUT/no-multipart/HEAD, durable ledger, remote caps, latest
   protected references та private receipt поза VM. Це новий acceptance для wrapper,
   не повторення дослідження H-001L3. Current Hermes/poller мають лишитися незмінні.
8. Лише з окремим дозволом власника Local встановлює/enables **обидва** timers,
   перевіряє один фактичний cycle, freshness/outbox/receipt, journal і €0 usage.
   Не виконувати enable тут. Backup — daily 03:00 UTC, watcher — hourly + boot.
   UTC 03:00 = 05:00 Europe/Kyiv 7 листопада; влітку локальний час інший.
9. Renewal не автоматичний: зупинити scheduled activation за потреби, приватно
   звірити inventory/cost/last known receipt, зберегти старий ledger, отримати нове
   рішення щодо quota window. Не стирати state і не підвищувати caps для обходу
   відмови. Новий policy digest потребує explicit reconciliation/init, не relock
   dependencies чи нового H-001L3. Remote pruning — тільки окремий approved gate.

## Статус перевірок

Offline: real wrapper + accepted helper з stub age/OCI, budget/version/error paths,
durable attempts, expired/revoked approvals, owner-only sender contract, persisted
retry/freshness/receipts, systemd sanity, existing backup/guard regression.
Усі зовнішні sockets у тестах заборонені; реальних повідомлень/ресурсів не створено.
Підсумок: [H002C report](../reports/h002c-readiness.json).

Не перевірено live: inventory permission/installed CLI shape, root/service/credential
mount rights, OnFailure context, Telegram delivery/outage recovery, scheduled cycle,
account aggregate allowance та незалежність ключа/record. Не гарантуємо unlimited
unattended retention, моментальний outage alert або €0 при зміні зовнішніх умов.
