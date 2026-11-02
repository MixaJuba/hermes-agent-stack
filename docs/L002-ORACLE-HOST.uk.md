# L-002 — перевірений Oracle Always Free host

Дата: **2 листопада 2026 року**.

Цей документ фіксує sanitized результат етапу L-002. Він не містить public IP, OCID, SSH private key, токенів або інших credentials.

## Результат

**L-002: PASS.** Створено рівно одну Oracle Compute VM `hermes-agent-prod` і перевірено її базову придатність як цільового ARM64 host-а. Hermes, Docker, inference provider, Exa і Telegram token на цьому етапі не встановлювалися.

## Підтверджений host

- Lifecycle: `RUNNING`.
- Shape: `VM.Standard.A1.Flex`.
- Availability domain: `EU-FRANKFURT-1-AD-1`.
- OCPU: **1**; підтверджено з самої VM.
- RAM: **6 GB**; ОС бачить приблизно **5.8 GiB**.
- Architecture: **aarch64**.
- OS: **Ubuntu 24.04.5 LTS Minimal**.
- Boot volume: **50 GB**, Balanced 10 VPU; root filesystem приблизно 48G.
- Capacity error: відсутній; перша provisioning-спроба в AD-1 успішна.

## Always Free / usage

Після provisioning Oracle usage відповідав одній A1 VM:

- A1: **1/2 OCPU**;
- RAM: **6/12 GB**;
- storage: **50/200 GB**.

Платних ресурсів у межах L-002 не створювали.

## Мережа

Підтверджено:

- public subnet;
- public IPv4: ephemeral, assigned;
- default route: `0.0.0.0/0 -> Internet Gateway`;
- ingress: тільки `TCP/22` з погодженого source `/32`;
- інших ingress rules не додано;
- outbound HTTPS працює;
- GitHub public HTTPS повертає `200` з успішною TLS verification.

Приватний репозиторій без GitHub credentials закономірно повертав `401`; це не мережевий блокер. Git на Minimal-образі відсутній і навмисно не встановлювався в L-002.

## SSH

- Для VM створено окремий локальний Ed25519 key.
- Private key не передавався в Git, чат або Oracle.
- SSH працює.
- Повторне SSH-підключення успішне.
- Локальний private-key ACL обмежений власником.

Public IP, OCID і key material у цьому документі навмисно не зберігаються.

## Що L-002 НЕ перевіряв

- Hermes runtime на ARM64;
- Docker на Oracle host;
- GitHub private-repository authentication;
- inference provider;
- Exa;
- Telegram gateway/token/owner ID;
- systemd Hermes service;
- reboot/autostart;
- production backup/restore;
- full E2E.

## Наступний gate

**L-003 — Runtime on Oracle.**

Потрібно доставити прийнятий repository state на VM без витоку GitHub credentials, встановити лише необхідні системні prerequisites, розгорнути pinned Hermes `v0.22.5` через підготовлений `scripts/hermes_runtime.py`, перевірити нативний ARM64 CLI/runtime і Docker sandbox. Provider OAuth/API keys, Exa та Telegram ще не підключати.
