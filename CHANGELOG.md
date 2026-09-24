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
