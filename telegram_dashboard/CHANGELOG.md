## 1.0.8

### Fixed
- Fixed UI startup initialization failure caused by stale icon picker event listener reference.
- Telegram message rendering: removed spoiler overlay from update timestamp so the time is immediately visible without clicking.
- Synchronized add-on version across all UI badges, manifests, and documentation.

### Added
- Navigation section buttons: added interactive up/down arrow controls to reorder buttons per section with live preview and Telegram message parity.
- Modern high-resolution add-on icon and logo for Home Assistant supervisor store and add-on UI header.

## 1.0.7

### Changed
- Entity picker: filters grouped into 4 logical categories — Controls & Devices, Sensors & States, Automations & Scripts, Home Assistant & System.
- Entity picker: improved multi-token search across friendly names, entity IDs and areas (word order no longer matters).

## 1.0.6

### Fixed
- Fixed inline text editor crash (`nameInput` → `inputVal`): "Add text" now works again.
- Entity picker: removed restrictive domain filters — search matches by name and entity ID directly.
- Fixed Home Assistant REST payload for service calls (entity_id flattened to top level).
- Fixed `/api/template` plain-text response parsing.
- Telegram bot: section-level access checks enforced in callback handlers before executing actions.
- Companion integration: configured Telegram bot token is auto-written to `configuration.yaml` during sync, so automation actions work without manual re-entry.
- Fixed TTS service call splitting domain and service for media players.
- Web API now accurately reports Telegram send failures instead of pretending success.

## 1.0.5

### Security & Fixes
- Security: HTML-escape entity and button labels in constructor lists to prevent stored attribute injection.
- Security: HTML-escape dynamic entity state strings.
- HA Integration: companion integration auto-sync to `/homeassistant` with services for Automations and Scripts.
- Integration: cleanup dead ternary in inline_keyboard payload builder.

## 1.0.3

### Added
- Home Assistant sidebar: full add-on title `panel_title: "Telegram Dashboard"`.
- Interactive entity builder across all sections with 3-row input layout (icon + name + indent toggle, entity selector, cancel/save).
- Sequential ordering of section elements (texts and entities appear in order above the 3 add buttons and render synchronously in UI preview and Telegram message).
- Real-time preview and Telegram bot rendering for entities (icon, name, value).
- Full bilingual localization (`en` and `uk`).

## 1.0.1

### Fixed
- Fix: correct Home Assistant API base URL so the entity picker and bot states work (entities are no longer empty).
- Fix: bot token from add-on options is now passed to user sync; sync no longer depends on config.json.
- Fix: entity picker falls back to sample entities with a visible warning when HA is unreachable.
- UI: icon picker block on the left of the section name field; manual icon text input removed.
- UI: nav panel items keep exactly one icon each.
- UI: "Add user" button wraps instead of overflowing its block.
- UI: background no longer scrolls behind open modals.
- UI: entity selection fields show area, state, full entity id and never truncate names.
- Fix: saving an action recovers the chosen entity if the picker selection was lost.
