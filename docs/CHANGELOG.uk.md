# Основні етапи розвитку

Це коротка історія, а не заміна [Git commits](https://github.com/MixaJuba/hermes-agent-stack/commits/main/) та [evidence](../reports/).

## 7 листопада 2026

- **H-001L3:** за наданим власником звітом Локального Codex — приватний OCI bucket, обмежені IAM-права, один реальний age upload/download/SHA256 та isolated restore; Telegram без рестарту, timer OFF. Власник підтвердив читання двох записів ключа. [Межі доказу](../reports/h001l3-operator-summary.json).
- **H-001C-FINAL:** код і документацію H-001 злито через [PR №1](https://github.com/MixaJuba/hermes-agent-stack/pull/1). 21 цільовий і 50 regression тестів за звітом Cloud Codex; age/OCI імітувалися.
- **L-007A / L-007S:** read-only перевірка production та новий локальний backup без перезапуску gateway.

## 2 листопада 2026

- **L-006F:** робочий owner-only Telegram-агент, пам'ять, Exa, tool call, systemd/reboot, локальний isolated restore.
- **L-005, L-004C, C-001/C-002/C-002A:** вибір Exa та Cloudflare, обробка квот, конфігурація й перевірка plugin pin.
- **L-001—L-003:** підготовка Oracle ARM64, Hermes runtime та ізольованого Docker.

Історичні документи зберігають статуси на момент створення. Нові результати **додають**, а не переписують минулі докази.
