// ================================
// ScamSniper Frontend JS
// Fully integrated with FastAPI backend
// ================================

// Shortcuts
const $ = s => document.querySelector(s);
const $$ = s => Array.from(document.querySelectorAll(s));

// -------------------------------
// --- Navigation & Sections ---
// -------------------------------
const navItems = $$('.nav-item');
const sections = $$('.section');

function showSection(id) {
  sections.forEach(s => s.style.display = 'none');
  const sec = $(`#${id}`);
  if (sec) sec.style.display = 'block';
  navItems.forEach(n => n.classList.remove('active'));
  const activeNav = navItems.find(n => n.dataset.section === id);
  if (activeNav) activeNav.classList.add('active');
}

// Show first section on load
if (sections.length) showSection(sections[0].id);

navItems.forEach(n => {
  n.addEventListener('click', () => {
    const sec = n.dataset.section;
    if (sec) showSection(sec);
  });
});

// -------------------------------
// --- Profile Handling ---
// -------------------------------
// const profile = JSON.parse(localStorage.getItem('profile') || '{}');

// function loadProfileForm() {
//   $('#profileName').value = profile.name || '';
//   $('#profileEmail').value = profile.email || '';
//   $('#profilePhone').value = profile.phone || '';
//   $('#profileUsername').value = profile.username || '';
//   // $('#profileImg').src = profile.image || 'https://via.placeholder.com/120';
// }

// function loadDashboardProfile() {
//   const username = profile.username || 'Guest';
//   const email = profile.email || '--';
//   const registered = profile.registered || '--';
//   const lastLogin = profile.lastLogin || '--';
//   const status = profile.status || 'Active';
//   // const image = profile.image || 'https://via.placeholder.com/120';

//   $('#dashboardUsername').textContent = username;
//   $('#dashboardEmail').textContent = email;
//   $('#dashboardRegistered').textContent = registered;
//   $('#dashboardLastLogin').textContent = lastLogin;
//   $('#dashboardStatus').textContent = status;

  // const img = $('#dashboardProfileImg');
  // img.src = image;
  // img.style.cssText = `
  //   width:180px;height:180px;border-radius:50%;object-fit:cover;
  //   border:4px solid transparent;padding:4px;
  //   background:linear-gradient(135deg,var(--accent),var(--accent-2));
  //   box-shadow:0 6px 20px rgba(0,0,0,0.4);
  // `;
// }

// loadProfileForm();
// loadDashboardProfile();

// Profile Upload
// $('#profileUpload')?.addEventListener('change', e => {
//   const file = e.target.files[0];
//   if (!file) return;
//   const reader = new FileReader();
//   reader.onload = event => {
//     profile.image = event.target.result;
//     $('#profileImg').src = profile.image;
//     loadDashboardProfile();
//   };
//   reader.readAsDataURL(file);
// });

// // Save Profile
// $('#saveProfileBtn')?.addEventListener('click', () => {
//   profile.name = $('#profileName').value.trim();
//   profile.email = $('#profileEmail').value.trim();
//   profile.phone = $('#profilePhone').value.trim();
//   profile.username = $('#profileUsername').value.trim() || 'Guest';
//   profile.registered = profile.registered || new Date().toLocaleDateString();
//   profile.lastLogin = new Date().toLocaleString();
//   profile.status = profile.status || 'Active';

//   localStorage.setItem('profile', JSON.stringify(profile));
//   $('#profileResult').textContent = 'Profile saved successfully!';
//   setTimeout(() => $('#profileResult').textContent = '', 3000);
//   loadDashboardProfile();
// });

// -------------------------------
// --- State Handling ---
// -------------------------------
const state = {
  scans: [],
  feedback: [],
  reports: [], 
  theme: localStorage.getItem('theme') || 'dark'
};

// -------------------------------
// --- Theme Handling ---
// -------------------------------
function applyTheme(theme) {
  document.body.classList.toggle('light', theme === 'light');
  state.theme = theme;
  localStorage.setItem('theme', theme);
}

applyTheme(state.theme);

$('#themeToggle')?.addEventListener('click', () => {
  const newTheme = state.theme === 'dark' ? 'light' : 'dark';
  applyTheme(newTheme);
});

// -------------------------------
// --- Helper Functions ---
// -------------------------------
const truncate = (str, n) => str.length > n ? str.slice(0, n - 1) + '…' : str;

async function saveScan(scan) {
  // 1️⃣ Save locally as before
  state.scans.push(scan);
  localStorage.setItem('scans', JSON.stringify(state.scans));
  refreshStats();

  // 2️⃣ Send scan to backend
  try {
    const res = await fetch('/scan/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(scan)
    });
    const data = await res.json();
    if (!data.success) {
      console.warn('Backend failed to save scan:', data);
    }
  } catch (err) {
    console.error('Error saving scan to backend:', err);
  }

  // 3️⃣ Update live alerts
  const live = $('#liveAlerts');
  if (live) {
    live.innerHTML = `<div style="padding:8px;border-radius:8px;background:rgba(255,255,255,0.02);margin-bottom:8px">
      <strong>${scan.type}</strong> — ${scan.verdict} 
      <div class="small">${new Date(scan.when).toLocaleTimeString()}</div>
    </div>` + live.innerHTML;
  }
}


function refreshStats() {
  const hist = $('#historyTable tbody');
  if (!hist) return;
  hist.innerHTML = '';
  state.scans.slice().reverse().forEach(s => {
    const tr = document.createElement('tr');
    tr.innerHTML = `<td style="font-size:14px;">${new Date(s.when).toLocaleString()}</td>
                    <td style="font-size:16px;">${truncate(s.input, 50)}</td>`;
    hist.appendChild(tr);
  });
}

// -------------------------------
// --- Backend API Helpers ---
// -------------------------------
async function postAPI(url, data) {
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    });
    if (!response.ok) throw new Error('API request failed');
    return await response.json();
  } catch (err) {
    console.error(`Error calling ${url}:`, err);
    return { error: err.message };
  }
}

async function postFormAPI(url, formData) {
  try {
    const response = await fetch(url, { method: 'POST', body: formData });
    if (!response.ok) throw new Error('API request failed');
    return await response.json();
  } catch (err) {
    console.error(`Error calling ${url}:`, err);
    return { error: err.message };
  }
}

function renderScanner(type) {
    const area = $('#scannerArea');
    area.innerHTML = '';

    let html = '';

    // Build scanner input fields
    if (type === 'text' || type === 'url' || type === 'otp') {
        const placeholder = type === 'text' ? 'Enter text to check' :
                            type === 'url' ? 'Enter URL to scan' :
                            'Enter OTP to verify';
        const btnText = type === 'otp' ? 'Check OTP' : `Scan ${type.charAt(0).toUpperCase() + type.slice(1)}`;
        html = `<${type==='text'?'textarea':'input'} id="scanInput" class="input" placeholder="${placeholder}"></${type==='text'?'textarea':'input'}>
                <button class="btn" id="scanBtn">${btnText}</button>
                <div class="result" id="scanResult"></div>`;
    } else if (type === 'image' || type === 'ocr') {
        html = `<input type="file" id="scanFile" accept="image/*">
                <button class="btn" id="scanBtn">Scan Image</button>
                <div class="result" id="scanResult"></div>`;
    } else if (type === 'email') {
        html = `<input type="text" id="emailSender" class="input" placeholder="Sender email">
                <input type="text" id="emailSubject" class="input" placeholder="Email subject">
                <textarea id="emailBody" class="input" placeholder="Email body"></textarea>
                <button class="btn" id="scanBtn">Scan Email</button>
                <div class="result" id="scanResult"></div>`;
    } else if (type === 'transaction') {
        html = `
            <div id="txnForm">
                <input type="number" id="txnAmount" placeholder="Amount" class="input"><br>
                <input type="text" id="txnCurrency" placeholder="Currency (USD/INR/...)" class="input"><br>
                <input type="text" id="txnTimestamp" placeholder="Timestamp (YYYY-MM-DD HH:MM:SS)" class="input"><br>
                <input type="text" id="txnId" placeholder="Transaction ID" class="input"><br>
                <input type="text" id="txnSender" placeholder="Sender Name" class="input"><br>
                <input type="text" id="txnRecipient" placeholder="Recipient Name" class="input"><br>
                <input type="text" id="txnStatus" placeholder="Status (completed/pending/etc.)" class="input"><br>
                <textarea id="txnDescription" placeholder="Description" class="input"></textarea><br>
                <input type="file" id="txnFile" accept="image/*"><br>
                <button class="btn" id="scanBtn">Scan Transaction</button>
                <div class="result" id="scanResult"></div>
            </div>
        `;
    }

    area.innerHTML = html;

    const btn = $('#scanBtn');
    if (!btn) return;

    function getRiskCategory(score) {
        if (score < 40) return { label: 'Safe', color: '#10b981' };
        if (score < 80) return { label: 'Suspicious', color: '#ffbf00' };
        return { label: 'Scam', color: '#ef4444' };
    }

    btn.addEventListener('click', async () => {
    const resultDiv = $('#scanResult');
    let input = '', verdict = 'Safe', score = 0, reasons = [];

    try {
      if(type === 'text' || type === 'url') {
        input = $('#scanInput').value.trim();
        if (!input) { alert(`Enter ${type}`); return; }
        const body = type==='text' ? { text: input, url: null } : { text: '', url: input };
        const data = await postAPI('/api/classify/', body);
        verdict = data.status?.toUpperCase() || 'SAFE';
        score = data.score ?? 0;
        reasons = data.reasons ?? [];
        const color = verdict === "SCAM" ? "#ef4444" : verdict === "SUSPICIOUS" ? "#ffbf00" : "#10b981";
        const reasonsDiv = reasons.length ? `<div class="small">Reasons: ${reasons.join(', ')}</div>` : '';
        resultDiv.innerHTML = `<div class="risk" style="color:${color}; font-weight:800;">${verdict}</div>
                               Score: ${score}${reasonsDiv}`;

      } else if(type === 'transaction') {
        const txnData = {
          amount: parseFloat($('#txnAmount').value),
          currency: $('#txnCurrency').value.trim(),
          timestamp: $('#txnTimestamp').value.trim(),
          transaction_id: $('#txnId').value.trim(),
          sender: $('#txnSender').value.trim(),
          recipient: $('#txnRecipient').value.trim(),
          status: $('#txnStatus').value.trim(),
          description: $('#txnDescription').value.trim()
        };
        const file = $('#txnFile').files[0];
        let data;
        if(file) {
          const formData = new FormData();
          formData.append('file', file);
          formData.append('transaction_json', JSON.stringify(txnData));
          const res = await fetch('/api/transaction/check-image', { method: 'POST', body: formData });
          data = await res.json();
        } else {
          const res = await fetch('/api/transaction/validate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(txnData)
          });
          data = await res.json();
        }
        score = data.risk_score ?? 0;
        const { label, color } = getRiskCategory(score);
        verdict = label;
        reasons = data.reasons ?? [];
        input = JSON.stringify(txnData);
        const textPreview = data.extracted_text ? `<div class="small">Extracted Text: ${data.extracted_text.substring(0,300)}</div>` : '';
        const reasonsDiv = reasons.length ? `<div class="small">Reasons: ${reasons.join(', ')}</div>` : '';
        resultDiv.innerHTML = `<div class="risk" style="color:${color}; font-weight:800;">${verdict.toUpperCase()}</div>
                               Score: ${score}${textPreview}${reasonsDiv}`;

      } else if(type === 'image' || type === 'ocr') {
        const file = $('#scanFile').files[0];
        if (!file) { alert('Select an image'); return; }
        input = file.name;
        const formData = new FormData();
        formData.append('file', file);
        const res = await fetch('/api/ocr/scan', { method:'POST', body: formData });
        const data = await res.json();
        if(data.error){
          verdict="Unknown"; score=0; resultDiv.textContent="Error: "+data.error;
        } else {
          score=data.score??0; 
          const {label,color}=getRiskCategory(score); 
          verdict=label;
          const textPreview = data.text_extracted ? `<div class="small">Text: ${data.text_extracted.substring(0,100)}</div>` : '';
          resultDiv.innerHTML=`<div class="risk" style="color:${color}; font-weight:800;">${verdict}</div>Score: ${score}${textPreview}`;
        }

      } else if(type === 'email') {
        const sender = $('#emailSender').value.trim();
        const subject = $('#emailSubject').value.trim();
        const bodyText = $('#emailBody').value.trim();
        if (!sender || !subject || !bodyText) { alert('Enter sender, subject, body'); return; }
        const body = { sender, subject, body: bodyText };
        input = `${sender} | ${truncate(subject,50)}`;
        const res = await fetch('/api/email/check', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body)});
        const data = await res.json();
        score=data.risk_score??0;
        const {label,color}=getRiskCategory(score);
        verdict=label;
        reasons=data.reasons??[];
        const reasonsDiv = reasons.length ? `<div class="small">Reasons: ${reasons.join(', ')}</div>` : '';
        resultDiv.innerHTML=`<div class="risk" style="color:${color}; font-weight:800;">${verdict}</div>Score: ${score}${reasonsDiv}`;
      }

      // ✅ Save scan exactly once
      saveScan({ type, input, verdict, score, when: Date.now() });
      renderTrendChart();
      renderRiskGauge(score);

    } catch(err){
      console.error(err);
      resultDiv.textContent='Error: Failed to scan.';
    }
  });
}

// Initialize scanner
$('#scannerType').addEventListener('change', e => renderScanner(e.target.value));
renderScanner($('#scannerType').value);



// -------------------------------
// --- Feedback & Complaints ---
// -------------------------------
// Submit feedback
// Load feedback from backend
async function loadFeedback() {
    try {
        const res = await fetch('/feedback/all');
        if (!res.ok) throw new Error('Failed to fetch feedback');
        state.feedback = await res.json();

        // Optionally render feedback in a table or list
        const tbody = $('#feedbackTable tbody');
        if (!tbody) return;
        tbody.innerHTML = '';
        state.feedback.slice().reverse().forEach(f => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${new Date(f.timestamp).toLocaleString()}</td>
                <td>${f.message}</td>
                <td>${f.id}</td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        console.error(err);
    }
}

// Submit new feedback
async function submitFeedback(message) {
    if (!message.trim()) {
        alert('Enter a message for feedback');
        return;
    }

    const payload = { message: message.trim() };

    try {
        const res = await fetch('/feedback/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await res.json();

        if (data.id) {
            state.feedback.push({ ...payload, id: data.id, timestamp: Date.now() });
            $('#feedbackInput').value = '';
            $('#feedbackResult').textContent = 'Feedback submitted successfully!';
            setTimeout(() => { $('#feedbackResult').textContent = ''; }, 3000);
            await loadFeedback(); // Refresh table from backend
        } else {
            $('#feedbackResult').textContent = 'Failed to submit feedback.';
        }
    } catch (err) {
        console.error(err);
        $('#feedbackResult').textContent = 'Error submitting feedback.';
    }
}

// Event listener for feedback submission
$('#submitFeedbackBtn')?.addEventListener('click', () => {
    const message = $('#feedbackInput')?.value || '';
    submitFeedback(message);
});

// Initial load
loadFeedback();


// -------------------------------
// --- Scam Report Submission ---
// -------------------------------

$('#submitReportBtn')?.addEventListener('click', async () => {
    const text = $('#reportText').value.trim();
    const category = $('#reportCategory').value.trim();

    if (!text) {
        alert('Enter text for the report');
        return;
    }

    const payload = { text, category: category || null };

    try {
        const res = await fetch('/report/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await res.json();

        if (data.report_id) {
            $('#reportResult').textContent = `Reported successfully! ID: ${data.report_id}`;
            $('#reportText').value = '';
            $('#reportCategory').value = '';
            await fetchReports();  // Refresh table after successful submission
        } else {
            $('#reportResult').textContent = 'Failed to report.';
        }

        setTimeout(() => { $('#reportResult').textContent = ''; }, 5000);
    } catch (err) {
        console.error(err);
        $('#reportResult').textContent = 'Error submitting report.';
    }
});

// -------------------------------
// --- Fetch & Render Reports ---
// -------------------------------
async function fetchReports() {
    try {
        const res = await fetch('/report/all');
        if (!res.ok) throw new Error('Failed to fetch reports');
        const reports = await res.json();

        const tbody = $('#reportsTable tbody');
        if (!tbody) return;

        tbody.innerHTML = '';
        reports.slice().reverse().forEach(r => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${new Date(r.timestamp).toLocaleString()}</td>
                <td>${truncate(r.text, 50)}</td>
                <td>${r.category || '-'}</td>
                <td>${r.id}</td>
            `;
            tbody.appendChild(tr);
        });

    } catch (err) {
        console.error(err);
    }
}

// -------------------------------
// --- Initial Load ---
// -------------------------------
fetchReports();



// -------------------------------
// --- Logout ---
// -------------------------------
$('#logout')?.addEventListener('click', () => alert('Demo logout'));

// -------------------------------
// --- Charts ---
// -------------------------------
const trendCtx = document.getElementById('trendChart')?.getContext('2d');
let trendChart = trendCtx ? new Chart(trendCtx, {
  type: 'line',
  data: { labels: [], datasets: [{ label: 'Scans', data: [], fill: true, tension: 0.4 }] },
  options: { plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } }
}) : null;

function renderTrendChart() {
  if (!trendChart) return;
  const last7 = state.scans.slice(-7);
  trendChart.data.labels = last7.map(s => new Date(s.when).toLocaleDateString());
  trendChart.data.datasets[0].data = last7.map(s => s.score);
  trendChart.update();
}

function renderRiskGauge(score=80) {
  const canvas = document.getElementById("riskGauge");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  if (window.riskGaugeChart) window.riskGaugeChart.destroy();

  const gradient = ctx.createLinearGradient(0, 0, canvas.width, 0);
  gradient.addColorStop(0, "#0ba7b5");
  gradient.addColorStop(1, "#2fe3b0");

  window.riskGaugeChart = new Chart(ctx, {
    type: "doughnut",
    data: { datasets: [{ data: [score, 100 - score], backgroundColor: [gradient, "#22303F"], borderWidth: 0 }] },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      rotation: -90 * Math.PI / 180,
      circumference: 180 * Math.PI / 180,
      cutout: "65%",
      plugins: { legend: { display: false }, tooltip: { enabled: false } }
    }
  });

  const t = document.getElementById("riskText");
  if (t) t.textContent = score > 70 ? "High Risk" : score > 40 ? "Medium Risk" : "Low Risk";
}

// -------------------------------
// --- Initial Setup ---
// -------------------------------
$$('.package').forEach((p,i)=>p.style.display = i<3 ? 'block' : 'none');

const notificationBtn = $('#notificationBtn');
const notificationDropdown = $('#notificationDropdown');
notificationBtn?.addEventListener('click', e => {
  e.stopPropagation();
  notificationDropdown.style.display = notificationDropdown.style.display==='block'?'none':'block';
});
document.addEventListener('click', () => { if(notificationDropdown) notificationDropdown.style.display = 'none'; });

refreshStats();
renderTrendChart();
renderRiskGauge(80);
