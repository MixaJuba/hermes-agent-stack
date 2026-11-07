# C-002 — Cloudflare production configuration

Історичний evidence C-002/C-002A: описані нижче тодішні next gates вже пройдені
в L-005/L-006F. Поточний стан — PROJECT_STATE; нове розгортання/відновлення:
[RECOVERY-RUNBOOK.uk.md](RECOVERY-RUNBOOK.uk.md). Не повторювати старі gates.

**Корекція C-002A після прийняття C-002:** перша реальна Oracle attestation у
L-005 виявила false positive: штатний pinned catalog installer додає
`.hermes-catalog.json` у папку плагіна, чого C-002 fixture не моделювала.
Approved source hashes та authoritative install metadata залишалися правильними;
ознак plugin compromise за наданою діагностикою немає. Виправлення дозволяє й
валідує тільки цей inert sidecar, не довіряючи йому provenance. Подробиці й
офлайн-тести: [C002A-CATALOG-SIDECAR.uk.md](C002A-CATALOG-SIDECAR.uk.md).
Live Oracle re-attestation ще не виконана; L-005 продовжити з Gate 2 після прийняття fix.

База: main `06875acd61448e86aebfb90892ef43fcd228760b`. Це підготовка коду,
не deployment на Oracle. Live inference, Telegram, Exa та приватні акаунти
в C-002 не використовуються. Наступний gate після прийняття: **L-005 Exa — Local Codex**.

## Production policy

Єдиний provider/model: `workers-ai / @cf/zai-org/glm-4.7-flash`.
Обидва `fallback_model` та `fallback_providers` порожні. OpenAI-compatible SDK
є транспортом Hermes, не дозволом використовувати OpenAI/Codex provider.
NVIDIA — TEST ONLY; OpenAI/Codex, Gemini, Groq, OpenRouter не є production routes.

Тарифні факти, вже перевірені координатором: Workers Free — 10 000 Neurons/day,
після вичерпання безкоштовного allocation операції відмовляють без automatic
paid overage. GLM-4.7 Flash Free-compatible, context 131072, function calling
та multi-turn tools supported; default text-generation rate limit 300 RPM.
Це не вимірювання залишку акаунта. L-004C точний Neuron counter — UNKNOWN.
Джерела: [pricing](https://developers.cloudflare.com/workers-ai/platform/pricing/),
[limits](https://developers.cloudflare.com/workers-ai/platform/limits/),
[qualification](L004C-CLOSEOUT.uk.md).

## Profile і startup

`deploy/render_config.py` створює JSON-as-YAML config/SOUL та український overlay
без перезапису наявних файлів. У tracked config немає account-specific base URL
чи ключа; обидва читає Hermes per-profile через ProviderProfile:

- `CLOUDFLARE_WORKERS_AI_API_TOKEN`;
- `CLOUDFLARE_WORKERS_AI_BASE_URL`.

`.env.example` містить лише порожній token та `<ACCOUNT_ID>` placeholder.
Реальні значення вже захищено на Oracle; C-002 їх не читає і не відтворює.
Майбутній gateway guard вимагає token/base URL, Exa token, Telegram token та
рівно одного numeric owner. URL має бути лише HTTPS API Cloudflare, account
OpenAI-compatible `/ai/v1`, без userinfo/query/alternate host. Помилка не друкує URL.
NVIDIA більше не required production secret; старий route відхиляється.

Guard також перевіряє порожні fallback-и, Exa-only/no-keyless, owner/pairing,
Docker no-network/no-host-mount/no-env-forward/socket, disabled external login
adoption/lazy installs, agent retry=1 та recovery=0. Plugin source/provenance
attestation обов'язкова перед запуском. Auto plugin apply/check вимкнено.
У C-002 guard не запускає gateway й не додає setup-вимог до cloud environment.

## Exact community plugin

Official **pinned Hermes catalog** містить community
`cloudflare-workers-ai-provider` на commit
`f6821d058d504ee6324b0d3217564b93124c09f9`. Manifest та hashes усіх трьох
файлів зафіксовані в `config/cloudflare-plugin.json`.

На вже встановленому pinned runtime, після прийняття C-002, Local Codex може
використати штатний catalog installer через helper:

```bash
python3 /opt/hermes-agent-stack/scripts/hermes_runtime.py \
  --source /opt/hermes-agent --home /var/lib/hermes-agent \
  --tools /var/lib/hermes-agent/tools python -- \
  /opt/hermes-agent-stack/deploy/cloudflare_plugin.py install \
  --source /opt/hermes-agent --home /var/lib/hermes-agent
```

Helper використовує `load_catalog` саме з pinned source, не mutable live catalog;
перевіряє entry repo/subdir/tier/sha та викликає native `install_catalog_entry`
з exact `ref` і `force=False`. PM dependency admission залишається штатним:
нового package manager, pip install або permanent dependency не додаємо.
Plugin не декларує сторонніх runtime dependencies. Невідповідний existing plugin
не замінюється; helper завершується відмовою. C-002 цей installer не запускав:
native invocation contract перевірено offline, exact source отримано з public Git.

Native install metadata `pinned/revision/source` та SHA256 файлів перевіряються
stdlib-only attestation, включно зі startup guard. Symlink, інший SHA, змінений
код або додатковий profile plugin блокують запуск. Тому restore не може тихо
прийняти новішу довільну revision. `check --home ...` не потребує secrets.

Це маленький декларативний community ProviderProfile поверх Hermes transport:
немає tools/hooks/middleware, threads/processes чи власного network client.
Його `default_aux_model` відрізняється від нашої моделі та його каталог включає
paid-only моделі: ці defaults не є production policy. Exact pin + L-004C PASS
прийняті для цього deployment; будь-який upgrade Hermes/plugin — requalification.

## Auxiliary audit pinned v0.22.5

- `session_search` і `web_extract` більше **не використовують auxiliary LLM**;
  коментарі `hermes_cli/config_defaults.py` та native implementations це фіксують.
  Старі NVIDIA auxiliary blocks видалено, пошук лишається keyed Exa без rescue.
- Усі 17 стандартних auxiliary slots нашого профілю явно закріплені на той самий
  workers-ai/GLM із порожніми chains: compression, approval, vision, skills_hub,
  review, mcp, title_generation, memory_query_rewrite, tts_audio_tags, voice_chat,
  triage_specifier, kanban_decomposer, profile_describer, goal_judge, curator,
  monitor, background_review. Це не вмикає відповідні tools/voice/services.
- Title generation/model upgrade, background review та curator вимкнені.
  Other opt-in features (MoA/delegation/browser/voice) не ввімкнено в toolsets.
- Native `_resolve_task_provider_model` та `get_text_auxiliary_client` перевірені
  для всіх slots: explicit model перекриває plugin default_aux_model; endpoint
  походить із синтетичного env; SDK retries=0.
- У pinned code explicit main/provider + порожні chains забороняють discovery
  інших залогінених провайдерів. Main-agent fallback на ідентичну route пропускається.
  Tripwires перевіряють, що OpenRouter/Codex/discovery не викликаються.

## Synthetic quota і межі тесту

Використано стандартний Cloudflare v4 errors envelope з наданою документованою
семантикою HTTP429/account limited/daily free allocation exhausted. Це synthetic
fixture без вигаданого вимірювання акаунта чи error code; реальну квоту не вичерпували.

Native AIAgent + справжній approved quota patch + profile overlay: одна спроба,
український final, `failed/completed/reason/retryable/error` збережені; нуль зміни
provider/model чи paid fallback. Native auxiliary failure також перевірений через
реальний SDK та MockTransport: **2 bounded same-provider attempts**. Другий —
один hardcoded credential-recovery retry для rate-limit у pinned Hermes;
`auxiliary.transient_retries: 0` вимикає окрему transport retry ladder, не цей rung.
Обидва requests залишилися на exact Free endpoint/model; інших provider/model
викликів немає. Це не нескінченний retry і не provider/model fallback.

У test fixture використано native `NoopRelayRuntime` для ізоляції SDK від
незалежної Rust Relay middleware initialization. Routing/classifier/quota copy
не підміняються; HTTP socket tripwire не спрацював. Production Relay не змінювали.
Live Telegram delivery і billing metadata rendering ще не заявляються як PASS.

Narrow commands (public exact plugin source fixture потрібний для native imports):

```bash
python3 -m unittest discover -s tests -p test_deployment_guard.py -v
python3 -m unittest discover -s tests -p test_cloudflare_deploy.py -v
python3 scripts/hermes_runtime.py python -- /workspace/hermes-agent-stack/tests/check_cloudflare_production.py
```

Нативні докази: `reports/c002-native-check.json`. Фінальний project regression
`python3 -m unittest discover -s tests -v`: **24 PASS**, один запуск після narrow PASS. Історичні C-001/NVIDIA reports залишено.

`scripts/check_access.py` — історична NVIDIA TEST ONLY діагностика, не production
health check Cloudflare. Її live probes у C-002 не запускаються.
