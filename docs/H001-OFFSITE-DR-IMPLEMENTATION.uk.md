# H-001C — encrypted off-instance DR artifacts

H-001 **не завершено**. Це offline implementation від canonical
`247b0ccd3051a6b057951d99552d58f15aff5222`, не зміна працюючого Telegram-агента.
Дизайн: [H001-OFFSITE-DR-DESIGN.uk.md](H001-OFFSITE-DR-DESIGN.uk.md).

## CONFIRMED OFFLINE

Stdlib helpers: `scripts/offsite_backup.py`, `offsite_restore.py`, `offsite_native.py`.
Full backup використовує справжній Hermes `run_backup`, WAL-safe копіювання.
Raw ZIP 0600 залишається в private directory 0700. Helper захищає останній
перевірений raw та ніколи не видаляє L-006F/L-007S або unowned copies; точна
bounded retention policy нижче. Перед upload обов'язковий age recipient із bech32 checksum;
відсутній/неправильний recipient або відсутні binaries — відмова. До OCI може
потрапити лише `.age` artifact з age header; рахується encrypted SHA256,
залишається локальний checksum. Unique UTC timestamp + UUID, no overwrite,
Standard tier, sanitized format/timestamp/SHA/Hermes metadata. Після put
обов'язковий HEAD: encrypted size, SHA та format. SHA metadata — integrity
check, не заміна age authentication чи позаоб'єктного trusted recovery digest.

OCI CLI: explicit `--output json`, `--auth instance_principal`, `--config-file /dev/null`,
`--max-retries 0`, bounded timeouts. OCI environment overrides відхиляються;
CLI subprocess має allowlisted environment без user credentials/proxies.
Немає API signing key, auth token, public/PAR URL чи login. Service не підтягує
production EnvironmentFile. Backup може включати .env/auth як opaque backup
contents: вони не друкуються і upload можливий лише після encryption.

Restore вимагає explicit empty canonical target — без symlink/overlap з live
home, прямий `restore-*` child заданого restore_root. Вимагає explicit trusted
encrypted SHA256 і protected temporary identity file (0600, own UID, поза live
home), яку helper не створює й не додає у config. Download -> checksum -> age
-> native import. Небезпечні ZIP paths/symlinks/external-provider/profile entries
відхиляються до extraction. Приглушено тільки post-import gateway revival callback.
Extraction, memory/history/config restore справжні. Перевіряються bytes config/
memories, SQLite integrity й рівність sessions/messages з archive. Наявні snapshots
із зовнішнім memory storage/profiles потребують окремого review, не blind import.
Невдала спроба може лишити partial isolated target; повторний запуск його відхилить.

HEAD читається як **плоский JSON заголовків**, з `content-length` і окремими
`opc-meta-sha256` / `opc-meta-format`; вкладений `data` або `opc-meta` не є
підтвердженням цілісності. Регістр назв заголовків неважливий; неоднозначні дублікати,
відсутні/некоректні length, SHA або format відхиляються. Restore перевіряє HEAD
до get, потім regular downloaded file, розмір і trusted SHA **до decrypt**.
GET пише object bytes у `--file`; stdout не використовується як вміст backup.
Порожній stdout або JSON headers допускаються; не-JSON/не-object response — відмова.

Tests: stubbed age/OCI pipeline, fail-closed config/auth, encrypted-only upload,
checksum/HEAD, retention при failure, unsafe targets, systemd static verify;
окремий повний orchestrator roundtrip із синтетичним фактом/3 повідомленнями:
real native backup → stub age → real CLI adapter / stub subprocess response
put → flat HEAD → get → checksum → stub decrypt → real native isolated import.
Для disposable home worker використовує вже вибраний PM interpreter, без копіювання
installation records або перевстановлення runtime. Нативні extraction/memory/history/
config не підмінені; fresh-process verification підтверджує відновлені дані/права.
External socket
tripwire активний; справжніх age keys, OCI або network calls у тестах немає.
Stub ciphertext **не є доказом криптографічної працездатності age**.

### Bounded raw retention / failure policy

Updated config обов'язково містить `max_raw_archives=2`, `max_archive_bytes=67108864`
(64 MiB), `max_local_bytes=536870912` (512 MiB), `min_free_bytes=268435456`
(256 MiB). Це консервативні стартові межі, не виміряний growth. Native child
отримує RLIMIT_FSIZE до імпортів; після backup перевіряються cap, CRC/required
config/state ZIP members, native success і private permissions. Увесь helper
утримує nonblocking flock: одночасний manual/timer run відмовляється.

До створення ZIP рахуються **всі** raw `.zip` і залишені killed native writer
`.zip.<pid>-<thread>.partial` у private local_dir та bytes усіх
файлів, включно з failed/unmanaged artifacts; резервується місце для capped ZIP
та age output плюс заданий disk reserve. За браком місця/двох raw — відмова до
native backup. Частковий native/age/upload failure не видаляє попередню копію;
після одного failed attempt поряд з verified raw наступні runs зупиняються до
Local review. Нескінченного accumulation/retry немає.

Лише після нового successful native backup/encryption/put/HEAD, fsync нових raw,
ciphertext та private `.h001c-<UTC_UUID>.json` receipt helper може unlink старий
raw: потрібні власний строгий filename, receipt version/name/verified flag, exact
raw size/SHA і SHA збереженого ciphertext. Спочатку перевіряється існування/хеші
**нової** retained copy. Receipt не є remote provenance або off-VM recovery record.
Немає glob-delete за mtime або upstream `--keep N`. Unreceipted старі H-001C ZIP
також не усиновлюються; mismatch/symlink/permission/fsync/unlink failure → FAIL,
latest copy залишається. Тести зберігають synthetic L-006F/L-007S без змін.

Encrypted local artifacts, receipts і remote objects **не видаляються автоматично**:
local byte cap зупинить helper до заповнення диска. Local контролює growth/free
storage, приватно розбирає failures і лише після перевіреного recovery та окремого
дозволу прибирає конкретні зайві H-001C artifacts. L-006F/L-007S — поза cleanup.
Зміна меж потребує capacity review, не вимкнення guard. Нативні SQLite temporary
snapshots теж потребують фактичного VM free-space monitoring; offline cap не є
filesystem quota. Timer failure сам не доставляє alert власнику.

Початкове розгортання, promotion, provenance, key custody та off-VM recovery record:
[RECOVERY-RUNBOOK.uk.md](RECOVERY-RUNBOOK.uk.md), G1–G4. Приватні records/keys/ZIP
ігноруються Git; у repo є лише placeholder recovery-record example.
Підсумкові offline результати й залишкові ризики:
[H-001C-FINAL report](../reports/h001c-final-readiness.json).

### Coordinator review correction

Попередній commit `4fd5cd2a1906c45a14b93b948ac37d3b51f98fe8` помилково
читав HEAD через `['data']`; попередні stubs відтворювали цю ж неправильну
передумову. Їхній PASS не доводив сумісність із фактичним CLI HEAD.
Виправлено обидва helpers; спільна перевірка HEAD використовується і для upload,
і для restore. Нова fixture перевіряє аргументи CLI, flat user metadata, file-based
get, empty/header-only stdout, а також corruption і format/size mismatch.
Офіційний контракт: [OCI CLI object head](https://docs.oracle.com/en-us/iaas/tools/oci-cli/latest/oci_cli_docs/cmdref/os/object/head.html).
Це offline contract verification, **не запуск установленого OCI CLI проти Oracle**.
Фактичні результати: [sanitized report](../reports/h001c-offline.json).

## PLANNED LIVE — тільки Local Codex після acceptance

1. Перевірити actual Always Free usage/20 GB aggregate allowance та API allowance.
2. Створити private **Standard** bucket, versioning ENABLED, retention NONE,
   без lifecycle deletion/replication/paid features. Контролювати actual growth;
   helpers не виконують retention/delete/cleanup policy.
3. Dynamic group matching rule: `instance.id = '<PRODUCTION_INSTANCE_OCID>'`.
   Усі angle-bracket identifiers тут — placeholders, не реальні OCID.
4. Мінімальна object policy у конкретному compartment, bucket name condition:

```text
Allow dynamic-group <DYNAMIC_GROUP_NAME> to manage objects in compartment id <COMPARTMENT_OCID> where all {target.bucket.name = '<PRIVATE_BUCKET_NAME>', any {request.permission = 'OBJECT_CREATE', request.permission = 'OBJECT_READ', request.permission = 'OBJECT_INSPECT'}}
```

Це filtered object permissions, не tenancy-wide manage. Не надавати instance
bucket/IAM management, object delete/overwrite або PAR creation. Namespace і
region задаються explicit, namespace discovery permission не потрібний.
Local має перевірити фактичну policy semantics для put/head/get у tenancy.
Після втрати VM новій recovery instance знадобиться окрема точкова авторизація
Local Codex; правило не повинне автоматично матчити всі instances.

5. Встановити/перевірити age ARM64 та OCI CLI підтримуваним шляхом, не змінюючи
   Hermes PM dependencies. Згенерувати identity тільки поза production/Cloud,
   зберігати приватно offline; перенести на сервер лише PUBLIC recipient.
   Private identity при recovery подається protected temporary file; після
   контрольованого recovery Local видаляє temporary copy. Постійне зберігання
   private identity на Oracle не передбачається й не дозволене.
6. Заповнити private non-secret settings за `config/offsite-backup.example.json`
   і розмістити `/etc/hermes-offsite.json`; explicit hermes_source/hermes_tools
   вказують на вже встановлений Oracle PM runtime (не Cloud /workspace defaults); непотрібні/credential поля заборонені.
   Запуск від `hermes-agent` з service prerequisites та існуючим PM runtime:

```bash
python3 /opt/hermes-agent-stack/scripts/offsite_backup.py --config /etc/hermes-offsite.json
python3 /opt/hermes-agent-stack/scripts/offsite_restore.py --config /etc/hermes-offsite.json --target /var/lib/hermes-dr-restores/restore-controlled --identity <TEMP_PROTECTED_IDENTITY_PATH> --object <TIMESTAMPED_OBJECT_NAME> --sha256 <TRUSTED_ENCRYPTED_SHA256>
```

Private identity ніколи не передавати literal value у CLI/history; лише path.
Не робити restore на live home або зупинку/перезапуск working gateway.

7. Один real upload/HEAD/download/decrypt/native isolated restore; memory/history/
   config/permissions PASS, poller count залишається 1. Перевірити billing/usage.
8. Лише після live qualification розглянути активацію `hermes-backup-offsite.timer`.
   Unit templates не встановлені/не enabled. Oneshot, один daily UTC invocation,
   Persistent catch-up одного пропущеного cycle, Restart=no, no inbound binds.
   Після failure наступна scheduled спроба — наступного дня, internal loop немає.

## NOT YET VERIFIED

Real age encryption/decryption; actual installed CLI/OCI put/HEAD/get execution,
IAM/instance principal/bootstrap metadata access, bucket private/Standard/versioning,
zero-cost account allowance/growth, real remote recovery та live timer activation.
Cloud artifacts не доводять live H-001 PASS. Tenancy loss залишається residual risk.
Без recipient/identity custody/IAM/free allowance — STOP перед rollout.

GitHub network використано тільки для дозволених sync/branch push. Production
provider/model/web/Telegram/systemd gateway unit не змінювалися.
