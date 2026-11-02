# H-001 — zero-cost off-instance disaster recovery design

Дата: 2 листопада 2026 року.

## Мета

Посилити вже прийнятий production baseline без зміни робочого Hermes runtime.

Поточний L-006F backup реально відновлюється, але лежить на boot volume тієї ж Oracle VM. Він захищає від логічних помилок/пошкодження даних, але не від повної втрати instance/boot volume.

H-001 має додати окрему encrypted recovery copy поза production boot volume і перевірити реальний recovery path.

## Обраний перший крок

Основний storage target: **OCI Object Storage Always Free** у поточній Oracle tenancy.

Причини:

- Oracle Always Free надає 20 GB сумарного Object/Archive Storage;
- Always Free включає 50 000 Object Storage API requests на місяць;
- поточний production backup приблизно 1.9 MB, тому запас по free storage дуже великий;
- Object Storage є окремим сервісом від compute boot volume;
- усі objects шифруються at rest AES-256 за замовчуванням;
- доступ із VM можна організувати через **instance principal**, без статичного OCI API key на сервері.

Це дає захист від втрати самої VM/boot volume. Це ще не multi-cloud/off-account DR; повна втрата Oracle tenancy залишається окремим residual risk.

## Модель доступу

Для production VM використовувати OCI **instance principal**:

1. окрема dynamic group, яка матчить тільки `hermes-agent-prod`;
2. IAM policy з мінімальним доступом лише до одного backup bucket;
3. OCI CLI/SDK працює з `--auth instance_principal`;
4. user API keys/private keys на VM не створюються.

Bucket має бути private. Public access / pre-authenticated public URL не використовувати.

## Модель шифрування

Мінімум, який Oracle забезпечує автоматично: server-side AES-256 для всіх objects.

Для H-001 production rollout бажаний додатковий client-side encryption layer **до upload**. Рекомендований кандидат — `age` з asymmetric recipient model:

- на Oracle зберігається лише public recipient;
- private recovery identity не повинна зберігатися на production VM, у Git, chat або logs;
- backup шифрується до upload;
- restore потребує private identity, що подається лише під час контрольованого recovery.

Ubuntu 24.04 має ARM64 пакет `age`, тому цей варіант технічно сумісний із host architecture. Остаточну live key-handling процедуру має кваліфікувати Local Codex без витоку private identity.

Якщо безпечне зберігання private identity поза VM не може бути гарантоване, H-001 повинен STOP до client-side rollout, а не зберігати ключ на Oracle “тимчасово назавжди”.

## Bucket policy

Рекомендовано:

- Standard tier;
- private bucket;
- object versioning enabled;
- timestamped immutable object names для кожного backup;
- без lifecycle deletion на першому rollout, поки фактичний storage growth не виміряний;
- без retention rule одночасно з versioning, оскільки OCI не дозволяє цю комбінацію.

Versioning захищає від випадкового overwrite/delete; старі версії також споживають storage, тому usage треба контролювати.

## Backup flow

```text
Hermes native backup
    ↓
private local archive (0600)
    ↓
client-side encryption (preferred)
    ↓
checksum
    ↓
OCI Object Storage private bucket
    ↓
HEAD/list verification
```

Після підтвердженого remote upload локальний production backup можна залишити відповідно до чинної retention policy; H-001 не повинен видаляти єдину working copy автоматично.

## Recovery test

H-001 вважається PASS тільки після реального controlled recovery:

1. отримати remote encrypted object назад;
2. перевірити checksum;
3. decrypt поза live production home;
4. restore у separate isolated test home;
5. підтвердити memory, session/history, config/state;
6. не створити другий Telegram poller;
7. не overwrite live production home;
8. після validation прибрати лише isolated restore-test state.

## Zero-cost guard

Перед створенням bucket Local Codex повинен live-перевірити:

- Object Storage usage зараз нижче Always Free allowance;
- вибраний tier входить у Always Free;
- немає paid-only replication/egress/managed feature;
- H-001 не вмикає paid subscription, auto-recharge або новий paid resource.

Якщо Oracle UI/API показує, що конкретна tenancy вимагає оплату для запланованої конфігурації, task зупиняється до створення ресурсу.

## Розподіл ролей

### Cloud Codex

Готує тільки code/tests/artifacts для H-001 у окремій branch:

- backup/upload helper;
- configuration schema без secrets;
- systemd service/timer proposal;
- offline tests з network tripwire/stubs;
- recovery helper/test harness;
- documentation.

Cloud Codex не створює bucket, IAM, dynamic group і не працює з live secrets.

### Local Codex

Після coordinator acceptance:

- перевіряє Free allowance в Oracle;
- створює dynamic group/IAM/bucket;
- безпечно готує encryption key material;
- розгортає accepted artifacts;
- виконує один real upload/download/restore;
- перевіряє zero-cost/billing state;
- повертає sanitized evidence.

## Acceptance criteria

H-001 = PASS лише якщо:

- production Telegram agent весь час залишається працездатним;
- Object Storage target підтверджений як zero-cost у фактичній tenancy;
- bucket private;
- VM access без static OCI API credentials;
- remote backup існує поза boot volume;
- encryption policy підтверджена;
- real remote download + isolated restore PASS;
- secrets не потрапили в Git/chat/logs;
- second poller = NO;
- paid route/resource = NONE.

## Після H-001

Наступний hardening напрям — zero-cost monitoring/alerting. Він не починається, доки H-001 не прийнятий coordinator-ом.
