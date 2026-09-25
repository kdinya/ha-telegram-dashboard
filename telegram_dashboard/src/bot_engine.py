"""Telegram Bot Engine handling commands, navigation, callbacks and access control."""
from __future__ import annotations

import logging
from typing import Any, Callable, Awaitable
from .access_controller import AccessController
from .renderer import MessageRenderer, friendly_name

logger = logging.getLogger("telegram_dashboard.bot")

ENTITIES_PAGE_SIZE = 8


class BotEngine:
    """Core logic for routing commands, rendering screens and editing messages."""

    def __init__(
        self,
        config: dict[str, Any],
        access_controller: AccessController,
        renderer: MessageRenderer,
        ha_call_service: Callable[[str, str, dict | None], Awaitable[Any]] | None = None,
        get_ha_state: Callable[[], Awaitable[dict[str, Any]]] | None = None,
        get_all_states: Callable[[], Awaitable[dict[str, str]]] | None = None,
        get_catalog: Callable[[], Awaitable[dict[str, Any]]] | None = None,
        config_manager: Any | None = None,
    ) -> None:
        self.config = config
        self.access = access_controller
        self.renderer = renderer
        self.ha_call_service = ha_call_service
        self.get_ha_state = get_ha_state
        self.get_all_states = get_all_states
        self.get_catalog = get_catalog
        self.cm = config_manager
        self.catalog: dict[str, Any] = {}

    def auto_discover_user(self, telegram_id: int, name: str) -> None:
        """Auto-register user from incoming Telegram update."""
        default_role = self.config.get("default_role", "guest")
        if self.cm and hasattr(self.cm, "auto_discover_user"):
            user = self.cm.auto_discover_user(telegram_id, name, default_role)
            self.config = self.cm.config
        else:
            users = self.config.setdefault("users", [])
            for u in users:
                if u.get("telegram_id") == telegram_id:
                    if name and not u.get("name"):
                        u["name"] = name
                    user = u
                    break
            else:
                user = {
                    "telegram_id": telegram_id,
                    "name": name or f"User {telegram_id}",
                    "role": default_role,
                }
                users.append(user)

        if hasattr(self.access, "users"):
            self.access.users[telegram_id] = user

    def set_catalog(self, catalog: dict[str, Any]) -> None:
        self.catalog = catalog or {}

    def _entity_maps(self) -> tuple[dict[str, str], dict[str, str]]:
        """Invert the catalog into entity -> area and entity -> domain maps."""
        area_of: dict[str, str] = {}
        for area, entities in (self.catalog.get("areas") or {}).items():
            for ent in entities or []:
                area_of[ent] = area
        domain_of: dict[str, str] = {}
        for domain, entities in (self.catalog.get("domains") or {}).items():
            for ent in entities or []:
                domain_of[ent] = domain
        return area_of, domain_of

    def _source_entities(self, section: dict) -> list[str]:
        """Resolve the entity list of an 'entities' section."""
        explicit = section.get("entities") or section.get("items")
        if explicit and isinstance(explicit, list):
            res = []
            for e in explicit:
                if isinstance(e, dict):
                    res.append(str(e.get("entity_id", "")))
                elif e:
                    res.append(str(e))
            return [x for x in res if x]
        source = section.get("source") or {}
        mode = source.get("mode", "all")
        value = source.get("value", "")
        domains = self.catalog.get("domains") or {}
        areas = self.catalog.get("areas") or {}
        labels = self.catalog.get("labels") or {}
        if mode == "domain":
            return list(domains.get(value, []))
        if mode == "area":
            return list(areas.get(value, []))
        if mode == "label":
            return list(labels.get(value, []))
        seen: set[str] = set()
        for ents in list(domains.values()) + list(areas.values()) + list(labels.values()):
            seen.update(ents or [])
        return sorted(seen)

    def _visible_entities(self, section: dict, user_id: int) -> list[str]:
        """Catalog entities of a section filtered by per-user RBAC."""
        area_of, domain_of = self._entity_maps()
        visible: list[str] = []
        for ent in self._source_entities(section):
            decision = self.access.check_entity(
                user_id, ent, area=area_of.get(ent), domain=domain_of.get(ent)
            )
            if decision.allowed:
                visible.append(ent)
        return visible

    def _get_first_section_key(self) -> str:
        menu = self.config.get("menu", {})
        if not menu:
            return "main"
        if "main" in menu:
            return "main"
        return next(iter(menu.keys()))


    def find_menu_by_command(self, cmd: str) -> str | None:
        """Find menu section key by Telegram command (e.g. /dashboard or /menu)."""
        if not cmd:
            return None
        clean_cmd = cmd.strip().lower().lstrip("/")
        menu = self.config.get("menu", {})
        for sec_key, sec in menu.items():
            sec_cmd = str(sec.get("command", "")).strip().lower().lstrip("/")
            if sec_cmd and sec_cmd == clean_cmd:
                return sec_key
        # Default fallbacks for the primary menu
        if clean_cmd in ("dashboard", "menu", "start", "home"):
            return self._get_first_section_key()
        return None

    def build_keyboard(
        self, section_key: str, user_id: int, page: int = 0, state: dict[str, Any] | None = None
    ) -> list[list[dict[str, str]]]:
        """Generate inline keyboard for a section respecting user role."""
        menu = self.config.get("menu", {})
        section = menu.get(section_key, {})
        keyboard: list[list[dict[str, str]]] = []
        first_key = self._get_first_section_key()
        state = state or {}

        # 1. Navigation buttons for sub-sections
        sub_keys = section.get("sections")
        if sub_keys is None:
            sub_keys = section.get("menu_sections")
            if sub_keys is None and (section_key == first_key or section.get("type") in ("main", "menu")):
                sub_keys = [k for k in menu.keys() if k != first_key]

        if sub_keys:
            row: list[dict[str, str]] = []
            for sub_key in sub_keys:
                if sub_key == section_key:
                    continue
                sub_section = menu.get(sub_key, {})
                decision = self.access.check_section(user_id, sub_key, sub_section)
                if decision.allowed:
                    icon = sub_section.get("icon", "📁")
                    title = sub_section.get("title", sub_key)
                    row.append({"text": f"{icon} {title}".strip(), "callback_data": f"td:/sec_{sub_key}"})
                    if len(row) == 2:
                        keyboard.append(row)
                        row = []
            if row:
                keyboard.append(row)

        # 2. Entity browser buttons if type == 'entities'
        if section.get("type") == "entities":
            visible = self._visible_entities(section, user_id)
            total_pages = max(1, (len(visible) + ENTITIES_PAGE_SIZE - 1) // ENTITIES_PAGE_SIZE)
            page = max(0, min(page, total_pages - 1))
            chunk = visible[page * ENTITIES_PAGE_SIZE:(page + 1) * ENTITIES_PAGE_SIZE]
            for idx, ent in enumerate(chunk):
                global_idx = page * ENTITIES_PAGE_SIZE + idx
                keyboard.append([{
                    "text": f"🔘 {friendly_name(ent)}",
                    "callback_data": f"td:/tog_{section_key}_{global_idx}",
                }])
            nav_row: list[dict[str, str]] = []
            if page > 0:
                nav_row.append({"text": "⬅️", "callback_data": f"td:/ent_{section_key}_{page - 1}"})
            nav_row.append({"text": f"{page + 1}/{total_pages}", "callback_data": f"td:/ent_{section_key}_{page}"})
            if page < total_pages - 1:
                nav_row.append({"text": "➡️", "callback_data": f"td:/ent_{section_key}_{page + 1}"})
            keyboard.append(nav_row)

        # 3. Action / Control buttons
        buttons = section.get("buttons")
        if buttons is not None:
            for idx, btn in enumerate(buttons):
                target_entity = btn.get("entity_id")
                raw_label = btn.get("label", "Кнопка")
                if target_entity:
                    area_of, domain_of = self._entity_maps()
                    decision = self.access.check_entity(
                        user_id, target_entity, area=area_of.get(target_entity), domain=domain_of.get(target_entity)
                    )
                    if not decision.allowed:
                        continue
                btn_text = raw_label
                if target_entity and target_entity in state:
                    ent_raw = state[target_entity]
                    ent_st = (ent_raw.get("state") if isinstance(ent_raw, dict) else str(ent_raw)) or ""
                    ent_st_lower = ent_st.lower()
                    if ent_st_lower in ("on", "open", "true"):
                        btn_text = f"🟢 {raw_label}"
                    elif ent_st_lower in ("off", "closed", "false"):
                        btn_text = f"🔴 {raw_label}"
                keyboard.append([{"text": btn_text, "callback_data": f"td:/btn_{section_key}_{idx}"}])
        else:
            actions = section.get("actions", [])
            allowed_actions = self.access.filter_actions(user_id, actions)
            for idx, act in enumerate(allowed_actions):
                act_id = act.get("id") or f"act_{idx}"
                raw_label = act.get("label", "Дія")
                keyboard.append([{"text": raw_label, "callback_data": f"td:/act_{act_id}"}])

        # 4. Standard footer buttons
        from datetime import datetime
        now_time = state.get("updated_at")
        if not now_time or now_time == "—":
            now_time = datetime.now().strftime("%H:%M:%S")
            state["updated_at"] = now_time

        if section_key == first_key:
            keyboard.append([{"text": "🔄 Оновити", "callback_data": f"td:/sec_{section_key}"}])
        else:
            keyboard.append([
                {"text": "🔄 Оновити", "callback_data": f"td:/sec_{section_key}"},
                {"text": "⬅️ Головна", "callback_data": f"td:/sec_{first_key}"},
            ])

        return keyboard

    async def handle_navigation(
        self, user_id: int, section_key: str, state: dict[str, Any], page: int = 0
    ) -> dict[str, Any]:
        """Process section navigation, returning the message body and keyboard."""
        menu = self.config.get("menu", {})
        section = menu.get(section_key)
        first_key = self._get_first_section_key()

        if not section:
            return {
                "text": "❌ Розділ не знайдено.",
                "keyboard": [[{"text": "⬅️ Назад", "callback_data": f"td:/sec_{first_key}"}]],
            }

        decision = self.access.check_section(user_id, section_key, section)
        if not decision.allowed:
            return {
                "text": f"⛔ <b>Доступ обмежено</b>\n\n{decision.reason}",
                "keyboard": [[{"text": "⬅️ Головна", "callback_data": f"td:/sec_{first_key}"}]],
                "parse_mode": "HTML",
            }

        if section.get("type") == "entities":
            all_states: dict[str, str] = {}
            if self.get_all_states:
                try:
                    all_states = await self.get_all_states() or {}
                except Exception as e:
                    logger.error("Failed to fetch entity states: %s", e)
            text = self.renderer.render_entity_list(section, all_states)
            keyboard = self.build_keyboard(section_key, user_id, page=page, state=state)
            return {"text": text, "keyboard": keyboard, "parse_mode": "HTML"}

        from datetime import datetime
        if not state.get("updated_at") or state.get("updated_at") == "—":
            state["updated_at"] = datetime.now().strftime("%H:%M:%S")
        state["telegram_msg_width"] = self.config.get("telegram_msg_width", 100)

        text = self.renderer.render_section(section, state)
        keyboard = self.build_keyboard(section_key, user_id, page=page, state=state)
        return {"text": text, "keyboard": keyboard, "parse_mode": "HTML"}

    def _find_action(self, action_id: str) -> tuple[dict | None, str | None]:
        for sec_key, sec in self.config.get("menu", {}).items():
            for idx, act in enumerate(sec.get("actions", [])):
                if str(act.get("id")) == str(action_id) or f"act_{idx}" == str(action_id) or str(idx) == str(action_id):
                    return act, sec_key
            for idx, btn in enumerate(sec.get("buttons", [])):
                if str(btn.get("id")) == str(action_id) or f"btn_{idx}" == str(action_id) or str(idx) == str(action_id):
                    return btn, sec_key
        return None, None

    async def _run_service(self, domain: str, service: str, payload: dict | None) -> None:
        if self.ha_call_service:
            await self.ha_call_service(domain, service, payload)

    async def handle_button_click(
        self, user_id: int, section_key: str, btn_index_or_id: str, state: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute action for a section button and return result."""
        menu = self.config.get("menu", {})
        section = menu.get(section_key, {})
        if not section:
            return {"ok": False, "toast": "Розділ не знайдено", "section_key": section_key}
        roles = section.get("roles")
        if roles:
            sec_decision = self.access.check_section(user_id, section_key, section)
            if not sec_decision.allowed:
                msg = f"⛔ Немає доступу до розділу: {sec_decision.reason}"
                return {"ok": False, "toast": msg, "section_key": section_key}
        buttons = section.get("buttons", [])

        target_btn = None
        try:
            idx = int(btn_index_or_id)
            if 0 <= idx < len(buttons):
                target_btn = buttons[idx]
        except ValueError:
            pass

        if not target_btn:
            for b in buttons:
                if str(b.get("id")) == str(btn_index_or_id):
                    target_btn = b
                    break

        if not target_btn:
            # Fallback to actions
            return await self.handle_action(user_id, btn_index_or_id, state)

        target_entity = target_btn.get("entity_id")
        if not target_entity:
            return {"ok": False, "toast": "Сутність не вказана", "section_key": section_key}

        area_of, domain_of = self._entity_maps()
        decision = self.access.check_entity(
            user_id, target_entity, area=area_of.get(target_entity), domain=domain_of.get(target_entity)
        )
        if not decision.allowed:
            return {"ok": False, "toast": f"⛔ Відмовлено: {decision.reason}", "section_key": section_key}

        domain = target_entity.split(".")[0] if "." in target_entity else "homeassistant"
        service = target_btn.get("service") or target_btn.get("action")
        if not service:
            if domain in ("switch", "light", "input_boolean"):
                service = "toggle"
            elif domain == "valve":
                cur_st = str(state.get(target_entity, {}).get("state", "")).lower()
                service = "close_valve" if cur_st in ("open", "opening") else "open_valve"
            elif domain == "script":
                service = "turn_on"
            elif domain == "automation":
                service = "trigger"
            elif domain == "button":
                service = "press"
            else:
                service = "toggle"

        payload = {"entity_id": [target_entity]}
        try:
            await self._run_service(domain, service, payload)
            label = target_btn.get("label") or friendly_name(target_entity)
            return {"ok": True, "toast": f"✅ {label}: виконано", "section_key": section_key}
        except Exception as e:
            logger.error("Service call failed: %s", e)
            return {"ok": False, "toast": f"Помилка: {e}", "section_key": section_key}

    async def handle_action(self, user_id: int, action_id: str, state: dict[str, Any]) -> dict[str, Any]:
        """Execute a Home Assistant action requested by an inline button."""
        target_action, sec_key = self._find_action(action_id)

        if not target_action:
            return {"ok": False, "toast": "Дію не знайдено", "section_key": "main"}

        decision = self.access.check_action(user_id, target_action)
        if not decision.allowed:
            return {"ok": False, "toast": f"⛔ Відмовлено: {decision.reason}", "section_key": sec_key}

        atype = target_action.get("type", "service")
        area_of, domain_of = self._entity_maps()

        if atype == "speak":
            speaker = str(target_action.get("entity_id", ""))
            speaker_decision = self.access.check_entity(
                user_id, speaker, area=area_of.get(speaker), domain=domain_of.get(speaker)
            )
            if not speaker_decision.allowed:
                return {"ok": False, "toast": f"⛔ Відмовлено: {speaker_decision.reason}", "section_key": sec_key}
            tts_service = str(target_action.get("tts_service", "tts.google_translate_say"))
            domain, _, service = tts_service.partition(".")
            payload = {
                "entity_id": [speaker],
                "message": str(target_action.get("message", "")),
            }
            try:
                await self._run_service(domain, service, payload)
                return {"ok": True, "toast": "🔊 Озвучено", "section_key": sec_key}
            except Exception as e:
                logger.error("TTS failed: %s", e)
                return {"ok": False, "toast": "Помилка озвучки", "section_key": sec_key}

        domain = target_action.get("domain")
        service = target_action.get("service", "toggle")
        target_entity = target_action.get("entity_id") or (target_action.get("target") or {}).get("entity_id")
        if not domain and "." in str(service):
            domain, _, service = str(service).partition(".")
        if not domain and target_entity and "." in str(target_entity):
            domain = str(target_entity).split(".", 1)[0]
        if not domain:
            domain = "homeassistant"
        if target_entity:
            entity_decision = self.access.check_entity(
                user_id, target_entity, area=area_of.get(target_entity), domain=domain_of.get(target_entity)
            )
            if not entity_decision.allowed:
                return {"ok": False, "toast": f"⛔ Відмовлено: {entity_decision.reason}", "section_key": sec_key}
            payload = {"entity_id": [target_entity]}
        else:
            payload = target_action.get("data")

        try:
            await self._run_service(domain, service, payload)
            label = target_action.get("label", "Дія")
            return {"ok": True, "toast": f"✅ {label}: виконано", "section_key": sec_key}
        except Exception as e:
            logger.error("Action %s failed: %s", action_id, e)
            return {"ok": False, "toast": "Помилка виклику HA", "section_key": sec_key}

    async def handle_entity_toggle(self, user_id: int, section_key: str, entity_index: int) -> dict[str, Any]:
        """Toggle an entity clicked from the entity browser."""
        menu = self.config.get("menu", {})
        section = menu.get(section_key, {})
        visible = self._visible_entities(section, user_id)
        if entity_index < 0 or entity_index >= len(visible):
            return {"ok": False, "toast": "Сутність не знайдено"}

        entity_id = visible[entity_index]
        area_of, domain_of = self._entity_maps()
        decision = self.access.check_entity(
            user_id, entity_id, area=area_of.get(entity_id), domain=domain_of.get(entity_id)
        )
        if not decision.allowed:
            return {"ok": False, "toast": f"⛔ Відмовлено: {decision.reason}"}

        domain = entity_id.split(".", 1)[0]
        service = "toggle"
        if domain in ("media_player", "vacuum"):
            service = "toggle"
        elif domain == "cover":
            service = "toggle"
        elif domain not in ("light", "switch", "input_boolean"):
            return {"ok": False, "toast": "Сутність не підтримує перемикання"}

        try:
            await self._run_service(domain, service, {"entity_id": [entity_id]})
            return {"ok": True, "toast": f"🔄 {friendly_name(entity_id)} змінено"}
        except Exception as e:
            logger.error("Toggle %s failed: %s", entity_id, e)
            return {"ok": False, "toast": "Помилка перемикання"}
