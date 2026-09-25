# AI Agent Instructions for Home Assistant Telegram Dashboard

## 1. Operating Rules & Workflow

1. **Self-Modification Restriction**:
   - The AI must NEVER edit or modify `AGENTS.md` unilaterally.
   - If the AI identifies missing rules, optimizations, or necessary changes to this file, it must explicitly propose them to the user for approval first.

2. **User Interaction & Tone**:
   - Communicate with the user in Ukrainian.
   - Keep answers concise, clear, and directly to the point without filler or unnecessary verbosity.
   - When given a direct command to fix/do something, execute directly.
   - When asked to analyze, review, or evaluate ideas, first present a concise plan/analysis and wait for approval before modifying code.

3. **Version & Release Policy**:
   - **Default Rule**: Always update the current version in place until the user explicitly commands to create a new version.
   - **Version Format**: Follow semantic versioning (`v1.0.x`).
   - **Version Bumping**: When instructed to create a new version, increment the patch digit (e.g., `1.0.0` -> `1.0.1`).
   - For major architectural or feature overhauls, the minor digit may be bumped (e.g., `1.1.0`); the AI should proactively suggest this to the user when appropriate.
   - When creating a new version, synchronize version strings across:
     - `telegram_dashboard/config.yaml` (`version`)
     - `telegram_dashboard/src/__init__.py` (`__version__`)
     - `telegram_dashboard/CHANGELOG.md`
     - `CHANGELOG.md` (root)
     - `README.md` (if badge/header lists version)
   - **Changelog Quality & Sync Invariant**:
     - Home Assistant Supervisor update dialog renders `telegram_dashboard/CHANGELOG.md` directly. It MUST always contain the latest version header at the top and stay 100% in sync with root `CHANGELOG.md`.
     - Changelog entries must be grouped by standard sections (e.g. `### Added`, `### Changed`, `### Fixed`, `### Security`).
     - Entries must describe meaningful user-facing changes clearly and concisely. Minor tweaks, minor layout adjustments or internal micro-refactors must be generalized into coherent points rather than listed line-by-line.

4. **Source of Truth & Git Discipline**:
   - Always verify and pull the latest changes from `origin/main` before making changes.
   - Maintain minimal diffs: touch only lines strictly related to the task.
   - Never overwrite user configurations or introduce breaking changes without warning.
   - Git commits should be concise, following conventional commit format (`fix:`, `feat:`, `docs:`, `perf:`, `test:`, `chore:`).
   - Commit author identity: `kdinya <kdinya@users.noreply.github.com>` (GitHub profile email, never a real mailbox).

5. **Mandatory CI Checks & Zero-Error Policy**:
   - Before pushing any commit or declaring a task complete, the AI MUST run full local verification matching the CI pipeline:
     - `flake8 telegram_dashboard/src tests --max-line-length=120 --ignore=E203,W503,F401`
     - `python -m pytest tests/ -v`
   - Zero errors, zero test failures, and zero lint violations are strictly mandatory. Pushing code that breaks CI is strictly prohibited.
   - Immediately after pushing, the AI must verify the GitHub Actions run status via the GitHub API to ensure the build has passed successfully.

---

## 2. Core Architecture & Strict Invariants

1. **Add-on Configuration & Ingress**:
   - `telegram_dashboard/config.yaml` is the manifest for Home Assistant Supervisor.
   - `ingress: true` with internal port `8099` must always be supported.
   - Supervisor API token (`SUPERVISOR_TOKEN`) is passed as an environment variable to communicate with Home Assistant Core (`http://supervisor/core/api`).

2. **Role-Based Access Control (RBAC) Invariant**:
   - Every Telegram incoming update (command or callback query) must pass through `AccessController`.
   - Never expose administrative or destructive actions (such as PC reboot/shutdown, main valve manipulation, AC state toggle) to unauthenticated users or users without the required role (`admin`, `member`, `guest`).
   - Unregistered users must be denied or routed to a restricted guest view based on configuration.
   - Per-user restrictions (`allowed_domains`, `allowed_areas`, `allowed_labels`, `blocked_entities`) must be enforced on every entity-level action, not only on menu sections.

3. **Message Rendering & Typography**:
   - Telegram message rendering uses standard Telegram HTML parse mode (`<b>`, `<code>`, `<i>`, `<blockquote>`, `<pre>`).
   - Hierarchy and readability are preserved with structured tree lines (`├`, `└`) and visual progress bars (`[▰▰▰▰▱▱]`).
   - All dynamic messages sent in response to inline buttons must use `edit_message` logic with callback query acknowledgment (`answerCallbackQuery`) to avoid spam and lingering loading spinners.

4. **Persistence & Data Safety**:
   - Dynamic user settings and menu schemas reside in `/data/config.json`.
   - When running outside of HA (e.g. standalone test mode), fallback to local `config.json` without crashing.
   - Always validate JSON against the schema on load and create atomic backups before saving.
   - Any code change must ensure user settings, menu schemas, and user lists are never reset or wiped during add-on updates, restarts, or config migrations; storage schemas must stay backwards-compatible across versions.

5. **Full Catalog Access**:
   - The bot and the builder UI must be able to reach the whole Home Assistant instance: all devices and entities, all domains (lights, switches, climate, covers, media players, ...), all scripts, automations (trigger/enable/disable), scenes, and individual services per entity.
   - Grouping must support areas (rooms), labels (categories), and domains; no entity may be unreachable through the UI builder.
   - Speech output to smart speakers (TTS) must target `media_player` entities and use a configurable TTS service; speaker actions (speak, volume up/down/set, mute) are first-class action types.

6. **Localization & Multi-Language Support**:
   - The add-on interface supports English (`en`, default) and Ukrainian (`uk`) with live instant language switching and persistent preference storage.
   - When adding, modifying, or removing any elements in the add-on UI (buttons, labels, headings, tooltips, placeholders, modals, toasts, or statuses), they must be fully integrated into the translation system (`i18n.js` / translation dictionary) in both English and Ukrainian (`en` and `uk`).
   - Hardcoded UI strings without localization keys are strictly prohibited.
   - Custom user-defined objects and names (such as custom section names, user-typed text items, user names, and Home Assistant entity names/states) are preserved as-is and are not subjected to static dictionary translation.

7. **Test Invariant**:
   - All business logic (RBAC, Message Renderer, Config Manager, HA Connector, Bot Engine) must have 100% passing tests in `tests/`.
   - Run `pytest` before every release and commit.

8. **UI Component Style Consistency Invariant**:
   - Any new popup, modal, dialog, toast/notification, or dropdown (`<select>` or custom listbox) added anywhere in the UI must be styled strictly using the existing design system (CSS variables in `style.css`: colors, radii, shadows, typography, spacing). No ad-hoc or browser-default styling is allowed.
   - Reuse existing shared classes (e.g. `.form-control`, `.panel-card`, `.modal`) instead of introducing new one-off styles; if a new shared class is needed, add it to `style.css` following the established naming and variable conventions.

9. **Constructor Preview & Telegram Message Parity Invariant**:
   - Whenever menu sections or their elements (texts, entities, buttons, headings, icons) are edited, added, or removed in the constructor, the preview in the web UI must accurately and synchronously reflect all changes.
   - The rendered preview must strictly match the composition, formatting, hierarchy, and style of the message that is sent to Telegram. What is configured in the constructor must be identical in the UI preview and in the actual Telegram bot message delivery (WYSIWYG parity).

---

## 3. Pre-Flight Verification Checklist

Before pushing any commit or releasing:
1. **Lint**: `flake8 telegram_dashboard/src tests --max-line-length=120 --ignore=E203,W503,F401` — zero errors.
2. **Unit Tests**: `python -m pytest tests/ -v` — 100% passing.
3. **Clean Working Tree**: no temporary artifacts or unstaged files remain.
4. **Constructor Preview & Telegram Parity Check**: ensure changes to sections and their elements immediately render in the UI live preview and strictly correspond to the Telegram message formatting.

---

## 4. Reference Documentation & Sources of Truth

When facing unknowns, investigating APIs, or verifying expected schemas, payload formats, or behavior, the AI **MUST first consult these official references** before searching elsewhere:

1. **Home Assistant Telegram Bot Integration**:
   - Integration overview & event schemas (`telegram_command`, `telegram_callback`, etc.):
     https://www.home-assistant.io/integrations/telegram_bot/
   - Action `telegram_bot.send_message`:
     https://www.home-assistant.io/actions/telegram_bot.send_message/
   - Action `telegram_bot.edit_message`:
     https://www.home-assistant.io/actions/telegram_bot.edit_message/
   - Action `telegram_bot.answer_callback_query`:
     https://www.home-assistant.io/actions/telegram_bot.answer_callback_query/

2. **Home Assistant WebSocket API**:
   - Realtime event subscriptions, authentication, and service calls:
     https://developers.home-assistant.io/docs/api/websocket/

3. **Telegram Bot API**:
   - Official Telegram Bot API Reference (inline keyboards, formatting, limits):
     https://core.telegram.org/bots/api
   - BotFather (Bot creation & configuration commands):
     https://t.me/BotFather

4. **Project Repository**:
   - Source code, issue tracker, and releases:
     https://github.com/kdinya/ha-telegram-dashboard

Only if an answer cannot be determined from these primary sources should the AI proceed with broader web search or external documentation.
