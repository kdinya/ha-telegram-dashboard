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
    haEntitiesDatalist.innerHTML = availableEntities
      .map(e => `<option value="${e.entity_id}">${e.friendly_name} (${e.entity_id})</option>`)
      .join('');
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
    showToast('Помилка завантаження конфігурації', true);
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
  btnOpenIconPicker.addEventListener('click', () => {
    iconPickerModal.classList.add('open');
    renderIconCategories();
    renderIconGrid();
  });

  btnCloseIconPicker.addEventListener('click', () => iconPickerModal.classList.remove('open'));
  iconPickerModal.addEventListener('click', e => {
    if (e.target === iconPickerModal) iconPickerModal.classList.remove('open');
  });
  iconSearchInput.addEventListener('input', renderIconGrid);
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
      secIcon.value = item.dataset.icon;
      secIconDisplay.textContent = item.dataset.icon;
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

function renderEntityPickerList() {
  const search = (entitySearchInput.value || '').toLowerCase();
  const activeDomain = domainFiltersTabs.querySelector('.domain-tab-btn.active')?.dataset.domain || 'all';

  let list = availableEntities;
  if (activeDomain !== 'all') list = list.filter(e => e.domain === activeDomain);
  if (search) {
    list = list.filter(e =>
      (e.friendly_name || '').toLowerCase().includes(search) ||
      (e.entity_id || '').toLowerCase().includes(search)
    );
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

  entityPickerList.innerHTML = list.map(e => `
    <button type="button" class="entity-item" data-id="${e.entity_id}" data-name="${e.friendly_name}" data-domain="${e.domain}">
      <span class="entity-item-domain">${e.domain}</span>
      <div class="entity-item-info">
        <span class="entity-item-name">${e.friendly_name}</span>
        <span class="entity-item-id">${e.entity_id}</span>
      </div>
      <span class="entity-item-state">${e.state || ''}</span>
    </button>
  `).join('');

  entityPickerList.querySelectorAll('.entity-item').forEach(item => {
    item.addEventListener('click', () => {
      const eid = item.dataset.id;
      const name = item.dataset.name;
      const domain = item.dataset.domain;
      entityPickerModal.classList.remove('open');

      if (entityPickerContext === 'widget') {
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
      showToast('Спершу оберіть сутність', true);
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
    showToast('Дію додано');
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
  Object.keys(config.menu).forEach(key => {
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
function loadSectionIntoEditor(key) {
  if (!config || !config.menu || !config.menu[key]) return;
  const sec = config.menu[key];
  editorSectionKey.textContent = key;
  secTitle.value = stripLeadingEmoji(sec.title || '');
  secIcon.value = sec.icon || '📁';
  secIconDisplay.textContent = sec.icon || '📁';
  const typeVal = sec.type || (key === 'main' ? 'main' : 'section');
  secType.value = (typeVal === 'menu') ? 'main' : typeVal;
  const secNoteInput = document.getElementById('sec-note');
  if (secNoteInput) secNoteInput.value = sec.note || sec.description || '';

  const roles = sec.roles || ['admin', 'member', 'guest'];
  roleAdmin.checked = roles.includes('admin');
  roleMember.checked = roles.includes('member');
  roleGuest.checked = roles.includes('guest');

  handleSectionTypeChange(sec.type || 'section', sec);
  $('btn-delete-section').style.display = key === 'main' ? 'none' : 'inline-flex';
}

function handleSectionTypeChange(type, sec) {
  // Always display navigation buttons block and items (widgets/actions) block for all section types
  blockMenuSections.style.display = 'block';
  blockSectionItems.style.display = 'block';
  if (blockEntitiesSource) blockEntitiesSource.style.display = 'none';

  renderMenuChecklist(sec ? sec.sections || [] : []);
  renderWidgetsList(sec ? sec.widgets || [] : []);
  renderActionsList(sec ? sec.actions || [] : []);
}

function renderMenuChecklist(selectedKeys) {
  const allKeys = Object.keys(config.menu).filter(k => k !== currentSectionKey);
  menuSectionsChecklist.innerHTML = allKeys.map(k => {
    const s = config.menu[k];
    const cleanTitle = stripLeadingEmoji(s.title || k);
    const isChecked = selectedKeys.includes(k) ? 'checked' : '';
    return `<label><input type="checkbox" value="${k}" ${isChecked}> ${s.icon || '📁'} ${cleanTitle}</label>`;
  }).join('');
}

// --- Widgets ---
function renderWidgetsList(widgets) {
  if (!widgets.length) {
    widgetsList.innerHTML = '<p class="field-hint">Віджети ще не додані.</p>';
    return;
  }
  widgetsList.innerHTML = widgets.map((w, index) => `
    <div class="item-row" data-index="${index}">
      <div class="item-info">
        <span style="font-size: 20px;">${w.icon || '📊'}</span>
        <div>
          <div class="item-title">${w.label || w.entity_id || 'Віджет'}</div>
          <div class="item-desc">${w.kind} • ${w.entity_id || w.name || ''}</div>
        </div>
      </div>
      <button type="button" class="btn btn-danger btn-sm btn-remove-widget" data-index="${index}">✕</button>
    </div>
  `).join('');

  widgetsList.querySelectorAll('.btn-remove-widget').forEach(btn => {
    btn.addEventListener('click', () => {
      const idx = parseInt(btn.dataset.index, 10);
      const sec = config.menu[currentSectionKey];
      if (sec && sec.widgets) {
        sec.widgets.splice(idx, 1);
        renderWidgetsList(sec.widgets);
        updatePreview();
      }
    });
  });
}

function addWidgetFromEntity(entityId, friendlyName, domain) {
  const kindMap = {
    'sensor': 'sensor',
    'binary_sensor': 'sensor',
    'switch': 'switch',
    'light': 'switch',
    'battery': 'battery',
  };
  const iconMap = {
    'sensor': '📈', 'binary_sensor': '🚨', 'switch': '🔌', 'light': '💡',
    'climate': '🌡️', 'battery': '🔋', 'cover': '🪟', 'media_player': '🔊'
  };

  const sec = config.menu[currentSectionKey];
  if (!sec.widgets) sec.widgets = [];
  sec.widgets.push({
    kind: kindMap[domain] || 'sensor',
    label: friendlyName,
    entity_id: entityId,
    icon: iconMap[domain] || '📊'
  });
  renderWidgetsList(sec.widgets);
  updatePreview();
}

$('btn-add-widget').addEventListener('click', () => openEntityPicker('widget', 'Оберіть сутність для віджета'));

// --- Actions ---
function renderActionsList(actions) {
  if (!actions.length) {
    actionsList.innerHTML = '<p class="field-hint">Кнопки дій ще не додані.</p>';
    return;
  }
  actionsList.innerHTML = actions.map((a, index) => `
    <div class="item-row" data-index="${index}">
      <div class="item-info">
        <span style="font-size: 18px;">⚡</span>
        <div>
          <div class="item-title">${a.label || 'Дія'}</div>
          <div class="item-desc">${a.service || ''} • ${a.target?.entity_id || a.entity_id || ''}</div>
        </div>
      </div>
      <button type="button" class="btn btn-danger btn-sm btn-remove-action" data-index="${index}">✕</button>
    </div>
  `).join('');

  actionsList.querySelectorAll('.btn-remove-action').forEach(btn => {
    btn.addEventListener('click', () => {
      const idx = parseInt(btn.dataset.index, 10);
      const sec = config.menu[currentSectionKey];
      if (sec && sec.actions) {
        sec.actions.splice(idx, 1);
        renderActionsList(sec.actions);
        updatePreview();
      }
    });
  });
}

$('btn-add-action').addEventListener('click', () => {
  selectedActionEntity = '';
  actionEntityDisplay.value = '';
  actionServiceSelect.innerHTML = '<option value="">Спершу оберіть сутність</option>';
  actionLabelInput.value = '';
  actionConfigModal.classList.add('open');
});

// --- Section creation: title only, slug and icon guessed ---
$('btn-add-section').addEventListener('click', () => {
  const title = prompt('Введіть назву нового розділу:');
  if (!title || !title.trim()) return;

  const cleanTitle = stripLeadingEmoji(title.trim());
  const rawSlug = slugify(cleanTitle) || 'section';
  let slug = rawSlug;
  let counter = 1;
  while (config.menu[slug]) slug = `${rawSlug}_${counter++}`;

  let guessedIcon = '📁';
  const lower = cleanTitle.toLowerCase();
  if (lower.includes('клімат') || lower.includes('температур')) guessedIcon = '🌡️';
  else if (lower.includes('світл') || lower.includes('ламп')) guessedIcon = '💡';
  else if (lower.includes('розетк') || lower.includes('вимикач')) guessedIcon = '🔌';
  else if (lower.includes('безпек') || lower.includes('сигнал')) guessedIcon = '🛡️';
  else if (lower.includes('камер')) guessedIcon = '📹';
  else if (lower.includes('вод')) guessedIcon = '🚰';
  else if (lower.includes('замок') || lower.includes('двер')) guessedIcon = '🔒';
  else if (lower.includes('штор')) guessedIcon = '🪟';

  config.menu[slug] = {
    title: cleanTitle,
    icon: guessedIcon,
    type: 'section',
    roles: ['admin', 'member'],
    widgets: [],
    actions: []
  };

  currentSectionKey = slug;
  renderSectionsPills();
  loadSectionIntoEditor(slug);
  updatePreview();
  showToast(`Розділ "${cleanTitle}" створено (id: ${slug})`);
});

$('btn-delete-section').addEventListener('click', () => {
  if (currentSectionKey === 'main') {
    alert('Головний розділ (main) не можна видалити.');
    return;
  }
  if (!confirm(`Видалити розділ "${currentSectionKey}"?`)) return;
  delete config.menu[currentSectionKey];
  currentSectionKey = 'main';
  renderSectionsPills();
  loadSectionIntoEditor('main');
  updatePreview();
  showToast('Розділ видалено');
});

// --- Apply section ---
$('btn-apply-section').addEventListener('click', () => {
  const sec = config.menu[currentSectionKey];
  if (!sec) return;

  sec.title = stripLeadingEmoji(secTitle.value.trim()) || 'Розділ';
  sec.icon = secIcon.value.trim() || '📁';
  sec.type = secType.value;
  const secNoteInput = document.getElementById('sec-note');
  if (secNoteInput) sec.note = secNoteInput.value.trim();

  const roles = [];
  if (roleAdmin.checked) roles.push('admin');
  if (roleMember.checked) roles.push('member');
  if (roleGuest.checked) roles.push('guest');
  sec.roles = roles.length ? roles : ['admin'];

  // Save selected sub-sections for navigation
  const checked = [];
  menuSectionsChecklist.querySelectorAll('input:checked').forEach(i => checked.push(i.value));
  sec.sections = checked;

  renderSectionsPills();
  updatePreview();
  showToast('Зміни розділу застосовано');
});

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
        ${isGuest ? `<button class="btn btn-primary btn-sm btn-approve-user" data-id="${user.telegram_id}" style="margin-right: 6px;">✅ Підтвердити</button>` : ''}
        <button class="btn btn-danger btn-sm btn-delete-user" data-id="${user.telegram_id}">Видалити</button>
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
        showToast(`Користувача ${user.name || id} підтверджено!`);
      }
    });
  });

  usersTbody.querySelectorAll('.btn-delete-user').forEach(btn => {
    btn.addEventListener('click', async () => {
      const id = parseInt(btn.dataset.id, 10);
      if (confirm(`Видалити користувача ${id}?`)) await deleteUser(id);
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
    showToast('Користувача оновлено');
  } catch (e) {
    showToast(`Помилка: ${e.message}`, true);
  }
}

async function deleteUser(id) {
  try {
    await api(`api/users/${id}`, { method: 'DELETE' });
    config.users = config.users.filter(u => u.telegram_id !== id);
    renderUsers();
    showToast('Користувача видалено');
  } catch (e) {
    showToast('Помилка видалення', true);
  }
}

$('btn-add-user').addEventListener('click', async () => {
  const tid = prompt('Введіть Telegram ID користувача (число):');
  if (!tid || isNaN(tid)) return;
  const name = prompt("Введіть ім'я або юзернейм:") || 'Користувач';
  const role = prompt('Оберіть роль (admin, member, guest):', 'member') || 'member';
  const user = { telegram_id: parseInt(tid, 10), name, role };
  await saveUser(user);
  config.users.push(user);
  renderUsers();
});

$('btn-sync-users').addEventListener('click', async () => {
  const btn = $('btn-sync-users');
  btn.disabled = true;
  btn.textContent = '⏳ Синхронізація...';
  try {
    const data = await api('api/users/sync', { method: 'POST' });
    if (data.users) {
      config.users = data.users;
      renderUsers();
      showToast(`Синхронізовано. Нових користувачів: ${data.discovered || 0}`);
    }
  } catch (e) {
    showToast(`Помилка синхронізації: ${e.message}`, true);
  } finally {
    btn.disabled = false;
    btn.textContent = '🔄 Оновити / Синхронізувати';
  }
});

// --- Settings ---
function loadSettings() {
  if (!config) return;
  $('setting-bot-token').value = config.telegram_token || '';
  $('setting-theme').value = config.theme || 'cards';
  $('setting-default-role').value = config.default_role || 'guest';
}

function applySettings() {
  if (!config) return;
  config.telegram_token = $('setting-bot-token').value.trim();
  config.theme = $('setting-theme').value;
  config.default_role = $('setting-default-role').value;
}

// --- Save config ---
$('btn-save').addEventListener('click', async () => {
  $('btn-apply-section').click();
  applySettings();
  try {
    const res = await fetch('api/config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config)
    });
    if (res.ok) {
      showToast('Всі зміни успішно збережено!');
      updatePreview();
    } else {
      const err = await res.json();
      showToast(`Помилка: ${err.error}`, true);
    }
  } catch (e) {
    showToast('Не вдалося зберегти зміни', true);
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
  secTitle.addEventListener('input', () => {
    const sec = config.menu[currentSectionKey];
    if (sec) sec.title = secTitle.value;
  });
  secIcon.addEventListener('input', () => {
    secIconDisplay.textContent = secIcon.value || '📁';
  });
  secType.addEventListener('change', () => {
    handleSectionTypeChange(secType.value, config.menu[currentSectionKey]);
  });
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
    btn.addEventListener('click', () => {
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
