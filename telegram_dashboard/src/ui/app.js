let config = null;
let currentSection = "main";
let currentRole = "admin";

async function loadConfig() {
  try {
    const res = await fetch("/api/config");
    config = await res.json();
    renderSections();
    renderUsers();
    updatePreview();
  } catch (err) {
    console.error("Failed to load config:", err);
  }
}

function renderSections() {
  const container = document.getElementById("sections-list");
  if (!container || !config) return;
  container.innerHTML = "";

  Object.entries(config.menu).forEach(([key, sec]) => {
    const item = document.createElement("div");
    item.className = `section-item ${key === currentSection ? "active" : ""}`;
    item.innerHTML = `
      <div class="section-item-header">
        <strong>${sec.icon || "📄"} ${sec.title || key}</strong>
        <span class="badge">${(sec.roles || []).join(", ")}</span>
      </div>
      <small style="color: #94a3b8;">/${key}</small>
    `;
    item.onclick = () => {
      currentSection = key;
      renderSections();
      updatePreview();
    };
    container.appendChild(item);
  });
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
      <td><button class="btn btn-secondary btn-sm" onclick="removeUser(${u.telegram_id})">Видалити</button></td>
    `;
    tbody.appendChild(tr);
  });
}

async function removeUser(uid) {
  if (!confirm(`Видалити користувача ${uid}?`)) return;
  await fetch(`/api/users/${uid}`, { method: "DELETE" });
  loadConfig();
}

async function updatePreview() {
  if (!config) return;
  const sec = config.menu[currentSection] || config.menu["main"];
  const res = await fetch("/api/preview", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ section: sec })
  });
  const data = await res.json();
  document.getElementById("preview-text").innerHTML = data.html || "—";

  // Render mock inline buttons
  const btnContainer = document.getElementById("preview-buttons");
  btnContainer.innerHTML = "";
  if (currentSection === "main") {
    const row = document.createElement("div");
    row.className = "tg-btn-row";
    row.innerHTML = `
      <button class="tg-btn" onclick="selectSection('climate')">🌡 Клімат</button>
      <button class="tg-btn" onclick="selectSection('water')">🚰 Вода</button>
    `;
    btnContainer.appendChild(row);
    const row2 = document.createElement("div");
    row2.className = "tg-btn-row";
    row2.innerHTML = `
      <button class="tg-btn" onclick="selectSection('battery')">🔋 Батареї</button>
      <button class="tg-btn" onclick="selectSection('system')">⚙️ Система</button>
    `;
    btnContainer.appendChild(row2);
  } else {
    const backRow = document.createElement("div");
    backRow.className = "tg-btn-row";
    backRow.innerHTML = `
      <button class="tg-btn" onclick="updatePreview()">🔄 Оновити</button>
      <button class="tg-btn" onclick="selectSection('main')">⬅️ Головна</button>
    `;
    btnContainer.appendChild(backRow);
  }
}

function selectSection(key) {
  currentSection = key;
  renderSections();
  updatePreview();
}

// Tab navigation
document.querySelectorAll(".nav-item").forEach(btn => {
  btn.onclick = () => {
    document.querySelectorAll(".nav-item").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".tab-pane").forEach(p => p.classList.remove("active"));
    btn.classList.add("active");
    const target = document.getElementById(`tab-${btn.dataset.tab}`);
    if (target) target.classList.add("active");
  };
});

document.getElementById("preview-role-select").onchange = (e) => {
  currentRole = e.target.value;
  updatePreview();
};

document.getElementById("btn-save").onclick = async () => {
  const res = await fetch("/api/config", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(config)
  });
  if (res.ok) alert("✅ Налаштування успішно збережено!");
};

loadConfig();
