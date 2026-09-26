"""Regression checks for settings and the mobile Telegram preview UI."""
import re
from pathlib import Path


UI_DIR = Path(__file__).resolve().parent.parent / "telegram_dashboard" / "src" / "ui"


def test_settings_omits_redundant_telegram_integration_notice():
    html = (UI_DIR / "index.html").read_text(encoding="utf-8")
    translations = (UI_DIR / "i18n.js").read_text(encoding="utf-8")
    styles = (UI_DIR / "style.css").read_text(encoding="utf-8")

    assert "panel-notice-box" not in html
    assert "settings_ha_tg_integration_title" not in translations
    assert "settings_ha_tg_integration_desc" not in translations
    assert ".panel-notice-box" not in styles


def test_preview_uses_dynamic_telegram_bot_name():
    html = (UI_DIR / "index.html").read_text(encoding="utf-8")
    app = (UI_DIR / "app.js").read_text(encoding="utf-8")

    assert 'id="preview-bot-name"' in html
    assert "Smart Home Bot" not in html
    assert "api/bot/info" in app
    assert "loadTelegramBotName" in app


def test_preview_chat_starts_at_header_and_item_controls_stack_above_content():
    styles = (UI_DIR / "style.css").read_text(encoding="utf-8")
    assert ".tg-messages-area > :first-child" not in styles

    actions_rule = re.search(r"\.section-text-item-actions\s*\{([^}]*)\}", styles)
    assert actions_rule is not None
    assert "position: relative" in actions_rule.group(1)
    assert "z-index: 5" in actions_rule.group(1)


def test_section_editor_declares_command_input_and_rebinds_navigation_lock():
    html = (UI_DIR / "index.html").read_text(encoding="utf-8")
    app = (UI_DIR / "app.js").read_text(encoding="utf-8")

    assert 'id="edit-sec-command"' in html
    assert "const editSecCommand = $('edit-sec-command')" in app
    assert "btnBlockLock.onclick =" in app
    assert "btnBlockLock.dataset.bound" not in app


def test_entity_picker_search_normalizes_ids_and_matches_state_metadata():
    app = (UI_DIR / "app.js").read_text(encoding="utf-8")

    assert ".normalize('NFKC')" in app
    assert "e.area_name" in app
    assert "e.attributes?.device_class" in app
    assert "e.state" in app


def test_preview_anchors_chat_to_bottom_and_colors_standard_buttons():
    styles = (UI_DIR / "style.css").read_text(encoding="utf-8")
    app = (UI_DIR / "app.js").read_text(encoding="utf-8")

    assert "justify-content: flex-end" in styles
    assert "restoreScrollPosition();" in app
    assert ".tg-button.is-back" in styles
    assert ".tg-button.is-close" in styles
    assert "button.classList.add('is-back')" in app
    assert "button.classList.add('is-close')" in app
    assert "tg-standard-icon" in app
    assert "tg-back-icon" in styles
    assert "tg-close-icon" in styles
    assert "id=\"preview-timestamp\"" in (UI_DIR / "index.html").read_text(encoding="utf-8")
    assert "timestampNode?.remove()" in app
    assert "previewTimestampEl.textContent" in app
    assert "background-color: var(--tg-btn);" in styles


def test_navigation_list_grows_instead_of_clipping_sections():
    styles = (UI_DIR / "style.css").read_text(encoding="utf-8")
    assert "max-height: none" in styles
    assert "overflow: visible" in styles


def test_mobile_preview_hides_editor_that_would_push_phone_down():
    styles = (UI_DIR / "style.css").read_text(encoding="utf-8")
    assert ".split-view:has(.preview-pane.mobile-active) .editor-pane" in styles
    assert "display: none !important" in styles


def test_preview_refresh_preserves_scroll_position_unless_already_at_bottom():
    app = (UI_DIR / "app.js").read_text(encoding="utf-8")
    styles = (UI_DIR / "style.css").read_text(encoding="utf-8")
    assert "const previousScrollTop = msgArea?.scrollTop || 0" in app
    assert "const wasAtBottom = msgArea" in app
    assert "msgArea.scrollTop = wasAtBottom ? msgArea.scrollHeight : previousScrollTop" in app
    assert "is-overflowing" in app
    assert "height: calc(100dvh - 110px) !important" in styles
    assert "min-height: min(680px, calc(100dvh - 110px)) !important" in styles


def test_mobile_preview_drag_scrolls_page_from_phone_frame():
    app = (UI_DIR / "app.js").read_text(encoding="utf-8")
    styles = (UI_DIR / "style.css").read_text(encoding="utf-8")
    assert "const previewPage = document.querySelector('.preview-pane')" in app
    assert "window.scrollTo(0, Math.max(0, pageStartScrollY - delta))" in app
    assert "{ passive: false }" in app
    assert "touch-action: none" in styles
    assert ".preview-pane.is-page-dragging" in styles


def test_section_items_support_touch_reorder_and_localized_drag_labels():
    app = (UI_DIR / "app.js").read_text(encoding="utf-8")
    styles = (UI_DIR / "style.css").read_text(encoding="utf-8")
    i18n = (UI_DIR / "i18n.js").read_text(encoding="utf-8")
    assert "const reorderSectionItems = (fromIdx, toIdx)" in app
    assert "e.target.closest('.item-drag-handle')" in app
    assert "addEventListener('pointermove'" in app
    assert "pointercancel', stopPointerReorder" in app
    assert "addEventListener('touchstart'" in app
    assert "addEventListener('touchmove'" in app
    assert "addEventListener('touchend', stopTouchReorder" in app
    assert "touch-action: none" in styles
    for key in ("btn_edit_item_title", "drag_handle_title", "drag_handle_aria", "toast_order_updated"):
        assert i18n.count(f"{key}:") == 2
        assert f"t('{key}')" in app


def test_section_command_and_save_flow_are_explained_and_translated():
    html = (UI_DIR / "index.html").read_text(encoding="utf-8")
    i18n = (UI_DIR / "i18n.js").read_text(encoding="utf-8")
    assert 'data-i18n="label_section_command"' in html
    assert 'data-i18n="section_command_hint"' in html
    assert 'data-i18n="save_flow_hint"' in html
    assert 'label_section_command:' in i18n
    assert 'section_command_hint:' in i18n


def test_preview_sanitizes_html_and_save_preserves_message_width():
    app = (UI_DIR / "app.js").read_text(encoding="utf-8")
    assert "function sanitizePreviewHtml(html)" in app
    assert "NodeFilter.SHOW_ELEMENT" in app
    assert "renderedHtml.innerHTML = sanitizePreviewHtml" in app
    assert "config.telegram_msg_width = 60;" in app
    assert "Number.isFinite(Number(config.telegram_msg_width))" in app
