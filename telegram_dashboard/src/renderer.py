"""Beautiful Telegram HTML message renderer."""
from __future__ import annotations

import html
from typing import Any


def battery_bar(level: int, width: int = 10) -> str:
    """Render a visual progress bar like [▰▰▰▰▰▰▰▰▱▱] 80%."""
    level = max(0, min(100, int(level)))
    filled = round(level / 100 * width)
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
    "scene": "🎬", "media_player": "🔊", "climate": "🌡", "cover": "🪟",
    "binary_sensor": "🚨", "sensor": "📈", "input_boolean": "🔘",
    "fan": "🌀", "humidifier": "💧", "vacuum": "🧹", "lock": "🔒",
    "button": "🔘", "siren": "🚨", "water_heater": "🔥", "number": "🔢",
}


class MessageRenderer:
    """Renders menu sections into styled Telegram HTML messages."""

    def render_main(self, state: dict[str, Any]) -> str:
        """Main dashboard card with a tree of sections."""
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
        """Render one menu section by its type."""
        if section.get("type") == "menu" or section.get("sections"):
            return self.render_main(state)
        title = html.escape(str(section.get("title", "")))
        rows = [f"<blockquote><b>{title}</b>", "──────────────"]
        for widget in section.get("widgets", []):
            rows.append(self._render_widget(widget, state))
        rows.append("──────────────")
        rows.append(
            f"<tg-spoiler><i>⏱ Оновлено: {html.escape(str(state.get('updated_at', '—')))}</i></tg-spoiler></blockquote>"
        )
        return "\n".join(rows)

    def render_entity_list(self, section: dict, states: dict[str, Any]) -> str:
        """Render an auto-generated entity browser section."""
        title = html.escape(str(section.get("title", "")))
        rows = [f"<blockquote><b>{title}</b>", "──────────────"]
        source = section.get("source") or {}
        engine_view = source.get("mode", "all")
        _ = engine_view  # entities come pre-filtered via states keys
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
        kind = widget.get("kind")
        label = html.escape(str(widget.get("label", "—")))
        if kind == "sensor":
            value = html.escape(str(state.get(widget.get("entity"), "—")))
            unit = html.escape(str(widget.get("unit", "")))
            return f"├ <b>{label}:</b> <code>{value}{unit}</code>"
        if kind == "switch":
            on = bool(state.get(widget.get("entity")))
            icon = "🟢" if on else "🔴"
            text = (
                html.escape(str(widget.get("on_text", "Увімк.")))
                if on else html.escape(str(widget.get("off_text", "Вимк.")))
            )
            return f"├ <b>{label}:</b> {icon} {text}"
        if kind == "battery":
            return battery_line(label, state.get(widget.get("entity")))
        if kind == "leak":
            on = bool(state.get(widget.get("entity")))
            icon = "⚠️ <b>ПРОТІКАННЯ</b>" if on else "🟢 Сухо"
            return f"├ <b>{label}:</b> {icon}"
        return f"├ <b>{label}:</b> —"
