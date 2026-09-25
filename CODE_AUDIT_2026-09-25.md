# Повний аудит `ha-telegram-dashboard`

Дата: 2026-09-25  
Гілка: `main`  
Версія: `1.1.3`  
Останній коміт на момент аудиту: `0c517bb`

## Резюме

Критичних ознак шкідливого коду, зашитих токенів або підозрілих виконуваних скриптів не знайдено. Репозиторій містить очікувані інтеграції з Home Assistant і Telegram.

Після аудиту виправлено критичні проблеми з live-RBAC, callback authorization, entity-state filtering, auto-discovery, TTS allowlist та frontend/Telegram HTML injection. HTTP API все ще розраховує на захист Home Assistant Supervisor Ingress і не має окремого application-level login; не відкривайте порт add-on напряму у недовірену мережу.

### Статус після hardening

- Виправлено: stale AccessController snapshot після save/user changes.
- Виправлено: section RBAC bypass у button/action/entity callbacks.
- Виправлено: витік state snapshot поза дозволеними entity.
- Виправлено: auto-discovery на невідомих commands/callbacks і небезпечний `default_role: admin`.
- Виправлено: довільний `tts_service` поза domain `tts`.
- Виправлено: ключові frontend interpolation points, preview HTML і Telegram dynamic state/unit escaping.
- Виправлено: serialized/fsynced config persistence, tracked bounded WebSocket callbacks, malformed Telegram ID handling, short-screen preview sizing та dead Add button flow.
- Залишилось: HTTP API auth/CSRF та runtime config-file atomicity — потребують окремого контракту з Supervisor Ingress, щоб не зламати штатний UI.

## Результати перевірок

- `flake8 telegram_dashboard/src tests --max-line-length=120 --ignore=E203,W503,F401` — PASS.
- `python -m pytest tests/ -q` — **48 passed**.
- `node --check telegram_dashboard/src/ui/app.js` — PASS.
- `node --check telegram_dashboard/src/ui/i18n.js` — PASS.
- `python -m compileall -q telegram_dashboard custom_components` — PASS.
- `python -m pip check` — PASS.
- `git diff --check` — PASS.
- Покриття через `pytest-cov` не отримано: плагін `pytest-cov` не встановлений у середовищі.
- GitHub CI на момент останнього коміту був зеленим, але він не тестує повний runtime Home Assistant, Docker-збірку, авторизацію HTTP API або custom component setup.

---

## P0 / високий ризик — виправити першими

### 1. Усі HTTP API маршрути не мають application-level авторизації

**Файли:** `telegram_dashboard/src/web_server.py:110-131`, `159-194`, `345-458`; `telegram_dashboard/src/main.py:192-195`.

`aiohttp.Application` створюється без auth middleware. Без перевірки доступу доступні:

- читання і перезапис `/api/config`;
- додавання, зміна ролі та видалення користувачів;
- читання каталогів і станів Home Assistant;
- відправлення, редагування та видалення Telegram-повідомлень;
- передавання довільних `chat_id` і списків отримувачів.

Supervisor Ingress може захищати UI у штатній конфігурації, але це не замінює захист самих endpoints. Порт `8099` і reverse proxy можуть бути доступні інакше, а код не перевіряє ні користувача HA, ні origin, ні CSRF.

**Вплив:** віддалений клієнт із доступом до listener може отримати конфігурацію, підвищити собі роль до admin, змінити dashboard і відправляти Telegram-повідомлення.

**Рекомендація:** додати middleware автентифікації для кожного API route, перевірку HA/Ingress identity, CSRF-захист mutating-запитів, перевірку `Host`/`Origin`, і тести неавторизованих GET/POST/DELETE.

### 2. `AccessController` залишається зі старим snapshot користувачів

**Файли:** `telegram_dashboard/src/access_controller.py:31-48`; `telegram_dashboard/src/bot_engine.py:38-61`; `telegram_dashboard/src/web_server.py:159-194`.

`AccessController` зберігає користувачів у приватному `_users`. Після UI-змін `save_config`, `upsert_user` або `delete_user` controller не перезавантажується. У `auto_discover_user` перевіряється `hasattr(self.access, "users")`, але такого атрибута немає — є `_users`.

**Вплив:**

- видалений або понижений admin може продовжити використовувати старі права до restart;
- новий користувач або підвищений member може не отримати нові права;
- зміни `blocked_entities` і whitelist не застосовуються одразу.

**Рекомендація:** додати атомарні `reload/update/upsert/remove` методи в `AccessController` і викликати їх після кожної зміни конфігурації та auto-discovery.

### 3. Callback action може обійти section RBAC і викликати довільний HA service

**Файли:** `telegram_dashboard/src/bot_engine.py:372-431`; `access_controller.py:134-142`.

`handle_action()` шукає action глобально через `_find_action()`, але не викликає `check_section()` для секції-власника. `min_role` за замовчуванням — `guest`. Domain/service беруться з конфігурації, а payload може бути широким або без конкретної entity.

**Вплив:** користувач може вручну сформувати callback `td:/act_<id>` і виконати action із прихованої admin-секції. Action без явного `min_role` може бути доступним guest і викликати небезпечний сервіс.

**Рекомендація:**

- перевіряти `check_section()` перед виконанням;
- вимагати явний `min_role` для кожної state-changing action;
- за замовчуванням відмовляти, а не дозволяти guest;
- дозволяти тільки відомі domain/service;
- вимагати і перевіряти entity target;
- перевіряти всі entity у payload через entity-level RBAC.

### 4. Entity browser показує restricted users усі стани Home Assistant

**Файл:** `telegram_dashboard/src/bot_engine.py:267-276`; wiring у `src/main.py:141-146`; `renderer.py` `render_entity_list()`.

Для секції `type == "entities"` `handle_navigation()` передає у renderer весь результат `get_all_states()`. Клавіатура фільтрується через `_visible_entities()`, але текст повідомлення — ні.

**Вплив:** користувач може побачити назви й поточні значення всіх entity, включно із сенсорами безпеки, присутністю, замками та іншими restricted entity.

**Рекомендація:** спочатку сформувати authorized entity set, відфільтрувати state mapping, і тільки потім передавати його в renderer. Renderer не повинен самостійно отримувати або бачити необмежений snapshot.

### 5. Auto-discovery приймає будь-які Telegram events і пише їх на диск

**Файли:** `telegram_dashboard/src/telegram_bot.py:217-238`, `275-303`; `config_manager.py:162-195`.

`auto_discover_user()` викликається до перевірки, чи command взагалі належить dashboard. Будь-який невідомий command/callback може створити запис guest і виконати save. Якщо `default_role` встановити як admin, новий Telegram user отримає admin.

**Вплив:** можливе створення необмеженої кількості записів, повторні disk writes/backups, DoS через storage/write contention. Небезпечний `default_role=admin` дає admin невідомим користувачам.

**Рекомендація:** auto-discover тільки для розпізнаного dashboard command/callback; невідомих користувачів не записувати або записувати у bounded pending queue; заборонити admin як default role для auto-discovery; додати rate limit і ліміт користувачів.

---

## P1 / високий або середньо-високий ризик

### 6. `speak` приймає довільний Home Assistant service

**Файл:** `custom_components/telegram_dashboard/__init__.py:82-89`, `196-211`.

Поле `tts_service` довільне: код розділяє його на domain/service і викликає `hass.services.async_call()`. Не перевіряється ні TTS domain, ні тип entity.

**Вплив:** service `speak` фактично стає generic HA service dispatcher для того, хто може викликати цей service.

**Рекомендація:** дозволити тільки allowlist TTS services, вимагати `media_player` або окремий whitelist entity і додати негативні тести.

### 7. XSS через unescaped значення у frontend `innerHTML`

**Файл:** `telegram_dashboard/src/ui/app.js:376-378`, `1785-1790`, `1856-1859`, `1961-1970`, `2607-2610`.

`escapeHtml()` існує, але не застосовується до всіх значень. У шаблони напряму потрапляють `friendly_name`, `entity_id`, state, user name, device name та інші дані з API/HA/config.

**Вплив:** значення з malicious friendly name або user name можуть зламати markup і виконати HTML/event-handler payload у UI origin.

**Рекомендація:** використовувати `createElement()` + `textContent`/`value`/`dataset`; або escape кожного динамічного значення в кожному HTML attribute/text context. Додати XSS tests з кавичками, `<img onerror>` та entity names.

### 8. Preview довіряє `data.html` і вставляє його через `innerHTML`

**Файл:** `telegram_dashboard/src/ui/app.js:2178-2184`.

HTML із `/api/preview` вставляється у тимчасовий DOM і потім копіюється у `previewText.innerHTML`. Allowlist sanitizer немає.

**Вплив:** будь-яка неочікувана HTML-розмітка з menu/config/HA metadata може виконати markup payload або зламати preview.

**Рекомендація:** повертати structured AST і будувати DOM через text nodes або санітизувати allowlist тегів Telegram (`b`, `i`, `code`, `pre`, `blockquote`) без небезпечних атрибутів.

### 9. `ensure_ha_integration_enabled()` і `sync_custom_component()` змінюють `/config` під час кожного старту

**Файл:** `telegram_dashboard/src/main.py:32-93`.

Код копіює companion integration через `copytree(..., dirs_exist_ok=True)` і дописує `telegram_dashboard:` у `configuration.yaml` без YAML parsing, lock, backup або atomic replace.

**Вплив:** add-on може перезаписати user-installed файли, додати дублікати або залишити пошкоджений `configuration.yaml` при interruption. Це великий blast radius, бо manifest має `homeassistant_config:rw`.

**Рекомендація:** не інсталювати custom component автоматично на runtime; якщо migration необхідна — робити verified backup, структурне YAML редагування, temp+fsync+atomic replace і rollback.

### 10. Динамічні HA state/unit значення не всюди escape у Telegram HTML

**Файл:** `telegram_dashboard/src/renderer.py:88-114`, `239-247`.

`format_entity_value()` повертає raw state/unit, а renderer вставляє значення у HTML. Заголовки й labels escape-яться, але не всі state/unit fragments.

**Вплив:** спеціальне значення HA може вставити Telegram HTML або зламати parse mode.

**Рекомендація:** escape values/units у formatter або використовувати safe fragments із чітким розділенням renderer-owned tags і dynamic text.

---

## P2 / середній ризик і надійність

### 11. WebSocket callback tasks не відстежуються

**Файл:** `telegram_dashboard/src/ha_client.py:192-249`.

Кожна подія запускає `asyncio.create_task(cb(...))`, але tasks не зберігаються, exceptions не збираються, concurrency не обмежена, subscription result не перевіряється.

**Вплив:** burst подій може створити багато tasks, помилки можуть бути unobserved, а shutdown не дочекається/не скасує callbacks.

**Рекомендація:** task set із done callback, bounded semaphore/queue, cancel+gather у `close()`, перевірка subscribe responses і backoff.

### 12. Config saves не серіалізовані

**Файл:** `telegram_dashboard/src/config_manager.py:135-153`.

Backup завжди один — `.json.bak`; save не має lock/fsync і може одночасно виконуватися з web request та auto-discovery.

**Вплив:** last-write-wins може втратити зміни; concurrent save може пошкодити або перекрити backup.

**Рекомендація:** lock на load/mutate/save, fsync temp і directory, rotating/timestamped backups, тести concurrent saves/interrupted writes.

### 13. Некоректні числові IDs можуть викидати uncaught `ValueError`

**Файл:** `telegram_dashboard/src/telegram_bot.py:70-81`, `100-110`, `161-167`, `178-185`, `303-345`.

`int(chat_id)`, `int(message_id)` і `int(callback_query_id)` виконуються до безпечної обробки. Malformed HA event може перервати handler і залишити callback без acknowledgment.

**Рекомендація:** спільний safe integer parser, reject malformed events, catch conversion errors, по можливості acknowledge valid callback query.

### 14. Error responses розкривають внутрішні exception details

**Файли:** `web_server.py:159-167`, `298-343`; `bot_engine.py:365-370`.

У клієнт повертаються `str(e)` та raw upstream error. Service exception також може потрапити користувачу в toast.

**Вплив:** витік шляхів, HA response details і внутрішньої структури; додатково raw text може потрапити в HTML/Telegram markup.

**Рекомендація:** generic user-facing errors + server-side logs із correlation ID.

### 15. CI не тестує найризикованіші частини

**Файл:** `.github/workflows/ci.yaml`.

CI запускає lint/unit tests і JS syntax, але не тестує:

- web route authentication/authorization;
- CSRF/recipient authorization;
- custom component setup/unload;
- Docker build/runtime;
- HA WebSocket lifecycle;
- startup writes у `/config`;
- concurrent config save;
- frontend XSS/parity scenarios.

`pytest-cov` також не встановлений, тому coverage report не доступний.

**Рекомендація:** додати security/integration suite, Docker smoke test, Home Assistant stubs або supported HA test environment, coverage threshold і dependency vulnerability scan.

### 16. Frontend має порушення localization invariant і dead UI flow

**Файли:** `telegram_dashboard/src/ui/app.js:2117`, `2267`, `2524-2560`, `2587`, `2597`, `2647`, `2695`; `index.html:123-126`.

Є hardcoded Ukrainian strings у UI, які не проходять через `t()`. Кнопка `Add button` існує в інтерфейсі, але її handler показує `coming soon` і не створює кнопку.

**Вплив:** mixed-language UI; користувач бачить доступну дію, яка фактично не працює.

**Рекомендація:** додати всі strings до `i18n.js` для `en`/`uk`; або приховати/disable `Add button`, доки flow не реалізований.

### 17. `min-height: 680px` ламає короткі mobile viewport

**Файл:** `telegram_dashboard/src/ui/style.css:944-950`, `2145-2155`.

Разом із `height: calc(100dvh - 110px)` залишається `min-height: 680px`. На екрані висотою 568–667px телефон гарантовано більший за viewport.

**Вплив:** зайвий page scroll і винесені за екран controls.

**Рекомендація:** `clamp()` або min-height, що залежить від viewport; перевірити 320×568, 375×667, landscape.

---

## Що не вважаю проблемою

- У git tree не знайдено `.env`, приватних ключів або реальних секретів.
- Використання `SUPERVISOR_TOKEN` через environment — правильний підхід.
- `ConfigManager.save()` використовує temp file + `os.replace`, тобто базовий atomic replace є; проблема саме у відсутності lock/fsync і rotation backup.
- Наявність `innerHTML` сама по собі не є вразливістю, але конкретні неекрановані interpolation points є проблемою.
- 44 існуючі тести проходять, але їхній green status не покриває виявлені security/runtime gaps.

## Рекомендований порядок виправлень

1. Закрити HTTP API auth/CSRF/recipient authorization.
2. Виправити live synchronization `AccessController`.
3. Заблокувати arbitrary actions/services і додати section RBAC до callbacks.
4. Фільтрувати entity states перед renderer.
5. Прибрати auto-discovery для невідомих events і заборонити default admin.
6. Закрити frontend XSS і HTML sanitizer/structured preview rendering.
7. Обмежити `speak` allowlist-ом.
8. Прибрати небезпечні startup writes або зробити їх atomic/rollback-safe.
9. Додати integration/security tests і Docker/HA CI smoke test.
10. Після цього виправити localization, config concurrency, WebSocket lifecycle і responsive edge cases.
