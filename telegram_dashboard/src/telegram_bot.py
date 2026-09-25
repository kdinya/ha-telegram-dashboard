"""Telegram Bot integration bridge connecting through Home Assistant telegram_bot actions and events."""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable, Awaitable

logger = logging.getLogger("telegram_dashboard.telegram_bot")

TD_CALLBACK_PREFIX = "td:"


def format_inline_keyboard_for_ha(
    keyboard: list[list[dict[str, str]]] | None,
) -> list[list[list[str]]] | None:
    """Format inline keyboard for Home Assistant telegram_bot actions.

    Home Assistant expects each row to contain entries formatted as:
    [[text, callback_data_or_url], [text2, callback_data_or_url]]
    When passed as dicts, HA unpacks dict keys ('text', 'callback_data'),
    causing all buttons to display the label 'text'.
    """
    if not keyboard:
        return None
    ha_keyboard: list[list[list[str]]] = []
    for row in keyboard:
        ha_row: list[list[str]] = []
        for btn in row:
            if isinstance(btn, dict):
                text = str(btn.get('text', ''))
                data = str(btn.get('callback_data') or btn.get('url', ''))
                ha_row.append([text, data])
            elif isinstance(btn, (list, tuple)) and len(btn) >= 2:
                ha_row.append([str(btn[0]), str(btn[1])])
            else:
                ha_row.append([str(btn), str(btn)])
        ha_keyboard.append(ha_row)
    return ha_keyboard


class TelegramBotRunner:
    """Bridges Telegram messages and callbacks through Home Assistant telegram_bot integration."""

    def __init__(
        self,
        ha_client: Any,
        bot_engine: Any,
        get_ha_state: Callable[[], Awaitable[dict[str, Any]]] | None = None,
    ) -> None:
        self.ha_client = ha_client
        self.bot_engine = bot_engine
        self.get_ha_state = get_ha_state
        self._running = False
        self._auto_delete_tasks: dict[tuple[int, int], asyncio.Task] = {}

    @staticmethod
    def _safe_int(value: Any) -> int | None:
        try:
            return int(value)
        except (TypeError, ValueError, OverflowError):
            return None

    async def send_message(
        self,
        chat_id: int | str,
        text: str,
        reply_markup: dict | None = None,
        parse_mode: str = "html",
        disable_notification: bool = False,
        return_response: bool = False,
    ) -> dict[str, Any] | None:
        """Send message via Home Assistant telegram_bot.send_message action."""
        if not self.ha_client:
            logger.warning("ha_client is not configured; cannot send message")
            return None

        safe_chat_id = self._safe_int(chat_id)
        if safe_chat_id is None:
            logger.warning("Ignoring send_message with invalid chat_id")
            return None
        service_data: dict[str, Any] = {
            "chat_id": [safe_chat_id],
            "message": text,
            "parse_mode": parse_mode.lower(),
            "disable_notification": disable_notification,
        }
        if reply_markup and "inline_keyboard" in reply_markup:
            service_data["inline_keyboard"] = format_inline_keyboard_for_ha(reply_markup["inline_keyboard"])

        try:
            return await self.ha_client.call_service(
                "telegram_bot", "send_message", service_data=service_data, return_response=return_response
            )
        except Exception as e:
            logger.error("Failed to send message through HA telegram_bot: %s", e)
            return None

    async def edit_message_text(
        self,
        chat_id: int | str,
        message_id: int,
        text: str,
        reply_markup: dict | None = None,
        parse_mode: str = "html",
    ) -> dict[str, Any] | None:
        """Edit message text via Home Assistant telegram_bot.edit_message action."""
        if not self.ha_client:
            logger.warning("ha_client is not configured; cannot edit message")
            return None

        safe_chat_id = self._safe_int(chat_id)
        safe_message_id = self._safe_int(message_id)
        if safe_chat_id is None or safe_message_id is None:
            logger.warning("Ignoring edit_message with invalid identifiers")
            return None
        service_data: dict[str, Any] = {
            "chat_id": safe_chat_id,
            "message_id": safe_message_id,
            "message": text,
            "parse_mode": parse_mode.lower(),
        }
        if reply_markup and "inline_keyboard" in reply_markup:
            service_data["inline_keyboard"] = format_inline_keyboard_for_ha(reply_markup["inline_keyboard"])

        try:
            return await self.ha_client.call_service("telegram_bot", "edit_message", service_data=service_data)
        except Exception as e:
            logger.error("Failed to edit message through HA telegram_bot: %s", e)
            return None

    def schedule_auto_delete(self, chat_id: int | str, message_id: int) -> None:
        """Schedule automatic message deletion after period of inactivity."""
        try:
            cid = int(chat_id)
            mid = int(message_id)
        except (ValueError, TypeError):
            return

        self.cancel_auto_delete(cid, mid)

        timeout = 180
        if hasattr(self.bot_engine, "config"):
            try:
                timeout = int(self.bot_engine.config.get("auto_delete_timeout", 180))
            except (TypeError, ValueError):
                logger.warning("Invalid auto_delete_timeout; using default of 180 seconds")
                timeout = 180

        if timeout <= 0:
            return

        async def _auto_delete_coro():
            try:
                await asyncio.sleep(timeout)
                logger.info("Auto-deleting inactive dashboard message %s in chat %s after %ds", mid, cid, timeout)
                await self.delete_message(cid, mid)
            except asyncio.CancelledError:
                pass
            finally:
                key = (cid, mid)
                if self._auto_delete_tasks.get(key) is asyncio.current_task():
                    self._auto_delete_tasks.pop(key, None)

        self._auto_delete_tasks[(cid, mid)] = asyncio.create_task(_auto_delete_coro())

    def cancel_auto_delete(self, chat_id: int | str, message_id: int) -> None:
        """Cancel auto deletion for a message."""
        try:
            cid = int(chat_id)
            mid = int(message_id)
        except (ValueError, TypeError):
            return
        task = self._auto_delete_tasks.pop((cid, mid), None)
        if task and not task.done():
            task.cancel()

    async def delete_message(self, chat_id: int | str, message_id: int) -> dict[str, Any] | None:
        """Delete message via Home Assistant telegram_bot.delete_message action."""
        if not self.ha_client:
            return None
        safe_chat_id = self._safe_int(chat_id)
        safe_message_id = self._safe_int(message_id)
        if safe_chat_id is None or safe_message_id is None:
            logger.warning("Ignoring delete_message with invalid identifiers")
            return None
        service_data = {"chat_id": safe_chat_id, "message_id": safe_message_id}
        try:
            return await self.ha_client.call_service("telegram_bot", "delete_message", service_data=service_data)
        except Exception as e:
            logger.error("Failed to delete message through HA telegram_bot: %s", e)
            return None

    async def answer_callback_query(
        self, callback_query_id: str | int, text: str | None = None, show_alert: bool = False
    ) -> dict[str, Any] | None:
        """Acknowledge callback query via Home Assistant telegram_bot.answer_callback_query action."""
        if not self.ha_client:
            return None
        safe_callback_id = self._safe_int(callback_query_id)
        if safe_callback_id is None:
            logger.warning("Ignoring answer_callback_query with invalid callback id")
            return None
        service_data: dict[str, Any] = {
            "callback_query_id": safe_callback_id,
            "message": text or "",
            "show_alert": show_alert,
        }
        try:
            return await self.ha_client.call_service(
                "telegram_bot", "answer_callback_query", service_data=service_data
            )
        except Exception as e:
            logger.error("Failed to answer callback query through HA telegram_bot: %s", e)
            return None

    async def _current_state(self) -> dict[str, Any]:
        if self.get_ha_state:
            try:
                return await self.get_ha_state() or {}
            except Exception as e:
                logger.error("Failed to fetch state for bot: %s", e)
        return {}

    def _extract_user_info(self, event_data: dict[str, Any]) -> tuple[int | None, str]:
        user_id = event_data.get("user_id") or event_data.get("from_id")
        if not user_id:
            return None, ""
        first = (event_data.get("from_first_name") or "").strip()
        last = (event_data.get("from_last_name") or "").strip()
        username = (event_data.get("username") or "").strip()
        full_name = f"{first} {last}".strip()
        if full_name and username:
            display_name = f"{full_name} (@{username})"
        elif full_name:
            display_name = full_name
        elif username:
            display_name = f"@{username}"
        else:
            display_name = f"User {user_id}"
        safe_user_id = self._safe_int(user_id)
        return safe_user_id, display_name if safe_user_id is not None else ""

    async def handle_ha_command(self, data: dict[str, Any]) -> None:
        """Handle incoming telegram_command event from Home Assistant."""
        command = str(data.get("command", "")).strip()
        chat_id = self._safe_int(data.get("chat_id"))
        user_id, display_name = self._extract_user_info(data)

        if user_id is None or chat_id is None or not command:
            return

        # Multi-menu routing: match command against configured menu commands
        sec_key = None
        if hasattr(self.bot_engine, "find_menu_by_command"):
            sec_key = self.bot_engine.find_menu_by_command(command)
        elif command.lstrip("/").lower() in ("dashboard", "menu", "start", "home"):
            sec_key = "main"

        if not sec_key:
            # Not a Telegram Dashboard command; leave untouched for user automations
            return

        if hasattr(self.bot_engine, "auto_discover_user"):
            self.bot_engine.auto_discover_user(user_id, display_name)

        state = await self._current_state()
        res = await self.bot_engine.handle_navigation(user_id, sec_key, state)
        reply_markup = {"inline_keyboard": res.get("keyboard", [])} if res.get("keyboard") else None
        response = await self.send_message(
            chat_id, res.get("text", ""), reply_markup=reply_markup, return_response=True
        )
        message_id = self._extract_sent_message_id(response, chat_id)
        if message_id is not None:
            self.schedule_auto_delete(chat_id, message_id)
        else:
            logger.warning("Home Assistant did not return a message_id; auto-delete cannot be scheduled")

    @staticmethod
    def _extract_sent_message_id(response: Any, chat_id: int | str) -> int | None:
        """Extract Telegram message_id from HA's return_response payload."""
        expected_chat_id = int(chat_id)
        pending = [response]
        while pending:
            value = pending.pop()
            if isinstance(value, dict):
                chats = value.get("chats")
                if isinstance(chats, list):
                    for chat in chats:
                        if not isinstance(chat, dict):
                            continue
                        try:
                            if int(chat.get("chat_id", expected_chat_id)) == expected_chat_id:
                                return int(chat["message_id"])
                        except (KeyError, TypeError, ValueError):
                            continue
                pending.extend(value.values())
            elif isinstance(value, list):
                pending.extend(value)
        return None

    async def handle_ha_callback(self, data: dict[str, Any]) -> None:
        """Handle incoming telegram_callback event from Home Assistant."""
        cb_data = str(data.get("data", ""))
        cb_id = data.get("id")
        chat_id = self._safe_int(data.get("chat_id"))
        msg = data.get("message") or {}
        msg_id_raw = msg.get("message_id") if isinstance(msg, dict) else data.get("message_id")
        msg_id = self._safe_int(msg_id_raw)

        # Ignore callbacks without our namespace prefix (let HA automations handle them)
        if not cb_data.startswith(TD_CALLBACK_PREFIX):
            return

        # Strip our prefix for internal routing
        action_data = cb_data[len(TD_CALLBACK_PREFIX):]

        user_id, display_name = self._extract_user_info(data)
        if user_id is None or chat_id is None or msg_id is None:
            if cb_id:
                await self.answer_callback_query(cb_id)
            return

        state = await self._current_state()
        toast = None

        # Reset inactivity timer on any interaction
        self.schedule_auto_delete(chat_id, int(msg_id))

        if action_data in ("/close", "close"):
            self.cancel_auto_delete(chat_id, int(msg_id))
            await self.delete_message(chat_id, int(msg_id))
            if cb_id:
                await self.answer_callback_query(cb_id)
            return
        elif action_data.startswith("/sec_"):
            sec_key = action_data[5:]
            res = await self.bot_engine.handle_navigation(user_id, sec_key, state)
            reply_markup = {"inline_keyboard": res.get("keyboard", [])} if res.get("keyboard") else None
            await self.edit_message_text(chat_id, int(msg_id), res.get("text", ""), reply_markup=reply_markup)
        elif action_data.startswith("/ent_"):
            sec_key, _, tail = action_data[5:].rpartition("_")
            page = int(tail) if tail.isdigit() else 0
            res = await self.bot_engine.handle_navigation(user_id, sec_key, state, page=page)
            reply_markup = {"inline_keyboard": res.get("keyboard", [])} if res.get("keyboard") else None
            await self.edit_message_text(chat_id, int(msg_id), res.get("text", ""), reply_markup=reply_markup)
        elif action_data.startswith("/btn_"):
            sec_key, _, tail = action_data[5:].rpartition("_")
            btn_id = tail if tail else "0"
            res = await self.bot_engine.handle_button_click(user_id, sec_key, btn_id, state)
            toast = res.get("toast")
            ret_sec = res.get("section_key") or sec_key
            await asyncio.sleep(0.3)
            state = await self._current_state()
            nav = await self.bot_engine.handle_navigation(user_id, ret_sec, state)
            reply_markup = {"inline_keyboard": nav.get("keyboard", [])} if nav.get("keyboard") else None
            await self.edit_message_text(chat_id, int(msg_id), nav.get("text", ""), reply_markup=reply_markup)
        elif action_data.startswith("/act_"):
            act_id = action_data[5:]
            res = await self.bot_engine.handle_action(user_id, act_id, state)
            toast = res.get("toast")
            sec_key = res.get("section_key") or "main"
            await asyncio.sleep(0.3)
            state = await self._current_state()
            nav = await self.bot_engine.handle_navigation(user_id, sec_key, state)
            reply_markup = {"inline_keyboard": nav.get("keyboard", [])} if nav.get("keyboard") else None
            await self.edit_message_text(chat_id, int(msg_id), nav.get("text", ""), reply_markup=reply_markup)
        elif action_data.startswith("/tog_"):
            sec_key, _, tail = action_data[5:].rpartition("_")
            idx = int(tail) if tail.isdigit() else 0
            res = await self.bot_engine.handle_entity_toggle(user_id, sec_key, idx)
            toast = res.get("toast")
            nav = await self.bot_engine.handle_navigation(user_id, sec_key, state)
            reply_markup = {"inline_keyboard": nav.get("keyboard", [])} if nav.get("keyboard") else None
            await self.edit_message_text(chat_id, int(msg_id), nav.get("text", ""), reply_markup=reply_markup)

        if cb_id:
            await self.answer_callback_query(cb_id, text=toast)

    def start(self) -> None:
        """Register HA event listeners and start WebSocket connection."""
        if self._running:
            return
        self._running = True
        if self.ha_client and hasattr(self.ha_client, "register_event_listener"):
            self.ha_client.register_event_listener("telegram_command", self.handle_ha_command)
            self.ha_client.register_event_listener("telegram_callback", self.handle_ha_callback)
            self.ha_client.start_websocket()
            logger.info("TelegramBotRunner registered HA event listeners for telegram_command and telegram_callback")

    async def stop(self) -> None:
        self._running = False
        tasks = list(self._auto_delete_tasks.values())
        self._auto_delete_tasks.clear()
        for task in tasks:
            if not task.done():
                task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
