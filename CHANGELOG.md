## 1.0.9

### Fixed
- Constructor live preview no longer crashes with a rendering error when updating the message bubble width.
- Bot token field in Settings now correctly shows the token configured in the add-on options when no token has been set via the UI.

### Changed
- Dropdown menus across the UI restyled to match the app's dark design system instead of default browser styling.
- Notification toast moved to the top-right corner with a slightly translucent look.

## 1.0.8

### Fixed
- Fixed UI startup initialization failure caused by stale icon picker event listener reference.
- Telegram message rendering: removed spoiler overlay from update timestamp so the time is immediately visible without clicking.
- Synchronized add-on version across all UI badges, manifests, and documentation.

### Added
- Navigation section buttons: added interactive up/down arrow controls to reorder buttons per section with live preview and Telegram message parity.
- Modern high-resolution add-on icon and logo for Home Assistant supervisor store and add-on UI header.

## 1.0.1

- Fix: correct Home Assistant API base URL so the entity picker and bot states work (entities are no longer empty).
- Fix: bot token from add-on options is now passed to user sync; sync no longer depends on config.json.
- Fix: entity picker falls back to sample entities with a visible warning when HA is unreachable.
- UI: icon picker block on the left of the section name field; manual icon text input removed.
- UI: nav panel items keep exactly one icon each.
- UI: "Add user" button wraps instead of overflowing its block.
- UI: background no longer scrolls behind open modals.
- UI: entity selection fields show area, state, full entity id and never truncate names.
- Fix: saving an action recovers the chosen entity if the picker selection was lost.
# Changelog

## [1.1.1] - 2026-03-29

### Fixed
- Fixed inline keyboard buttons displaying the word 'text' in Telegram by converting button rows to Home Assistant's expected `[[text, callback_data]]` format.
- Fixed simulator/live preview navigation when clicking buttons with the isolated `td:` namespace prefix.
- Handled both array and dictionary button representations seamlessly in the simulator UI.

### Changed
- Removed deprecated Telegram bot token configuration, schema entries, and direct API `getUpdates` from the add-on.
- Updated add-on description and documentation to clearly highlight operation on top of Home Assistant's official `telegram_bot` integration.
- Added informative integration card to settings modal.


## [1.1.0] - 2026-03-29

### Added
- Multi-menu routing by Telegram command: each menu section can now define its own trigger command (e.g. , , ).
- Telegram Command input field in the web UI section settings modal with persistence to config.
- Home Assistant  event bridge listening to  and  via HA WebSocket.
- Callback namespace isolation ( prefix) so external Telegram automations and dashboard callbacks do not conflict.
- Comprehensive test suite for HA bridge routing and namespace isolation ().

### Changed
- Shifted Telegram messaging from direct API polling to Home Assistant official  actions (, , , ).
- Decoupled add-on runtime from direct Telegram bot tokens; communications are proxied cleanly through Home Assistant.

## [1.0.7] - 2026-03-31

### Changed
- Grouped Entity Picker filters into 4 logical categories: Controls & Devices, Sensors & States, Automations & Scripts, and Home Assistant & System.
- Improved search in Entity Picker: supports multi-token search across friendly names, entity IDs, and areas without strict order.

## [1.0.6] - 2026-03-31

### Fixed
- Fixed ReferenceError in  (focusInput referencing undefined nameInput instead of inputVal), allowing inline text creation to work seamlessly.
- Removed restrictive domain tabs in Entity Picker so all entities are searchable by name and entity ID directly.
- Fixed  REST payload by flattening target entity_id to top-level for Home Assistant REST API.
- Fixed  to support plain-text template response parsing.
- Enforced section-level permission checks in Telegram bot callback handlers before executing button or entity actions.
- Automatically write configured Telegram bot token to Home Assistant  during companion integration sync so automation actions (, , etc.) work without manual re-entry.
- Split TTS service call domain and service in  handler for Home Assistant media players.
- Accurately propagate Telegram send message failure status codes in web API.

## [1.0.3] - 2026-09-25
### Added
- Home Assistant sidebar: set full add-on name `panel_title: "Telegram Dashboard"`.
- Constructor: full interactive "Add entity" builder for all sections placed under already created items and above action buttons.
- 3-row entity configuration block:
  1) Icon picker with library/no-icon support, custom display name field, and toggle button for indent.
  2) Home Assistant entity selector (grouped dropdown and visual modal picker).
  3) Cancel and Save buttons.
- Unified sequential element ordering: texts and entities are displayed in exact creation order under already created items and synchronously rendered in UI preview and Telegram messages.
- Real-time WYSIWYG parity for entities: preview displays icon, name, and live/formatted value with or without tree indent.
- Complete English (`en`) and Ukrainian (`uk`) localization for entity builder, indent toggles, and deletion confirmations.

## [1.0.2] - 2026-09-24
### Fixed
- Added `panel_icon: "mdi:telegram"` to display official Telegram icon on Home Assistant sidebar.
- Constructor UI: direct entities and action buttons with live status indication.

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-09-24

### Fixed
- Add-on startup crash with `s6-overlay-suexec: fatal: can only run as pid 1`. The app now runs directly as PID 1 (`ENTRYPOINT []`), independent of Docker `--init` behavior.
- Added official My Home Assistant one-click installation button to README.

### Added
- First public release of Telegram Dashboard Home Assistant Add-on.
- Visual Ingress Web UI builder for interactive Telegram dashboards.
- Role-Based Access Control (RBAC) with granular user permissions per section and action.
- Advanced Telegram HTML message renderer with quotes (`<blockquote>`), hierarchy trees (`├`, `└`), and visual battery progress bars (`[▰▰▰▰▱▱]`).
- Interactive inline buttons with automatic `edit_message` navigation and state toggling.
- Direct Supervisor API integration for zero-config Home Assistant communication.
- Full pytest test suite and GitHub Actions CI workflow.

## [1.0.5] - 2026-09-25
### Security & Bug Fixes
- UI: HTML-escape entity and button labels in `renderEntitiesList` and `renderButtonsList` to prevent stored DOM/attribute injection.
- UI: HTML-escape dynamic entity state badge values.
- Add-on & HA: Ensure companion custom integration is synced to `/homeassistant` config directory with automated `telegram_dashboard:` entry.
- Integration: Cleaned dead ternary logic in `inline_keyboard` payload builder.

## [1.0.4] - 2026-09-25
### Added
- Native Home Assistant services in Automations and Scripts UI (`telegram_dashboard.send_message`, `edit_message`, `delete_message`, `answer_callback`, `send_photo`, `send_document`, `speak`).
- Companion integration in `custom_components/telegram_dashboard/` with full visual selectors and translations.
- Auto-sync companion integration into `/config/custom_components` on container start.
- REST API endpoints on Ingress server for bot execution (`/api/bot/*`).
- Docker volume map `config:rw` to enable direct integration sync into HA Core.
