"""Configuration manager: loads, validates and persists bot configuration."""
from __future__ import annotations

import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

DEFAULT_CONFIG: dict[str, Any] = {
    "version": "1.0.0",
    "language": "en",
    "menu": {
        "main": {
            "title": "🏠 Smart Home",
            "type": "menu",
            "icon": "🏠",
            "roles": ["admin", "member", "guest"],
            "widgets": [],
            "sections": ["climate", "water", "home", "battery", "system"],
        },
        "climate": {
            "title": "🌡 Climate",
            "type": "section",
            "icon": "🌡",
            "roles": ["admin", "member", "guest"],
            "widgets": [],
            "actions": [],
        },
        "water": {
            "title": "🚰 Water",
            "type": "section",
            "icon": "🚰",
            "roles": ["admin", "member"],
            "widgets": [],
            "actions": [],
        },
        "battery": {
            "title": "🔋 Batteries",
            "type": "section",
            "icon": "🔋",
            "roles": ["admin", "member"],
            "widgets": [],
        },
        "system": {
            "title": "⚙️ System",
            "type": "section",
            "icon": "⚙️",
            "roles": ["admin"],
            "widgets": [],
            "actions": [],
        },
    },
    "users": [],
}

REQUIRED_ROLES = {"admin", "member", "guest"}


class ConfigError(ValueError):
    """Raised when configuration file is invalid."""


def validate_config(config: Any) -> dict[str, Any]:
    """Validate an already-parsed config object, raise ConfigError on problems."""
    if not isinstance(config, dict):
        raise ConfigError("config must be a JSON object")
    menu = config.get("menu")
    if not isinstance(menu, dict) or not menu:
        raise ConfigError("config.menu must be a non-empty object")
    if "main" not in menu:
        raise ConfigError("config.menu must contain a 'main' entry")
    users = config.get("users")
    if not isinstance(users, list):
        raise ConfigError("config.users must be a list")
    for user in users:
        if not isinstance(user, dict):
            raise ConfigError("each user must be an object")
        if "telegram_id" not in user:
            raise ConfigError("each user needs 'telegram_id'")
        if user.get("role") not in REQUIRED_ROLES:
            raise ConfigError(
                f"user role must be one of {sorted(REQUIRED_ROLES)}"
            )
    for key, section in menu.items():
        if not isinstance(section, dict):
            raise ConfigError(f"menu section '{key}' must be an object")
        roles = section.get("roles")
        if not isinstance(roles, list) or not roles:
            raise ConfigError(f"menu section '{key}' needs a non-empty roles list")
        for role in roles:
            if role not in REQUIRED_ROLES:
                raise ConfigError(
                    f"menu section '{key}' has unknown role '{role}'"
                )
        widgets = section.get("widgets", [])
        if not isinstance(widgets, list):
            raise ConfigError(f"menu section '{key}' widgets must be a list")
    return config


class ConfigManager:
    """Load, validate, persist and back up the dynamic bot configuration."""

    def __init__(self, path: str | os.PathLike[str]) -> None:
        self._path = Path(path)
        self._config: dict[str, Any] | None = None

    @property
    def path(self) -> Path:
        return self._path

    def load(self) -> dict[str, Any]:
        """Load configuration from disk; fall back to defaults when absent."""
        if self._path.exists():
            raw = self._path.read_text(encoding="utf-8")
            try:
                parsed = json.loads(raw) if raw.strip() else dict(DEFAULT_CONFIG)
            except json.JSONDecodeError as exc:
                raise ConfigError(f"invalid JSON in {self._path}: {exc}") from exc
            self._config = validate_config(parsed)
        else:
            self._config = validate_config(json.loads(json.dumps(DEFAULT_CONFIG)))
        return self._config

    @property
    def config(self) -> dict[str, Any]:
        if self._config is None:
            return self.load()
        return self._config

    def save(self, config: dict[str, Any] | None = None) -> None:
        """Validate and atomically persist the configuration with a backup."""
        validated = validate_config(config if config is not None else self.config)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if self._path.exists():
            backup = self._path.with_suffix(".json.bak")
            shutil.copy2(self._path, backup)
        fd, tmp_name = tempfile.mkstemp(
            dir=str(self._path.parent), suffix=".tmp"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(validated, handle, ensure_ascii=False, indent=2)
            os.replace(tmp_name, self._path)
        except BaseException:
            if os.path.exists(tmp_name):
                os.unlink(tmp_name)
            raise
        self._config = validated

    # -- user management -------------------------------------------------
    def get_user(self, telegram_id: int) -> dict[str, Any] | None:
        for user in self.config.get("users", []):
            if user.get("telegram_id") == telegram_id:
                return user
        return None

    def upsert_user(self, telegram_id: int, name: str, role: str) -> dict[str, Any]:
        if role not in REQUIRED_ROLES:
            raise ConfigError(f"unknown role '{role}'")
        users = self.config.setdefault("users", [])
        for user in users:
            if user.get("telegram_id") == telegram_id:
                user["name"] = name
                user["role"] = role
                break
        else:
            users.append(
                {"telegram_id": telegram_id, "name": name, "role": role}
            )
        self.save()
        return {"telegram_id": telegram_id, "name": name, "role": role}

    def auto_discover_user(self, telegram_id: int, name: str, default_role: str = "guest") -> dict[str, Any]:
        """Automatically register or update a user interacting with the Telegram bot."""
        users = self.config.setdefault("users", [])
        for user in users:
            if user.get("telegram_id") == telegram_id:
                if name and (not user.get("name") or user.get("name").startswith("User ")):
                    user["name"] = name
                    self.save()
                return user
        role = default_role if default_role in REQUIRED_ROLES else "guest"
        new_user = {
            "telegram_id": telegram_id,
            "name": name or f"User {telegram_id}",
            "role": role,
        }
        users.append(new_user)
        self.save()
        return new_user

    def remove_user(self, telegram_id: int) -> bool:
        users = self.config.get("users", [])
        for index, user in enumerate(users):
            if user.get("telegram_id") == telegram_id:
                del users[index]
                self.save()
                return True
        return False
