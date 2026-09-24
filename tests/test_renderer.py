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
    assert "<blockquote>" in rendered
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
    assert "├ 💡 Автоматизація увімкнена" in rendered
    assert "<b>🛋️ Вітальня</b>" in rendered
