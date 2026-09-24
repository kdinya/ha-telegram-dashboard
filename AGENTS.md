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

4. **Source of Truth & Git Discipline**:
   - Always verify and pull the latest changes from `origin/main` before making changes.
   - Maintain minimal diffs: touch only lines strictly related to the task.
   - Never overwrite user configurations or introduce breaking changes without warning.
   - Git commits should be concise, following conventional commit format (`fix:`, `feat:`, `docs:`, `perf:`, `test:`, `chore:`).
   - Commit author identity: `kdinya <tomchik2@gmail.com>`.

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

3. **Message Rendering & Typography**:
   - Telegram message rendering uses standard Telegram HTML parse mode (`<b>`, `<code>`, `<i>`, `<blockquote>`, `<pre>`).
   - Hierarchy and readability are preserved with structured tree lines (`├`, `└`) and visual progress bars (`[▰▰▰▰▱▱]`).
   - All dynamic messages sent in response to inline buttons must use `edit_message` logic with callback query acknowledgment (`answerCallbackQuery`) to avoid spam and lingering loading spinners.

4. **Persistence & Data Safety**:
   - Dynamic user settings and menu schemas reside in `/data/config.json`.
   - When running outside of HA (e.g. standalone test mode), fallback to local `config.json` without crashing.
   - Always validate JSON against the schema on load and create atomic backups before saving.

5. **Test Invariant**:
   - All business logic (RBAC, Message Renderer, Config Manager, HA Connector) must have 100% passing tests in `tests/`.
   - Run `pytest` before every release and commit.
