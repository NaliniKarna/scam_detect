// ================================
// Admin Dashboard JS - Backend Integrated
// ================================

// Shortcuts
const $ = s => document.querySelector(s);
const $$ = s => Array.from(document.querySelectorAll(s));

// --- LOGIN FLOW ---
const loginForm = $('#loginForm');
const loginError = $('#loginError');
const loginPage = $('#loginPage');
const dashboardPage = $('#dashboardPage');
const logoutBtn = $('#logout');

// Hardcoded admin credentials
const ADMIN_EMAIL = "admin@gmail.com";
const ADMIN_PASSWORD = "admin123";

// Show login first
loginPage.style.display = "flex";
dashboardPage.style.display = "none";

// LOGIN FORM SUBMIT
loginForm.addEventListener("submit", e => {
  e.preventDefault();
  const email = $("#email").value.trim();
  const password = $("#password").value.trim();

  if (email === ADMIN_EMAIL && password === ADMIN_PASSWORD) {
    loginPage.style.display = "none";
    dashboardPage.style.display = "flex";
    loginError.textContent = "";
    refreshStats();
  } else {
    loginError.textContent = "Invalid email or password";
  }
});

// --- PASSWORD TOGGLE ---
const togglePassword = $('#togglePassword');
const passwordInput = $('#password');

if (togglePassword && passwordInput) {
  togglePassword.addEventListener('click', () => {
    const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
    passwordInput.setAttribute('type', type);
    togglePassword.classList.toggle('fa-eye-slash');
  });
}

// --- LOGOUT ---
logoutBtn.addEventListener("click", () => {
  dashboardPage.style.display = "none";
  loginPage.style.display = "flex";
});

// --- NAVIGATION ---
$$('.nav-item').forEach(n => {
  n.addEventListener('click', () => {
    $$('.nav-item').forEach(i => i.classList.remove('active'));
    n.classList.add('active');

    const sec = n.dataset.section;
    $$('.section').forEach(s => s.style.display = 'none');
    $(`#${sec}`).style.display = 'block';
  });
});

// --- STATE ---
const state = {
  scans: [],
  feedback: [],
  support: [],
  settings: {},
  theme: 'dark'
};

// --- FETCH SETTINGS ---
async function loadSettings() {
  try {
    const res = await fetch("/api/settings");
    if (!res.ok) throw new Error("Failed to fetch settings");
    state.settings = await res.json();
    renderSettings();
  } catch (err) {
    console.error(err);
  }
}

// --- RENDER SETTINGS ---
function renderSettings() {
  for (const key in state.settings) {
    const el = document.getElementById(key);
    if (el) el.textContent = state.settings[key];
  }
}

// --- INIT EDIT BUTTONS ---
function initSettingsEdit() {
  document.querySelectorAll('.edit-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      const itemValue = btn.previousElementSibling;
      if (!itemValue) return;

      if (itemValue.isContentEditable) {
        // Save changes
        itemValue.contentEditable = false;
        btn.textContent = 'Edit';
        const key = itemValue.id;
        const value = itemValue.textContent;

        // Update backend
        try {
          const res = await fetch("/api/settings", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ key, value })
          });
          const data = await res.json();
          if (data.success) {
            state.settings[key] = value;
          }
        } catch (err) {
          console.error("Failed to update setting:", err);
          alert("Failed to save setting");
        }

      } else {
        // Enable editing
        itemValue.contentEditable = true;
        itemValue.focus();
        btn.textContent = 'Save';
      }
    });
  });
}

// --- INITIALIZE ---
loadSettings().then(initSettingsEdit);

// --- THEME ---
$('#themeToggle').addEventListener('click', () => {
  document.body.classList.toggle('light');
  state.theme = document.body.classList.contains('light') ? 'light' : 'dark';
});

const themeSelect = $('#themeSelect');
themeSelect.addEventListener('change', () => {
  const val = themeSelect.value;
  document.body.classList.toggle('light', val === 'light');
  state.theme = val;
});

// --- SCANS ---
// Load scans from backend
async function loadScans() {
  try {
    const res = await fetch("/scan/all");
    if (!res.ok) throw new Error("Failed to load scans");
    state.scans = await res.json();
    renderHistoryTable();
    refreshStats();
  } catch (err) {
    console.error(err);
  }
}

// Save scan to backend
async function saveScan(scan) {
  try {
    const res = await fetch("/scan/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(scan)
    });
    const data = await res.json();
    if (data.id) scan.id = data.id;
    scan.when = Date.now();
    state.scans.push(scan);
    renderHistoryTable();
    refreshStats();
  } catch (err) {
    console.error(err);
  }
}

// --- HELPERS ---
function truncate(str, n) {
  return str.length > n ? str.slice(0, n - 1) + "…" : str;
}

// --- DELETE SCAN ---
async function deleteHistory(index) {
  if (!confirm("Delete this history entry?")) return;
  const scan = state.scans[index];
  state.scans.splice(index, 1);
  renderHistoryTable();
  refreshStats();
  // Optionally you can add a backend delete endpoint
}

// --- CLEAR ALL HISTORY ---
async function clearAllHistory() {
  if (!confirm("Clear ALL scan history?")) return;
  state.scans = [];
  renderHistoryTable();
  refreshStats();
  // Optionally add backend support for clearing all scans
}

// --- RENDER HISTORY ---
function renderHistoryTable() {
  const tbody = $('#historyTable tbody');
  if (!tbody) return;

  tbody.innerHTML = "";
  state.scans.slice().reverse().forEach((s, idx) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${s.username || "admin"}</td>
      <td>${truncate(s.input || "N/A", 40)}</td>
      <td class="small">${new Date(s.when).toLocaleString()}</td>
      <td>
        <button class="btn ghost btn-sm" onclick="deleteHistory(${state.scans.length - 1 - idx})">
          Delete
        </button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

// --- DASHBOARD STATS ---
function refreshStats() {
  $('#totalScans').textContent = state.scans.length;
  $('#scamsDetected').textContent = state.scans.filter(s => s.verdict === "Scam").length;
  $('#activeUsers').textContent = 57;
  renderHistoryTable();
}

// --- SIMPLE CHART ---
const ctx = document.getElementById("trendChart").getContext("2d");
new Chart(ctx, {
  type: "line",
  data: {
    labels: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
    datasets: [
      {
        label: "Scans",
        data: [12, 19, 8, 15, 22, 11, 18],
        fill: true,
        tension: 0.4
      }
    ]
  },
  options: { plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } }
});

// --- FEEDBACK ---
async function loadFeedback() {
  try {
    const res = await fetch("/feedback/all");
    if (!res.ok) throw new Error("Failed to load feedback");
    state.feedback = await res.json();
    renderFeedbackTable();
  } catch (err) { console.error(err); }
}

function renderFeedbackTable() {
  const tbody = $('#feedbackTable tbody');
  if (!tbody) return;
  tbody.innerHTML = "";
  state.feedback.slice().reverse().forEach(f => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${f.message}</td>
      <td class="small">${new Date(f.when).toLocaleString()}</td>
    `;
    tbody.appendChild(tr);
  });
}

$('#submitFeedback').addEventListener("click", async () => {
  const f = $("#feedbackInput").value.trim();
  if (!f) return alert("Enter feedback");

  const payload = { message: f };
  try {
    const res = await fetch("/feedback/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (data.feedback_id) {
      state.feedback.push({ message: f, id: data.feedback_id, when: Date.now() });
      $("#feedbackInput").value = "";
      renderFeedbackTable();
    }
  } catch (err) { console.error(err); }
});

// --- SUPPORT ---
async function loadSupport() {
  try {
    const res = await fetch("/support/all");
    if (!res.ok) throw new Error("Failed to load support");
    state.support = await res.json();
    renderSupportTable();
  } catch (err) { console.error(err); }
}

function renderSupportTable() {
  const tbody = $('#supportTable tbody');
  if (!tbody) return;
  tbody.innerHTML = "";
  state.support.slice().reverse().forEach(s => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${s.text || "N/A"}</td>
      <td class="small">${new Date(s.when).toLocaleString()}</td>
      <td>${s.file || "-"}</td>
    `;
    tbody.appendChild(tr);
  });
}

$('#submitSupport').addEventListener("click", async () => {
  const txt = $("#supportInput").value.trim();
  const fileInput = $("#supportFile")?.files[0];
  if (!txt && !fileInput) return alert("Enter issue or file");

  const formData = new FormData();
  formData.append("text", txt);
  if (fileInput) formData.append("file", fileInput);

  try {
    const res = await fetch("/support/", { method: "POST", body: formData });
    const data = await res.json();
    if (data.support_id) {
      state.support.push({ text: txt, file: fileInput?.name, id: data.support_id, when: Date.now() });
      $("#supportInput").value = "";
      if ($("#supportFile")) $("#supportFile").value = "";
      renderSupportTable();
    }
  } catch (err) { console.error(err); }
});

// --- INIT ---
loadScans();
loadFeedback();
loadSupport();
refreshStats();
