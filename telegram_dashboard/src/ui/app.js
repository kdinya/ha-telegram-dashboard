let config = null;
let currentSection = "main";
let currentRole = "admin";

function showToast(msg) {
  const toast = document.getElementById("toast");
  if (!toast) return;
  toast.innerText = msg;
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), 3000);
}

function apiUrl(endpoint) {
  return endpoint.replace(/^\//, '');
}

async function loadConfig() {
  try {
    const res = await fetch(apiUrl("api/config"));
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    config = await res.json();
    populateSettings();
    renderSections();
    renderUsers();
    loadSectionEditor(currentSection);
    updatePreview();
  } catch (err) {
    console.error("Failed to load config:", err);
    showToast("⚠️ Помилка завантаження конфігурації: " + err.message);
  }
}

function populateSettings() {
  if (!config) return;
  const tokenInput = document.getElementById("setting-bot-token");
  if (tokenInput && config.telegram_token) {
    tokenInput.value = config.telegram_token;
  }
  const themeInput = document.getElementById("setting-theme");
  if (themeInput && config.theme) {
    themeInput.value = config.theme;
  }
  const roleInput = document.getElementById("setting-default-role");
  if (roleInput && config.default_role) {
    roleInput.value = config.default_role;
  }
}

function renderSections() {
  const container = document.getElementById("sections-list");
  if (!container || !config || !config.menu) return;
  container.innerHTML = "";

  Object.entries(config.menu).forEach(([key, sec]) => {
    const item = document.createElement("div");
    item.className = `section-item ${key === currentSection ? "active" : ""}`;
    item.innerHTML = `
      <div class="section-item-header">
        <strong>${sec.icon || "📄"} ${sec.title || key}</strong>
        <span class="badge">${(sec.roles || []).join(", ")}</span>
      </div>
      <small style="color: #94a3b8; font-size: 11px;">/${key} &bull; тип: ${sec.type || "section"}</small>
    `;
    item.onclick = () => {
      currentSection = key;
      renderSections();
      loadSectionEditor(key);
      updatePreview();
    };
    container.appendChild(item);
  });
}

function loadSectionEditor(key) {
  if (!config || !config.menu || !config.menu[key]) return;
  const sec = config.menu[key];
  document.getElementById("editor-section-key").innerText = key;
  document.getElementById("sec-title").value = sec.title || "";
  document.getElementById("sec-icon").value = sec.icon || "";
  document.getElementById("sec-type").value = sec.type || "section";

  const roles = sec.roles || ["admin", "member", "guest"];
  document.getElementById("role-admin").checked = roles.includes("admin");
  document.getElementById("role-member").checked = roles.includes("member");
  document.getElementById("role-guest").checked = roles.includes("guest");

  const delBtn = document.getElementById("btn-delete-section");
  if (delBtn) {
    delBtn.style.display = key === "main" ? "none" : "inline-flex";
  }
}

function applySectionEditor() {
  if (!config || !config.menu || !config.menu[currentSection]) return;
  const sec = config.menu[currentSection];
  sec.title = document.getElementById("sec-title").value.trim() || currentSection;
  sec.icon = document.getElementById("sec-icon").value.trim() || "📄";
  sec.type = document.getElementById("sec-type").value;

  const roles = [];
  if (document.getElementById("role-admin").checked) roles.push("admin");
  if (document.getElementById("role-member").checked) roles.push("member");
  if (document.getElementById("role-guest").checked) roles.push("guest");
  sec.roles = roles.length ? roles : ["admin"];

  renderSections();
  updatePreview();
  showToast(`✅ Зміни в розділі /${currentSection} застосовано`);
}

function addNewSection() {
  const key = prompt("Введіть ідентифікатор нового розділу (англійськими літерами, напр. security або garden):");
  if (!key) return;
  const cleanKey = key.trim().toLowerCase().replace(/[^a-z0-9_]/g, "");
  if (!cleanKey) {
    alert("Некоректний ідентифікатор!");
    return;
  }
  if (config.menu[cleanKey]) {
    alert("Розділ з таким ідентифікатором вже існує!");
    return;
  }
  const title = prompt("Введіть назву розділу:", "Новий розділ") || cleanKey;
  config.menu[cleanKey] = {
    title: title,
    icon: "📂",
    type: "section",
    roles: ["admin", "member"],
    widgets: [],
    actions: []
  };
  if (config.menu.main && Array.isArray(config.menu.main.sections)) {
    config.menu.main.sections.push(cleanKey);
  }
  currentSection = cleanKey;
  renderSections();
  loadSectionEditor(cleanKey);
  updatePreview();
  showToast(`Розділ /${cleanKey} додано!`);
}

function deleteCurrentSection() {
  if (currentSection === "main") {
    alert("Неможливо видалити головний розділ!");
    return;
  }
  if (!confirm(`Видалити розділ /${currentSection}?`)) return;
  delete config.menu[currentSection];
  if (config.menu.main && Array.isArray(config.menu.main.sections)) {
    config.menu.main.sections = config.menu.main.sections.filter(s => s !== currentSection);
  }
  currentSection = "main";
  renderSections();
  loadSectionEditor("main");
  updatePreview();
  showToast("Розділ видалено");
}

function renderUsers() {
  const tbody = document.getElementById("users-tbody");
  if (!tbody || !config) return;
  tbody.innerHTML = "";

  (config.users || []).forEach(u => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><code>${u.telegram_id}</code></td>
      <td>${u.name || "—"}</td>
      <td><span class="badge">${u.role}</span></td>
      <td>${u.role === "admin" ? "Повний доступ" : u.role === "member" ? "Керування приладами" : "Тільки перегляд"}</td>
      <td><button class="btn btn-danger btn-sm" onclick="removeUser(${u.telegram_id})">Видалити</button></td>
    `;
    tbody.appendChild(tr);
  });
}

async function addNewUser() {
  const tgIdStr = prompt("Введіть Telegram User ID (число):");
  if (!tgIdStr) return;
  const tgId = parseInt(tgIdStr.trim(), 10);
  if (isNaN(tgId)) {
    alert("Telegram ID має бути числом!");
    return;
  }
  const name = prompt("Введіть ім'я або примітку:", "Користувач") || "";
  const role = prompt("Роль (admin, member, guest):", "member") || "member";
  if (!["admin", "member", "guest"].includes(role)) {
    alert("Невідома роль!");
    return;
  }

  try {
    const res = await fetch(apiUrl("api/users"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ telegram_id: tgId, name: name, role: role })
    });
    if (res.ok) {
      showToast("Користувача додано");
      loadConfig();
    } else {
      const err = await res.json();
      alert("Помилка: " + (err.error || "не вдалося додати"));
    }
  } catch (e) {
    alert("Помилка запиту: " + e.message);
  }
}

async function removeUser(uid) {
  if (!confirm(`Видалити користувача ${uid}?`)) return;
  try {
    await fetch(apiUrl(`api/users/${uid}`), { method: "DELETE" });
    showToast("Користувача видалено");
    loadConfig();
  } catch (e) {
    alert("Помилка видалення: " + e.message);
  }
}

async function updatePreview() {
  if (!config) return;
  const sec = config.menu[currentSection] || config.menu["main"];
  try {
    const res = await fetch(apiUrl("api/preview"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ section: sec, section_key: currentSection, role: currentRole })
    });
    const data = await res.json();
    document.getElementById("preview-text").innerHTML = data.html || "—";

    const btnContainer = document.getElementById("preview-buttons");
    btnContainer.innerHTML = "";

    const keyboard = data.keyboard || [];
    if (keyboard.length > 0) {
      keyboard.forEach(row => {
        const rowDiv = document.createElement("div");
        rowDiv.className = "tg-btn-row";
        row.forEach(btn => {
          const button = document.createElement("button");
          button.className = "tg-btn";
          button.innerText = btn.text;
          button.onclick = () => handlePreviewButtonClick(btn.callback_data);
          rowDiv.appendChild(button);
        });
        btnContainer.appendChild(rowDiv);
      });
    } else {
      // Fallback preview buttons
      const row = document.createElement("div");
      row.className = "tg-btn-row";
      if (currentSection === "main") {
        (sec.sections || []).forEach(subKey => {
          const sub = config.menu[subKey] || {};
          const b = document.createElement("button");
          b.className = "tg-btn";
          b.innerText = `${sub.icon || "📄"} ${sub.title || subKey}`;
          b.onclick = () => selectSection(subKey);
          row.appendChild(b);
        });
      } else {
        const back = document.createElement("button");
        back.className = "tg-btn";
        back.innerText = "⬅️ Головна";
        back.onclick = () => selectSection("main");
        row.appendChild(back);
      }
      btnContainer.appendChild(row);
    }
  } catch (err) {
    console.error("Preview render failed:", err);
  }
}

function handlePreviewButtonClick(cbData) {
  if (!cbData) return;
  if (cbData.startsWith("/sec_")) {
    const secKey = cbData.replace("/sec_", "");
    selectSection(secKey);
  } else if (cbData === "/menu" || cbData === "/main") {
    selectSection("main");
  } else {
    showToast(`Симуляція кнопки: ${cbData}`);
  }
}

function selectSection(key) {
  currentSection = key;
  renderSections();
  loadSectionEditor(key);
  updatePreview();
}

// Event bindings
document.querySelectorAll(".nav-item").forEach(btn => {
  btn.onclick = () => {
    document.querySelectorAll(".nav-item").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".tab-pane").forEach(p => p.classList.remove("active"));
    btn.classList.add("active");
    const target = document.getElementById(`tab-${btn.dataset.tab}`);
    if (target) target.classList.add("active");
  };
});

document.getElementById("btn-add-section").onclick = addNewSection;
document.getElementById("btn-delete-section").onclick = deleteCurrentSection;
document.getElementById("btn-apply-section").onclick = applySectionEditor;
document.getElementById("btn-add-user").onclick = addNewUser;

document.getElementById("preview-role-select").onchange = (e) => {
  currentRole = e.target.value;
  updatePreview();
};

document.getElementById("btn-save").onclick = async () => {
  if (!config) return;
  // Sync settings
  const tokenInput = document.getElementById("setting-bot-token");
  if (tokenInput) config.telegram_token = tokenInput.value.trim();
  const themeInput = document.getElementById("setting-theme");
  if (themeInput) config.theme = themeInput.value;
  const roleInput = document.getElementById("setting-default-role");
  if (roleInput) config.default_role = roleInput.value;

  try {
    const res = await fetch(apiUrl("api/config"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(config)
    });
    if (res.ok) {
      showToast("✅ Всі зміни збережено успішно!");
    } else {
      const err = await res.json();
      alert("Помилка збереження: " + (err.error || "невідома помилка"));
    }
  } catch (e) {
    alert("Помилка збереження: " + e.message);
  }
};

loadConfig();
