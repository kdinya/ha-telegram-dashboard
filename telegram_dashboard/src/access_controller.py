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
