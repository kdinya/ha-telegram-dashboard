"""Role-Based Access Control for the Telegram bot."""
from __future__ import annotations

from dataclasses import dataclass, field


ROLE_PRIORITY = {"admin": 3, "member": 2, "guest": 1}
DEFAULT_ROLE = "guest"


@dataclass
class AccessDecision:
    allowed: bool
    role: str
    reason: str = ""
    hidden_actions: list[str] = field(default_factory=list)


class AccessController:
    """Decides what a Telegram user may see and do.

    A user is looked up in the configured user list by ``telegram_id``.
    Unknown users fall back to ``default_role`` (usually ``guest``).

    Per-user restriction lists (optional):
      - ``allowed_domains`` / ``allowed_areas`` / ``allowed_labels`` /
        ``allowed_entities``: whitelist; absent or null means unrestricted.
      - ``blocked_entities``: always denied, even for members.
    """

    def __init__(self, users: list[dict], default_role: str = DEFAULT_ROLE) -> None:
        self._users = {
            int(user["telegram_id"]): user for user in users
        }
        if default_role not in ROLE_PRIORITY:
            raise ValueError(f"unknown default role '{default_role}'")
        self._default_role = default_role

    def role_of(self, telegram_id: int) -> str:
        user = self._users.get(int(telegram_id))
        if user is None:
            return self._default_role
        return str(user.get("role", self._default_role))

    def user_record(self, telegram_id: int) -> dict:
        return self._users.get(int(telegram_id), {})

    def is_registered(self, telegram_id: int) -> bool:
        return int(telegram_id) in self._users

    def check_section(self, telegram_id: int, section_key: str, section: dict) -> AccessDecision:
        """Check whether the user may open a menu section."""
        role = self.role_of(telegram_id)
        allowed_roles = section.get("roles", [])
        if role in allowed_roles:
            return AccessDecision(True, role)
        return AccessDecision(
            False,
            role,
            reason=(
                f"Section '{section_key}' requires one of {allowed_roles}, "
                f"but your role is '{role}'."
            ),
        )

    def check_entity(
        self,
        telegram_id: int,
        entity_id: str,
        area: str | None = None,
        domain: str | None = None,
        labels: list[str] | None = None,
    ) -> AccessDecision:
        """Entity-level gate honoring per-user domain/area/label/entity limits."""
        role = self.role_of(telegram_id)
        if role == "admin":
            return AccessDecision(True, role)
        user = self.user_record(telegram_id)
        if entity_id in set(user.get("blocked_entities", []) or []):
            return AccessDecision(False, role, reason=f"Сутність {entity_id} заблокована для вас.")

        def whitelist(key: str) -> list | None:
            value = user.get(key)
            return value if isinstance(value, list) else None

        allowed_entities = whitelist("allowed_entities")
        if allowed_entities is not None and entity_id not in allowed_entities:
            return AccessDecision(False, role, reason=f"Сутність {entity_id} не дозволена для вас.")
        allowed_domains = whitelist("allowed_domains")
        if allowed_domains is not None and domain is not None and domain not in allowed_domains:
            return AccessDecision(False, role, reason=f"Категорія '{domain}' не дозволена для вас.")
        allowed_areas = whitelist("allowed_areas")
        if allowed_areas is not None and area is not None and area not in allowed_areas:
            return AccessDecision(False, role, reason=f"Зона '{area}' не дозволена для вас.")
        allowed_labels = whitelist("allowed_labels")
        if allowed_labels is not None and labels:
            if not any(label in allowed_labels for label in labels):
                return AccessDecision(False, role, reason="Категорія не дозволена для вас.")
        return AccessDecision(True, role)

    def filter_actions(self, telegram_id: int, actions: list[dict]) -> list[dict]:
        """Return only the actions the user is allowed to trigger."""
        role = self.role_of(telegram_id)
        priority = ROLE_PRIORITY.get(role, 0)
        visible: list[dict] = []
        for action in actions:
            min_role = action.get("min_role", "guest")
            if ROLE_PRIORITY.get(min_role, 0) <= priority:
                visible.append(action)
        return visible

    def check_action(self, telegram_id: int, action: dict) -> AccessDecision:
        """Check a single action; destructive actions need at least 'member'."""
        role = self.role_of(telegram_id)
        min_role = action.get("min_role", "guest")
        if ROLE_PRIORITY.get(min_role, 0) > ROLE_PRIORITY.get(role, 0):
            return AccessDecision(
                False, role, reason=f"Action requires role '{min_role}' or higher."
            )
        return AccessDecision(True, role)
