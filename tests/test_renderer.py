from telegram_dashboard.src.renderer import MessageRenderer, battery_bar, battery_line


def test_battery_bar():
    assert battery_bar(100, 10) == "[▰▰▰▰▰▰▰▰▰▰]"
    assert battery_bar(0, 10) == "[▱▱▱▱▱▱▱▱▱▱]"
    assert battery_bar(50, 10) == "[▰▰▰▰▰▱▱▱▱▱]"


def test_render_main_html():
    renderer = MessageRenderer()
    state = {
        "outside_temp": 17.5,
        "people_home": "1 особа",
        "climate": {"Зал": {"temperature": 21.0, "humidity": 50}},
        "water_valve": {"open": True},
        "leaks": {"Кухня": {"on": False}},
        "batteries": {"Зал": {"level": 85}},
        "updated_at": "12:00:00"
    }
    rendered = renderer.render_main(state)
    assert "🏠 ДІМ І БЕЗПЕКА" in rendered
    assert "🏠 ДІМ І БЕЗПЕКА" in rendered
    assert "17.5°C" in rendered
    assert "🟢 <b>Відкритий</b>" in rendered
    assert "<code>[▰" in rendered


def test_render_section_with_texts_and_parity():
    renderer = MessageRenderer()
    section = {
        "title": "Вітальня",
        "icon": "🛋️",
        "texts": [
            {"icon": "📌", "text": "Важлива інформація", "is_heading": True},
            {"icon": "💡", "text": "Автоматизація увімкнена", "is_heading": False}
        ],
        "entities": []
    }
    rendered = renderer.render_section(section, {})
    assert "<b>📌 Важлива інформація</b>" in rendered
    assert "💡 Автоматизація увімкнена" in rendered
    assert "<b>🛋️ Вітальня</b>" in rendered


def test_render_section_with_ordered_items_entities_and_indent():
    renderer = MessageRenderer()
    section = {
        "title": "Вітальня",
        "icon": "🛋️",
        "items": [
            {"type": "text", "icon": "📌", "text": "Керування", "is_heading": True},
            {
                "type": "entity",
                "entity_id": "light.living_room",
                "label": "Основне світло",
                "icon": "💡",
                "show_indent": True,
            },
            {
                "type": "entity",
                "entity_id": "switch.boiler",
                "label": "Бойлер",
                "icon": "🔌",
                "show_indent": False,
            },
            {"type": "text", "icon": "", "text": "Примітка в кінці", "is_heading": False},
        ],
    }
    state = {
        "light.living_room": {"state": "on", "attributes": {"friendly_name": "Світло"}},
        "switch.boiler": {"state": "off", "attributes": {"friendly_name": "Бойлер"}},
        "updated_at": "12:30:00",
    }
    rendered = renderer.render_section(section, state)
    assert "<b>📌 Керування</b>" in rendered
    assert "💡 <b>Основне світло:</b> 🟢 Увімкнено" in rendered
    assert "🔌 <b>Бойлер:</b> 🔴 Вимкнено" in rendered
    assert "Примітка в кінці" in rendered


def test_addon_config_sidebar_title_and_version():
    import yaml
    with open("telegram_dashboard/config.yaml", "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    assert cfg.get("panel_title") == "Telegram Dashboard"
    assert cfg.get("version") == "1.1.0"


def test_render_section_with_dividers_and_spacers():
    renderer = MessageRenderer()
    section = {
        "title": "Вітальня",
        "icon": "🛋️",
        "items": [
            {"type": "text", "icon": "", "text": "Блок один", "is_heading": False},
            {"type": "divider", "style": "line"},
            {"type": "text", "icon": "", "text": "Блок два", "is_heading": False},
            {"type": "spacer", "style": "space"},
            {"type": "entity", "entity_id": "light.living_room", "label": "Світло", "icon": "💡"},
            {"type": "divider", "style": "dashed"},
            {"type": "text", "icon": "", "text": "Блок три", "is_heading": False},
        ],
    }
    state = {
        "light.living_room": {"state": "on", "attributes": {"friendly_name": "Світло"}},
        "updated_at": "12:00:00",
    }
    rendered = renderer.render_section(section, state)
    lines = rendered.split("\n")
    # Solid divider between block one and two
    solid = "─" * 24
    dashed = "┄" * 24
    assert solid in lines
    assert dashed in lines
    # Blank spacer line exists
    assert "" in lines
    assert "Блок один" in rendered
    assert "Блок три" in rendered
    # Full-width dividers widen the Telegram bubble (no short legacy dividers remain)
    assert not any(line == "─" * 14 for line in lines)
