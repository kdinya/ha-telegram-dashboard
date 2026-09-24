/**
 * Telegram Dashboard Web UI Client
 */

// --- Global State ---
let config = null;
let currentSectionKey = 'main';
let currentSimulatedRole = 'admin';
let isPhonePreviewHidden = false;
let availableEntities = [];

// --- Transliteration for Ukrainian/Cyrillic to slug ---
const cyrillicMap = {
  'а':'a','б':'b','в':'v','г':'h','ґ':'g','д':'d','е':'e','є':'ye','ж':'zh','з':'z',
  'и':'y','і':'i','ї':'yi','й':'y','к':'k','л':'l','м':'m','н':'n','о':'o','п':'p',
  'р':'r','с':'s','т':'t','у':'u','ф':'f','х':'kh','ц':'ts','ч':'ch','ш':'sh','щ':'shch',
  'ь':'','ю':'yu','я':'ya',' ':'_','-':'_'
};

function slugify(text) {
  return text.toLowerCase()
    .split('')
    .map(char => cyrillicMap[char] !== undefined ? cyrillicMap[char] : char)
    .join('')
    .replace(/[^a-z0-9_]/g, '')
    .replace(/_+/g, '_')
    .replace(/^_+|_+$/g, '');
}

// --- Smart Home Icon Database ---
const ICON_DATABASE = {
  'Клімат та погода': ['🌡️', '❄️', '🔥', '☀️', '⛅', '🌧️', '💨', '💧', '♨️', '🌪️', '🌫️'],
  'Освітлення': ['💡', '🔦', '🕯️', '🔆', '🏮', '✨', '🌈', '🪩', '🎇'],
  'Безпека та дім': ['🏠', '🏡', '🚪', '🔒', '🔓', '🛡️', '🚨', '🚰', '🧯', '🔔', '📹', '🔑'],
  'Кімнати': ['🛋️', '🛏️', '🍳', '🚿', '🛁', '🪴', '🧺', '👶', '🚗', '🏊'],
  'Прилади та гаджети': ['⚡', '🔋', '🔌', '🧹', '📺', '🔊', '📻', '☕', '💻', '🎮', '🖨️'],
  'Керування та статус': ['⚙️', '📊', '▶️', '⏸️', '⏹️', '🔄', '✔️', '❌', 'ℹ️', '📱', '👤']
};

// --- DOM Elements ---
const navItems = document.querySelectorAll('.nav-item');
const tabPanes = document.querySelectorAll('.tab-pane');
const sectionsList = document.getElementById('sections-list');
const sectionEditor = document.getElementById('section-editor');
const editorSectionKey = document.getElementById('editor-section-key');
const secTitle = document.getElementById('sec-title');
const secIcon = document.getElementById('sec-icon');
const secIconDisplay = document.getElementById('sec-icon-display');
const btnOpenIconPicker = document.getElementById('btn-open-icon-picker');
const secType = document.getElementById('sec-type');
const roleAdmin = document.getElementById('role-admin');
const roleMember = document.getElementById('role-member');
const roleGuest = document.getElementById('role-guest');
const blockMenuSections = document.getElementById('block-menu-sections');
const blockEntitiesSource = document.getElementById('block-entities-source');
const blockSectionItems = document.getElementById('block-section-items');
const menuSectionsChecklist = document.getElementById('menu-sections-checklist');
const entSourceMode = document.getElementById('ent-source-mode');
const entSourceValWrap = document.getElementById('ent-source-val-wrap');
const entSourceVal = document.getElementById('ent-source-val');
const widgetsList = document.getElementById('widgets-list');
const actionsList = document.getElementById('actions-list');
const btnAddWidget = document.getElementById('btn-add-widget');
const btnAddAction = document.getElementById('btn-add-action');
const btnAddSection = document.getElementById('btn-add-section');
const btnDeleteSection = document.getElementById('btn-delete-section');
const btnApplySection = document.getElementById('btn-apply-section');
const btnSave = document.getElementById('btn-save');
const btnTogglePreview = document.getElementById('btn-toggle-preview');
const btnBackToEditor = document.getElementById('btn-back-to-editor');
const previewPane = document.getElementById('preview-pane');
const previewText = document.getElementById('preview-text');
const previewButtons = document.getElementById('preview-buttons');
const previewRoleSelect = document.getElementById('preview-role-select');
const usersTbody = document.getElementById('users-tbody');
const btnAddUser = document.getElementById('btn-add-user');
const btnSyncUsers = document.getElementById('btn-sync-users');
const settingBotToken = document.getElementById('setting-bot-token');
const settingTheme = document.getElementById('setting-theme');
const settingDefaultRole = document.getElementById('setting-default-role');
const toastEl = document.getElementById('toast');
const iconPickerModal = document.getElementById('icon-picker-modal');
const btnCloseIconPicker = document.getElementById('btn-close-icon-picker');
const iconCategoriesTabs = document.getElementById('icon-categories-tabs');
const iconPickerGrid = document.getElementById('icon-picker-grid');
const haEntitiesDatalist = document.getElementById('ha-entities-datalist');

// --- Init & Fetch ---
async function init() {
  setupNavigation();
  setupIconPicker();
  await fetchEntities();
  await loadConfig();
  setupEventListeners();
}

async function fetchEntities() {
  try {
    const res = await fetch('api/entities');
    if (res.ok) {
      const data = await res.json();
      if (data.entities) {
        availableEntities = data.entities;
        haEntitiesDatalist.innerHTML = availableEntities
          .map(e => `<option value="${e.entity_id}">${e.friendly_name} (${e.entity_id})</option>`)
          .join('');
      }
    }
  } catch (e) {
    console.warn('Could not fetch entities:', e);
  }
}

async function loadConfig() {
  try {
    const res = await fetch('api/config');
    config = await res.json();
    renderSectionsPills();
    loadSectionIntoEditor(currentSectionKey);
    renderUsers();
    loadSettings();
    updatePreview();
  } catch (e) {
    showToast('Помилка завантаження конфігурації', true);
  }
}

// --- Navigation Tabs ---
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
        tabPanes.forEach(p => {
          p.classList.toggle('active', p.id === `tab-${targetTab}`);
        });
      }
    });
  });

  btnBackToEditor?.addEventListener('click', () => {
    const builderNav = document.querySelector('[data-tab="builder"]');
    builderNav?.click();
  });
}

// --- Icon Picker ---
function setupIconPicker() {
  btnOpenIconPicker.addEventListener('click', () => {
    iconPickerModal.classList.add('open');
  });

  btnCloseIconPicker.addEventListener('click', () => {
    iconPickerModal.classList.remove('open');
  });

  iconPickerModal.addEventListener('click', (e) => {
    if (e.target === iconPickerModal) iconPickerModal.classList.remove('open');
  });

  const categories = Object.keys(ICON_DATABASE);
  iconCategoriesTabs.innerHTML = categories.map((cat, i) => `
    <button class="icon-cat-btn ${i === 0 ? 'active' : ''}" data-cat="${cat}">${cat}</button>
  `).join('');

  renderIconGrid(categories[0]);

  iconCategoriesTabs.addEventListener('click', (e) => {
    const btn = e.target.closest('.icon-cat-btn');
    if (!btn) return;
    document.querySelectorAll('.icon-cat-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    renderIconGrid(btn.dataset.cat);
  });
}

function renderIconGrid(category) {
  const icons = ICON_DATABASE[category] || [];
  iconPickerGrid.innerHTML = icons.map(icon => `
    <button type="button" class="icon-pick-item" data-icon="${icon}">${icon}</button>
  `).join('');

  iconPickerGrid.querySelectorAll('.icon-pick-item').forEach(item => {
    item.addEventListener('click', () => {
      const chosen = item.dataset.icon;
      secIcon.value = chosen;
      secIconDisplay.textContent = chosen;
      iconPickerModal.classList.remove('open');
    });
  });
}

// --- Section Pill List ---
function renderSectionsPills() {
  if (!config || !config.menu) return;
  sectionsList.innerHTML = '';
  Object.keys(config.menu).forEach(key => {
    const sec = config.menu[key];
    const pill = document.createElement('div');
    pill.className = `section-pill ${key === currentSectionKey ? 'active' : ''}`;
    pill.innerHTML = `<span>${sec.icon || '📁'}</span> <span>${sec.title || key}</span>`;
    pill.addEventListener('click', () => {
      currentSectionKey = key;
      renderSectionsPills();
      loadSectionIntoEditor(key);
      updatePreview();
    });
    sectionsList.appendChild(pill);
  });
}

// --- Load Section in Editor ---
function loadSectionIntoEditor(key) {
  if (!config || !config.menu || !config.menu[key]) return;
  const sec = config.menu[key];
  editorSectionKey.textContent = key;
  secTitle.value = sec.title || '';
  secIcon.value = sec.icon || '📁';
  secIconDisplay.textContent = sec.icon || '📁';
  secType.value = sec.type || 'section';

  const roles = sec.roles || ['admin', 'member', 'guest'];
  roleAdmin.checked = roles.includes('admin');
  roleMember.checked = roles.includes('member');
  roleGuest.checked = roles.includes('guest');

  handleSectionTypeChange(sec.type || 'section', sec);
  btnDeleteSection.style.display = key === 'main' ? 'none' : 'inline-flex';
}

function handleSectionTypeChange(type, sec) {
  blockMenuSections.style.display = type === 'menu' ? 'block' : 'none';
  blockEntitiesSource.style.display = type === 'entities' ? 'block' : 'none';
  blockSectionItems.style.display = type === 'section' ? 'block' : 'none';

  if (type === 'menu') {
    renderMenuChecklist(sec ? sec.sections || [] : []);
  } else if (type === 'entities') {
    const src = sec && sec.source ? sec.source : { mode: 'all' };
    entSourceMode.value = src.mode || 'all';
    entSourceValWrap.style.display = src.mode === 'all' ? 'none' : 'block';
    if (src.value) entSourceVal.value = src.value;
  } else if (type === 'section') {
    renderWidgetsList(sec ? sec.widgets || [] : []);
    renderActionsList(sec ? sec.actions || [] : []);
  }
}

secType.addEventListener('change', () => {
  handleSectionTypeChange(secType.value, config.menu[currentSectionKey]);
});

entSourceMode.addEventListener('change', () => {
  entSourceValWrap.style.display = entSourceMode.value === 'all' ? 'none' : 'block';
});

// --- Menu Checklist ---
function renderMenuChecklist(selectedKeys) {
  const allKeys = Object.keys(config.menu).filter(k => k !== currentSectionKey);
  menuSectionsChecklist.innerHTML = allKeys.map(k => {
    const s = config.menu[k];
    const isChecked = selectedKeys.includes(k) ? 'checked' : '';
    return `<label><input type="checkbox" value="${k}" ${isChecked}> ${s.icon || '📁'} ${s.title || k}</label>`;
  }).join('');
}

// --- Widgets Editor ---
function renderWidgetsList(widgets) {
  if (!widgets.length) {
    widgetsList.innerHTML = '<p class="field-hint">Віджети ще не додані. Натисніть "+ Додати віджет".</p>';
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
    btn.addEventListener('click', (e) => {
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

btnAddWidget.addEventListener('click', () => {
  const label = prompt('Введіть назву показника (наприклад: Температура у залі):', '');
  if (!label) return;
  const entityId = prompt('Введіть entity_id Home Assistant (або оберіть зі списку):', 'sensor.');
  if (!entityId) return;
  const kind = prompt('Оберіть тип віджета (sensor, switch, battery, leak):', 'sensor') || 'sensor';
  const icon = prompt('Іконка віджета:', '🌡️') || '📊';

  const sec = config.menu[currentSectionKey];
  if (!sec.widgets) sec.widgets = [];
  sec.widgets.push({
    kind: kind,
    label: label,
    entity_id: entityId,
    icon: icon
  });
  renderWidgetsList(sec.widgets);
  updatePreview();
});

// --- Actions Editor ---
function renderActionsList(actions) {
  if (!actions.length) {
    actionsList.innerHTML = '<p class="field-hint">Кнопки дій ще не додані. Натисніть "+ Додати дію".</p>';
    return;
  }
  actionsList.innerHTML = actions.map((a, index) => `
    <div class="item-row" data-index="${index}">
      <div class="item-info">
        <span style="font-size: 18px;">⚡</span>
        <div>
          <div class="item-title">${a.label || 'Дія'}</div>
          <div class="item-desc">${a.service || a.action || ''} • ${a.entity_id || ''}</div>
        </div>
      </div>
      <button type="button" class="btn btn-danger btn-sm btn-remove-action" data-index="${index}">✕</button>
    </div>
  `).join('');

  actionsList.querySelectorAll('.btn-remove-action').forEach(btn => {
    btn.addEventListener('click', (e) => {
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

btnAddAction.addEventListener('click', () => {
  const label = prompt('Текст на кнопці (наприклад: Увімкнути світло):', '');
  if (!label) return;
  const service = prompt('Служба HA (наприклад: light.turn_on або switch.toggle):', 'switch.toggle');
  if (!service) return;
  const entityId = prompt('Цільовий entity_id Home Assistant:', 'switch.');

  const sec = config.menu[currentSectionKey];
  if (!sec.actions) sec.actions = [];
  sec.actions.push({
    label: label,
    service: service,
    target: { entity_id: entityId }
  });
  renderActionsList(sec.actions);
  updatePreview();
});

// --- Section Creation: Asking ONLY Title and generating slug ---
btnAddSection.addEventListener('click', () => {
  const title = prompt('Введіть назву нового розділу:');
  if (!title || !title.trim()) return;

  const rawSlug = slugify(title.trim()) || 'section';
  let slug = rawSlug;
  let counter = 1;
  while (config.menu[slug]) {
    slug = `${rawSlug}_${counter++}`;
  }

  // Guess icon from title
  let guessedIcon = '📁';
  const lower = title.toLowerCase();
  if (lower.includes('клімат') || lower.includes('температур')) guessedIcon = '🌡️';
  else if (lower.includes('світл') || lower.includes('ламп')) guessedIcon = '💡';
  else if (lower.includes('розетк') || lower.includes('вимикач')) guessedIcon = '🔌';
  else if (lower.includes('безпек') || lower.includes('сигнал')) guessedIcon = '🛡️';
  else if (lower.includes('камер')) guessedIcon = '📹';
  else if (lower.includes('вод')) guessedIcon = '🚰';

  config.menu[slug] = {
    title: title.trim(),
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
  showToast(`Розділ "${title}" створено з ідентифікатором "${slug}"`);
});

btnDeleteSection.addEventListener('click', () => {
  if (currentSectionKey === 'main') {
    alert('Головний розділ (main) не можна видалити.');
    return;
  }
  if (!confirm(`Ви дійсно бажаєте видалити розділ "${currentSectionKey}"?`)) return;
  delete config.menu[currentSectionKey];
  currentSectionKey = 'main';
  renderSectionsPills();
  loadSectionIntoEditor('main');
  updatePreview();
  showToast('Розділ видалено');
});

// --- Apply Section Form Changes ---
btnApplySection.addEventListener('click', () => {
  const sec = config.menu[currentSectionKey];
  if (!sec) return;

  sec.title = secTitle.value.trim();
  sec.icon = secIcon.value.trim() || '📁';
  sec.type = secType.value;

  const roles = [];
  if (roleAdmin.checked) roles.push('admin');
  if (roleMember.checked) roles.push('member');
  if (roleGuest.checked) roles.push('guest');
  sec.roles = roles.length ? roles : ['admin'];

  if (sec.type === 'menu') {
    const checked = [];
    menuSectionsChecklist.querySelectorAll('input:checked').forEach(i => checked.push(i.value));
    sec.sections = checked;
  } else if (sec.type === 'entities') {
    sec.source = {
      mode: entSourceMode.value,
      value: entSourceMode.value === 'all' ? undefined : entSourceVal.value
    };
  }

  renderSectionsPills();
  updatePreview();
  showToast('Зміни розділу застосовано');
});

// --- Users Management ---
function renderUsers() {
  if (!config || !config.users) return;
  usersTbody.innerHTML = '';
  config.users.forEach(user => {
    const tr = document.createElement('tr');
    const isGuest = user.role === 'guest';
    const statusBadge = isGuest
      ? '<span style="background: rgba(234, 179, 8, 0.2); color: #eab308; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600;">Очікує підтвердження</span>'
      : '<span style="background: rgba(16, 185, 129, 0.2); color: #10b981; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600;">Підтверджено</span>';

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

  // Event handlers
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
      if (confirm(`Видалити користувача з ID ${id}?`)) {
        await deleteUser(id);
      }
    });
  });
}

async function saveUser(user) {
  try {
    await fetch('api/users', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(user)
    });
    showToast('Користувача оновлено');
  } catch (e) {
    showToast('Помилка оновлення користувача', true);
  }
}

async function deleteUser(id) {
  try {
    const res = await fetch(`api/users/${id}`, { method: 'DELETE' });
    if (res.ok) {
      config.users = config.users.filter(u => u.telegram_id !== id);
      renderUsers();
      showToast('Користувача видалено');
    }
  } catch (e) {
    showToast('Помилка видалення', true);
  }
}

btnAddUser.addEventListener('click', async () => {
  const tid = prompt('Введіть Telegram ID користувача (число):');
  if (!tid || isNaN(tid)) return;
  const name = prompt('Введіть ім\'я або юзернейм:') || 'Користувач';
  const role = prompt('Оберіть роль (admin, member, guest):', 'member') || 'member';

  const user = { telegram_id: parseInt(tid, 10), name: name, role: role };
  await saveUser(user);
  config.users.push(user);
  renderUsers();
});

btnSyncUsers.addEventListener('click', async () => {
  btnSyncUsers.disabled = true;
  btnSyncUsers.textContent = '⏳ Синхронізація...';
  try {
    const res = await fetch('api/users/sync', { method: 'POST' });
    const data = await res.json();
    if (data.users) {
      config.users = data.users;
      renderUsers();
      showToast(`Синхронізацію завершено. Нових: ${data.discovered || 0}`);
    }
  } catch (e) {
    showToast('Помилка синхронізації з Telegram Bot', true);
  } finally {
    btnSyncUsers.disabled = false;
    btnSyncUsers.textContent = '🔄 Синхронізувати з Telegram Bot';
  }
});

// --- Settings Tab ---
function loadSettings() {
  if (!config) return;
  settingBotToken.value = config.telegram_token || '';
  settingTheme.value = config.theme || 'cards';
  settingDefaultRole.value = config.default_role || 'guest';
}

function applySettings() {
  if (!config) return;
  config.telegram_token = settingBotToken.value.trim();
  config.theme = settingTheme.value;
  config.default_role = settingDefaultRole.value;
}

// --- Save Config via API ---
btnSave.addEventListener('click', async () => {
  btnApplySection.click();
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

// --- Realtime Simulator Preview ---
async function updatePreview() {
  if (!config || !config.menu) return;
  try {
    const res = await fetch('api/preview', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        section_key: currentSectionKey,
        section: config.menu[currentSectionKey],
        role: currentSimulatedRole
      })
    });
    if (res.ok) {
      const data = await res.json();
      previewText.innerHTML = data.html || 'Немає даних для показу';
      renderTelegramKeyboard(data.keyboard || []);
    }
  } catch (e) {
    previewText.textContent = 'Помилка рендеру прев\'ю';
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
      button.addEventListener('click', () => {
        handlePreviewButtonClick(btn.callback_data);
      });
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
    showToast(`Натиснуто дію: ${callbackData}`);
  }
}

// --- Preview Controls ---
previewRoleSelect.addEventListener('change', (e) => {
  currentSimulatedRole = e.target.value;
  updatePreview();
});

btnTogglePreview.addEventListener('click', () => {
  isPhonePreviewHidden = !isPhonePreviewHidden;
  previewPane.style.display = isPhonePreviewHidden ? 'none' : 'flex';
  btnTogglePreview.querySelector('.preview-toggle-label').textContent = isPhonePreviewHidden ? 'Показати' : 'Прев\'ю';
});

function showToast(message, isError = false) {
  toastEl.textContent = message;
  toastEl.style.backgroundColor = isError ? 'var(--danger)' : 'var(--primary)';
  toastEl.style.color = isError ? '#ffffff' : '#0f172a';
  toastEl.classList.add('show');
  setTimeout(() => toastEl.classList.remove('show'), 3000);
}

function setupEventListeners() {
  secTitle.addEventListener('input', () => {
    const sec = config.menu[currentSectionKey];
    if (sec) sec.title = secTitle.value;
  });
  secIcon.addEventListener('input', () => {
    secIconDisplay.textContent = secIcon.value || '📁';
  });
}

// Start
document.addEventListener('DOMContentLoaded', init);
