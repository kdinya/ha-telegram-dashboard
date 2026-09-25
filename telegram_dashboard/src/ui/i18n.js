/**
 * Telegram Dashboard Localization (i18n)
 * Supports English ('en', default) and Ukrainian ('uk').
 */
(function() {
  const TRANSLATIONS = {
    en: {
      // Navigation & Header
      nav_builder: "Builder",
      nav_rbac: "Users",
      nav_settings: "Settings",
      nav_preview: "Bot Preview",
      ha_status_online: "Home Assistant online",
      ha_status_offline: "Home Assistant offline",
      ha_status_error: "Connection error",
      header_title: "Telegram Menu Builder",
      header_subtitle: "Manage sections, entities, widgets, and actions",
      btn_preview: "Preview",
      btn_preview_title: "Show or hide preview",
      btn_save_changes: "💾 Save changes",

      // Builder Section
      sections_title: "📂 Menu Sections",
      btn_add_section: "+ Add section",
      editor_title_prefix: "✏️ Main section name:",
      badge_main_screen: "⭐ Main screen",
      btn_delete: "🗑️ Delete",
      label_icon: "Icon",
      btn_icon_select_title: "Choose icon from library",
      label_section_title: "Section name",
      placeholder_section_title: "e.g. Climate",
      label_allowed_roles: "Allowed roles",
      role_admin: "Administrator",
      role_member: "Family member",
      role_guest: "Guest",
      block_nav_buttons_title: "Navigation buttons to sections",
      block_nav_buttons_hint: "Select sections whose navigation buttons will be shown in this bot section:",
      block_section_content_title: "Section elements",
      btn_action_add_text: "Add text",
      btn_action_add_entity: "Add entity",
      btn_action_add_button: "Add button",
      btn_move_up: "Move up",
      btn_move_down: "Move down",
      btn_action_add_divider: "Add spacer",
      badge_divider: "Spacer",
      divider_style_line: "Solid line",
      divider_style_space: "Blank space",
      divider_style_dashed: "Dashed line",
      btn_change_divider_style: "Change spacer style",
      toast_divider_added: "Horizontal spacer added",
      confirm_delete_divider_item: "Delete this horizontal spacer?",
      badge_heading: "Heading",
      btn_edit_text_title: "Edit text",
      btn_delete_text_title: "Delete text",
      placeholder_text_input: "Enter text...",
      btn_bold_title: "Heading (bold)",
      header_word: "Heading",
      confirm_delete_text_item: "Delete this text item?",
      confirm_delete_entity: "Remove this entity from section?",
      confirm_delete_button: "Delete this button?",
      confirm_delete_device: "Remove this device from section?",

      btn_save_item_title: "Save",
      btn_cancel_item_title: "Cancel",
      empty_icon_title: "No icon",
      btn_inline_icon_title: "Choose icon or leave empty",
      empty_texts_hint: "No text items yet. Click \"Add text\" to create the first one.",

      // RBAC / Users
      rbac_title: "👥 Bot Users",
      rbac_desc: "Users are automatically added when they message the bot. Confirm them here and assign roles.",
      btn_sync_users: "🔄 Refresh / Sync",
      btn_add_user: "+ Add manually",
      th_telegram_id: "Telegram ID",
      th_name: "Name / Username",
      th_role: "Role",
      th_status: "Access Status",
      th_actions: "Actions",
      status_guest: "Pending approval",
      status_member: "Active access",
      status_admin: "Administrator (full)",
      btn_confirm_user: "Confirm",
      btn_save_user: "Save",
      btn_delete_user: "Delete",
      empty_users: "No registered users",

      // Settings
      settings_title: "⚙️ Telegram Bot Settings",
      settings_language: "Interface language",
      lang_en: "English (Default)",
      lang_uk: "Ukrainian (Українська)",
      settings_bot_token: "Telegram Bot Token",
      settings_bot_token_hint: "Get a token from @BotFather or specify it in add-on configuration.",
      settings_theme: "Message style",
      theme_cards: "Modern (HTML Cards)",
      theme_minimal: "Minimalist",
      theme_tree: "Tree view with progress bars",
      settings_default_role: "Default role for new users",
      role_guest_hint: "Guest (pending approval)",
      role_member_hint: "Family member (immediately active)",
      role_admin_hint: "Administrator",

      // Preview
      preview_mobile_title: "📱 Telegram Simulator",
      preview_size_label: "Preview size:",
      preview_size_compact: "Compact (290px)",
      preview_size_standard: "Standard (320px)",
      preview_size_large: "Large (360px)",
      preview_size_wide: "Wide (400px)",
      btn_save_section_meta: "Save",
      btn_save: "Save",

      preview_back_btn: "⬅️ Back to editor",
      preview_sim_role: "Role simulation:",

      // Modals: Add Section
      modal_add_section_title: "Add new section",
      modal_edit_section_title: "Edit section",
      btn_edit_section_meta_title: "Edit section name and icon",
      toast_section_updated: "Section updated",
      modal_add_section_label: "Section name",
      modal_add_section_placeholder: "e.g. Climate or Lighting",
      modal_add_section_hint: "Identifier will be generated automatically from the title.",
      btn_cancel: "Cancel",
      btn_create_section: "Create section",

      // Modals: Confirm Dialog
      confirm_dialog_title: "Confirmation",
      confirm_delete_section: "Delete section \"{title}\"?",
      confirm_delete_user: "Delete user {name}?",
      alert_cannot_delete_main: "The main section (main) cannot be deleted.",

      // Icon Picker
      icon_picker_title: "Smart home icon library",
      icon_picker_search_ph: "🔍 Search icons (e.g. lamp, climate, lock)...",
      btn_clear_icon: "🚫 No icon",
      cat_all: "All",
      cat_climate: "Climate",
      cat_light: "Lighting",
      cat_security: "Security",
      cat_energy: "Energy",
      cat_media: "Media",
      cat_water: "Water",
      cat_home: "Home",
      cat_other: "Other",

      // Entity Picker
      entity_picker_title: "Choose Home Assistant entity",
      entity_picker_search_ph: "🔍 Search by name or entity_id (e.g. kitchen, light, boiler)...",
      domain_all: "All",
      domain_controls: "💡 Controls & Devices",
      domain_sensors: "📈 Sensors & States",
      domain_automations: "⚡ Automations & Scripts",
      domain_system: "⚙️ Home Assistant & System",

      // Widget Modal
      widget_modal_title: "📊 Add indicator / entity",
      widget_selected_entity: "Selected entity",
      widget_label_input: "Custom indicator label",
      widget_label_ph: "e.g. Current temperature, Main valve, Battery level",
      widget_unit_input: "Unit of measurement (optional)",
      widget_unit_ph: "e.g. °C, %, bar, W",
      btn_add_widget: "Add indicator",

      // Action Modal
      action_modal_title: "⚡ Configure action",
      action_selected_entity: "Selected entity / device",
      action_entity_ph: "Select entity...",
      btn_choose: "Choose",
      action_service_label: "Available Home Assistant action",
      action_button_label: "Button label in Telegram",
      action_button_ph: "e.g. Turn on light",
      btn_save_action: "Add action to section",

      // Prompts
      prompt_user_id: "Enter user Telegram ID:",
      prompt_user_name: "Enter user name:",
      toast_enter_section_name: "Please enter a section name",

      // Toasts / Notifications
      toast_cfg_load_error: "Failed to load configuration",
      toast_entity_added: "Entity \"{name}\" added",
      toast_select_entity_first: "First select an entity",
      toast_action_added: "Action added",
      toast_enter_text_first: "Please enter text before saving",
      toast_text_updated: "Text updated successfully",
      toast_item_deleted: "Item deleted",
      toast_text_added: "Text added successfully",
      toast_section_created: "Section \"{title}\" created (id: {slug})",
      toast_section_deleted: "Section deleted",
      toast_user_confirmed: "User {name} confirmed!",
      toast_user_updated: "User updated",
      toast_user_deleted: "User deleted",
      toast_user_delete_error: "Failed to delete user",
      toast_users_synced: "Synchronized. New users: {count}",
      toast_sync_error: "Sync error: {err}",
      toast_all_saved: "All changes saved successfully!",
      toast_save_error: "Failed to save changes",
            btn_toggle_indent: "Toggle indent",
      btn_toggle_indent_on: "With indent (tree branch)",
      btn_toggle_indent_off: "Without indent",
      placeholder_entity_name: "Custom name (optional)",
      placeholder_entity_select: "Choose Home Assistant entity...",
      badge_entity: "Entity",
      badge_indent: "Indent",
      badge_no_indent: "No indent",
      toast_entity_added_success: "Entity added successfully",
      toast_entity_updated_success: "Entity updated successfully",
      toast_select_entity_first_validation: "Please choose an entity first",
      confirm_delete_entity_item_unified: "Delete this entity from section?",
      toast_entity_coming_soon: "Adding entities will be available soon",
      toast_buttons_coming_soon: "Adding buttons will be available soon"
    },

    uk: {
      // Navigation & Header
      nav_builder: "Конструктор",
      nav_rbac: "Користувачі",
      nav_settings: "Налаштування",
      nav_preview: "Прев'ю бота",
      ha_status_online: "Home Assistant онлайн",
      ha_status_offline: "Home Assistant офлайн",
      ha_status_error: "Помилка зв'язку",
      header_title: "Конструктор меню Telegram",
      header_subtitle: "Керування розділами, сутностями, віджетами та діями",
      btn_preview: "Прев'ю",
      btn_preview_title: "Сховати або показати прев'ю",
      btn_save_changes: "💾 Зберегти зміни",

      // Builder Section
      sections_title: "📂 Розділи меню",
      btn_add_section: "+ Додати розділ",
      editor_title_prefix: "✏️ Основна назва розділу:",
      badge_main_screen: "⭐ Головний екран",
      btn_delete: "🗑️ Видалити",
      label_icon: "Іконка",
      btn_icon_select_title: "Обрати іконку з бази",
      label_section_title: "Назва розділу",
      placeholder_section_title: "Наприклад: Клімат",
      label_allowed_roles: "Дозволені ролі",
      role_admin: "Адміністратор",
      role_member: "Член родини",
      role_guest: "Гість",
      block_nav_buttons_title: "Кнопки переходу до розділів",
      block_nav_buttons_hint: "Оберіть розділи, кнопки переходу до яких відображатимуться у цьому розділі бота:",
      block_section_content_title: "Елементи розділу",
      btn_action_add_text: "Додати текст",
      btn_action_add_entity: "Додати ентіті",
      btn_action_add_button: "Додати кнопку",
      btn_move_up: "Вгору",
      btn_move_down: "Вниз",
      btn_action_add_divider: "Додати відступ",
      badge_divider: "Відступ",
      divider_style_line: "Суцільна лінія",
      divider_style_space: "Порожній відступ",
      divider_style_dashed: "Пунктирна лінія",
      btn_change_divider_style: "Змінити стиль відступу",
      toast_divider_added: "Горизонтальний відступ додано",
      confirm_delete_divider_item: "Видалити цей горизонтальний відступ?",
      badge_heading: "Заголовок",
      btn_edit_text_title: "Редагувати текст",
      btn_delete_text_title: "Видалити текст",
      placeholder_text_input: "Введіть текст...",
      btn_bold_title: "Заголовок (жирний)",
      header_word: "Заголовок",
      confirm_delete_text_item: "Видалити цей текстовий елемент?",
      confirm_delete_entity: "Видалити цю сутність із розділу?",
      confirm_delete_button: "Видалити цю кнопку?",
      confirm_delete_device: "Видалити цей пристрій із розділу?",

      btn_save_item_title: "Зберегти",
      btn_cancel_item_title: "Скасувати",
      empty_icon_title: "Без іконки",
      btn_inline_icon_title: "Обрати іконку або залишити пустою",
      empty_texts_hint: "Немає текстових елементів. Натисніть «Додати текст», щоб створити перший.",

      // RBAC / Users
      rbac_title: "👥 Користувачі бота",
      rbac_desc: "Користувачі автоматично додаються при повідомленні боту. Тут ви підтверджуєте їх та призначаєте ролі.",
      btn_sync_users: "🔄 Оновити / Синхронізувати",
      btn_add_user: "+ Додати вручну",
      th_telegram_id: "Telegram ID",
      th_name: "Ім'я / Юзернейм",
      th_role: "Роль",
      th_status: "Статус доступу",
      th_actions: "Дії",
      status_guest: "Очікує схвалення",
      status_member: "Активний доступ",
      status_admin: "Адміністратор (повний)",
      btn_confirm_user: "Підтвердити",
      btn_save_user: "Зберегти",
      btn_delete_user: "Видалити",
      empty_users: "Немає зареєстрованих користувачів",

      // Settings
      settings_title: "⚙️ Параметри Telegram-бота",
      settings_language: "Мова інтерфейсу",
      lang_en: "English (за замовчуванням)",
      lang_uk: "Українська",
      settings_bot_token: "Токен Telegram-бота (Bot Token)",
      settings_bot_token_hint: "Отримайте токен у @BotFather або вкажіть у конфігурації add-on.",
      settings_theme: "Стиль повідомлень",
      theme_cards: "Сучасний (HTML Картки)",
      theme_minimal: "Мінімалістичний",
      theme_tree: "Деревовидний із прогрес-барами",
      settings_default_role: "Роль за замовчуванням для нових людей",
      role_guest_hint: "Гість (очікує підтвердження)",
      role_member_hint: "Член родини (одразу активний)",
      role_admin_hint: "Адміністратор",

      // Preview
      preview_mobile_title: "📱 Симулятор Telegram",
      preview_size_label: "Розмір прев'ю:",
      preview_size_compact: "Компактний (290px)",
      preview_size_standard: "Стандартний (320px)",
      preview_size_large: "Великий (360px)",
      preview_size_wide: "Широкий (400px)",
      btn_save_section_meta: "Зберегти",
      btn_save: "Зберегти",

      preview_back_btn: "⬅️ До налаштувань",
      preview_sim_role: "Симуляція ролі:",

      // Modals: Add Section
      modal_add_section_title: "Додати новий розділ",
      modal_edit_section_title: "Редагувати розділ",
      btn_edit_section_meta_title: "Редагувати назву та іконку розділу",
      toast_section_updated: "Розділ оновлено",
      modal_add_section_label: "Назва розділу",
      modal_add_section_placeholder: "Наприклад: Клімат або Освітлення",
      modal_add_section_hint: "Ідентифікатор буде згенеровано автоматично з назви.",
      btn_cancel: "Скасувати",
      btn_create_section: "Створити розділ",

      // Modals: Confirm Dialog
      confirm_dialog_title: "Підтвердження",
      confirm_delete_section: "Видалити розділ \"{title}\"?",
      confirm_delete_user: "Видалити користувача {name}?",
      alert_cannot_delete_main: "Головний розділ (main) не можна видалити.",

      // Icon Picker
      icon_picker_title: "База іконок для розумного дому",
      icon_picker_search_ph: "🔍 Пошук іконки (наприклад: лампа, клімат, замок)...",
      btn_clear_icon: "🚫 Без іконки",
      cat_all: "Всі",
      cat_climate: "Клімат",
      cat_light: "Світло",
      cat_security: "Безпека",
      cat_energy: "Енергія",
      cat_media: "Мультимедіа",
      cat_water: "Вода",
      cat_home: "Дім",
      cat_other: "Різне",

      // Entity Picker
      entity_picker_title: "Оберіть сутність Home Assistant",
      entity_picker_search_ph: "🔍 Пошук за назвою або entity_id (наприклад: кухня, light, boiler)...",
      domain_all: "Всі",
      domain_controls: "💡 Керування та пристрої",
      domain_sensors: "📈 Сенсори та стан",
      domain_automations: "⚡ Автоматизації та скрипти",
      domain_system: "⚙️ Home Assistant та система",

      // Widget Modal
      widget_modal_title: "📊 Додавання показника / сутності",
      widget_selected_entity: "Обрана сутність",
      widget_label_input: "Власна назва показника",
      widget_label_ph: "Наприклад: Поточна температура, Кран ввідний, Заряд",
      widget_unit_input: "Одиниця виміру (якщо потрібна)",
      widget_unit_ph: "Наприклад: °C, %, бар, Вт",
      btn_add_widget: "Додати показник",

      // Action Modal
      action_modal_title: "⚡ Налаштування дії",
      action_selected_entity: "Обрана сутність / пристрій",
      action_entity_ph: "Оберіть сутність...",
      btn_choose: "Вибрати",
      action_service_label: "Доступна дія з Home Assistant",
      action_button_label: "Текст на кнопці в Telegram",
      action_button_ph: "Наприклад: Увімкнути світло",
      btn_save_action: "Додати дію до розділу",

      // Prompts
      prompt_user_id: "Введіть Telegram ID користувача:",
      prompt_user_name: "Введіть ім'я користувача:",
      toast_enter_section_name: "Введіть назву нового розділу",

      // Toasts / Notifications
      toast_cfg_load_error: "Помилка завантаження конфігурації",
      toast_entity_added: "Ентіті \"{name}\" додано",
      toast_select_entity_first: "Спершу оберіть сутність",
      toast_action_added: "Дію додано",
      toast_enter_text_first: "Введіть текст перед збереженням",
      toast_text_updated: "Текст успішно оновлено",
      toast_item_deleted: "Елемент видалено",
      toast_text_added: "Текст успішно додано",
      toast_section_created: "Розділ \"{title}\" створено (id: {slug})",
      toast_section_deleted: "Розділ видалено",
      toast_user_confirmed: "Користувача {name} підтверджено!",
      toast_user_updated: "Користувача оновлено",
      toast_user_deleted: "Користувача видалено",
      toast_user_delete_error: "Помилка видалення",
      toast_users_synced: "Синхронізовано. Нових користувачів: {count}",
      toast_sync_error: "Помилка синхронізації: {err}",
      toast_all_saved: "Всі зміни успішно збережено!",
      toast_save_error: "Не вдалося зберегти зміни",
            btn_toggle_indent: "Перемкнути відступ",
      btn_toggle_indent_on: "З відступом (гілка дерева)",
      btn_toggle_indent_off: "Без відступу",
      placeholder_entity_name: "Власна назва (необов'язково)",
      placeholder_entity_select: "Оберіть сутність Home Assistant...",
      badge_entity: "Ентіті",
      badge_indent: "З відступом",
      badge_no_indent: "Без відступу",
      toast_entity_added_success: "Ентіті успішно додано",
      toast_entity_updated_success: "Ентіті успішно оновлено",
      toast_select_entity_first_validation: "Будь ласка, оберіть сутність",
      confirm_delete_entity_item_unified: "Видалити цю сутність із розділу?",
      toast_entity_coming_soon: "Додавання ентіті буде доступне незабаром",
      toast_buttons_coming_soon: "Додавання кнопок буде доступне незабаром"
    }
  };

  const STORAGE_KEY = 'ha_tg_dashboard_lang';
  let currentLanguage = 'en';

  function getLanguage() {
    return currentLanguage;
  }

  function t(key, params = {}) {
    const dict = TRANSLATIONS[currentLanguage] || TRANSLATIONS.en;
    let str = dict[key] || TRANSLATIONS.en[key] || key;
    if (params && typeof params === 'object') {
      Object.keys(params).forEach(p => {
        str = str.replace(new RegExp(`\\{${p}\\}`, 'g'), params[p]);
      });
    }
    return str;
  }

  function setLanguage(lang, triggerRerender = true) {
    const valid = (lang === 'uk') ? 'uk' : 'en';
    currentLanguage = valid;
    try {
      localStorage.setItem(STORAGE_KEY, valid);
    } catch (e) {
      // Storage unavailable or quota exceeded
    }

    if (document.documentElement) {
      document.documentElement.lang = valid;
    }

    // Update settings dropdown if exists
    const sel = document.getElementById('setting-language');
    if (sel && sel.value !== valid) {
      sel.value = valid;
    }

    // Apply translations to all DOM elements with data-i18n attributes
    applyDomTranslations();

    // Notify listeners / app to re-render dynamic elements
    if (triggerRerender && typeof window.onDashboardLanguageChanged === 'function') {
      window.onDashboardLanguageChanged(valid);
    }
  }

  function applyDomTranslations() {
    document.querySelectorAll('[data-i18n]').forEach(el => {
      const key = el.getAttribute('data-i18n');
      if (key) {
        el.textContent = t(key);
      }
    });

    document.querySelectorAll('[data-i18n-html]').forEach(el => {
      const key = el.getAttribute('data-i18n-html');
      if (key) {
        el.innerHTML = t(key);
      }
    });

    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
      const key = el.getAttribute('data-i18n-placeholder');
      if (key) {
        el.setAttribute('placeholder', t(key));
      }
    });

    document.querySelectorAll('[data-i18n-title]').forEach(el => {
      const key = el.getAttribute('data-i18n-title');
      if (key) {
        el.setAttribute('title', t(key));
      }
    });
  }

  function initLanguage(initialPreference) {
    let lang = 'en';
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored === 'uk' || stored === 'en') {
        lang = stored;
      } else if (initialPreference === 'uk' || initialPreference === 'en') {
        lang = initialPreference;
      }
    } catch (e) {
      if (initialPreference === 'uk') lang = 'uk';
    }
    setLanguage(lang, false);
    return lang;
  }

  window.I18N = {
    TRANSLATIONS,
    t,
    setLanguage,
    getLanguage,
    initLanguage,
    applyDomTranslations
  };
  window.t = t;
})();
