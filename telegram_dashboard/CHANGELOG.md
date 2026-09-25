## 1.0.5

- Security: HTML-escape entity and button labels in constructor lists to prevent stored attribute injection.
- UI: HTML-escape dynamic entity state strings.
- HA Integration: Companion integration auto-sync to /homeassistant with services for Automations and Scripts.
- Integration: Cleanup dead ternary in inline_keyboard payload builder.

## 1.0.3

- Home Assistant sidebar: full add-on title `panel_title: "Telegram Dashboard"`.
- Interactive entity builder across all sections with 3-row input layout (icon + name + indent toggle, entity selector, cancel/save).
- Sequential ordering of section elements (texts and entities appear in order above the 3 add buttons and render synchronously in UI preview and Telegram message).
- Real-time preview and Telegram bot rendering for entities (icon, name, value).
- Full bilingual localization (`en` and `uk`).

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
# Changelog - Telegram Dashboard Add-on

## 1.0.0

- Initial Beta release: visual builder, RBAC, Telegram HTML rendering, full catalog (areas/domains/labels), speaker TTS and volume actions.
- Fixed startup crash: `s6-overlay-suexec: fatal: can only run as pid 1`. App runs directly as PID 1.
- Initial release with visual dashboard builder, RBAC, and modern HTML message styling.

## [1.0.4] - 2026-09-25
### Added
- Native Home Assistant services in Automations and Scripts UI (`telegram_dashboard.send_message`, `edit_message`, `delete_message`, `answer_callback`, `send_photo`, `send_document`, `speak`).
- Companion integration in `custom_components/telegram_dashboard/` with full visual selectors and translations.
- Auto-sync companion integration into `/config/custom_components` on container start.
- REST API endpoints on Ingress server for bot execution (`/api/bot/*`).
- Docker volume map `config:rw` to enable direct integration sync into HA Core.
