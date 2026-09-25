"""Unified Telegram HTML message renderer for Home Assistant."""
from __future__ import annotations

import html
from typing import Any

escape_html = html.escape


def battery_bar(level: int, width: int = 10) -> str:
    """Render a visual progress bar like [▰▰▰▰▰▰▰▰▱▱]."""
    try:
        level = max(0, min(100, int(level)))
    except (ValueError, TypeError):
        level = 0
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
    "light": "💡", "switch": "🔌", "script": "📜", "automation": "🤖",
    "scene": "🎬", "media_player": "🔊", "climate": "🌡️", "cover": "🪟",
    "binary_sensor": "🚨", "sensor": "📈", "input_boolean": "🔘",
    "fan": "🌀", "humidifier": "💧", "vacuum": "🧹", "lock": "🔒",
    "button": "🔘", "siren": "🚨", "water_heater": "🔥", "valve": "🚰",
}


def format_entity_value(entity_id: str, raw_state: Any, custom_unit: str = "") -> tuple[str, str]:
    """Format entity state and icon for Telegram HTML display: (icon, formatted_value)."""
    if raw_state is None:
        return "❓", "Невідомо"

    state_str = ""
    attrs: dict[str, Any] = {}
    if isinstance(raw_state, dict):
        state_str = str(raw_state.get("state", ""))
        attrs = raw_state.get("attributes", {})
    else:
        state_str = str(raw_state)

    state_lower = state_str.lower().strip()
    domain = entity_id.split(".")[0] if "." in entity_id else ""
    device_class = attrs.get("device_class", "")
    unit = custom_unit or attrs.get("unit_of_measurement", "")

    # Switches, lights, boolean
    if domain in ("switch", "light", "input_boolean"):
        if state_lower in ("on", "true", "1"):
            return "💡" if domain == "light" else "🔌", "🟢 Увімкнено"
        elif state_lower in ("off", "false", "0"):
            return "💡" if domain == "light" else "🔌", "🔴 Вимкнено"

    if domain == "valve" or "valve" in entity_id or "tap" in entity_id or "water" in entity_id:
        if state_lower in ("open", "on", "opening", "true"):
            return "🚰", "🟢 Відкрито"
        elif state_lower in ("closed", "off", "closing", "false"):
            return "🚰", "🔴 Закрито"

    if domain == "binary_sensor":
        if device_class in ("moisture", "leak"):
            return "💧", "🚨 Протікання!" if state_lower in ("on", "true") else "✅ Сухо"
        if device_class in ("door", "window", "opening"):
            return "🚪", "🔴 Відчинено" if state_lower in ("on", "true") else "🟢 Зачинено"
        if device_class == "motion":
            return "🚶", "🚨 Рух виявлено" if state_lower in ("on", "true") else "Спокійно"
        if state_lower in ("on", "true"):
            return "🚨", "Активно"
        return "✅", "Норма"

    if domain == "climate":
        temp = attrs.get("current_temperature") or attrs.get("temperature") or state_str
        return "🌡️", f"{temp} °C"

    # Battery
    if "battery" in entity_id or device_class == "battery":
        try:
            val_num = int(float(state_str))
            return "🔋", f"{val_num}% <code>{battery_bar(val_num, 6)}</code>"
        except ValueError:
            pass

    # Sensor units
    if device_class == "temperature" or "temp" in entity_id or unit in ("°C", "°F"):
        return "🌡️", f"{state_str} {unit or '°C'}".strip()

    if device_class == "humidity" or "humidity" in entity_id or unit == "%":
        return "💧", f"{state_str} %".strip() if not unit else f"{state_str} {unit}".strip()

    if device_class == "power" or unit in ("W", "kW"):
        return "⚡", f"{state_str} {unit}".strip()

    if state_lower in ("unavailable", "unknown"):
        return "⚠️", "Недоступно"

    val_display = f"{state_str} {unit}".strip() if unit else state_str
    return DOMAIN_ICONS.get(domain, "🔹"), val_display or "—"


class MessageRenderer:
    """Renders menu sections into styled Telegram HTML messages."""

    def __init__(self, theme: str = "cards"):
        self.theme = theme

    def render_main(self, state: dict[str, Any]) -> str:
        """Main dashboard summary view."""
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
        climate_block = "\n".join(climate_rows) if climate_rows else "├ <i>Немає даних</i>"

        water_open = bool(state.get("water_valve", {}).get("open", False))
        water_status = "🟢 <b>Відкритий</b>" if water_open else "🔴 <b>Перекритий</b>"

        leak_alerts = []
        for loc, data in state.get("leaks", {}).items():
            if data.get("on"):
                leak_alerts.append(f"🚨 <b>ПРОТІКАННЯ: {html.escape(str(loc))}</b>")
        leaks_block = ("\n".join(leak_alerts) + "\n") if leak_alerts else ""

        bat_rows = []
        for dev, bdata in state.get("batteries", {}).items():
            bat_rows.append(battery_line(dev, bdata.get("level", 0)))
        bat_block = "\n".join(bat_rows) if bat_rows else "├ <i>Всі заряди в нормі</i>"

        parts = [
            "<b>🏠 ДІМ І БЕЗПЕКА</b>",
            f"<i>За бортом: {outside}°C • {people}</i>",
            "────────────────────────────",
            "<b>Клімат у кімнатах:</b>",
            climate_block,
            "────────────────────────────",
            "<b>Водопостачання та безпека:</b>",
            f"├ Ввідний кран: {water_status}",
        ]
        if leaks_block:
            parts.append(leaks_block.strip())
        parts.extend([
            "────────────────────────────",
            "<b>Заряди пристроїв:</b>",
            bat_block,
            "────────────────────────────",
            f"<i>⏱ Оновлено: {html.escape(str(state.get('updated_at', '—')))}</i>"
        ])
        return "\n".join(parts)

    def render_section(self, section: dict[str, Any], state: dict[str, Any]) -> str:
        """Render one section with header, note and 'Назва: Дані' entities."""
        title = html.escape(str(section.get("title") or "Розділ"))
        icon = section.get("icon") or "📁"
        note = html.escape(str(section.get("note") or section.get("description") or ""))

        rows = [f"<b>{icon} {title}</b>"]
        if note:
            rows.append(f"<i>{note}</i>")

        # Unified ordered items: texts and entities rendered in saved order
        items = section.get("items")
        if items is None:
            # Backward compatibility: synthesize from legacy texts/entities
            items = []
            for t_item in section.get("texts", []):
                if isinstance(t_item, dict):
                    items.append({"type": "text", **t_item})
            for e_item in section.get("entities", []):
                if isinstance(e_item, dict):
                    items.append({"type": "entity", **e_item})
            if not items:
                widgets = section.get("widgets", [])
                items = [
                    {
                        "type": "entity",
                        "entity_id": w.get("entity_id") or w.get("entity"),
                        "label": w.get("label"),
                        "unit": w.get("unit", ""),
                    }
                    for w in widgets
                    if (w.get("entity_id") or w.get("entity"))
                ]

        has_items = False
        for item in items:
            if not isinstance(item, dict):
                continue
            item_type = item.get("type", "text")
            explicit_icon = item.get("icon")
            has_explicit_icon = explicit_icon is not None
            item_icon = str(explicit_icon or "").strip()
            indent = item.get("show_indent", True)
            prefix = "    " if indent else ""

            if item_type == "text":
                t_text = str(item.get("text", "")).strip()
                if not t_text:
                    continue
                has_items = True
                icon_prefix = f"{item_icon} " if item_icon else ""
                if item.get("is_heading", False):
                    rows.append(f"{prefix}<b>{icon_prefix}{html.escape(t_text)}</b>")
                else:
                    rows.append(f"{prefix}{icon_prefix}{html.escape(t_text)}")
            elif item_type == "entity":
                eid = item.get("entity_id")
                if not eid:
                    continue
                has_items = True
                label = item.get("label") or friendly_name(eid)
                unit = item.get("unit") or ""
                raw_st = state.get(eid)
                if has_explicit_icon:
                    ic = item_icon or ""
                else:
                    ic, _ = format_entity_value(eid, raw_st, unit)
                _, val_formatted = format_entity_value(eid, raw_st, unit)
                icon_part = f"{ic} " if ic else ""
                rows.append(
                    f"{prefix}{icon_part}<b>{html.escape(label)}:</b> {val_formatted}"
                )
            elif item_type in ("divider", "spacer"):
                has_items = True
                style = item.get("style", "line")
                if style == "space":
                    rows.append("")
                elif style == "dashed":
                    rows.append("┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄")
                elif style == "dotted":
                    rows.append("························")
                else:
                    rows.append("────────────────────────")

        if not has_items:
            rows.append("<i>Показники не налаштовані.</i>")

        # Telegram bubble width spacer based on telegram_msg_width (20-100%)
        width_pct = int(section.get("telegram_msg_width") or state.get("telegram_msg_width") or 100)
        width_pct = max(20, min(100, width_pct))
        width_chars = int((width_pct - 20) / 80 * 42)
        if width_chars > 0:
            spacer = "⠀" * width_chars
            rows.append(f"<code>{spacer}</code>")

        updated = html.escape(str(state.get("updated_at", "—")))
        rows.append(f"<i>⏱ Оновлено: {updated}</i>")

        return "\n".join(rows)

    def render_entity_list(self, section: dict, states: dict[str, Any]) -> str:
        """Render an auto-generated entity browser section."""
        title = html.escape(str(section.get("title", "")))
        rows = [f"<b>{title}</b>", "────────────────────────────"]
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
        rows.append("────────────────────────────")
        rows.append(f"<i>Всього: {count}</i>")
        return "\n".join(rows)


TelegramRenderer = MessageRenderer
