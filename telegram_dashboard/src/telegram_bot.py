"""Lightweight async Telegram Bot polling service using aiohttp."""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable, Awaitable
import aiohttp

logger = logging.getLogger("telegram_dashboard.bot_polling")


class TelegramBotRunner:
    def __init__(
        self, token: str, bot_engine: Any, get_ha_state: Callable[[], Awaitable[dict[str, Any]]] | None = None
    ) -> None:
        self.token = token
        self.bot_engine = bot_engine
        self.get_ha_state = get_ha_state
        self.base_url = f"https://api.telegram.org/bot{token}"
        self._session: aiohttp.ClientSession | None = None
        self._running = False
        self._task: asyncio.Task | None = None

    async def _post(self, method: str, data: dict[str, Any]) -> dict[str, Any] | None:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        url = f"{self.base_url}/{method}"
        try:
            async with self._session.post(url, json=data, timeout=30) as resp:
                if resp.status == 200:
                    return await resp.json()
                text = await resp.text()
                logger.warning("Telegram %s returned %s: %s", method, resp.status, text[:150])
        except Exception as e:
            logger.error("Telegram %s request error: %s", method, e)
        return None

    async def send_message(
        self, chat_id: int | str, text: str, reply_markup: dict | None = None,
        parse_mode: str = "HTML", disable_notification: bool = False
    ) -> dict[str, Any] | None:
        payload: dict[str, Any] = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_notification": disable_notification,
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup
        return await self._post("sendMessage", payload)

    async def edit_message_text(
        self, chat_id: int | str, message_id: int, text: str,
        reply_markup: dict | None = None, parse_mode: str = "HTML"
    ) -> dict[str, Any] | None:
        payload: dict[str, Any] = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "parse_mode": parse_mode,
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup
        return await self._post("editMessageText", payload)

    async def delete_message(self, chat_id: int | str, message_id: int) -> dict[str, Any] | None:
        return await self._post("deleteMessage", {"chat_id": chat_id, "message_id": message_id})

    async def answer_callback_query(
        self, callback_query_id: str, text: str | None = None, show_alert: bool = False
    ) -> dict[str, Any] | None:
        payload: dict[str, Any] = {"callback_query_id": callback_query_id, "show_alert": show_alert}
        if text:
            payload["text"] = text
        return await self._post("answerCallbackQuery", payload)

    async def send_photo(
        self, chat_id: int | str, photo: str, caption: str | None = None,
        reply_markup: dict | None = None, parse_mode: str = "HTML"
    ) -> dict[str, Any] | None:
        payload: dict[str, Any] = {
            "chat_id": chat_id,
            "photo": photo,
            "parse_mode": parse_mode,
        }
        if caption:
            payload["caption"] = caption
        if reply_markup:
            payload["reply_markup"] = reply_markup
        return await self._post("sendPhoto", payload)

    async def send_document(
        self, chat_id: int | str, document: str, caption: str | None = None,
        reply_markup: dict | None = None, parse_mode: str = "HTML"
    ) -> dict[str, Any] | None:
        payload: dict[str, Any] = {
            "chat_id": chat_id,
            "document": document,
            "parse_mode": parse_mode,
        }
        if caption:
            payload["caption"] = caption
        if reply_markup:
            payload["reply_markup"] = reply_markup
        return await self._post("sendDocument", payload)

    async def _current_state(self) -> dict[str, Any]:
        if self.get_ha_state:
            try:
                return await self.get_ha_state() or {}
            except Exception as e:
                logger.error("Failed to fetch state for bot: %s", e)
        return {}

    def _extract_user_info(self, from_user: dict[str, Any]) -> tuple[int | None, str]:
        user_id = from_user.get("id")
        if not user_id:
            return None, ""
        first = (from_user.get("first_name") or "").strip()
        last = (from_user.get("last_name") or "").strip()
        username = (from_user.get("username") or "").strip()
        full_name = f"{first} {last}".strip()
        if full_name and username:
            display_name = f"{full_name} (@{username})"
        elif full_name:
            display_name = full_name
        elif username:
            display_name = f"@{username}"
        else:
            display_name = f"User {user_id}"
        return int(user_id), display_name

    async def _process_update(self, update: dict[str, Any]) -> None:
        state = await self._current_state()

        if "message" in update:
            msg = update["message"]
            from_user = msg.get("from") or {}
            user_id, display_name = self._extract_user_info(from_user)
            chat_id = msg.get("chat", {}).get("id")
            text = (msg.get("text") or "").strip()

            if not user_id or not chat_id:
                return

            if hasattr(self.bot_engine, "auto_discover_user"):
                self.bot_engine.auto_discover_user(user_id, display_name)

            if text in ("/start", "/menu", "/home"):
                res = await self.bot_engine.handle_navigation(user_id, "main", state)
                reply_markup = {"inline_keyboard": res.get("keyboard", [])} if res.get("keyboard") else None
                await self.send_message(chat_id, res.get("text", ""), reply_markup=reply_markup)
            elif text.startswith("/"):
                sec_key = text[1:].split()[0]
                res = await self.bot_engine.handle_navigation(user_id, sec_key, state)
                reply_markup = {"inline_keyboard": res.get("keyboard", [])} if res.get("keyboard") else None
                await self.send_message(chat_id, res.get("text", ""), reply_markup=reply_markup)

        elif "callback_query" in update:
            cb = update["callback_query"]
            cb_id = cb.get("id")
            from_user = cb.get("from") or {}
            user_id, display_name = self._extract_user_info(from_user)
            data = cb.get("data", "")
            msg = cb.get("message")
            chat_id = msg.get("chat", {}).get("id") if msg else None
            msg_id = msg.get("message_id") if msg else None

            if not user_id or not chat_id or not msg_id:
                if cb_id:
                    await self.answer_callback_query(cb_id)
                return

            if hasattr(self.bot_engine, "auto_discover_user"):
                self.bot_engine.auto_discover_user(user_id, display_name)

            toast = None
            if data.startswith("/sec_"):
                sec_key = data[5:]
                res = await self.bot_engine.handle_navigation(user_id, sec_key, state)
                reply_markup = {"inline_keyboard": res.get("keyboard", [])} if res.get("keyboard") else None
                await self.edit_message_text(chat_id, msg_id, res.get("text", ""), reply_markup=reply_markup)
            elif data.startswith("/ent_"):
                sec_key, _, tail = data[5:].rpartition("_")
                page = int(tail) if tail.isdigit() else 0
                res = await self.bot_engine.handle_navigation(user_id, sec_key, state, page=page)
                reply_markup = {"inline_keyboard": res.get("keyboard", [])} if res.get("keyboard") else None
                await self.edit_message_text(chat_id, msg_id, res.get("text", ""), reply_markup=reply_markup)
            elif data.startswith("/btn_"):
                sec_key, _, tail = data[5:].rpartition("_")
                btn_id = tail if tail else "0"
                res = await self.bot_engine.handle_button_click(user_id, sec_key, btn_id, state)
                toast = res.get("toast")
                ret_sec = res.get("section_key") or sec_key
                await asyncio.sleep(0.3)
                state = await self._current_state()
                nav = await self.bot_engine.handle_navigation(user_id, ret_sec, state)
                reply_markup = {"inline_keyboard": nav.get("keyboard", [])} if nav.get("keyboard") else None
                await self.edit_message_text(chat_id, msg_id, nav.get("text", ""), reply_markup=reply_markup)
            elif data.startswith("/act_"):
                act_id = data[5:]
                res = await self.bot_engine.handle_action(user_id, act_id, state)
                toast = res.get("toast")
                sec_key = res.get("section_key") or "main"
                await asyncio.sleep(0.3)
                state = await self._current_state()
                nav = await self.bot_engine.handle_navigation(user_id, sec_key, state)
                reply_markup = {"inline_keyboard": nav.get("keyboard", [])} if nav.get("keyboard") else None
                await self.edit_message_text(chat_id, msg_id, nav.get("text", ""), reply_markup=reply_markup)
            elif data.startswith("/tog_"):
                sec_key, _, tail = data[5:].rpartition("_")
                idx = int(tail) if tail.isdigit() else 0
                res = await self.bot_engine.handle_entity_toggle(user_id, sec_key, idx)
                toast = res.get("toast")
                nav = await self.bot_engine.handle_navigation(user_id, sec_key, state)
                reply_markup = {"inline_keyboard": nav.get("keyboard", [])} if nav.get("keyboard") else None
                await self.edit_message_text(chat_id, msg_id, nav.get("text", ""), reply_markup=reply_markup)

            if cb_id:
                await self.answer_callback_query(cb_id, text=toast)

    async def _polling_loop(self) -> None:
        logger.info("Starting Telegram Bot polling loop...")
        offset = 0
        while self._running:
            try:
                res = await self._post("getUpdates", {"offset": offset, "timeout": 20})
                if res and res.get("ok"):
                    for item in res.get("result", []):
                        offset = item["update_id"] + 1
                        asyncio.create_task(self._process_update(item))
                else:
                    await asyncio.sleep(2)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in bot polling loop: %s", e)
                await asyncio.sleep(5)

    def start(self) -> None:
        if self._running or not self.token:
            return
        self._running = True
        self._task = asyncio.create_task(self._polling_loop())

    async def stop(self) -> None:
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        if self._session and not self._session.closed:
            await self._session.close()
