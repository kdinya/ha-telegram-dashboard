"""Telegram Bot Engine handling commands, navigation, callbacks and access control."""
from __future__ import annotations

import logging
from typing import Any, Callable, Awaitable
from .access_controller import AccessController
from .renderer import MessageRenderer

logger = logging.getLogger("telegram_dashboard.bot")


class BotEngine:
    """Core logic for routing commands, rendering screens and editing messages."""

    def __init__(
        self,
        config: dict[str, Any],
        access_controller: AccessController,
        renderer: MessageRenderer,
        ha_call_service: Callable[[str, str, dict | None], Awaitable[Any]] | None = None,
        get_ha_state: Callable[[], Awaitable[dict[str, Any]]] | None = None,
    ) -> None:
        self.config = config
        self.access = access_controller
        self.renderer = renderer
        self.ha_call_service = ha_call_service
        self.get_ha_state = get_ha_state

    def build_keyboard(self, section_key: str, user_id: int) -> list[list[dict[str, str]]]:
        """Generate inline keyboard for a section respecting user role."""
        menu = self.config.get("menu", {})
        section = menu.get(section_key, {})
        keyboard: list[list[dict[str, str]]] = []

        if section_key == "main":
            row: list[dict[str, str]] = []
            for sub_key in section.get("sections", []):
                sub_section = menu.get(sub_key, {})
                decision = self.access.check_section(user_id, sub_key, sub_section)
                if decision.allowed:
                    icon = sub_section.get("icon", "")
                    title = sub_section.get("title", sub_key)
                    row.append({"text": f"{icon} {title}".strip(), "callback_data": f"/sec_{sub_key}"})
                    if len(row) == 2:
                        keyboard.append(row)
                        row = []
            if row:
                keyboard.append(row)
            keyboard.append([{"text": "🔄 Оновити", "callback_data": "/sec_main"}])
        else:
            # Action buttons inside this section
            actions = section.get("actions", [])
            allowed_actions = self.access.filter_actions(user_id, actions)
            for act in allowed_actions:
                keyboard.append([{"text": act.get("label", "Дія"), "callback_data": f"/act_{act.get('id')}"}])
            keyboard.append([
                {"text": "🔄 Оновити", "callback_data": f"/sec_{section_key}"},
                {"text": "⬅️ Головна", "callback_data": "/sec_main"},
            ])
        return keyboard

    async def handle_navigation(self, user_id: int, section_key: str, state: dict[str, Any]) -> dict[str, Any]:
        """Prepare message text, parse mode and inline keyboard for a section."""
        menu = self.config.get("menu", {})
        section = menu.get(section_key)

        if not section:
            return {
                "text": "❌ Розділ не знайдено.",
                "keyboard": [[{"text": "⬅️ Назад", "callback_data": "/sec_main"}]],
            }

        decision = self.access.check_section(user_id, section_key, section)
        if not decision.allowed:
            return {
                "text": f"⛔ <b>Доступ обмежено</b>\n\n{decision.reason}",
                "keyboard": [[{"text": "⬅️ Головна", "callback_data": "/sec_main"}]],
                "parse_mode": "HTML",
            }

        text = self.renderer.render_section(section, state)
        keyboard = self.build_keyboard(section_key, user_id)
        return {
            "text": text,
            "keyboard": keyboard,
            "parse_mode": "HTML",
        }

    async def handle_action(self, user_id: int, action_id: str, state: dict[str, Any]) -> dict[str, Any]:
        """Execute a Home Assistant action requested by an inline button."""
        # Find action across all sections
        target_action = None
        for sec in self.config.get("menu", {}).values():
            for act in sec.get("actions", []):
                if act.get("id") == action_id:
                    target_action = act
                    break
            if target_action:
                break

        if not target_action:
            return {"ok": False, "toast": "Дію не знайдено"}

        decision = self.access.check_action(user_id, target_action)
        if not decision.allowed:
            return {"ok": False, "toast": f"⛔ Відмовлено: {decision.reason}"}

        domain = target_action.get("domain")
        service = target_action.get("service")
        target = target_action.get("target")

        if self.ha_call_service and domain and service:
            try:
                await self.ha_call_service(domain, service, target)
                return {"ok": True, "toast": f"✅ Виконано: {target_action.get('label', '')}"}
            except Exception as e:
                logger.error("Failed to execute HA service: %s", e)
                return {"ok": False, "toast": "Помилка виклику сервісу"}

        return {"ok": True, "toast": "Симуляція: дію виконано"}
