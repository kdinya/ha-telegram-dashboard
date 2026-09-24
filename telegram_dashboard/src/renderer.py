"""Beautiful Telegram HTML message renderer."""
from __future__ import annotations

from datetime import datetime
import html
from typing import Any


def battery_bar(level: int, width: int = 10) -> str:
    """Render a visual progress bar like [▰▰▰▰▰▰▰▰▱▱] 80%."""
    try:
        level_int = max(0, min(100, int(float(level))))
    except (TypeError, ValueError):
        level_int = 0
    filled = round(level_int / 100 * width)
    return "[" + "▰" * filled + "▱" * (width - filled) + "]"


def battery_line(label: str, level: Any, low_threshold: int = 20) -> str:
    """One battery row: icon, label, bar and percentage."""
    try:
        level_int = int(float(level))
    except (TypeError, ValueError):
        level_int = 0
    icon = "🔋" if level_int >= low_threshold else "🪫"
    bar = battery_bar(level_int)
    escaped = html.escape(str(label))
    return f"├ {icon} {escaped}: <code>{bar} {level_int}%</code>"


def friendly_name(entity_id: str) -> str:
    """Human-friendly name derived from an entity_id."""
    return entity_id.split(".", 1)[-1].replace("_", " ").strip().capitalize()


DOMAIN_ICONS = {
    "light": "💡", "switch": "🔀", "script": "📜", "automation": "🤖",
    "scene": "🎬", "media_player": "🔊", "climate": "🌡️", "cover": "🪟",
    "binary_sensor": "🚨", "sensor": "📈", "input_boolean": "🔘",
    "fan": "🌀", "humidifier": "💧", "vacuum": "🧹", "lock": "🔒",
    "button": "🔘", "siren": "🚨", "water_heater": "🔥", "number": "🔢",
    "valve": "🚰",
}

STATE_TRANSLATIONS = {
    "on": "🟢 Увімкнено",
    "off": "🔴 Вимкнено",
    "open": "🟢 Відкрито",
    "closed": "🔴 Закрито",
    "opening": "⬆️ Відкривається",
    "closing": "⬇️ Закривається",
    "cool": "❄️ Охолодження",
    "heat": "🔥 Обігрів",
    "auto": "🔄 Авто",
    "idle": "💤 Очікування",
    "home": "🏠 Вдома",
    "not_home": "🚶 Поза домом",
    "unavailable": "⚠️ Недоступно",
    "unknown": "❓ Невідомо",
}


def format_state_value(entity_id: str, val: str, unit: str, device_class: str = "") -> str:
    """Format an entity state into user-friendly Ukrainian text."""
    domain = entity_id.split(".", 1)[0] if "." in entity_id else ""
    val_lower = val.lower().strip()

    if domain == "binary_sensor" or device_class in ("door", "window", "opening", "garage_door"):
        if device_class in ("door", "window", "opening", "garage_door"):
            if val_lower == "on":
                return "⚠️ Відкрито"
            if val_lower == "off":
                return "🟢 Закрито"
        if device_class == "moisture":
            if val_lower == "on":
                return "⚠️ ПРОТІКАННЯ"
            if val_lower == "off":
                return "🟢 Сухо"
        if val_lower in STATE_TRANSLATIONS:
            return STATE_TRANSLATIONS[val_lower]

    if val_lower in STATE_TRANSLATIONS:
        return STATE_TRANSLATIONS[val_lower]

    if unit:
        return f"{val} {unit}"
    return val


class MessageRenderer:
    """Renders menu sections into styled Telegram HTML messages."""

    def render_main(self, state: dict[str, Any]) -> str:
        """Main dashboard card with a tree of sections (legacy fallback)."""
        outside = html.escape(str(state.get("outside_temp", "—")))
        people = html.escape(str(state.get("people_home", "—")))
        climate_rows = []
        for name, values in state.get("climate", {}).items():
            temp = html.escape(str(values.get("temperature", "—")))
            humidity = html.escape(str(values.get("humidity", "—")))
            extra = ""
            if values.get("ac_on"):
                extra += " ❄️"
            if values.get("window_open"):
                extra += " <i>(вікно відкрито)</i>"
            climate_rows.append(
                f"├ <b>{html.escape(str(name))}:</b> "
                f"<code>{temp}°C</code> • <code>{humidity}%</code>{extra}"
            )
        water_rows = []
        valve = state.get("water_valve", {})
        valve_label = "🟢 <b>Відкритий</b>" if valve.get("open") else "🔴 <b>Перекритий</b>"
        water_rows.append(f"├ <b>Ввідний кран:</b> {valve_label}")
        for name, leak in state.get("leaks", {}).items():
            icon = "⚠️ <b>ПРОТІКАННЯ</b>" if leak.get("on") else "🟢 Сухо"
            water_rows.append(
                f"├ <b>{html.escape(str(name))}:</b> {icon}"
            )
        battery_rows = [
            battery_line(name, values.get("level"))
            for name, values in state.get("batteries", {}).items()
        ]
        parts = [
            "<blockquote><b>🏠 ДІМ І БЕЗПЕКА</b>",
            "──────────────",
            f"<b>🌤 На вулиці:</b> <code>{outside}°C</code>",
            f"<b>👤 Вдома:</b> {people}",
            "",
            "<b>🌡 Клімат</b>",
        ]
        parts.extend(climate_rows or ["├ <i>—</i>"])
        parts += ["", "<b>🚰 Водопостачання</b>"]
        parts.extend(water_rows or ["├ <i>—</i>"])
        parts += ["", "<b>🔋 Заряд пристроїв</b>"]
        parts.extend(battery_rows or ["├ <i>—</i>"])
        parts.append("──────────────")
        parts.append(
            f"<tg-spoiler><i>⏱ Оновлено: {html.escape(str(state.get('updated_at', '—')))}</i></tg-spoiler></blockquote>"
        )
        return "\n".join(parts)

    def render_section(self, section: dict, state: dict[str, Any]) -> str:
        """Render one menu section by its configured widgets, entities, and actions."""
        # Backward compatibility for mock state in tests
        if (
            section.get("type") in ("main", "menu")
            and not section.get("widgets")
            and not section.get("actions")
            and any(k in state for k in ("outside_temp", "climate", "water_valve", "leaks"))
        ):
            return self.render_main(state)

        icon = section.get("icon", "📁")
        title = html.escape(str(section.get("title", "")))
        rows = [f"<blockquote><b>{icon} {title}</b>", "──────────────"]

        note = section.get("note") or section.get("description")
        if note:
            rows.append(f"<i>{html.escape(str(note))}</i>")
            rows.append("")

        widgets = section.get("widgets", [])
        entities = section.get("entities", [])

        has_items = False
        if widgets:
            for widget in widgets:
                row_str = self._render_widget(widget, state)
                if row_str:
                    rows.append(row_str)
                    has_items = True

        if entities:
            for ent_id in entities:
                ent_row = self._render_entity_row(ent_id, state)
                if ent_row:
                    rows.append(ent_row)
                    has_items = True

        if not has_items:
            child_sections = section.get("sections", [])
            if child_sections:
                rows.append("<i>Оберіть підрозділ нижче:</i>")
            else:
                rows.append("├ <i>Немає доданих показників</i>")

        rows.append("──────────────")
        upd = state.get("updated_at")
        if not upd:
            upd = datetime.now().strftime("%H:%M:%S")
        rows.append(
            f"<tg-spoiler><i>⏱ Оновлено: {html.escape(str(upd))}</i></tg-spoiler></blockquote>"
        )
        return "\n".join(rows)

    def _render_entity_row(self, entity_id: str, state: dict[str, Any]) -> str:
        raw = state.get(entity_id)
        val = "—"
        unit = ""
        device_class = ""
        name = friendly_name(entity_id)

        if isinstance(raw, dict):
            val = str(raw.get("state", "—"))
            attrs = raw.get("attributes", {})
            unit = str(attrs.get("unit_of_measurement", ""))
            device_class = str(attrs.get("device_class", ""))
            name = str(attrs.get("friendly_name", name))
        elif raw is not None:
            val = str(raw)

        domain = entity_id.split(".", 1)[0] if "." in entity_id else "sensor"
        icon = DOMAIN_ICONS.get(domain, "🔘")

        if domain == "sensor" and ("battery" in entity_id or unit == "%"):
            return battery_line(name, val)

        formatted = format_state_value(entity_id, val, unit, device_class)
        return f"├ {icon} <b>{html.escape(name)}:</b> <code>{html.escape(formatted)}</code>"

    def render_entity_list(self, section: dict, states: dict[str, Any]) -> str:
        """Render an auto-generated entity browser section."""
        title = html.escape(str(section.get("title", "")))
        rows = [f"<blockquote><b>{title}</b>", "──────────────"]
        count = 0
        for entity_id, value in sorted(states.items()):
            icon = DOMAIN_ICONS.get(entity_id.split(".", 1)[0], "🔘")
            rows.append(
                f"├ {icon} <b>{html.escape(friendly_name(entity_id))}:</b> "
                f"<code>{html.escape(str(value))}</code>"
            )
            count += 1
        if count == 0:
            rows.append("├ <i>Немає доступних сутностей</i>")
        rows.append("──────────────")
        rows.append(f"<i>Всього: {count}</i></blockquote>")
        return "\n".join(rows)

    def _render_widget(self, widget: dict, state: dict[str, Any]) -> str:
        kind = widget.get("kind", "sensor")
        entity_id = widget.get("entity") or widget.get("entity_id", "")
        label = html.escape(str(widget.get("label") or widget.get("name") or friendly_name(entity_id)))
        icon = widget.get("icon") or DOMAIN_ICONS.get(entity_id.split(".", 1)[0], "🔘")

        raw = state.get(entity_id) if entity_id else None
        val = "—"
        unit = str(widget.get("unit", ""))
        device_class = ""

        if isinstance(raw, dict):
            val = str(raw.get("state", "—"))
            attrs = raw.get("attributes", {})
            if not unit:
                unit = str(attrs.get("unit_of_measurement", ""))
            device_class = str(attrs.get("device_class", ""))
        elif raw is not None:
            val = str(raw)

        if kind == "battery" or (entity_id and "battery" in entity_id):
            return battery_line(label, val)

        if kind == "switch":
            on = val.lower() in ("on", "true", "1", "open")
            state_text = widget.get("on_text", "Увімкнено") if on else widget.get("off_text", "Вимкнено")
            st_icon = "🟢" if on else "🔴"
            return f"├ {icon} <b>{label}:</b> {st_icon} {html.escape(state_text)}"

        if kind == "leak":
            on = val.lower() in ("on", "true", "1")
            st_icon = "⚠️ <b>ПРОТІКАННЯ</b>" if on else "🟢 Сухо"
            return f"├ {icon} <b>{label}:</b> {st_icon}"

        formatted = format_state_value(entity_id, val, unit, device_class)
        return f"├ {icon} <b>{label}:</b> <code>{html.escape(formatted)}</code>"
