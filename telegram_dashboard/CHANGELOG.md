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
