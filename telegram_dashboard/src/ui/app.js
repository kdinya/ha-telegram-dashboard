// Default domain icons mapping
const DOMAIN_ICONS = {
  light: '💡',
  switch: '🔌',
  climate: '🌡️',
  cover: '🪟',
  sensor: '📊',
  binary_sensor: '🔔',
  media_player: '🔊',
  fan: '💨',
  lock: '🔒',
  camera: '📷',
  automation: '⚙️',
  script: '📜',
  scene: '🎬',
  vacuum: '🧹',
  weather: '☀️',
  water_heater: '♨️',
  valve: '🚰',
  siren: '🚨',
  device_tracker: '📍',
  person: '👤',
  timer: '⏱️',
  input_boolean: '🔘',
  input_number: '🔢',
  input_select: '📋',
  input_text: '📝',
  input_datetime: '📅',
  counter: '🔢'
};


function openAddSectionModal() {
  const modal = document.getElementById('modal-add-section');
  const input = document.getElementById('new-section-title-input');
  const btnConfirm = document.getElementById('btn-confirm-add-section');
  const btnCancel = document.getElementById('btn-cancel-add-section');
  const btnClose = document.getElementById('btn-close-add-section-modal');
  if (!modal || !input) return;

  input.value = '';
  modal.classList.add('open');
  input.focus();

  const cleanup = () => {
    modal.classList.remove('open');
    if (btnConfirm) btnConfirm.removeEventListener('click', onConfirm);
    if (btnCancel) btnCancel.removeEventListener('click', onCancel);
    if (btnClose) btnClose.removeEventListener('click', onCancel);
    input.removeEventListener('keydown', onKeyDown);
  };

  const onConfirm = () => {
    const title = input.value.trim();
    if (!title) {
      showToast(t('toast_enter_section_name'), true);
      return;
    }
    cleanup();
    createSectionWithTitle(title);
  };

  const onCancel = () => cleanup();

  const onKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      onConfirm();
    } else if (e.key === 'Escape') {
      e.preventDefault();
      onCancel();
    }
  };

  if (btnConfirm) btnConfirm.addEventListener('click', onConfirm);
  if (btnCancel) btnCancel.addEventListener('click', onCancel);
  if (btnClose) btnClose.addEventListener('click', onCancel);
  input.addEventListener('keydown', onKeyDown);
}

function createSectionWithTitle(title) {
  const cleanTitle = stripLeadingEmoji(title.trim());
  const rawSlug = slugify(cleanTitle) || 'section';
  let slug = rawSlug;
  let counter = 1;
  while (config.menu[slug]) slug = `${rawSlug}_${counter++}`;

  let guessedIcon = '📁';
  const lower = cleanTitle.toLowerCase();
  if (lower.includes('клімат') || lower.includes('температур') || lower.includes('climat') || lower.includes('temp')) guessedIcon = '🌡️';
  else if (lower.includes('світл') || lower.includes('ламп') || lower.includes('light') || lower.includes('lamp')) guessedIcon = '💡';
  else if (lower.includes('розетк') || lower.includes('вимикач') || lower.includes('switch') || lower.includes('plug')) guessedIcon = '🔌';
  else if (lower.includes('безпек') || lower.includes('сигнал') || lower.includes('security') || lower.includes('alarm')) guessedIcon = '🛡️';
  else if (lower.includes('камер') || lower.includes('cam')) guessedIcon = '📹';
  else if (lower.includes('вод') || lower.includes('water')) guessedIcon = '🚰';
  else if (lower.includes('замок') || lower.includes('двер') || lower.includes('lock') || lower.includes('door')) guessedIcon = '🔒';
  else if (lower.includes('штор') || lower.includes('blind') || lower.includes('curtain')) guessedIcon = '🪟';

  // Ensure section is placed at the end of sections and is explicitly NOT main screen
  delete config.menu[slug];
  config.menu[slug] = {
    title: cleanTitle,
    icon: guessedIcon,
    type: 'section',
    is_main: false,
    roles: ['admin', 'member'],
    widgets: [],
    actions: [],
    texts: []
  };

  currentSectionKey = slug;
  renderSectionsPills();
  loadSectionIntoEditor(slug);
  updatePreview();
  showToast(t('toast_section_created', { title: cleanTitle, slug }));
}

const t = (key, params) => (window.I18N && window.I18N.t ? window.I18N.t(key, params) : (params ? Object.keys(params).reduce((s, k) => s.replace('{' + k + '}', params[k]), key) : key));

// --- Custom Modal Helpers ---
function showCustomConfirm(title, message, confirmText = (window.t ? window.t('btn_delete') : 'Delete'), isDanger = true) {
  return new Promise((resolve) => {
    const modal = document.getElementById('modal-confirm-dialog');
    const titleEl = document.getElementById('confirm-dialog-title');
    const msgEl = document.getElementById('confirm-dialog-message');
    const btnConfirm = document.getElementById('btn-dialog-confirm');
    const btnCancel = document.getElementById('btn-dialog-cancel');
    const btnClose = document.getElementById('btn-close-confirm-modal');

    titleEl.textContent = title;
    msgEl.textContent = message;
    btnConfirm.textContent = confirmText;
    btnConfirm.className = isDanger ? 'btn btn-danger btn-sm' : 'btn btn-primary btn-sm';

    const cleanup = () => {
      modal.classList.remove('open');
      btnConfirm.removeEventListener('click', onConfirm);
      btnCancel.removeEventListener('click', onCancel);
      btnClose.removeEventListener('click', onCancel);
    };

    const onConfirm = () => { cleanup(); resolve(true); };
    const onCancel = () => { cleanup(); resolve(false); };

    btnConfirm.addEventListener('click', onConfirm);
    btnCancel.addEventListener('click', onCancel);
    btnClose.addEventListener('click', onCancel);

    modal.classList.add('open');
  });
}
/**
 * Telegram Dashboard Web UI Client
 */

let config = null;
let currentSectionKey = 'main';
let currentSimulatedRole = 'admin';
let availableEntities = [];
let entitiesLoadError = null;

const cyrillicMap = {
  'а':'a','б':'b','в':'v','г':'h','ґ':'g','д':'d','е':'e','є':'ye','ж':'zh','з':'z',
  'и':'y','і':'i','ї':'yi','й':'y','к':'k','л':'l','м':'m','н':'n','о':'o','п':'p',
  'р':'r','с':'s','т':'t','у':'u','ф':'f','х':'kh','ц':'ts','ч':'ch','ш':'sh','щ':'shch',
  'ь':'','ю':'yu','я':'ya',' ':'_','-':'_'
};

function slugify(text) {
  return text.toLowerCase()
    .split('')
    .map(c => cyrillicMap[c] !== undefined ? cyrillicMap[c] : c)
    .join('')
    .replace(/[^a-z0-9_]/g, '')
    .replace(/_+/g, '_')
    .replace(/^_+|_+$/g, '');
}

/** Strip leading emoji so icon + title don't duplicate */

function escapeHtml(str) {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function stripLeadingEmoji(text) {
  if (!text) return text;
  return text.replace(/^[^\p{L}\p{N}]+/u, '').trim();
}

// --- Icon database: clean category names without icons, searchable ---
const ICON_DATABASE = {
  'Клімат': ['🌡️', '❄️', '🔥', '☀️', '⛅', '🌧️', '💨', '💧', '♨️', '🌫️', '🌫️', '🥶', '🥵'],
  'Освітлення': ['💡', '🔦', '🕯️', '🔆', '🏮', '✨', '🌈', '🪩', '🎇', '🌟'],
  'Безпека': ['🚪', '🔒', '🔓', '🛡️', '🚨', '🚰', '🧯', '🔔', '📹', '🔑', '⚠️', '🆘'],
  'Кімнати': ['🏠', '🏡', '🛋️', '🛏️', '🍳', '🚿', '🛁', '🪴', '🧺', '👶', '🚗', '🏊', '🌳'],
  'Прилади': ['⚡', '🔋', '🔌', '🧹', '📺', '🔊', '📻', '☕', '💻', '🎮', '🖨️', '📱', '⌚'],
  'Статуси': ['📊', '📈', '✅', '❌', '⏳', '🔄', '▶️', '⏸️', '⏹️', 'ℹ️', '📌', '🗓️'],
  'Люди': ['👤', '👥', '👨', '👩', '🧑', '👶', '🙋', '🤝', '🚶'],
  'Дії': ['🎛️', '🎚️', '⬆️', '⬇️', '🔊', '🔉', '🔕', '🔀', '🔁', '📝', '🎯', '🚀']
};

// Suggested services by entity domain (HA standard services)
const DOMAIN_SERVICES = {
  'light': [
    { service: 'light.turn_on', label: 'Увімкнути світло' },
    { service: 'light.turn_off', label: 'Вимкнути світло' },
    { service: 'light.toggle', label: 'Перемкнути світло' },
  ],
  'switch': [
    { service: 'switch.turn_on', label: 'Увімкнути' },
    { service: 'switch.turn_off', label: 'Вимкнути' },
    { service: 'switch.toggle', label: 'Перемкнути' },
  ],
  'climate': [
    { service: 'climate.turn_on', label: 'Увімкнути клімат' },
    { service: 'climate.turn_off', label: 'Вимкнути клімат' },
    { service: 'climate.set_temperature', label: 'Встановити температуру' },
  ],
  'cover': [
    { service: 'cover.open_cover', label: 'Відкрити штори' },
    { service: 'cover.close_cover', label: 'Закрити штори' },
    { service: 'cover.stop_cover', label: 'Зупинити' },
  ],
  'media_player': [
    { service: 'media_player.play_pause', label: 'Пуск / Пауза' },
    { service: 'media_player.volume_up', label: 'Гучніше' },
    { service: 'media_player.volume_down', label: 'Тихіше' },
  ],
  'fan': [
    { service: 'fan.turn_on', label: 'Увімкнути вентилятор' },
    { service: 'fan.turn_off', label: 'Вимкнути вентилятор' },
  ],
  'vacuum': [
    { service: 'vacuum.start', label: 'Почати прибирання' },
    { service: 'vacuum.return_to_base', label: 'Повернутись на базу' },
  ],
  'lock': [
    { service: 'lock.lock', label: 'Заблокувати' },
    { service: 'lock.unlock', label: 'Розблокувати' },
  ],
  'water_heater': [
    { service: 'water_heater.turn_on', label: 'Увімкнути водонагрівач' },
    { service: 'water_heater.turn_off', label: 'Вимкнути водонагрівач' },
  ]
};

// Universal fallback actions for every entity
const UNIVERSAL_SERVICES = (entity_id) => {
  const domain = (entity_id || '').split('.')[0];
  const out = [];
  if (DOMAIN_SERVICES[domain]) out.push(...DOMAIN_SERVICES[domain]);
  out.push(
    { service: `homeassistant.toggle`, label: 'Перемкнути стан' },
    { service: `homeassistant.turn_on`, label: 'Увімкнути' },
    { service: `homeassistant.turn_off`, label: 'Вимкнути' },
  );
  return out;
};

// --- DOM ---
const $ = (id) => document.getElementById(id);
const navItems = document.querySelectorAll('.nav-item');
const tabPanes = document.querySelectorAll('.tab-pane');
const sectionsList = $('sections-list');
const editorSectionKey = $('editor-section-key');
const editorSectionIcon = $('editor-section-icon');
const editorSectionTitle = $('editor-section-title');
const btnEditSectionMeta = $('btn-edit-section-meta');
const modalEditSection = $('modal-edit-section');
const btnCloseEditSectionModal = $('btn-close-edit-section-modal');
const btnCancelEditSection = $('btn-cancel-edit-section');
const btnSaveEditSection = $('btn-save-edit-section');
const btnEditSectionIconPicker = $('btn-edit-section-icon-picker');
const editSecIcon = $('edit-sec-icon');
const editSectionIconDisplay = $('edit-section-icon-display');
const editSecTitle = $('edit-sec-title');
const secTitle = $('sec-title');
const secIcon = $('sec-icon');
const secIconDisplay = $('sec-icon-display');
const secType = $('sec-type');
const roleAdmin = $('role-admin');
const roleMember = $('role-member');
const roleGuest = $('role-guest');
const blockMenuSections = $('block-menu-sections');
const blockEntitiesSource = $('block-entities-source');
const blockSectionItems = $('block-section-items');
const menuSectionsChecklist = $('menu-sections-checklist');
const sectionDevicesList = $('section-devices-list');
const btnAddSectionDevice = $('btn-add-section-device');
const widgetsList = $('widgets-list');
const actionsList = $('actions-list');
const usersTbody = $('users-tbody');
const toastEl = $('toast');
const previewPane = $('preview-pane');
const previewText = $('preview-text');
const previewButtons = $('preview-buttons');
const haEntitiesDatalist = $('ha-entities-datalist');

// Icon picker elements
const iconPickerModal = $('icon-picker-modal');
const btnOpenIconPicker = $('btn-open-icon-picker');
const btnCloseIconPicker = $('btn-close-icon-picker');
const iconSearchInput = $('icon-search-input');
const iconCategoriesTabs = $('icon-categories-tabs');
const iconPickerGrid = $('icon-picker-grid');

// Entity picker elements
const entityPickerModal = $('entity-picker-modal');
const btnCloseEntityPicker = $('btn-close-entity-picker');
const entitySearchInput = $('entity-search-input');
const domainFiltersTabs = $('domain-filters-tabs');
const entityPickerList = $('entity-picker-list');
const entityPickerTitle = $('entity-picker-title');

// Action config modal elements
const actionConfigModal = $('action-config-modal');
const btnCloseActionConfig = $('btn-close-action-config');
const actionEntityDisplay = $('action-entity-display');
const btnActionChooseEntity = $('btn-action-choose-entity');
const actionServiceSelect = $('action-service-select');
const actionLabelInput = $('action-label-input');
const btnSaveConfiguredAction = $('btn-save-configured-action');

// Picker state
let entityPickerContext = 'widget'; // 'widget' | 'action'
let selectedActionEntity = '';

// --- Utils ---
function showToast(message, isError = false) {
  toastEl.textContent = message;
  toastEl.style.backgroundColor = isError ? '#ef4444' : '#38bdf8';
  toastEl.style.color = isError ? '#fff' : '#0f172a';
  toastEl.classList.add('show');
  setTimeout(() => toastEl.classList.remove('show'), 3000);
}

async function api(path, opts = {}) {
  const res = await fetch(path, opts);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: 'Невідома помилка' }));
    throw new Error(err.error || `HTTP ${res.status}`);
  }
  return res.json();
}

// --- Init ---
async function init() {
  setupNavigation();
  setupIconPicker();
  setupEntityPicker();
  setupActionConfig();
  setupWidgetConfig();
  await fetchEntities();
  await loadConfig();
  setupEventListeners();
}

async function fetchEntities() {
  try {
    const data = await api('api/entities');
    availableEntities = data.entities || [];
    if (haEntitiesDatalist) {
      haEntitiesDatalist.innerHTML = availableEntities
        .map(e => `<option value="${e.entity_id}">${e.friendly_name} (${e.entity_id})</option>`)
        .join('');
    }
  } catch (e) {
    console.warn('Could not fetch entities:', e);
    entitiesLoadError = e.message || 'Помилка завантаження сутностей';
  }
}

async function loadConfig() {
  try {
    config = await api('api/config');
    renderSectionsPills();
    loadSectionIntoEditor(currentSectionKey);
    renderUsers();
    loadSettings();
    updatePreview();
  } catch (e) {
    console.error('Помилка завантаження конфігурації або ініціалізації редактора:', e);
    showToast(t('toast_cfg_load_error'), true);
  }
}

// --- Navigation ---
function setupNavigation() {
  navItems.forEach(item => {
    item.addEventListener('click', () => {
      const targetTab = item.dataset.tab;
      navItems.forEach(n => n.classList.remove('active'));
      item.classList.add('active');

      if (targetTab === 'preview') {
        previewPane.classList.add('mobile-active');
        tabPanes.forEach(p => p.classList.remove('active'));
      } else {
        previewPane.classList.remove('mobile-active');
        tabPanes.forEach(p => p.classList.toggle('active', p.id === `tab-${targetTab}`));
      }
    });
  });

  $('btn-back-to-editor')?.addEventListener('click', () => {
    document.querySelector('[data-tab="builder"]')?.click();
  });
}

// --- Icon Picker ---
function setupIconPicker() {
  if (btnOpenIconPicker) {
    btnOpenIconPicker.addEventListener('click', () => {
      activeIconTarget = 'section';
      iconPickerModal?.classList.add('open');
      renderIconCategories();
      renderIconGrid();
    });
  }

  btnCloseIconPicker?.addEventListener('click', () => iconPickerModal?.classList.remove('open'));
  iconPickerModal?.addEventListener('click', e => {
    if (e.target === iconPickerModal) iconPickerModal.classList.remove('open');
  });
  iconSearchInput?.addEventListener('input', renderIconGrid);

  const btnClearIcon = document.getElementById('btn-clear-icon-selection');
  if (btnClearIcon) {
    btnClearIcon.addEventListener('click', () => {
      if (activeIconTarget === 'inline_text_item' || activeIconTarget === 'text_item' || activeIconTarget === 'inline_entity_item') {
        const parentId = activeIconTarget === 'inline_entity_item' ? '#inline-entity-row' : '#inline-edit-row';
        const textIconInput = document.querySelector(`${parentId} .item-icon-val`);
        const textIconDisplay = document.querySelector(`${parentId} .item-icon-display`);
        if (textIconInput) textIconInput.value = '';
        if (textIconDisplay) textIconDisplay.innerHTML = `<span class="icon-empty-slot" title="${t('empty_icon_title')}">∅</span>`;
      } else if (activeIconTarget === 'edit_section_meta') {
        if (editSecIcon) editSecIcon.value = '';
        if (editSectionIconDisplay) editSectionIconDisplay.textContent = '📁';
      } else {
        if (secIcon) secIcon.value = '';
        if (secIconDisplay) secIconDisplay.textContent = '📁';
      }
      iconPickerModal.classList.remove('open');
    });
  }
}

function renderIconCategories() {
  const cats = ['Всі', ...Object.keys(ICON_DATABASE)];
  iconCategoriesTabs.innerHTML = cats.map((cat, i) => `
    <button class="icon-cat-btn ${cat === 'Всі' ? 'active' : ''}" data-cat="${cat}">${cat}</button>
  `).join('');

  iconCategoriesTabs.querySelectorAll('.icon-cat-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      iconCategoriesTabs.querySelectorAll('.icon-cat-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      renderIconGrid();
    });
  });
}

function renderIconGrid() {
  const search = (iconSearchInput.value || '').toLowerCase();
  const activeCat = iconCategoriesTabs.querySelector('.icon-cat-btn.active')?.dataset.cat || 'Всі';

  let pool = [];
  if (activeCat === 'Всі') {
    Object.values(ICON_DATABASE).forEach(arr => pool.push(...arr));
  } else {
    pool = ICON_DATABASE[activeCat] || [];
  }

  // Deduplicate
  pool = [...new Set(pool)];

  let filtered = pool;
  if (search) {
    // Match by category name or the emoji itself
    filtered = pool.filter(icon => {
      const catOf = Object.keys(ICON_DATABASE).find(c => ICON_DATABASE[c].includes(icon)) || '';
      return catOf.toLowerCase().includes(search) || icon === search;
    });
    // If nothing matched by name, show all icons (user might just scroll)
    if (!filtered.length) filtered = pool;
  }

  iconPickerGrid.innerHTML = filtered.map(icon =>
    `<button type="button" class="icon-pick-item" data-icon="${icon}">${icon}</button>`
  ).join('');

  iconPickerGrid.querySelectorAll('.icon-pick-item').forEach(item => {
    item.addEventListener('click', () => {
      if (activeIconTarget === 'inline_text_item' || activeIconTarget === 'text_item') {
        const textIconInput = document.querySelector('#inline-edit-row .item-icon-val');
        const textIconDisplay = document.querySelector('#inline-edit-row .item-icon-display');
        if (textIconInput) textIconInput.value = item.dataset.icon;
        if (textIconDisplay) textIconDisplay.textContent = item.dataset.icon;
      } else if (activeIconTarget === 'inline_entity_item') {
        const textIconInput = document.querySelector('#inline-entity-row .item-icon-val');
        const textIconDisplay = document.querySelector('#inline-entity-row .item-icon-display');
        if (textIconInput) textIconInput.value = item.dataset.icon;
        if (textIconDisplay) textIconDisplay.textContent = item.dataset.icon;
      } else if (activeIconTarget === 'edit_section_meta') {
        if (editSecIcon) editSecIcon.value = item.dataset.icon;
        if (editSectionIconDisplay) editSectionIconDisplay.textContent = item.dataset.icon;
      } else {
        if (secIcon) secIcon.value = item.dataset.icon;
        if (secIconDisplay) secIconDisplay.textContent = item.dataset.icon;
      }
      iconPickerModal.classList.remove('open');
    });
  });
}

// --- Entity Picker Modal ---
function setupEntityPicker() {
  btnCloseEntityPicker.addEventListener('click', () => entityPickerModal.classList.remove('open'));
  entityPickerModal.addEventListener('click', e => {
    if (e.target === entityPickerModal) entityPickerModal.classList.remove('open');
  });
  entitySearchInput.addEventListener('input', renderEntityPickerList);
  domainFiltersTabs.addEventListener('click', e => {
    const btn = e.target.closest('.domain-tab-btn');
    if (!btn) return;
    domainFiltersTabs.querySelectorAll('.domain-tab-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    renderEntityPickerList();
  });
}

function openEntityPicker(context, title) {
  entityPickerContext = context;
  entityPickerTitle.textContent = title || 'Оберіть сутність Home Assistant';
  entitySearchInput.value = '';
  domainFiltersTabs.querySelectorAll('.domain-tab-btn').forEach((b, i) => b.classList.toggle('active', i === 0));
  entityPickerModal.classList.add('open');
  renderEntityPickerList();
}

function splitEntityName(friendlyName, domain, attributes) {
  if (!friendlyName) return { device: '', param: '' };

  // 1. Check explicit separators: " - ", " — ", " : ", ": ", " | ", " / "
  const sepMatch = friendlyName.match(/^(.+?)\s*(?:—|-|:|\||\/)\s*(.+)$/);
  if (sepMatch && sepMatch[1].trim() && sepMatch[2].trim()) {
    return { device: sepMatch[1].trim(), param: sepMatch[2].trim() };
  }

  // 2. Comprehensive list of known parameters/attributes (Ukrainian, English, common abbreviations)
  const paramKeywords = [
    // Multi-word parameters first
    'рівень заряду', 'battery level', 'якість повітря', 'air quality',
    'потужність сигналу', 'water leak', 'витік води', 'захист від протікання',
    'нічний режим', 'night mode',
    // Single word parameters
    'температура', 'temperature', 'temp',
    'вологість', 'humidity', 'hum',
    'тиск', 'pressure',
    'батарея', 'battery', 'batt',
    'освітленість', 'яскравість', 'освітлення', 'illuminance', 'brightness', 'light',
    'рух', 'motion', 'occupancy', 'присутність',
    'стан', 'статус', 'state', 'status',
    'потужність', 'power',
    'енергія', 'energy',
    'напруга', 'voltage',
    'струм', 'current',
    'швидкість', 'speed',
    'co2', 'voc', 'pm2.5', 'pm10', 'pm1', 'pm25',
    'відкриття', 'закриття', 'door', 'window', 'contact', 'контакт',
    'затоплення', 'протікання', 'leak', 'moisture',
    'дим', 'smoke', 'газ', 'gas', 'вібрація', 'vibration',
    'вимикач', 'switch', 'реле', 'relay', 'розетка', 'socket', 'plug',
    'кнопка', 'button', 'клапан', 'valve', 'замок', 'lock',
    'сирена', 'siren', 'гучність', 'volume',
    'доступність', 'availability', 'linkquality', 'rssi', 'ping'
  ];

  for (const kw of paramKeywords) {
    const regex = new RegExp(`^(.+?)\\s+(${kw.replace('.', '\\.')})$`, 'i');
    const m = friendlyName.match(regex);
    if (m && m[1].trim() && m[2].trim()) {
      return { device: m[1].trim(), param: m[2].trim() };
    }
  }

  // 3. Check attributes.device_class if present
  if (attributes && attributes.device_class) {
    const dc = String(attributes.device_class).toLowerCase();
    const dcRegex = new RegExp(`^(.+?)\\s+(${dc})$`, 'i');
    const m = friendlyName.match(dcRegex);
    if (m && m[1].trim() && m[2].trim()) {
      return { device: m[1].trim(), param: m[2].trim() };
    }
  }

  // 4. If name has 3 or more words, treat the last word as parameter if likely
  const words = friendlyName.trim().split(/\s+/);
  if (words.length >= 3) {
    return {
      device: words.slice(0, words.length - 1).join(' '),
      param: words[words.length - 1]
    };
  }

  return { device: '', param: friendlyName };
}

function isEntityInGroup(entity, group) {
  if (!group || group === 'all') return true;
  const domain = (entity.domain || (entity.entity_id || '').split('.')[0] || '').toLowerCase();
  const eid = (entity.entity_id || '').toLowerCase();
  const name = (entity.friendly_name || '').toLowerCase();

  if (group === 'controls') {
    return ['light', 'switch', 'cover', 'lock', 'climate', 'fan', 'media_player', 'valve', 'water_heater', 'vacuum', 'humidifier', 'siren'].includes(domain);
  }
  if (group === 'sensors') {
    return ['sensor', 'binary_sensor', 'device_tracker', 'person', 'weather', 'sun'].includes(domain) && !isSystemEntity(eid, name, domain);
  }
  if (group === 'automations') {
    return ['automation', 'script', 'scene', 'input_boolean', 'input_button', 'input_select', 'input_number', 'input_datetime', 'timer', 'counter', 'schedule'].includes(domain);
  }
  if (group === 'system') {
    return isSystemEntity(eid, name, domain);
  }
  return true;
}

function isSystemEntity(eid, name, domain) {
  if (['update', 'system_health', 'persistent_notification'].includes(domain)) return true;
  if (eid.startsWith('sensor.home_assistant_') || eid.startsWith('sensor.supervisor_') || eid.startsWith('sensor.disk_') || eid.startsWith('sensor.memory_') || eid.startsWith('sensor.cpu_')) return true;
  if (eid.includes('version') || eid.includes('uptime') || eid.includes('last_boot') || eid.includes('certificate')) return true;
  if (name.includes('home assistant') || name.includes('supervisor') || name.includes('система') || name.includes('версія') || name.includes('диск') || name.includes('процесор')) return true;
  return false;
}

function renderEntityPickerList() {
  const rawSearch = (entitySearchInput.value || '').toLowerCase().trim();
  const activeGroup = domainFiltersTabs.querySelector('.domain-tab-btn.active')?.dataset.domain || 'all';

  let list = availableEntities;

  // Filter by category group
  if (activeGroup !== 'all') {
    list = list.filter(e => isEntityInGroup(e, activeGroup));
  }

  // Multi-token search (matches all words regardless of order)
  if (rawSearch) {
    const tokens = rawSearch.split(/\s+/).filter(Boolean);
    list = list.filter(e => {
      const fn = (e.friendly_name || '').toLowerCase();
      const eid = (e.entity_id || '').toLowerCase();
      const area = (e.area || '').toLowerCase();
      const combined = `${fn} ${eid} ${area}`;
      return tokens.every(tok => combined.includes(tok));
    });
  }

  if (!list.length) {
    entityPickerList.innerHTML = entitiesLoadError
      ? `<p class="field-hint" style="padding: 20px;">Не вдалося завантажити сутності: ${entitiesLoadError}. <button type="button" class="btn btn-secondary btn-sm" id="btn-retry-entities">Повторити</button></p>`
      : '<p class="field-hint" style="padding: 20px;">Нічого не знайдено. Спробуйте інший пошук або фільтр.</p>';
    const retry = document.getElementById('btn-retry-entities');
    if (retry) retry.addEventListener('click', async () => {
      entitiesLoadError = null;
      await fetchEntities();
      renderEntityPickerList();
    });
    return;
  }

  entityPickerList.innerHTML = list.map(e => {
    const domain = escapeHtml(e.domain || (e.entity_id || '').split('.')[0] || '');
    const fullFriendlyName = e.friendly_name || e.entity_id || '';
    const entityId = escapeHtml(e.entity_id || '');
    const stateVal = escapeHtml(String(e.state !== undefined && e.state !== null ? e.state : ''));
    const unit = escapeHtml(e.attributes && e.attributes.unit_of_measurement ? e.attributes.unit_of_measurement : '');
    const displayParam = unit ? `${stateVal} ${unit}` : stateVal;

    const parts = splitEntityName(fullFriendlyName, domain, e.attributes);
    const escapedDevice = escapeHtml(parts.device);
    const escapedParam = escapeHtml(parts.param);
    const escapedFullName = escapeHtml(fullFriendlyName);

    const titleHtml = parts.device
      ? `<div class="entity-item-titles">
           <span class="entity-item-device" title="${escapedDevice}">${escapedDevice}</span>
           <span class="entity-item-sep">›</span>
           <span class="entity-item-param-name">${escapedParam}</span>
         </div>`
      : `<div class="entity-item-titles">
           <span class="entity-item-param-name is-standalone">${escapedParam}</span>
         </div>`;

    return `
    <button type="button" class="entity-item" data-id="${entityId}" data-name="${escapedFullName}" data-domain="${domain}">
      <div class="entity-item-main">
        <div class="entity-item-header">
          ${titleHtml}
          <span class="entity-item-domain-badge">${domain}</span>
        </div>
        <div class="entity-item-sub">
          <span class="entity-item-id"><code>${entityId}</code></span>
        </div>
      </div>
      <div class="entity-item-state-wrap">
        <span class="entity-item-param ${stateVal === 'unavailable' || stateVal === 'unknown' ? 'is-muted' : ''}">${displayParam || '—'}</span>
      </div>
    </button>
  `;
  }).join('');

  entityPickerList.querySelectorAll('.entity-item').forEach(item => {
    item.addEventListener('click', () => {
      const eid = item.dataset.id;
      const name = item.dataset.name;
      const domain = item.dataset.domain;
      entityPickerModal.classList.remove('open');

            if (entityPickerContext === 'inline_entity_item') {
        const row = document.getElementById('inline-entity-row');
        if (row) {
          const sel = row.querySelector('.entity-select-val');
          if (sel) {
            sel.value = eid;
            sel.dispatchEvent(new Event('change'));
          }
          
          const nameInput = row.querySelector('.item-name-input');
          if (nameInput && !nameInput.value.trim()) {
            nameInput.value = name || eid;
          }
          const iconInput = row.querySelector('.item-icon-val');
          const iconDisplay = row.querySelector('.item-icon-display');
          if (iconInput && !iconInput.value) {
            const domain = (eid || '').split('.')[0];
            const defIcon = (DOMAIN_ICONS && DOMAIN_ICONS[domain]) || '🔹';
            iconInput.value = defIcon;
            if (iconDisplay) iconDisplay.textContent = defIcon;
          }
        }
        entityPickerModal.classList.remove('open');
        return;
      } else if (entityPickerContext === 'entity_item') {
        const sec = config.menu[currentSectionKey];
        if (!sec.entities) sec.entities = [];
        sec.entities.push({
          entity_id: eid,
          label: name,
          unit: (availableEntities.find(e => e.entity_id === eid)?.attributes?.unit_of_measurement) || ''
        });
        renderEntitiesList(sec.entities);
        updatePreview();
        showToast(t('toast_entity_added', { name }));
      } else if (entityPickerContext === 'button_target') {
        selectedButtonTarget = { entityId: eid, friendlyName: name, domain: domain };
        const disp = document.getElementById('btn-target-display');
        const lbl = document.getElementById('btn-custom-label');
        if (disp) disp.value = `${name} (${eid})`;
        if (lbl && !lbl.value) lbl.value = name;
      } else if (entityPickerContext === 'widget') {
        pendingWidgetEntity = { entityId: eid, friendlyName: name, domain: domain };
        widgetEntityDisplay.value = `${name} (${eid})`;
        widgetLabelInput.value = name;
        const found = availableEntities.find(e => e.entity_id === eid);
        widgetUnitInput.value = (found && found.attributes && found.attributes.unit_of_measurement) || '';
        widgetConfigModal.classList.add('open');
      } else if (entityPickerContext === 'action') {
        selectedActionEntity = eid;
        actionEntityDisplay.value = `${name} (${eid})`;
        renderActionServiceOptions(domain, eid);
      } else if (entityPickerContext === 'section_device') {
        addDeviceToSection(eid);
      }
    });
  });
}

// --- Action Config Modal ---
function setupActionConfig() {
  btnCloseActionConfig.addEventListener('click', () => actionConfigModal.classList.remove('open'));
  actionConfigModal.addEventListener('click', e => {
    if (e.target === actionConfigModal) actionConfigModal.classList.remove('open');
  });

  btnActionChooseEntity.addEventListener('click', () => {
    openEntityPicker('action', 'Оберіть пристрій для дії');
  });

  btnSaveConfiguredAction.addEventListener('click', () => {
    if (!selectedActionEntity && actionEntityDisplay.value) {
      const m = actionEntityDisplay.value.match(/\(([a-z0-9_]+\.[a-z0-9_]+)\)\s*$/i);
      if (m) selectedActionEntity = m[1];
    }
    if (!selectedActionEntity) {
      showToast(t('toast_select_entity_first'), true);
      return;
    }
    let service = actionServiceSelect.value;
    let domain = 'homeassistant';
    if (service.includes('.')) {
      const parts = service.split('.');
      domain = parts[0];
      service = parts[1];
    } else if (selectedActionEntity && selectedActionEntity.includes('.')) {
      domain = selectedActionEntity.split('.')[0];
    }
    const label = actionLabelInput.value.trim() || 'Дія';
    const sec = config.menu[currentSectionKey];
    if (!sec.actions) sec.actions = [];
    const actId = `act_${Date.now()}_${Math.floor(Math.random() * 1000)}`;
    sec.actions.push({
      id: actId,
      label: label,
      domain: domain,
      service: service,
      entity_id: selectedActionEntity,
      target: { entity_id: selectedActionEntity }
    });
    renderActionsList(sec.actions);
    updatePreview();
    actionConfigModal.classList.remove('open');
    showToast(t('toast_action_added'));
  });
}

function renderActionServiceOptions(domain, entityId) {
  const services = UNIVERSAL_SERVICES(entityId);

  // Append automations / scripts as executable actions
  availableEntities.filter(e => e.domain === 'automation' || e.domain === 'script').forEach(e => {
    services.push({
      service: e.domain === 'automation' ? 'automation.trigger' : 'script.turn_on',
      label: `⚡ ${e.friendly_name} (${e.domain === 'automation' ? 'автоматизація' : 'скрипт'})`
    });
  });

  actionServiceSelect.innerHTML = services.map(s =>
    `<option value="${s.service}">${s.label}</option>`
  ).join('');

  // Auto-fill button label with first suggestion
  if (services.length) actionLabelInput.value = services[0].label;
}

// --- Sections Pills ---
function renderSectionsPills() {
  if (!config || !config.menu) return;
  sectionsList.innerHTML = '';
  const keys = Object.keys(config.menu);
  const otherKeys = keys.filter(k => k !== 'main');
  const orderedKeys = config.menu['main'] ? ['main', ...otherKeys] : keys;
  orderedKeys.forEach(key => {
    const sec = config.menu[key];
    const pill = document.createElement('div');
    pill.className = `section-pill ${key === currentSectionKey ? 'active' : ''}`;
    const cleanTitle = stripLeadingEmoji(sec.title || key);
    pill.innerHTML = `<span>${sec.icon || '📁'}</span> <span>${cleanTitle}</span>`;
    pill.addEventListener('click', () => {
      currentSectionKey = key;
      renderSectionsPills();
      loadSectionIntoEditor(key);
      updatePreview();
    });
    sectionsList.appendChild(pill);
  });
}


// --- Section editor ---
let selectedButtonTarget = null;
let activeIconTarget = 'section';
let editingItemIdx = null; // null | number (index being edited)
let addingItemType = null; // null | 'text' | 'entity'

function ensureSectionItems(sec) {
  if (!sec) return [];
  if (!Array.isArray(sec.items)) {
    sec.items = [];
    if (Array.isArray(sec.texts)) {
      sec.texts.forEach(t => {
        if (t && typeof t === 'object') {
          sec.items.push({
            type: 'text',
            icon: t.icon || '',
            text: t.text || '',
            is_heading: Boolean(t.is_heading),
            show_indent: t.show_indent !== undefined ? Boolean(t.show_indent) : (t.indent !== undefined ? Boolean(t.indent) : true)
          });
        }
      });
    }
    if (Array.isArray(sec.entities)) {
      sec.entities.forEach(e => {
        if (e && typeof e === 'object') {
          sec.items.push({
            type: 'entity',
            icon: e.icon || '',
            label: e.label || '',
            entity_id: e.entity_id || '',
            show_indent: e.show_indent !== undefined ? Boolean(e.show_indent) : (e.indent !== undefined ? Boolean(e.indent) : true),
            unit: e.unit || ''
          });
        }
      });
    }
  }
  return sec.items;
}

function syncSectionLegacyCollections(sec) {
  if (!sec || !Array.isArray(sec.items)) return;
  sec.texts = sec.items
    .filter(it => it.type === 'text')
    .map(it => ({
      icon: it.icon || '',
      text: it.text || '',
      is_heading: Boolean(it.is_heading),
      indent: it.show_indent !== false,
      show_indent: it.show_indent !== false
    }));
  sec.entities = sec.items
    .filter(it => it.type === 'entity')
    .map(it => ({
      entity_id: it.entity_id,
      label: it.label || '',
      icon: it.icon || '',
      indent: it.show_indent !== false,
      show_indent: it.show_indent !== false,
      unit: it.unit || ''
    }));
}

function createInlineEditRow(initialData = {}, onSave, onCancel) {
  const row = document.createElement('div');
  row.className = 'add-text-inline-row';
  row.id = 'inline-edit-row';

  const initialIcon = escapeHtml(initialData.icon || '');
  const initialText = escapeHtml(initialData.text || '');
  let isHeading = Boolean(initialData.is_heading);
  let showIndent = initialData.show_indent !== undefined ? Boolean(initialData.show_indent) : (initialData.indent !== undefined ? Boolean(initialData.indent) : true);
  const displayIcon = initialIcon ? initialIcon : `<span class="icon-empty-slot" title="${t('empty_icon_title')}">∅</span>`;

  row.innerHTML = `
    <div class="icon-input-wrap">
      <button type="button" class="btn-icon-select btn-inline-icon-picker" title="${t('btn_inline_icon_title')}">
        <span class="item-icon-display">${displayIcon}</span>
      </button>
      <input type="hidden" class="item-icon-val" value="${initialIcon}">
    </div>
    <input type="text" class="form-control flex-1 item-input-val ${isHeading ? 'is-heading' : ''}" placeholder="${t('placeholder_text_input')}" value="${initialText}">
    <button type="button" class="btn-toggle-bold ${isHeading ? 'active' : ''}" title="${t('header_word')} (${t('badge_heading')})" aria-pressed="${isHeading}">
      <b>B</b>
    </button>
    <button type="button" class="btn-toggle-indent ${showIndent ? 'active' : ''}" title="${showIndent ? t('btn_toggle_indent_on') : t('btn_toggle_indent_off')}" aria-pressed="${showIndent}">
      ⇥
    </button>
    <div class="add-text-inline-row-actions">
      <button type="button" class="btn btn-primary btn-sm btn-inline-action btn-save-inline" title="${t('btn_save_item_title')}">💾</button>
      <button type="button" class="btn btn-ghost btn-sm btn-inline-action btn-cancel-inline" title="${t('btn_cancel_item_title')}">✕</button>
    </div>
  `;

  const btnPicker = row.querySelector('.btn-inline-icon-picker');
  btnPicker.addEventListener('click', () => {
    activeIconTarget = 'inline_text_item';
    iconPickerModal.classList.add('open');
    renderIconCategories();
    renderIconGrid();
  });

  const inputVal = row.querySelector('.item-input-val');
  const iconVal = row.querySelector('.item-icon-val');
  const btnBold = row.querySelector('.btn-toggle-bold');
  const btnIndent = row.querySelector('.btn-toggle-indent');
  const btnSave = row.querySelector('.btn-save-inline');
  const btnCancel = row.querySelector('.btn-cancel-inline');

  btnBold.addEventListener('click', () => {
    isHeading = !isHeading;
    btnBold.classList.toggle('active', isHeading);
    btnBold.setAttribute('aria-pressed', String(isHeading));
    btnBold.setAttribute('title', isHeading ? `${t('header_word')} (${t('badge_heading')})` : t('btn_bold_title'));
    inputVal.classList.toggle('is-heading', isHeading);
  });

  if (btnIndent) {
    btnIndent.addEventListener('click', () => {
      showIndent = !showIndent;
      btnIndent.classList.toggle('active', showIndent);
      btnIndent.setAttribute('aria-pressed', String(showIndent));
      btnIndent.setAttribute('title', showIndent ? t('btn_toggle_indent_on') : t('btn_toggle_indent_off'));
    });
  }

  btnSave.addEventListener('click', () => {
    const text = (inputVal.value || '').trim();
    if (!text) {
      showToast(t('toast_enter_text_first'), true);
      inputVal.focus();
      return;
    }
    onSave({
      type: 'text',
      icon: (iconVal.value || '').trim(),
      text: text,
      is_heading: Boolean(isHeading),
      show_indent: Boolean(showIndent)
    });
  });

  btnCancel.addEventListener('click', onCancel);

  inputVal.addEventListener('keydown', e => {
    if (e.key === 'Enter') {
      e.preventDefault();
      btnSave.click();
    } else if (e.key === 'Escape') {
      e.preventDefault();
      onCancel();
    }
  });

  inputVal.setAttribute('autocomplete', 'off');
  inputVal.setAttribute('spellcheck', 'false');

  row.focusInput = () => {
    requestAnimationFrame(() => {
      inputVal.focus({ preventScroll: true });
      if (document.activeElement !== inputVal) {
        setTimeout(() => inputVal.focus({ preventScroll: true }), 50);
      }
    });
  };

  inputVal.addEventListener('click', (e) => {
    e.stopPropagation();
    inputVal.focus();
  });

  inputVal.setAttribute('autocomplete', 'off');
  inputVal.setAttribute('spellcheck', 'false');

  row.focusInput = () => {
    requestAnimationFrame(() => {
      inputVal.focus({ preventScroll: true });
    });
  };

  return row;
}

function createInlineEntityRow(initialData = {}, onSave, onCancel) {
  const row = document.createElement('div');
  row.className = 'add-entity-inline-card';
  row.id = 'inline-entity-row';

  const initialIcon = escapeHtml(initialData.icon || '');
  const initialLabel = escapeHtml(initialData.label || '');
  const initialEntityId = initialData.entity_id || '';
  let showIndent = initialData.show_indent !== undefined ? Boolean(initialData.show_indent) : true;
  const displayIcon = initialIcon ? initialIcon : `<span class="icon-empty-slot" title="${t('empty_icon_title')}">∅</span>`;
  const initialFound = (initialEntityId && Array.isArray(availableEntities))
    ? availableEntities.find(e => e.entity_id === initialEntityId)
    : null;
  const initialDisplay = initialFound ? `${initialFound.friendly_name || initialEntityId} · ${initialEntityId}` : initialEntityId;

  row.innerHTML = `
    <!-- Row 1: Icon picker, Name input, Indent toggle, Save button, Cancel button -->
    <div class="add-entity-row-1">
      <div class="icon-input-wrap">
        <button type="button" class="btn-icon-select btn-inline-icon-picker" title="${t('btn_inline_icon_title')}">
          <span class="item-icon-display">${displayIcon}</span>
        </button>
        <input type="hidden" class="item-icon-val" value="${initialIcon}">
      </div>
      <input type="text" class="form-control flex-1 item-name-input" placeholder="${t('placeholder_entity_name')}" value="${initialLabel}">
      <button type="button" class="btn-toggle-indent ${showIndent ? 'active' : ''}" title="${showIndent ? t('btn_toggle_indent_on') : t('btn_toggle_indent_off')}" aria-pressed="${showIndent}">
        ⇥
      </button>
      <div class="add-inline-row-actions">
        <button type="button" class="btn btn-primary btn-sm btn-inline-action btn-save-inline" title="${t('btn_save_item_title')}">💾</button>
        <button type="button" class="btn btn-ghost btn-sm btn-inline-action btn-cancel-inline" title="${t('btn_cancel_item_title')}">✕</button>
      </div>
    </div>

    <!-- Row 2: Entity search / picker trigger -->
    <div class="add-entity-row-2">
      <input type="hidden" class="entity-select-val" value="${escapeHtml(initialEntityId)}">
      <button type="button" class="form-control flex-1 entity-select-display" title="${t('placeholder_entity_select')}">
        <span class="entity-select-text">${initialEntityId ? escapeHtml(initialDisplay) : t('placeholder_entity_select')}</span>
        <span class="entity-select-icon" aria-hidden="true">🔍</span>
      </button>
    </div>
  `;

  const btnPicker = row.querySelector('.btn-inline-icon-picker');
  btnPicker.addEventListener('click', () => {
    activeIconTarget = 'inline_entity_item';
    iconPickerModal.classList.add('open');
    renderIconCategories();
    renderIconGrid();
  });

  const entitySelect = row.querySelector('.entity-select-val');
  const entityDisplayBtn = row.querySelector('.entity-select-display');
  const entityDisplayText = row.querySelector('.entity-select-text');
  const nameInput = row.querySelector('.item-name-input');
  const iconInput = row.querySelector('.item-icon-val');
  const iconDisplay = row.querySelector('.item-icon-display');
  const btnIndent = row.querySelector('.btn-toggle-indent');
  const btnSave = row.querySelector('.btn-save-inline');
  const btnCancel = row.querySelector('.btn-cancel-inline');

  const setEntityValue = (eid) => {
    entitySelect.value = eid || '';
    const found = (eid && Array.isArray(availableEntities))
      ? availableEntities.find(e => e.entity_id === eid)
      : null;
    if (entityDisplayText) {
      entityDisplayText.textContent = eid
        ? `${found ? (found.friendly_name || eid) : eid} · ${eid}`
        : t('placeholder_entity_select');
    }
    if (eid) {
      if (nameInput && !nameInput.value.trim()) {
        nameInput.value = found ? (found.friendly_name || eid) : eid;
      }
      if (iconInput && !iconInput.value) {
        const domain = eid.split('.')[0];
        const defIcon = (typeof DOMAIN_ICONS !== 'undefined' && DOMAIN_ICONS[domain]) || '🔹';
        iconInput.value = defIcon;
        if (iconDisplay) iconDisplay.textContent = defIcon;
      }
    }
  };

  entityDisplayBtn.addEventListener('click', () => {
    openEntityPicker('inline_entity_item', t('entity_picker_title'));
  });

  entitySelect.addEventListener('change', () => setEntityValue(entitySelect.value));

  if (initialEntityId) setEntityValue(initialEntityId);

  btnIndent.addEventListener('click', () => {
    showIndent = !showIndent;
    btnIndent.classList.toggle('active', showIndent);
    btnIndent.setAttribute('aria-pressed', String(showIndent));
    btnIndent.setAttribute('title', showIndent ? t('btn_toggle_indent_on') : t('btn_toggle_indent_off'));
  });

  btnSave.addEventListener('click', () => {
    const selectedEid = (entitySelect.value || '').trim();
    if (!selectedEid) {
      showToast(t('toast_select_entity_first_validation'), true);
      entityDisplayBtn.focus();
      return;
    }
    const label = (nameInput.value || '').trim() || (availableEntities.find(e => e.entity_id === selectedEid)?.friendly_name) || selectedEid;
    const chosenIcon = (iconInput.value || '').trim();

    onSave({
      type: 'entity',
      entity_id: selectedEid,
      label: label,
      icon: chosenIcon,
      show_indent: Boolean(showIndent)
    });
  });

  btnCancel.addEventListener('click', onCancel);

  nameInput.addEventListener('keydown', e => {
    if (e.key === 'Enter') {
      e.preventDefault();
      btnSave.click();
    } else if (e.key === 'Escape') {
      e.preventDefault();
      onCancel();
    }
  });

  return row;
}

function loadSectionIntoEditor(key) {
  if (!config || !config.menu || !config.menu[key]) return;
  const sec = config.menu[key];
  if (editorSectionKey) editorSectionKey.textContent = key;
  if (editorSectionIcon) editorSectionIcon.textContent = sec.icon || '📁';
  if (editorSectionTitle) editorSectionTitle.textContent = stripLeadingEmoji(sec.title || '') || key;
  if (secTitle) secTitle.value = stripLeadingEmoji(sec.title || '');
  if (secIcon) secIcon.value = sec.icon || '📁';
  if (secIconDisplay) secIconDisplay.textContent = sec.icon || '📁';

  const mainBadge = document.getElementById('main-badge-wrap');
  const allKeys = Object.keys(config.menu);
  const isMain = key === 'main' || key === allKeys[0];
  if (mainBadge) mainBadge.style.display = isMain ? 'block' : 'none';

  const secNoteInput = document.getElementById('sec-note');
  if (secNoteInput) secNoteInput.value = sec.note || sec.description || '';

  const roles = sec.roles || ['admin', 'member', 'guest'];
  roleAdmin.checked = roles.includes('admin');
  roleMember.checked = roles.includes('member');
  roleGuest.checked = roles.includes('guest');

  ensureSectionItems(sec);
  syncSectionLegacyCollections(sec);

  renderMenuChecklist(sec.sections || sec.menu_sections || []);

  editingItemIdx = null;
  addingItemType = null;
  renderSectionElements(sec.items);

  $('btn-delete-section').style.display = isMain ? 'none' : 'inline-flex';
}

function renderSectionElements(items) {
  const container = $('section-texts-list');
  if (!container) return;
  container.innerHTML = '';

  const sec = config && config.menu ? config.menu[currentSectionKey] : null;
  if (!sec) return;
  ensureSectionItems(sec);

  sec.items.forEach((item, idx) => {
    try {
    if (editingItemIdx === idx) {
      if (item.type === 'entity') {
        const editRow = createInlineEntityRow(item, (updatedData) => {
          sec.items[idx] = updatedData;
          syncSectionLegacyCollections(sec);
          editingItemIdx = null;
          renderSectionElements(sec.items);
          updatePreview();
          showToast(t('toast_entity_updated_success'));
        }, () => {
          editingItemIdx = null;
          renderSectionElements(sec.items);
        });
        container.appendChild(editRow);
      } else {
        const editRow = createInlineEditRow(item, (updatedData) => {
          sec.items[idx] = updatedData;
          syncSectionLegacyCollections(sec);
          editingItemIdx = null;
          renderSectionElements(sec.items);
          updatePreview();
          showToast(t('toast_text_updated'));
        }, () => {
          editingItemIdx = null;
          renderSectionElements(sec.items);
        });
        container.appendChild(editRow);
      }
      return;
    }

    const el = document.createElement('div');
    el.className = 'section-text-item';
    el.draggable = true;
    el.dataset.idx = String(idx);

    if (item.type === 'entity') {
      const eid = item.entity_id || '';
      const found = eid ? availableEntities.find(e => e.entity_id === eid) : null;
      const stateVal = found ? (found.state || '—') : '—';
      const rawIcon = (item.icon || (found ? DOMAIN_ICONS[eid.split('.')[0]] : '') || '🔹').trim();
      const safeIcon = escapeHtml(rawIcon);
      const safeLabel = escapeHtml(item.label || eid);
      const iconSpan = safeIcon ? `<span class="section-text-item-icon">${safeIcon}</span>` : '';
      const indentBadge = item.show_indent !== false
        ? `<span class="badge-text-type indent" title="${t('btn_toggle_indent_on')}">⇥ ${t('badge_indent')}</span>`
        : `<span class="badge-text-type" title="${t('btn_toggle_indent_off')}">${t('badge_no_indent')}</span>`;

      const isLocked = Boolean(item.locked);
      const lockTitle = isLocked ? t('btn_unlock') : t('btn_lock');
      const lockIcon = isLocked ? '🔒' : '🔓';
      const lockClass = isLocked ? 'btn-lock-elem-item is-locked' : 'btn-lock-elem-item';
      if (isLocked) el.classList.add('is-locked');
      el.draggable = !isLocked;

      el.innerHTML = `
        <div class="item-drag-handle" title="Перетягніть для зміни порядку" aria-label="Перетягнути">⠿</div>
        <div class="section-text-item-main">
          ${iconSpan}
          <span class="section-text-item-content"><b>${safeLabel}</b>: <code>${escapeHtml(stateVal)}</code></span>
          <span class="badge-text-type entity">${t('badge_entity')}</span>
          ${indentBadge}
        </div>
        <div class="section-text-item-actions">
          <button type="button" class="btn-icon-action btn-edit-elem-item" title="Редагувати" data-idx="${idx}" ${isLocked ? 'disabled' : ''}>✏️</button>
          <button type="button" class="btn-icon-action btn-remove-elem-item" title="${t('btn_delete')}" data-idx="${idx}" ${isLocked ? 'disabled' : ''}>🗑️</button>
          <button type="button" class="btn-icon-action ${lockClass}" title="${lockTitle}" data-idx="${idx}">${lockIcon}</button>
        </div>
      `;

      el.querySelector('.btn-lock-elem-item').addEventListener('click', (e) => {
        e.stopPropagation();
        item.locked = !item.locked;
        syncSectionLegacyCollections(sec);
        renderSectionElements(sec.items);
        showToast(item.locked ? t('toast_item_locked') : t('toast_item_unlocked'));
      });

      el.querySelector('.btn-edit-elem-item').addEventListener('click', () => {
        if (item.locked) {
          showToast(t('toast_item_is_locked'), true);
          return;
        }
        editingItemIdx = idx;
        addingItemType = null;
        renderSectionElements(sec.items);
      });

      el.querySelector('.btn-remove-elem-item').addEventListener('click', async () => {
        if (item.locked) {
          showToast(t('toast_item_is_locked'), true);
          return;
        }
        const confirmed = await showCustomConfirm(
          t('confirm_dialog_title'),
          t('confirm_delete_entity_item_unified'),
          t('btn_delete'),
          true
        );
        if (!confirmed) return;
        sec.items.splice(idx, 1);
        syncSectionLegacyCollections(sec);
        if (editingItemIdx === idx) editingItemIdx = null;
        renderSectionElements(sec.items);
        updatePreview();
        showToast(t('toast_item_deleted'));
      });
    } else if (item.type === 'divider' || item.type === 'spacer') {
      // Divider / Horizontal spacer item
      const style = item.style || 'line';
      let styleLabel = t('divider_style_line') || 'Суцільна лінія';
      let stylePreview = '────────────────────────';
      if (style === 'space') {
        styleLabel = t('divider_style_space') || 'Порожній відступ';
        stylePreview = '␣ (порожній відступ)';
      } else if (style === 'dashed') {
        styleLabel = t('divider_style_dashed') || 'Пунктирна лінія';
        stylePreview = '┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄';
      }

      const isLocked = Boolean(item.locked);
      const lockTitle = isLocked ? t('btn_unlock') : t('btn_lock');
      const lockIcon = isLocked ? '🔒' : '🔓';
      const lockClass = isLocked ? 'btn-lock-elem-item is-locked' : 'btn-lock-elem-item';
      if (isLocked) el.classList.add('is-locked');
      el.draggable = !isLocked;

      el.innerHTML = `
        <div class="item-drag-handle" title="Перетягніть для зміни порядку" aria-label="Перетягнути">⠿</div>
        <div class="section-text-item-main section-divider-item-main">
          <span class="section-divider-preview"><code>${escapeHtml(stylePreview)}</code></span>
          <span class="badge-text-type divider">${t('badge_divider')}</span>
          <span class="badge-text-type">${escapeHtml(styleLabel)}</span>
        </div>
        <div class="section-text-item-actions">
          <button type="button" class="btn-icon-action btn-cycle-divider-style" title="${t('btn_change_divider_style')}" data-idx="${idx}" ${isLocked ? 'disabled' : ''}>🔄</button>
          <button type="button" class="btn-icon-action btn-remove-elem-item" title="${t('btn_delete')}" data-idx="${idx}" ${isLocked ? 'disabled' : ''}>🗑️</button>
          <button type="button" class="btn-icon-action ${lockClass}" title="${lockTitle}" data-idx="${idx}">${lockIcon}</button>
        </div>
      `;

      el.querySelector('.btn-lock-elem-item').addEventListener('click', (e) => {
        e.stopPropagation();
        item.locked = !item.locked;
        syncSectionLegacyCollections(sec);
        renderSectionElements(sec.items);
        showToast(item.locked ? t('toast_item_locked') : t('toast_item_unlocked'));
      });

      el.querySelector('.btn-cycle-divider-style').addEventListener('click', () => {
        if (item.locked) {
          showToast(t('toast_item_is_locked'), true);
          return;
        }
        const currentStyle = item.style || 'line';
        const styles = ['line', 'space', 'dashed'];
        const nextStyle = styles[(styles.indexOf(currentStyle) + 1) % styles.length];
        item.style = nextStyle;
        syncSectionLegacyCollections(sec);
        renderSectionElements(sec.items);
        updatePreview();
      });

      el.querySelector('.btn-remove-elem-item').addEventListener('click', async () => {
        if (item.locked) {
          showToast(t('toast_item_is_locked'), true);
          return;
        }
        const confirmed = await showCustomConfirm(
          t('confirm_dialog_title'),
          t('confirm_delete_divider_item'),
          t('btn_delete'),
          true
        );
        if (!confirmed) return;
        sec.items.splice(idx, 1);
        syncSectionLegacyCollections(sec);
        if (editingItemIdx === idx) editingItemIdx = null;
        renderSectionElements(sec.items);
        updatePreview();
        showToast(t('toast_item_deleted'));
      });
    } else {
      // Text item
      const isHeading = Boolean(item.is_heading);
      const badgeHtml = isHeading
        ? `<span class="badge-text-type heading">${t('badge_heading')}</span>`
        : `<span class="badge-text-type">${t('header_word') === 'Заголовок' ? 'Текст' : 'Text'}</span>`;
      const contentClass = isHeading
        ? 'section-text-item-content section-text-item-heading'
        : 'section-text-item-content';

      const rawIcon = (item.icon || '').trim();
      const safeIcon = escapeHtml(rawIcon);
      const safeText = escapeHtml(item.text || '');
      const iconSpan = safeIcon ? `<span class="section-text-item-icon">${safeIcon}</span>` : '';
      const indentBadge = item.show_indent !== false
        ? `<span class="badge-text-type indent" title="${t('btn_toggle_indent_on')}">⇥ ${t('badge_indent')}</span>`
        : `<span class="badge-text-type" title="${t('btn_toggle_indent_off')}">${t('badge_no_indent')}</span>`;

      const isLocked = Boolean(item.locked);
      const lockTitle = isLocked ? t('btn_unlock') : t('btn_lock');
      const lockIcon = isLocked ? '🔒' : '🔓';
      const lockClass = isLocked ? 'btn-lock-elem-item is-locked' : 'btn-lock-elem-item';
      if (isLocked) el.classList.add('is-locked');
      el.draggable = !isLocked;

      el.innerHTML = `
        <div class="item-drag-handle" title="Перетягніть для зміни порядку" aria-label="Перетягнути">⠿</div>
        <div class="section-text-item-main">
          ${iconSpan}
          <span class="${contentClass}">${safeText}</span>
          ${badgeHtml}
          ${indentBadge}
        </div>
        <div class="section-text-item-actions">
          <button type="button" class="btn-icon-action btn-edit-elem-item" title="Редагувати" data-idx="${idx}" ${isLocked ? 'disabled' : ''}>✏️</button>
          <button type="button" class="btn-icon-action btn-remove-elem-item" title="${t('btn_delete')}" data-idx="${idx}" ${isLocked ? 'disabled' : ''}>🗑️</button>
          <button type="button" class="btn-icon-action ${lockClass}" title="${lockTitle}" data-idx="${idx}">${lockIcon}</button>
        </div>
      `;

      el.querySelector('.btn-lock-elem-item').addEventListener('click', (e) => {
        e.stopPropagation();
        item.locked = !item.locked;
        syncSectionLegacyCollections(sec);
        renderSectionElements(sec.items);
        showToast(item.locked ? t('toast_item_locked') : t('toast_item_unlocked'));
      });

      el.querySelector('.btn-edit-elem-item').addEventListener('click', () => {
        if (item.locked) {
          showToast(t('toast_item_is_locked'), true);
          return;
        }
        editingItemIdx = idx;
        addingItemType = null;
        renderSectionElements(sec.items);
      });

      el.querySelector('.btn-remove-elem-item').addEventListener('click', async () => {
        if (item.locked) {
          showToast(t('toast_item_is_locked'), true);
          return;
        }
        const confirmed = await showCustomConfirm(
          t('confirm_dialog_title'),
          t('confirm_delete_text_item'),
          t('btn_delete'),
          true
        );
        if (!confirmed) return;
        sec.items.splice(idx, 1);
        syncSectionLegacyCollections(sec);
        if (editingItemIdx === idx) editingItemIdx = null;
        renderSectionElements(sec.items);
        updatePreview();
        showToast(t('toast_item_deleted'));
      });
    }

    
    // Drag and Drop reordering
    el.addEventListener('dragstart', (e) => {
      e.dataTransfer.setData('text/plain', String(idx));
      e.dataTransfer.effectAllowed = 'move';
      el.classList.add('is-dragging');
    });

    el.addEventListener('dragend', () => {
      el.classList.remove('is-dragging');
      container.querySelectorAll('.section-text-item').forEach(node => {
        node.classList.remove('drag-over-top', 'drag-over-bottom');
      });
    });

    el.addEventListener('dragover', (e) => {
      e.preventDefault();
      e.dataTransfer.dropEffect = 'move';
      const rect = el.getBoundingClientRect();
      const mid = rect.top + rect.height / 2;
      if (e.clientY < mid) {
        el.classList.add('drag-over-top');
        el.classList.remove('drag-over-bottom');
      } else {
        el.classList.add('drag-over-bottom');
        el.classList.remove('drag-over-top');
      }
    });

    el.addEventListener('dragleave', () => {
      el.classList.remove('drag-over-top', 'drag-over-bottom');
    });

    el.addEventListener('drop', (e) => {
      e.preventDefault();
      el.classList.remove('drag-over-top', 'drag-over-bottom');
      const fromIdxStr = e.dataTransfer.getData('text/plain');
      if (fromIdxStr === '') return;
      const fromIdx = parseInt(fromIdxStr, 10);
      let toIdx = idx;
      const rect = el.getBoundingClientRect();
      if (e.clientY >= rect.top + rect.height / 2) {
        toIdx = idx + 1;
      }
      if (fromIdx === toIdx || fromIdx === toIdx - 1) return;
      const [movedItem] = sec.items.splice(fromIdx, 1);
      const targetIdx = fromIdx < toIdx ? toIdx - 1 : toIdx;
      sec.items.splice(targetIdx, 0, movedItem);
      syncSectionLegacyCollections(sec);
      renderSectionElements(sec.items);
      updatePreview();
      showToast('Порядок елементів оновлено');
    });

    container.appendChild(el);
    } catch (err) {
      console.error('Telegram Dashboard: failed to render section element', idx, err);
    }
  });

  // If adding a new element at the bottom (under already added elements, above the 3 add buttons)
  if (addingItemType === 'text') {
    const newRow = createInlineEditRow({ icon: '', text: '', is_heading: false }, (newData) => {
      sec.items.push(newData);
      syncSectionLegacyCollections(sec);
      addingItemType = null;
      renderSectionElements(sec.items);
      updatePreview();
      showToast(t('toast_text_added'));
    }, () => {
      addingItemType = null;
      renderSectionElements(sec.items);
    });
    container.appendChild(newRow);
  } else if (addingItemType === 'entity') {
    const newRow = createInlineEntityRow({ icon: '', label: '', entity_id: '', show_indent: true }, (newData) => {
      sec.items.push(newData);
      syncSectionLegacyCollections(sec);
      addingItemType = null;
      renderSectionElements(sec.items);
      updatePreview();
      showToast(t('toast_entity_added_success'));
    }, () => {
      addingItemType = null;
      renderSectionElements(sec.items);
    });
    container.appendChild(newRow);
  }
}

// Backward compatibility alias
function renderSectionTexts(texts) {
  const sec = config && config.menu ? config.menu[currentSectionKey] : null;
  if (sec) {
    ensureSectionItems(sec);
    renderSectionElements(sec.items);
  }
}

function renderMenuChecklist(selectedKeys) {
  const menuSectionsChecklist = document.getElementById('menu-sections-checklist');
  if (!menuSectionsChecklist || !config || !config.menu) return;

  const sec = config.menu[currentSectionKey];
  if (!sec) return;

  const validMenuKeys = Object.keys(config.menu).filter(k => k !== currentSectionKey);
  
  // Maintain stable list ordering: preserve existing order, only arrows move positions
  let fullOrder = Array.isArray(sec.sections_order) ? [...sec.sections_order] : [];
  fullOrder = fullOrder.filter(k => validMenuKeys.includes(k));
  
  // If no sections_order stored yet, start with current selected followed by unselected
  if (fullOrder.length === 0) {
    const currentSel = Array.isArray(selectedKeys) ? [...selectedKeys].filter(k => validMenuKeys.includes(k)) : [];
    const unsel = validMenuKeys.filter(k => !currentSel.includes(k));
    fullOrder = [...currentSel, ...unsel];
  } else {
    validMenuKeys.forEach(k => {
      if (!fullOrder.includes(k)) fullOrder.push(k);
    });
  }
  sec.sections_order = fullOrder;

  const currentSelected = Array.isArray(selectedKeys) ? [...selectedKeys].filter(k => validMenuKeys.includes(k)) : [];

  menuSectionsChecklist.innerHTML = '';
  menuSectionsChecklist.className = 'menu-sections-order-list';

  fullOrder.forEach((k, idx) => {
    const s = config.menu[k] || {};
    const cleanTitle = stripLeadingEmoji(s.title || k);
    const isChecked = currentSelected.includes(k);
    const itemEl = document.createElement('div');
    itemEl.className = `menu-section-order-item ${isChecked ? 'is-checked' : ''}`;
    itemEl.dataset.key = k;

    const canMoveUp = idx > 0;
    const canMoveDown = idx < fullOrder.length - 1;

    const isLocked = Boolean(sec.locked_nav_sections && sec.locked_nav_sections[k]);
    itemEl.className = `menu-section-order-item ${isChecked ? 'is-checked' : ''} ${isLocked ? 'is-locked' : ''}`;

    itemEl.innerHTML = `
      <label class="menu-section-label">
        <input type="checkbox" value="${k}" ${isChecked ? 'checked' : ''} ${isLocked ? 'disabled' : ''}>
        <span class="menu-section-icon">${s.icon || '📁'}</span>
        <span class="menu-section-name">${escapeHtml(cleanTitle)}</span>
      </label>
      <div class="menu-section-actions">
        <button type="button" class="btn-lock-elem-item btn-lock-nav-item ${isLocked ? 'is-locked' : ''}" title="${isLocked ? (t('toast_item_unlocked') || 'Розблокувати') : (t('toast_item_locked') || 'Заблокувати')}" data-key="${k}">
          ${isLocked ? '🔒' : '🔓'}
        </button>
        <div class="menu-section-order-controls">
          <button type="button" class="btn-order-arrow btn-order-up" title="${t('btn_move_up') || 'Вгору'}" ${canMoveUp && !isLocked ? '' : 'disabled style="opacity: 0.2; pointer-events: none;"'}>▲</button>
          <button type="button" class="btn-order-arrow btn-order-down" title="${t('btn_move_down') || 'Вниз'}" ${canMoveDown && !isLocked ? '' : 'disabled style="opacity: 0.2; pointer-events: none;"'}>▼</button>
        </div>
      </div>
    `;

    const btnLock = itemEl.querySelector('.btn-lock-nav-item');
    if (btnLock) {
      btnLock.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        sec.locked_nav_sections = sec.locked_nav_sections || {};
        sec.locked_nav_sections[k] = !sec.locked_nav_sections[k];
        showToast(sec.locked_nav_sections[k] ? t('toast_item_locked') : t('toast_item_unlocked'));
        renderMenuChecklist(sec.sections);
        syncCurrentSectionFromForm();
      });
    }

    const cb = itemEl.querySelector('input[type="checkbox"]');
    cb.addEventListener('change', () => {
      if (sec.locked_nav_sections && sec.locked_nav_sections[k]) {
        cb.checked = !cb.checked;
        showToast(t('toast_item_is_locked'), true);
        return;
      }
      // Toggle checked state without changing fullOrder position!
      let updatedSelected = Array.isArray(sec.sections) ? [...sec.sections] : [];
      if (cb.checked) {
        if (!updatedSelected.includes(k)) updatedSelected.push(k);
      } else {
        updatedSelected = updatedSelected.filter(itemKey => itemKey !== k);
      }
      // Keep selected items in the order defined by fullOrder
      updatedSelected = fullOrder.filter(itemKey => updatedSelected.includes(itemKey));
      sec.sections = updatedSelected;
      renderMenuChecklist(sec.sections);
      syncCurrentSectionFromForm();
      updatePreview();
    });

    const btnUp = itemEl.querySelector('.btn-order-up');
    btnUp.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      if (!canMoveUp || (sec.locked_nav_sections && sec.locked_nav_sections[k])) return;
      const temp = fullOrder[idx - 1];
      fullOrder[idx - 1] = fullOrder[idx];
      fullOrder[idx] = temp;
      sec.sections_order = fullOrder;
      
      let updatedSelected = Array.isArray(sec.sections) ? [...sec.sections] : [];
      sec.sections = fullOrder.filter(itemKey => updatedSelected.includes(itemKey));
      renderMenuChecklist(sec.sections);
      syncCurrentSectionFromForm();
      updatePreview();
    });

    const btnDown = itemEl.querySelector('.btn-order-down');
    btnDown.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      if (!canMoveDown || (sec.locked_nav_sections && sec.locked_nav_sections[k])) return;
      const temp = fullOrder[idx + 1];
      fullOrder[idx + 1] = fullOrder[idx];
      fullOrder[idx] = temp;
      sec.sections_order = fullOrder;
      
      let updatedSelected = Array.isArray(sec.sections) ? [...sec.sections] : [];
      sec.sections = fullOrder.filter(itemKey => updatedSelected.includes(itemKey));
      renderMenuChecklist(sec.sections);
      syncCurrentSectionFromForm();
      updatePreview();
    });

    menuSectionsChecklist.appendChild(itemEl);
  });
}

// --- Entities (Показники: Назва - Дані) ---
function renderEntitiesList(entities) {
  const container = document.getElementById('entities-list');
  if (!container) return;
  if (!entities || !entities.length) {
    container.innerHTML = '<p class="field-hint">Ентіті ще не додані. Натисніть «+ Додати ентіті».</p>';
    return;
  }

  container.innerHTML = entities.map((ent, index) => {
    const eid = ent.entity_id;
    const found = availableEntities.find(e => e.entity_id === eid);
    const currentVal = found ? `${found.state} ${ent.unit || (found.attributes && found.attributes.unit_of_measurement) || ''}`.trim() : '—';

    return `
      <div class="item-row" data-index="${index}">
        <div class="item-info" style="flex: 1;">
          <div style="display: flex; gap: 10px; align-items: center; width: 100%;">
            <input type="text" class="form-control form-control-sm ent-label-input" data-index="${index}" value="${escapeHtml(ent.label || '')}" placeholder="Назва показника" style="max-width: 200px; font-weight: 600;">
            <div style="font-size: 13px; color: var(--text-muted); flex: 1;">
              <code>${eid}</code>
            </div>
            <div style="font-weight: bold; color: var(--accent); padding: 0 10px; background: rgba(56, 189, 248, 0.1); border-radius: 4px;">
              ${currentVal}
            </div>
          </div>
        </div>
        <button type="button" class="btn btn-danger btn-sm btn-remove-entity" data-index="${index}">✕</button>
      </div>
    `;
  }).join('');

  container.querySelectorAll('.ent-label-input').forEach(input => {
    input.addEventListener('input', (e) => {
      const idx = parseInt(e.target.dataset.index, 10);
      const sec = config.menu[currentSectionKey];
      if (sec && sec.entities && sec.entities[idx]) {
        sec.entities[idx].label = e.target.value;
        updatePreview();
      }
    });
  });

  container.querySelectorAll('.btn-remove-entity').forEach(btn => {
    btn.addEventListener('click', async () => {
      const confirmed = await showCustomConfirm(
        t('confirm_dialog_title'),
        t('confirm_delete_entity'),
        t('btn_delete'),
        true
      );
      if (!confirmed) return;
      const idx = parseInt(btn.dataset.index, 10);
      const sec = config.menu[currentSectionKey];
      if (sec && sec.entities) {
        sec.entities.splice(idx, 1);
        renderEntitiesList(sec.entities);
        updatePreview();
      }
    });
  });
}

// --- Buttons (Кнопки дій / керування) ---
function renderButtonsList(buttons) {
  const container = document.getElementById('buttons-list');
  if (!container) return;
  if (!buttons || !buttons.length) {
    container.innerHTML = '<p class="field-hint">Кнопки ще не додані. Натисніть «+ Додати кнопку».</p>';
    return;
  }

  container.innerHTML = buttons.map((btn, index) => {
    const eid = btn.entity_id || '';
    const found = availableEntities.find(e => e.entity_id === eid);
    const stateStr = found ? (found.state || '') : '';
    let stateBadge = '';
    if (stateStr.toLowerCase() in { 'on': 1, 'open': 1, 'true': 1 }) {
      stateBadge = '<span class="badge-ok">🟢 Увімк</span>';
    } else if (stateStr.toLowerCase() in { 'off': 1, 'closed': 1, 'false': 1 }) {
      stateBadge = '<span class="badge-warn">🔴 Вимк</span>';
    } else if (stateStr) {
      stateBadge = `<span class="badge-ok">${escapeHtml(stateStr)}</span>`;
    }

    return `
      <div class="item-row" data-index="${index}">
        <div class="item-info" style="flex: 1;">
          <div style="display: flex; gap: 10px; align-items: center; width: 100%;">
            <input type="text" class="form-control form-control-sm btn-label-input" data-index="${index}" value="${escapeHtml(btn.label || '')}" placeholder="Текст на кнопці" style="max-width: 220px; font-weight: 600;">
            <div style="font-size: 13px; color: var(--text-muted); flex: 1;">
              <code>${eid}</code>
            </div>
            ${stateBadge}
          </div>
        </div>
        <button type="button" class="btn btn-danger btn-sm btn-remove-button" data-index="${index}">✕</button>
      </div>
    `;
  }).join('');

  container.querySelectorAll('.btn-label-input').forEach(input => {
    input.addEventListener('input', (e) => {
      const idx = parseInt(e.target.dataset.index, 10);
      const sec = config.menu[currentSectionKey];
      if (sec && sec.buttons && sec.buttons[idx]) {
        sec.buttons[idx].label = e.target.value;
        updatePreview();
      }
    });
  });

  container.querySelectorAll('.btn-remove-button').forEach(btn => {
    btn.addEventListener('click', async () => {
      const confirmed = await showCustomConfirm(
        t('confirm_dialog_title'),
        t('confirm_delete_button'),
        t('btn_delete'),
        true
      );
      if (!confirmed) return;
      const idx = parseInt(btn.dataset.index, 10);
      const sec = config.menu[currentSectionKey];
      if (sec && sec.buttons) {
        sec.buttons.splice(idx, 1);
        renderButtonsList(sec.buttons);
        updatePreview();
      }
    });
  });
}

// --- Section creation: title only, slug and icon guessed ---
$('btn-add-section').addEventListener('click', () => {
  openAddSectionModal();
});

$('btn-delete-section').addEventListener('click', async () => {
  if (currentSectionKey === 'main') {
    showToast(t('alert_cannot_delete_main'), true);
    return;
  }
  const secTitle = config.menu[currentSectionKey]?.title || currentSectionKey;
  const confirmed = await showCustomConfirm(
    t('confirm_dialog_title'),
    t('confirm_delete_section', { title: secTitle }),
    t('btn_delete'),
    true
  );
  if (!confirmed) return;
  delete config.menu[currentSectionKey];
  currentSectionKey = 'main';
  renderSectionsPills();
  loadSectionIntoEditor('main');
  updatePreview();
  showToast(t('toast_section_deleted'));
});

function syncCurrentSectionFromForm() {
  if (!config || !config.menu || !currentSectionKey) return;
  const sec = config.menu[currentSectionKey];
  if (!sec) return;

  if (secTitle) {
    sec.title = stripLeadingEmoji(secTitle.value.trim()) || 'Розділ';
  }
  if (secIcon) {
    sec.icon = secIcon.value.trim() || '📁';
  }

  const roles = [];
  if (roleAdmin?.checked) roles.push('admin');
  if (roleMember?.checked) roles.push('member');
  if (roleGuest?.checked) roles.push('guest');
  sec.roles = roles.length ? roles : ['admin'];

  const checked = [];
  document.getElementById('menu-sections-checklist')?.querySelectorAll('input:checked').forEach(i => checked.push(i.value));
  sec.sections = checked;
}

// --- Users ---
function renderUsers() {
  if (!config || !config.users) return;
  usersTbody.innerHTML = '';
  config.users.forEach(user => {
    const tr = document.createElement('tr');
    const isGuest = user.role === 'guest';
    const statusBadge = isGuest
      ? '<span class="badge-warn">Очікує підтвердження</span>'
      : '<span class="badge-ok">Підтверджено</span>';

    tr.innerHTML = `
      <td><code>${user.telegram_id}</code></td>
      <td><strong>${user.name || 'Користувач'}</strong></td>
      <td>
        <select class="form-control form-control-sm user-role-select" data-id="${user.telegram_id}" style="width: auto;">
          <option value="admin" ${user.role === 'admin' ? 'selected' : ''}>Адміністратор</option>
          <option value="member" ${user.role === 'member' ? 'selected' : ''}>Член родини</option>
          <option value="guest" ${user.role === 'guest' ? 'selected' : ''}>Гість</option>
        </select>
      </td>
      <td>${statusBadge}</td>
      <td style="white-space: nowrap;">
        ${isGuest ? `<button class="btn btn-primary btn-sm btn-approve-user" data-id="${user.telegram_id}" style="margin-right: 6px;">✅ ${t('btn_confirm_user')}</button>` : ''}
        <button class="btn btn-danger btn-sm btn-delete-user" data-id="${user.telegram_id}">${t('btn_delete_user')}</button>
      </td>
    `;
    usersTbody.appendChild(tr);
  });

  usersTbody.querySelectorAll('.user-role-select').forEach(sel => {
    sel.addEventListener('change', async () => {
      const id = parseInt(sel.dataset.id, 10);
      const user = config.users.find(u => u.telegram_id === id);
      if (user) {
        user.role = sel.value;
        await saveUser(user);
        renderUsers();
      }
    });
  });

  usersTbody.querySelectorAll('.btn-approve-user').forEach(btn => {
    btn.addEventListener('click', async () => {
      const id = parseInt(btn.dataset.id, 10);
      const user = config.users.find(u => u.telegram_id === id);
      if (user) {
        user.role = 'member';
        await saveUser(user);
        renderUsers();
        showToast(t('toast_user_confirmed', { name: user.name || id }));
      }
    });
  });

  usersTbody.querySelectorAll('.btn-delete-user').forEach(btn => {
    btn.addEventListener('click', async () => {
      const id = parseInt(btn.dataset.id, 10);
      const confirmed = await showCustomConfirm(
        t('confirm_dialog_title'),
        t('confirm_delete_user', { name: id }),
        t('btn_delete'),
        true
      );
      if (confirmed) await deleteUser(id);
    });
  });
}

async function saveUser(user) {
  try {
    await api('api/users', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(user)
    });
    showToast(t('toast_user_updated'));
  } catch (e) {
    showToast(`Помилка: ${e.message}`, true);
  }
}

async function deleteUser(id) {
  try {
    await api(`api/users/${id}`, { method: 'DELETE' });
    config.users = config.users.filter(u => u.telegram_id !== id);
    renderUsers();
    showToast(t('toast_user_deleted'));
  } catch (e) {
    showToast(t('toast_user_delete_error'), true);
  }
}

const btnAddUserEl = $('btn-add-user');
if (btnAddUserEl) {
  btnAddUserEl.addEventListener('click', async () => {
    const tid = prompt('Введіть Telegram ID користувача (число):');
    if (!tid || isNaN(tid)) return;
    const name = prompt("Введіть ім'я або юзернейм:") || 'Користувач';
    const role = prompt('Оберіть роль (admin, member, guest):', 'member') || 'member';
    const user = { telegram_id: parseInt(tid, 10), name, role };
    await saveUser(user);
    config.users.push(user);
    renderUsers();
  });
}

const btnSyncUsersEl = $('btn-sync-users');
if (btnSyncUsersEl) {
  btnSyncUsersEl.addEventListener('click', async () => {
    btnSyncUsersEl.disabled = true;
    try {
      const data = await api('api/users/sync', { method: 'POST' });
      if (data.users) {
        config.users = data.users;
        renderUsers();
        showToast(t('toast_users_synced', { count: data.discovered || 0 }));
      }
    } catch (e) {
      showToast(t('toast_sync_error', { err: e.message }), true);
    } finally {
      btnSyncUsersEl.disabled = false;
    }
  });
}

// --- Settings ---
function loadSettings() {
  if (!config) return;
  const currentLang = config.language || (window.I18N ? window.I18N.getLanguage() : 'en');
  if ($('setting-language')) $('setting-language').value = currentLang;
  if (window.I18N) window.I18N.setLanguage(currentLang, false);

  $('setting-bot-token').value = config.telegram_token || '';
  if ($('setting-theme')) $('setting-theme').value = config.theme || 'cards';
  $('setting-default-role').value = config.default_role || 'guest';
  if (config.telegram_msg_width) {
    localStorage.setItem('preview_slider_msg_width', String(config.telegram_msg_width));
  }
}

function applySettings() {
  if (!config) return;
  if ($('setting-language')) {
    config.language = $('setting-language').value;
  }
  config.telegram_token = $('setting-bot-token').value.trim();
  if ($('setting-theme')) config.theme = $('setting-theme').value;
  else config.theme = config.theme || 'cards';
  config.default_role = $('setting-default-role').value;
  const msgWVal = $('setting-tg-msg-width') ? parseInt($('setting-tg-msg-width').value, 10) : 100;
  config.telegram_msg_width = msgWVal || 100;
}

// --- Save config ---
$('btn-save').addEventListener('click', async () => {
  syncCurrentSectionFromForm();
  applySettings();
  try {
    const res = await fetch('api/config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config)
    });
    if (res.ok) {
      showToast(t('toast_all_saved'));
      updatePreview();
    } else {
      const err = await res.json();
      showToast(`Помилка: ${err.error}`, true);
    }
  } catch (e) {
    showToast(t('toast_save_error'), true);
  }
});

// --- Realtime Preview ---
async function updatePreview() {
  if (!config || !config.menu) return;
  try {
    const res = await fetch('api/preview', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        menu: config.menu,
        section_key: currentSectionKey,
        role: currentSimulatedRole
      })
    });
    if (res.ok) {
      const data = await res.json();
      previewText.innerHTML = data.html || 'Немає даних для показу';
      renderTelegramKeyboard(data.keyboard || []);
      const bubble = document.querySelector('.tg-message-bubble');
      if (bubble) {
        const savedMsgW = localStorage.getItem('preview_slider_msg_width') || '100';
        bubble.style.width = savedMsgW + '%';
        bubble.style.maxWidth = savedMsgW + '%';
      }
    }
  } catch (e) {
    previewText.textContent = 'Помилка рендеру превʼю: ' + e.message;
  }
}

function renderTelegramKeyboard(keyboard) {
  previewButtons.innerHTML = '';
  if (!keyboard || !keyboard.length) return;
  keyboard.forEach(row => {
    const rowEl = document.createElement('div');
    rowEl.className = 'tg-btn-row';
    row.forEach(btn => {
      const button = document.createElement('button');
      button.className = 'tg-button';
      button.textContent = btn.text;
      button.title = btn.callback_data;
      button.addEventListener('click', () => handlePreviewButtonClick(btn.callback_data));
      rowEl.appendChild(button);
    });
    previewButtons.appendChild(rowEl);
  });
}

function handlePreviewButtonClick(callbackData) {
  if (!callbackData) return;
  if (callbackData.startsWith('/sec_')) {
    const secKey = callbackData.replace('/sec_', '');
    if (config.menu[secKey]) {
      currentSectionKey = secKey;
      renderSectionsPills();
      loadSectionIntoEditor(secKey);
      updatePreview();
    }
  } else if (callbackData.startsWith('/act_') || callbackData.startsWith('/tog_')) {
    showToast(`Натиснуто: ${callbackData}`);
  }
}

$('preview-role-select').addEventListener('change', e => {
  currentSimulatedRole = e.target.value;
  updatePreview();
});

$('btn-toggle-preview').addEventListener('click', () => {
  const pane = previewPane;
  const hidden = pane.style.display === 'none';
  pane.style.display = hidden ? 'flex' : 'none';
  $('btn-toggle-preview').querySelector('.preview-toggle-label').textContent = hidden ? 'Превʼю' : 'Показати';
});

// --- Live section name/icon sync ---
function setupEventListeners() {

  // Preview & Telegram Message Slider Controls
  const phoneFrame = $('phone-frame');
  const rangeWidth = $('setting-preview-width');
  const valWidth = $('preview-width-val');
  const rangeTgMsgWidth = $('setting-tg-msg-width');
  const valTgMsgWidth = $('tg-msg-width-val');
  const btnResetPreviewSize = $('btn-reset-preview-size');

  const BASE_WIDTH = 320;
  const BASE_MSG_WIDTH = 100;

  function updatePreviewDimensions(w, msgW, save = true) {
    w = parseInt(w, 10) || BASE_WIDTH;
    msgW = parseInt(msgW, 10);
    if (isNaN(msgW) || msgW < 60 || msgW > 100) msgW = BASE_MSG_WIDTH;

    document.documentElement.style.setProperty('--preview-frame-w', w + 'px');
    document.documentElement.style.setProperty('--tg-msg-width', msgW + '%');

    if (rangeWidth) rangeWidth.value = w;
    if (valWidth) valWidth.textContent = w + ' px';

    if (rangeTgMsgWidth) rangeTgMsgWidth.value = msgW;
    if (valTgMsgWidth) valTgMsgWidth.textContent = msgW + '%';

    const bubble = document.querySelector('.tg-message-bubble');
    if (bubble) {
      bubble.style.width = msgW + '%';
      bubble.style.maxWidth = msgW + '%';
    }

    if (save) {
      localStorage.setItem('preview_slider_width', String(w));
      localStorage.setItem('preview_slider_msg_width', String(msgW));
      if (config) {
        config.telegram_msg_width = msgW;
      }
    }
  }

  function initPreviewControls() {
    let savedW = parseInt(localStorage.getItem('preview_slider_width'), 10);
    if (isNaN(savedW)) savedW = BASE_WIDTH;

    let savedMsgW = parseInt(localStorage.getItem('preview_slider_msg_width'), 10);
    if (isNaN(savedMsgW)) savedMsgW = BASE_MSG_WIDTH;

    updatePreviewDimensions(savedW, savedMsgW, false);

    if (rangeWidth) {
      rangeWidth.addEventListener('input', (e) => {
        const w = parseInt(e.target.value, 10) || BASE_WIDTH;
        const currentMsgW = rangeTgMsgWidth ? parseInt(rangeTgMsgWidth.value, 10) : BASE_MSG_WIDTH;
        updatePreviewDimensions(w, currentMsgW, true);
      });
    }

    if (rangeTgMsgWidth) {
      rangeTgMsgWidth.addEventListener('input', (e) => {
        const currentW = rangeWidth ? parseInt(rangeWidth.value, 10) : BASE_WIDTH;
        const msgW = parseInt(e.target.value, 10) || BASE_MSG_WIDTH;
        updatePreviewDimensions(currentW, msgW, true);
      });
    }

    if (btnResetPreviewSize) {
      btnResetPreviewSize.addEventListener('click', () => {
        updatePreviewDimensions(BASE_WIDTH, BASE_MSG_WIDTH, true);
        showToast(t('toast_reset_preview_size') || 'Розміри прев’ю скинуто');
      });
    }
  }

  initPreviewControls();

  // Setup Section Meta Modal (Title & Icon)
  if (btnEditSectionMeta) {
    btnEditSectionMeta.addEventListener('click', () => {
      const sec = config && config.menu ? config.menu[currentSectionKey] : null;
      if (!sec) return;
      if (editSecIcon) editSecIcon.value = sec.icon || '📁';
      if (editSectionIconDisplay) editSectionIconDisplay.textContent = sec.icon || '📁';
      if (editSecTitle) {
        editSecTitle.value = stripLeadingEmoji(sec.title || '');
      }
      modalEditSection?.classList.add('open');
      // Do not automatically autofocus title to prevent unwanted virtual keyboard popup on mobile
    });
  }

  const closeEditSectionModal = () => {
    modalEditSection?.classList.remove('open');
  };
  btnCloseEditSectionModal?.addEventListener('click', closeEditSectionModal);
  btnCancelEditSection?.addEventListener('click', closeEditSectionModal);

  const saveEditSectionMeta = () => {
    const sec = config && config.menu ? config.menu[currentSectionKey] : null;
    if (!sec) return;
    if (editSecTitle) {
      sec.title = stripLeadingEmoji(editSecTitle.value.trim()) || 'Розділ';
    }
    if (editSecIcon) {
      sec.icon = editSecIcon.value.trim() || '📁';
    }
    if (editorSectionIcon) editorSectionIcon.textContent = sec.icon || '📁';
    if (editorSectionTitle) editorSectionTitle.textContent = sec.title;
    closeEditSectionModal();
    renderSectionsPills();
    renderMenuChecklist(sec.sections || sec.menu_sections || []);
    updatePreview();
    showToast(t('toast_section_updated'));
  };

  btnSaveEditSection?.addEventListener('click', saveEditSectionMeta);
  editSecTitle?.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      saveEditSectionMeta();
    }
  });

  btnEditSectionIconPicker?.addEventListener('click', () => {
    activeIconTarget = 'edit_section_meta';
    iconPickerModal?.classList.add('open');
    renderIconCategories();
    renderIconGrid();
  });

  // Language selector live switch
  const langSelect = $('setting-language');
  if (langSelect) {
    langSelect.addEventListener('change', (e) => {
      const chosenLang = e.target.value;
      if (window.I18N) {
        window.I18N.setLanguage(chosenLang, true);
      }
      if (config) {
        config.language = chosenLang;
      }
    });
  }

  window.onDashboardLanguageChanged = function(lang) {
    if (config) {
      renderSectionsPills();
      loadSectionIntoEditor(currentSectionKey);
      renderUsers();
      updatePreview();
    }
  };


  // Setup Constructor Section Action Buttons (Text, Entity, Button)
  const btnActionAddText = $('btn-action-add-text');
  const btnActionAddEntity = $('btn-action-add-entity');
  const btnActionAddDivider = $('btn-action-add-divider');
  const btnActionAddButton = $('btn-action-add-button');

  if (btnActionAddDivider) {
    btnActionAddDivider.addEventListener('click', () => {
      const sec = config && config.menu ? config.menu[currentSectionKey] : null;
      if (!sec) return;
      ensureSectionItems(sec);
      sec.items.push({
        type: 'divider',
        style: 'line'
      });
      syncSectionLegacyCollections(sec);
      editingItemIdx = null;
      addingItemType = null;
      renderSectionElements(sec.items);
      updatePreview();
      showToast(t('toast_divider_added'));
    });
  }

  if (btnActionAddText) {
    btnActionAddText.addEventListener('click', () => {
      const sec = config && config.menu ? config.menu[currentSectionKey] : null;
      if (!sec) return;
      ensureSectionItems(sec);
      editingItemIdx = null;
      addingItemType = (addingItemType === 'text') ? null : 'text';
      renderSectionElements(sec.items);
    });
  }

  if (btnActionAddEntity) {
    btnActionAddEntity.addEventListener('click', () => {
      const sec = config && config.menu ? config.menu[currentSectionKey] : null;
      if (!sec) return;
      ensureSectionItems(sec);
      editingItemIdx = null;
      addingItemType = (addingItemType === 'entity') ? null : 'entity';
      renderSectionElements(sec.items);
    });
  }

  if (btnActionAddButton) {
    btnActionAddButton.addEventListener('click', () => {
      showToast(t('toast_buttons_coming_soon'));
    });
  }

  // Setup Add Entity & Add Button event listeners
  document.getElementById('btn-add-entity-item')?.addEventListener('click', () => {
    openEntityPicker('entity_item', 'Оберіть ентіті Home Assistant для показу даних');
  });

  document.getElementById('btn-add-button-item')?.addEventListener('click', () => {
    selectedButtonTarget = null;
    const disp = document.getElementById('btn-target-display');
    const lbl = document.getElementById('btn-custom-label');
    if (disp) disp.value = '';
    if (lbl) lbl.value = '';
    document.getElementById('modal-button-config')?.classList.add('open');
  });

  document.getElementById('btn-close-button-config')?.addEventListener('click', () => {
    document.getElementById('modal-button-config')?.classList.remove('open');
  });

  document.getElementById('btn-choose-btn-target')?.addEventListener('click', () => {
    openEntityPicker('button_target', 'Оберіть сутність для кнопки керування');
  });

  document.getElementById('btn-save-configured-button')?.addEventListener('click', () => {
    if (!selectedButtonTarget) {
      showToast(t('toast_select_entity_first'), true);
      return;
    }
    const lbl = document.getElementById('btn-custom-label')?.value.trim() || selectedButtonTarget.friendlyName;
    const sec = config.menu[currentSectionKey];
    if (!sec.buttons) sec.buttons = [];
    sec.buttons.push({
      entity_id: selectedButtonTarget.entityId,
      label: lbl,
      action: 'toggle'
    });
    renderButtonsList(sec.buttons);
    updatePreview();
    document.getElementById('modal-button-config')?.classList.remove('open');
    showToast('Кнопку додано');
  });

  secTitle?.addEventListener('input', () => {
    syncCurrentSectionFromForm();
    renderSectionsPills();
    updatePreview();
  });
  secIcon?.addEventListener('input', () => {
    if (secIconDisplay) secIconDisplay.textContent = secIcon.value || '📁';
    syncCurrentSectionFromForm();
    renderSectionsPills();
    updatePreview();
  });
  [roleAdmin, roleMember, roleGuest].forEach(cb => {
    cb?.addEventListener('change', () => {
      syncCurrentSectionFromForm();
      updatePreview();
    });
  });
  if (secType) {
    secType.addEventListener('change', () => {
      handleSectionTypeChange(secType.value, config.menu[currentSectionKey]);
    });
  }
  if (btnAddSectionDevice) {
    btnAddSectionDevice.addEventListener('click', () => {
      openEntityPicker('section_device', 'Оберіть пристрій для відображення');
    });
  }
}

document.addEventListener('DOMContentLoaded', init);

function renderSectionDevicesList(entities) {
  if (!sectionDevicesList) return;
  if (!entities.length) {
    sectionDevicesList.innerHTML = '<p class="field-hint">Пристрої ще не додані. Натисніть "+ Додати пристрій зі списку".</p>';
    return;
  }
  sectionDevicesList.innerHTML = entities.map((eid, index) => {
    const found = availableEntities.find(e => e.entity_id === eid);
    const name = found ? found.friendly_name : eid;
    const domain = eid.split('.')[0];
    return `
      <div class="item-row" data-index="${index}">
        <div class="item-info">
          <span style="font-size: 16px; font-weight: 600; color: #38bdf8;">${domain}</span>
          <div>
            <div class="item-title">${name}</div>
            <div class="item-desc">${eid}</div>
          </div>
        </div>
        <button type="button" class="btn btn-danger btn-sm btn-remove-device" data-index="${index}">✕</button>
      </div>
    `;
  }).join('');

  sectionDevicesList.querySelectorAll('.btn-remove-device').forEach(btn => {
    btn.addEventListener('click', async () => {
      const confirmed = await showCustomConfirm(
        t('confirm_dialog_title'),
        t('confirm_delete_device'),
        t('btn_delete'),
        true
      );
      if (!confirmed) return;
      const idx = parseInt(btn.dataset.index, 10);
      const sec = config.menu[currentSectionKey];
      if (sec && sec.entities) {
        sec.entities.splice(idx, 1);
        renderSectionDevicesList(sec.entities);
        updatePreview();
      }
    });
  });
}

function addDeviceToSection(eid) {
  const sec = config.menu[currentSectionKey];
  if (!sec) return;
  if (!sec.entities) sec.entities = [];
  if (!sec.entities.includes(eid)) {
    sec.entities.push(eid);
  }
  renderSectionDevicesList(sec.entities);
  updatePreview();
  showToast('Пристрій додано');
}

// Widget configuration modal elements
const widgetConfigModal = document.getElementById('widget-config-modal');
const btnCloseWidgetConfig = document.getElementById('btn-close-widget-config');
const widgetEntityDisplay = document.getElementById('widget-entity-display');
const widgetLabelInput = document.getElementById('widget-label-input');
const widgetUnitInput = document.getElementById('widget-unit-input');
const btnSaveConfiguredWidget = document.getElementById('btn-save-configured-widget');
let pendingWidgetEntity = null;

function setupWidgetConfig() {
  if (btnCloseWidgetConfig) {
    btnCloseWidgetConfig.addEventListener('click', () => widgetConfigModal.classList.remove('open'));
  }
  if (widgetConfigModal) {
    widgetConfigModal.addEventListener('click', e => {
      if (e.target === widgetConfigModal) widgetConfigModal.classList.remove('open');
    });
  }
  if (btnSaveConfiguredWidget) {
    btnSaveConfiguredWidget.addEventListener('click', () => {
      if (!pendingWidgetEntity) return;
      const sec = config.menu[currentSectionKey];
      if (!sec.widgets) sec.widgets = [];
      const customLabel = widgetLabelInput.value.trim() || pendingWidgetEntity.friendlyName;
      const customUnit = widgetUnitInput.value.trim();

      const kindMap = {
        'sensor': 'sensor', 'binary_sensor': 'sensor', 'switch': 'switch',
        'light': 'switch', 'battery': 'battery', 'climate': 'sensor'
      };
      const iconMap = {
        'sensor': '📈', 'binary_sensor': '🚨', 'switch': '🔌', 'light': '💡',
        'climate': '🌡️', 'battery': '🔋', 'cover': '🪟', 'media_player': '🔊'
      };

      sec.widgets.push({
        kind: kindMap[pendingWidgetEntity.domain] || 'sensor',
        label: customLabel,
        entity_id: pendingWidgetEntity.entityId,
        unit: customUnit,
        icon: iconMap[pendingWidgetEntity.domain] || '📊'
      });
      renderWidgetsList(sec.widgets);
      updatePreview();
      widgetConfigModal.classList.remove('open');
      showToast('Показник додано');
    });
  }
}
