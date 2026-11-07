# Від нового Linux host до перевіреного відновлення

Оновлено 7 листопада 2026. Виконавець майбутніх live кроків — Local Codex після
coordinator acceptance. Це інструкція, а не твердження про виконане cold recovery.
Працюючий Oracle/Telegram не змінювати заради перевірки цього документа.

## Точка входу та межі доказу

L-006F — accepted live baseline. За прийнятим handoff L-007A перевірив код/стан,
L-007S створив один свіжий локальний full backup 7 листопада; **restore цього ZIP
не виконували**, захищеної off-instance копії ще немає. Не повторювати L-007S.
`PROJECT_STATE.md` і актуальний `main` — чинні рішення; PR #1 — ще draft.
Документ закриває документаційні прогалини G1–G4; не закриває live H-001.

## G1 — початкове розгортання на чистому віддаленому host

**Gate 0: безкоштовність і доступ.** Local особисто перевіряє Always Free VM,
диск, приватний Standard bucket, aggregate storage/API allowances, €0 і відсутність
paid upgrade/overage/auto-top-up. Поточна розбіжність Oracle Trial commitment views
не є доведеним безкоштовним запасом. За непідтверджених умов — STOP до створення
ресурсів/трафіку. Instance principal: dynamic group тільки конкретної VM та scoped
policy з [implementation](H001-OFFSITE-DR-IMPLEMENTATION.uk.md). Ніяких user API
keys/PAR. На нову recovery VM потрібна окрема вузька авторизація, не broad group.

**Gate 1: ОС і файли.** Для заміни host: Ubuntu 24.04 ARM64, non-root service
account `hermes-agent`, private `/var/lib/hermes-agent` (0700), source
`/opt/hermes-agent`, public project code `/opt/hermes-agent-stack`, workspace
`/var/lib/hermes-agent/workspace`, restore root `/var/lib/hermes-dr-restores` (0700).
Встановити на **новому Linux**, не на ноутбуці: git, Python 3, CA certificates,
Docker Engine (accepted host мав 29.1.3), і лише для DR — age та OCI CLI. Local
обирає підписаний ARM64 package з офіційного repository, фіксує exact package
versions/checksums у private recovery record; не встановлює сліпо `latest`.
Конкретні age/OCI CLI versions ще треба кваліфікувати live. Не переносити user OCI
config/signing keys. Членство service account у Docker group фактично дає host
privileges: доступ групи не передається tool container.

**Gate 2: точний code export та runtime.** На новому host оператор отримує project
commit із незалежного recovery record / coordinator acceptance, а не плаваючого
HEAD. Наведені команди — тільки для порожніх, заздалегідь створених каталогів,
якими володіє `hermes-agent`; запускати від цього користувача. GitHub/downloads
дозволені майбутньому Local gate, у Cloud тут вони не виконуються.

```bash
set -euo pipefail
umask 077
export PYTHONDONTWRITEBYTECODE=1
STACK_SHA='<COORDINATOR_ACCEPTED_40_HEX_SHA>'
[[ "$STACK_SHA" =~ ^[0-9a-f]{40}$ ]]
git clone https://github.com/MixaJuba/hermes-agent-stack.git /var/tmp/hermes-stack-reference
git -C /var/tmp/hermes-stack-reference cat-file -e "$STACK_SHA^{commit}"
test -z "$(ls -A /opt/hermes-agent-stack)"
git -C /var/tmp/hermes-stack-reference archive "$STACK_SHA" | tar -x -C /opt/hermes-agent-stack
python3 /opt/hermes-agent-stack/scripts/stack_provenance.py \
  --reference /var/tmp/hermes-stack-reference --commit "$STACK_SHA" --export /opt/hermes-agent-stack
test -z "$(ls -A /opt/hermes-agent)"
git clone https://github.com/NousResearch/hermes-agent.git /opt/hermes-agent
git -C /opt/hermes-agent checkout --detach bf0203a794a07aac3ff764972ab9087baa4e4f4e
cd /opt/hermes-agent-stack
python3 scripts/hermes_runtime.py --source /opt/hermes-agent \
  --home /var/lib/hermes-agent --tools /var/lib/hermes-agent/tools apply-patch
python3 scripts/hermes_runtime.py --source /opt/hermes-agent \
  --home /var/lib/hermes-agent --tools /var/lib/hermes-agent/tools install
python3 scripts/hermes_runtime.py --source /opt/hermes-agent \
  --home /var/lib/hermes-agent --tools /var/lib/hermes-agent/tools cli -- --version
python3 scripts/hermes_runtime.py --source /opt/hermes-agent \
  --home /var/lib/hermes-agent --tools /var/lib/hermes-agent/tools python -- \
  -c 'import sys, importlib.metadata as m; assert sys.version_info[:3] == (3,14,9); assert m.version("exa-py") == "2.10.2"'
```

PM використовує upstream lockfiles, managed Python 3.14.9 та перевіряє артефакти.
Без raw pip/uv, relock, dependency update, Desktop/browser/voice extras. Wrapper
перевіряє exact base + quota patch manifest/hashes. Невідповідність — STOP.
Якщо runtime вже існує — **не виконувати install повторно**; лише attestation.
Для disaster recovery зараз перейти до G2, **не render config і не start service**.

**Gate 3: новий профіль (тільки коли немає даних для restore).** Ввести підтверджений
owner ID та потрібні secrets безпосередньо в protected target environment.
`TELEGRAM_ALLOWED_USERS` рівно один numeric ID, token/base URL/Exa key з `.env.example`;
не друкувати їх і не передавати через shell command literals. Створити `.env` 0600
owner `hermes-agent` через protected entry. Від `hermes-agent` запускати renderer
лише на новому home: він відмовляється перезаписувати config/SOUL/overlay.

```bash
python3 /opt/hermes-agent-stack/deploy/render_config.py --home /var/lib/hermes-agent
```

Для restored profile renderer не застосовується. Exact community plugin отримати
штатним installer з pinned catalog за [C-002](C002-CLOUDFLARE-PRODUCTION.uk.md),
helper `cloudflare_plugin.py install` з explicit source/home через PM wrapper.
Existing plugin не замінювати: спочатку `check`, mismatch → STOP. Усі routes тільки
`workers-ai / @cf/zai-org/glm-4.7-flash`, auxiliary теж, no fallback; keyed Exa only.

**Gate 4: sandbox і єдиний gateway.** Збудувати `deploy/Dockerfile.sandbox` з
його pinned multiarch base digest у `hermes-ua-sandbox:local`; перевірити non-root,
`network=none`, відсутність socket/host checkout/forwarded keys/published ports.
Від `hermes-agent` перевірити `deploy/gateway_guard.py --config
/var/lib/hermes-agent/config.yaml --secret-file /var/lib/hermes-agent/.env` та plugin
attestation. Не source/echo `.env` для тесту: guard читає його сам.
Лише після окремого дозволу на cutover: немає poller на старому host, webhook NONE,
systemd unit із repo встановлений без змін, `daemon-reload`, enable/start
`hermes-ua.service` **один раз**, ніякого manual gateway паралельно. Пройти Telegram
owner/outsider, tools/Exa, memory/restart/reboot й poller=1. Ці кроки не виконуються
в H-001C і не потрібні для першої live isolated DR qualification.

## G2 — одна процедура native restore, спочатку ізольовано

Передумови: verified runtime G1/Gate 2, private empty canonical `restore-*` target,
age/OCI CLI на Linux, instance principal доступ до конкретного bucket, незалежно
збережені encrypted SHA256/object identity та temporary identity file 0600 current
UID **поза live home**. При recovery на новій VM settings `home`/source/tools
вказують на встановлений runtime; `restore_root` — окремий private каталог.
Config — updated example з усіма explicit storage bounds. Ніколи не вставляти
private identity у config або значення CLI argument. Подається лише path.

```bash
set -euo pipefail
umask 077
export PYTHONDONTWRITEBYTECODE=1
RECOVERY_OBJECT='<FROM_PRIVATE_RECOVERY_RECORD>'
RECOVERY_SHA256='<TRUSTED_ENCRYPTED_SHA256>'
IDENTITY_PATH='<PROTECTED_TEMPORARY_IDENTITY_FILE_PATH>'
RESTORE_TARGET=/var/lib/hermes-dr-restores/restore-controlled
python3 /opt/hermes-agent-stack/scripts/offsite_restore.py \
  --config /etc/hermes-offsite.json --target "$RESTORE_TARGET" \
  --identity "$IDENTITY_PATH" --object "$RECOVERY_OBJECT" --sha256 "$RECOVERY_SHA256"
```

Helper виконує `oci --auth instance_principal` HEAD/get, flat `opc-meta-*`/length
verification, downloaded size/SHA256 **до decrypt**, age authentication, native
`run_import` через `offsite_native.py`. Приглушено тільки
`_revive_gateway_after_import`; extraction, SQLite sessions/messages, memory/config
не підмінені. Helper відхиляє live home, non-empty/symlink target, external/profile
archive entries. Ніякого прямого `hermes import` без цього контролю, `force`, другого
restore engine чи автоматичного gateway. Після failure partial target лишається
ізольованим; Local перевіряє path/ownership перед ручним прибиранням або обирає
інший empty target. Автоматичного видалення/перезапису target немає.

Критерії першої live перевірки: native success; конфігурація/спогади і точна історія
з archive збігаються, SQLite integrity OK, UID/modes private. Local додатково читає
відомий факт/попередній діалог у fresh process, **без inference/gateway**, не публікує
їх. Guard/plugin review restored profile має бути PASS без розширення allowlist або
provider routes; зняти приватні fingerprints config, не його contents. Перевірити
чинний service/poller=1 до/після, без restart. Звіт містить лише sanitized evidence.

**Promotion при справжній втраті VM — окремий cutover, не частина H-001 live smoke.**
На новій replacement VM, за відсутнього старого poller, після isolated PASS:
перенести вже native-restored data у новий canonical home, зберігаючи створені PM
`tools/installs` (вони не portable backup). Це перенесення перевіреного результату,
не повторна extraction/restore. Не виконувати на існуючому production home.

```bash
# Only NEW replacement host; operator has verified no old/current poller.
set -euo pipefail
test ! -e /var/lib/hermes-agent/config.yaml
test ! -e /var/lib/hermes-agent/.env
test ! -e /var/lib/hermes-agent/state.db
test -d "$RESTORE_TARGET"
for runtime_dir in tools installs backups .git; do
  test ! -e "$RESTORE_TARGET/$runtime_dir"
done
# Inspect bootstrap-only destination first; no unknown user data may be overwritten.
cp -a "$RESTORE_TARGET/." /var/lib/hermes-agent/
```

Якщо будь-який precondition не виконано — STOP; не застосовувати `rm -rf` чи
`--delete`. Перевірити `.env`/config/pairing owner-only, відсутність OpenAI/Codex
credentials, exact Cloudflare plugin, PM/source manifests та sandbox. Після
promotion G1/Gate 4 — один poller. Secrets з backup можуть бути відкликані/застарілі:
Local вводить актуальні protected values, а не підключає fallback. Recovery record
має містити цей cutover результат окремо від isolated PASS.

## Ключ і recovery record поза VM

Перед upload Local з власником обирає вже доступне захищене середовище **поза
production VM і Cloud Codex** з age-keygen. Не встановлювати нічого на ноутбук
за цією інструкцією. Не створювати identity через чат/Cloud/production server.
На цьому окремому операторському пристрої, у приватному каталозі:

```bash
umask 077
age-keygen -o /secure-offline/hermes-recovery-identity.txt
age-keygen -y /secure-offline/hermes-recovery-identity.txt
```

Друга команда показує тільки public recipient для server config. Private identity
зберігати у двох незалежних вже доступних encrypted offline copies / private
password vault без paid subscription, поза Oracle tenancy/Git/chat. Пароль носія
зберігати окремо. Власник перевіряє доступ і пробне decrypt синтетичного файлу
обома copies; не покладатися на пам'ять агента або єдину SSH session.
На Oracle постійно зберігається **лише public recipient**. Для recovery Local
передає identity на тимчасовий захищений RAM-backed/приватний path, після проби
видаляє лише цю temporary copy. Unlink не є гарантованим secure erase на SSD;
encrypted volume/volatile storage і заборона swap/core dump потрібні оператору.

Після одного verified upload Local заповнює **поза сервером** private
`config/recovery-record.example.json`: namespace/bucket/region/object/version,
independent encrypted digest/size, public recipient, accepted stack SHA/tree,
Hermes/patch/plugin pins, exact qualified tool versions, статус isolated test,
посилання-мітка на offline key custody (не ключ). Використати success JSON helper
і незалежно recomputed encrypted SHA; не довіряти одному SHA з remote HEAD.
Другу захищену copy record тримати окремо від VM; приймання перевіряє, що за нею
можна знайти object/key/code без SSH до старої VM. Не Git/chat: identifiers приватні.
Варто зберегти поруч code-only Git bundle/export та manifest прийнятого commit
на вже доступному offline носії — GitHub і tenancy теж можуть бути недоступні.
Не включати `.env`/private identity у code bundle.

Відсутність перевірених key copies або record — **STOP до timer**. Ciphertext без
ключа або digest/object identity не вважається recoverable DR. Ротація recipient
не скасовує потреби зберігати стару identity до перевіреного перенесення всіх copies.

## G3 — походження встановленої версії

L-007A спостерігав `/opt/hermes-agent-stack` як **export без `.git`**: 56/56 blobs
відповідали commit `f0f8a41857aa9b2c647638ee070900b529e11e19`, tree
`a4d147cf3aefc322d53966f031ef5ee93df37579`. Нові main SHA додавали docs, це
не вимога синхронізувати live code заради однакової назви версії.
`scripts/stack_provenance.py` тепер відтворює offline file-set/blob/mode verification
для code-only export проти точного trusted Git tree, не проти directory name.
Unexpected/missing/modified files або symlinks — FAIL. Виконувати **до imports**,
з `PYTHONDONTWRITEBYTECODE=1`; непояснені generated extras не ігнорувати мовчки.
Після rollout Local фіксує actual accepted code commit/tree/export proof privately.

Окремі незалежні перевірки: Hermes source HEAD + approved quota patch hashes
через wrapper; PM Python/CLI/Exa versions з G1; CF plugin source SHA + installer-owned
`.install-metadata.json` через helper. Sidecar не є provenance. `.env`, credentials
і весь runtime home не сканувати як Git export і не викладати в evidence. CLI
`--version` один не доводить жодну з цих чотирьох складових.

## G4 — історія проти поточного стану

`RUNTIME.uk.md`, `BACKUP-QUOTA.uk.md`, ранні provider/gate evidence — snapshots
своїх етапів. NVIDIA TEST ONLY, OpenAI/Codex production rejected; поточний маршрут
Cloudflare + keyed Exa, визначений PROJECT_STATE, а не історичним `requested_model`.
`config/upstream.json` фіксує pin, історичні NVIDIA fields не є active settings.
Не переписувати історичні PASS як помилки і не виконувати старі «next gate» заново.

## CONFIRMED OFFLINE / NOT YET VERIFIED

Offline: bounded raw retention/size/disk/concurrency/error checks, CLI contract,
native backup/import та fresh-process synthetic memory/history/config/permissions,
exact code-export verifier, shell syntax/doc references. Це не cold VM deployment.

NOT YET VERIFIED: actual age cryptography/key custody, installed OCI CLI semantics,
private bucket/IAM/free allowance, one encrypted real upload/download/isolated restore,
real current ZIP restore, complete replacement/cutover, activated timer/alerting.
Наступний Local gate — ці контрольовані live перевірки, а не повторний L-007 audit
чи нове написання runbook. Timer після PASS та off-VM record/custody; H-001 до того
не завершений. Tenancy loss, provider availability, missed changes after last backup
і відсутність автоматичних off-VM alerts залишаються ризиками.
