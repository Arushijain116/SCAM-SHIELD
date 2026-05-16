const BASE_URL = "http://127.0.0.1:5000";

// --------- GLOBAL STATE ---------
let polling = null;
let isScanning = false;
let pieChartInstance = null;
let barChartInstance = null;

// --------- AUTH ---------

async function loginUser() {
    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value.trim();

    if (!username || !password) {
        alert("Enter username and password");
        return;
    }

    try {
        const res = await fetch(`${BASE_URL}/login`, {
            method: "POST",
            credentials: "include",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ username, password })   // ✅ FIXED
        });

        const data = await res.json();

        if (res.ok) {
            window.location.href = "dashboard.html";
        } else {
            alert(data.error || "Login failed");
        }

    } catch (err) {
        console.error("❌ Login error:", err);
        alert("Server not reachable");
    }
}

async function loadAdminStats() {
  const res = await fetch(`${BASE_URL}/admin/stats`, {
    credentials: "include"
  });

  if (res.status === 403) return; // not admin

  const data = await res.json();

  const box = document.getElementById("adminPanel");
  if (!box) return;

  box.innerHTML = `
  <h2>👑 Admin Dashboard</h2>
  <p>Total Users: ${data.total_users}</p>
  <p>Total Scans: ${data.total_scans}</p>

  <canvas id="adminChart"></canvas>   <!-- 🔥 ADD THIS -->

  ${data.users.map(u => `
    <div>
      <b>${u.username}</b> – Scans: ${u.total_scans}
    </div>
  `).join("")}
`;
// 🔥 ADD HERE (AFTER innerHTML)
const ctx = document.getElementById("adminChart");

if (ctx && typeof Chart !== "undefined") {
    new Chart(ctx.getContext("2d"), {
        type: "bar",
        data: {
            labels: data.users.map(u => u.username),
            datasets: [{
                label: "Scans per user",
                data: data.users.map(u => u.total_scans)
            }]
        }
    });
}
}

async function register() {
  const username = document.getElementById("username").value.trim().toLowerCase();
  const password = document.getElementById("password").value.trim();

  try {
    const res = await fetch(`${BASE_URL}/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password })
    });

    const data = await res.json();
    alert(data.message || data.error);

  } catch (err) {
    console.error(err);
    alert("Server error");
  }
}

async function logout() {
  await fetch(`${BASE_URL}/logout`, { credentials: "include" });
  window.location.replace("login.html");
}

// --------- SCAN ---------

async function scan() {
  if (isScanning) return;

  const text = document.getElementById("inputText")?.value || "";
  const loading = document.getElementById("loading");

  if (!text.trim()) {
    alert("Enter text");
    return;
  }

  isScanning = true;
  stopPolling();
  loading && (loading.style.display = "block");

  try {
    const res = await fetch(`${BASE_URL}/predict`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
      credentials: "include"
    });

    if (res.status === 401) {
      window.location = "login.html";
      return;
    }

    const data = await res.json();

    localStorage.setItem("lastScan", JSON.stringify({ data, text }));
    updateUI(data, text);

  } catch (e) {
    console.error(e);
    alert("Backend error");
  } finally {
    loading && (loading.style.display = "none");
    isScanning = false;
  }
}

// --------- UI UPDATE ---------

function updateUI(data, text) {
  
 const result = document.getElementById("result");
  const meter = document.getElementById("meter");
  const scoreEl = document.getElementById("score");

  if (!result) return;

  result.classList.add("fade-in");

  // ---------- 🧠 AI EXPLANATION ----------
  const pros = Array.isArray(data.pros) ? data.pros : [];
  const cons = Array.isArray(data.cons) ? data.cons : [];

  const proshtml = pros.map(p => `<li>✅ ${p}</li>`).join("");
  const conshtml = cons.map(c => `<li>❌ ${c}</li>`).join("");

  result.innerHTML = `
    <h3>${badge(data.risk)} ${data.risk}</h3>
    <p><b>Confidence:</b> ${data.confidence}%</p>

    <h4>🧠 AI Explanation</h4>

    <div class="explain-box">
      <div>
        <h5>✅ Safe Signals</h5>
        <ul>${proshtml || "<li>No strong safe signals</li>"}</ul>
      </div>

      <div>
        <h5>⚠️ Risk Signals</h5>
        <ul>${conshtml || "<li>No strong safe signals</li>"}</ul>
      </div>
    </div>

    ${cons.some(c => c.includes("Link")) ? `
  <div class="link-warning">
    🔗 Suspicious link detected — avoid clicking
  </div>
` : ""}

    <p><b>Pattern:</b> ${data.pattern || "-"}</p>
    ${data.pattern === "Scam Pattern" ? `
    <div class="warning-box">
      ⚠️ This message contains potentially harmful links. Avoid clicking them.
    </div>
  ` : ""}

    <div class="summary-box">
  <h4>📌 Final Verdict</h4>
  <p>${data.summary || "No summary available"}</p>
</div>

    <div class="text-box">${escapeHtml(text)}</div>
  `; 

  // ---------- 🎯 AI RISK METER ----------
  if (meter && scoreEl) {
    let color = "#22c55e"; // Safe (green)
    if (data.risk === "Suspicious") color = "#f59e0b"; // yellow
    if (data.risk === "High Risk") color = "#ef4444"; // red

    let scoreValue = data.trust_score;

    if (scoreValue === undefined) {
    if (data.risk === "High Risk") scoreValue = 20;
    else if (data.risk === "Suspicious") scoreValue = 50;
    else scoreValue = 90;
    }

    const target = Math.max(0, Math.min(100, Number(scoreValue)));

    // 🧠 stop previous animation (IMPORTANT)
    if (window.meterAnim) cancelAnimationFrame(window.meterAnim);

    let current = 0;
    const duration = 700; // ms
    const startTime = performance.now();

    function animate(now) {
      const progress = Math.min((now - startTime) / duration, 1);
      current = Math.round(progress * target);

      meter.style.background =
        `conic-gradient(${color} ${current}%, #334155 ${current}%)`;
      scoreEl.innerText = current;

      if (progress < 1) {
        window.meterAnim = requestAnimationFrame(animate);
      }
    }

    window.meterAnim = requestAnimationFrame(animate);

    // ✨ Optional: dynamic glow based on risk
    meter.style.boxShadow =
      data.risk === "High Risk"
        ? "0 0 25px rgba(239,68,68,0.7)"
        : data.risk === "Suspicious"
        ? "0 0 25px rgba(245,158,11,0.7)"
        : "0 0 25px rgba(34,197,94,0.7)";
  }
}

// --------- HELPERS ---------

function setText(id, val) {
  const el = document.getElementById(id);
  if (el) el.innerText = val ?? 0;
}

function badge(risk) {
  if (risk === "High Risk") return `<span class="badge risk">High Risk</span>`;
  if (risk === "Suspicious") return `<span class="badge warn">Suspicious</span>`;
  return `<span class="badge safe">Safe</span>`;
}

function escapeHtml(s) {
  return (s || "").replace(/[&<>"']/g, m => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    "\"": "&quot;",
    "'": "&#39;"
  }[m]));
}

function login() {
    loginUser();
}
// --------- ALERTS ---------

async function loadAlerts() {
  const res = await fetch(`${BASE_URL}/alerts`, {
    credentials: "include"
  });

  const data = await res.json();

  const container = document.getElementById("alertsFeed");
  if (!container) return;

  container.innerHTML = data.map((a, index) => `
    <div class="alert-card">

      <div class="alert-title">
        🚨 ${a.type} (${a.level})
      </div>

      <div class="alert-desc">
        ${a.message}
      </div>

      <!-- 🔽 HIDDEN DETAILS -->
      <div class="alert-more hidden" id="more-${index}">
        <p><b>Why this is dangerous:</b> ${getExplanation(a.type)}</p>
        <p><b>What you should do:</b> ${generateAdvice(a.type)}</p>
      </div>

      <button class="read-btn" onclick="toggleAlert(${index})">
        Read More
      </button>

    </div>
  `).join("");
}

// --------- NOTIFICATIONS ---------

async function loadNotifications() {
  const res = await fetch(`${BASE_URL}/notifications`, { credentials: "include" });
  const data = await res.json();

  const box = document.getElementById("notificationBox");
  if (!box) return;

  box.innerHTML = "<b>Recent</b>";
  data.forEach(n => {
    box.innerHTML += `<p>${n.time} - ${n.msg}</p>`;
  });
}

// --------- STATS ---------

async function loadStats() {
  try {
    const res = await fetch(`${BASE_URL}/stats`, { credentials: "include" });
    const data = await res.json();

    // 🟢 CARDS
    setText("total", data.total);
    setText("scam", data.scam);
    setText("safe", data.safe);

    // 🟡 PIE CHART (Scam vs Safe)
    const pie = document.getElementById("pieChart");
    if (pie && typeof Chart !== "undefined") {
      if (pieChartInstance) pieChartInstance.destroy();

      pieChartInstance = new Chart(pie.getContext("2d"), {
        type: "doughnut",
        data: {
          labels: ["Scam", "Safe"],
          datasets: [{
            data: [data.scam, data.safe],
            backgroundColor: ["#ef4444", "#22c55e"]
          }]
        },
        options: {
          plugins: {
            legend: { labels: { color: "white" } },
            tooltip: {
              callbacks: {
                label: function(ctx) {
                  let total = ctx.dataset.data.reduce((a, b) => a + b, 0);
                  let val = ctx.raw;
                  let percent = ((val / total) * 100).toFixed(1);
                  return `${ctx.label}: ${val} (${percent}%)`;
                }
              }
            }
          }
        }
      });
    }

    // 🔵 BAR CHART (Risk over time)
    const bar = document.getElementById("barChart");
    if (bar && typeof Chart !== "undefined") {
      if (barChartInstance) barChartInstance.destroy();

      barChartInstance = new Chart(bar.getContext("2d"), {
        type: "bar",
        data: {
          labels: data.history.map(h => h.time),
          datasets: [{
            label: "Risk Level (1=Safe, 2=Suspicious, 3=High Risk)",
            data: data.history.map(h =>
              h.risk === "High Risk" ? 3 :
              h.risk === "Suspicious" ? 2 : 1
            ),
            backgroundColor: data.history.map(h =>
              h.risk === "High Risk" ? "#ef4444" :
              h.risk === "Suspicious" ? "#f59e0b" : "#22c55e"
            )
          }]
        },
        options: {
          scales: {
            y: {
              ticks: { color: "white" }
            },
            x: {
              ticks: { color: "white" }
            }
          },
          plugins: {
            legend: { labels: { color: "white" } }
          }
        }
      });
    }

    // 🔥 RISK DISTRIBUTION
    const riskCanvas = document.getElementById("riskChart");

    if (riskCanvas && data.risk_distribution) {
      if (window.riskChartInstance) window.riskChartInstance.destroy();

      window.riskChartInstance = new Chart(riskCanvas.getContext("2d"), {
        type: "pie",
        data: {
          labels: Object.keys(data.risk_distribution),
          datasets: [{
            data: Object.values(data.risk_distribution),
            backgroundColor: ["#ef4444", "#f59e0b", "#22c55e"]
          }]
        },
        options: {
          plugins: {
            legend: { labels: { color: "white" } },
            tooltip: {
              callbacks: {
                label: ctx => `${ctx.label}: ${ctx.raw} cases`
              }
            }
          }
        }
      });
    }

    // 📜 TABLE
    const tbody = document.querySelector("#historyTable tbody");
    if (tbody) {
      tbody.innerHTML = "";
      data.history.forEach(h => {
        tbody.innerHTML += `
          <tr>
            <td>${h.time}</td>
            <td>${h.text}</td>
            <td>${h.risk}</td>
          </tr>`;
      });
    }

    // 🧠 AI INSIGHTS (SAFE POSITION)
    const insightsBox = document.getElementById("insightsList");
    if (insightsBox) {
      const insights = generateInsights(data);
      insightsBox.innerHTML = insights.map(i => `<li>• ${i}</li>`).join("");
    }

  } catch (e) {
    console.error("Stats error:", e);
  }
}



// --------- POLLING ---------

function generateInsights(data) {
  const insights = [];

  const total = data.total || 0;
  const scam = data.scam || 0;
  const safe = data.safe || 0;
  const dist = data.risk_distribution || {};

  if (total === 0) {
    return ["No scan data available yet."];
  }

  const scamPercent = ((scam / total) * 100).toFixed(1);

  // 📊 Risk Level
  if (scam > safe) {
    insights.push(`🔴 High threat: ${scamPercent}% messages are scams.`);
  } else {
    insights.push(`🟢 Low threat: only ${scamPercent}% messages risky.`);
  }

  // ⚠️ Distribution
  if (dist["High Risk"] > 0) {
    insights.push(`⚠️ ${dist["High Risk"]} high-risk cases detected.`);
  }

  if (dist["Suspicious"] > dist["Safe"]) {
    insights.push("🟡 Suspicious activity is relatively high.");
  }

  // 📈 Activity
  if (data.history.length > 2) {
    insights.push("📈 Recent scanning activity is consistent.");
  }

  // 🧠 Recommendation
  insights.push("🔐 Avoid sharing OTPs and clicking unknown links.");

  return insights;
}



function startPolling() {
  if (polling) return;

  polling = setInterval(() => {

    // 🔥 DO NOT override result UI
    if (!document.getElementById("result")?.innerHTML) {
      if (document.getElementById("alertsContainer")) loadAlerts();
      if (document.getElementById("notificationBox")) loadNotifications();
      if (document.getElementById("pieChart")) loadStats();
    }

  }, 5000);
}

function stopPolling() {
  if (polling) {
    clearInterval(polling);
    polling = null;
  }
}

// --------- INIT ---------

window.onload = () => {
  const isScanPage = !!document.getElementById("inputText");
  const isDashboard = !!document.getElementById("pieChart");

  if (isScanPage) {
    const saved = localStorage.getItem("lastScan");
    if (saved) {
      const parsed = JSON.parse(saved);
      updateUI(parsed.data, parsed.text);
    }
  }

  if (isDashboard) {
    loadStats();
    loadAlerts();
    loadNotifications();
    loadAdminStats(); // 🔥 ADD THIS
}

  if (!isScanPage && !document.getElementById("result")) {
  startPolling();
}
};

// --------- HELP SECTION DATA ---------

const helpData = {

  alerts: {
    title: "🚨 Scam Alerts",
    content: `
      <p>Scam alerts highlight real-time fraud patterns used by attackers.</p>

      <ul>
        <li>Bank KYC scams via SMS</li>
        <li>Fake job offers demanding money</li>
        <li>OTP phishing calls</li>
      </ul>

      <div class="example-box">
        <b>Example:</b><br>
        "Your bank account will be blocked! Click here immediately."
      </div>

      <p><b>Key Trick:</b> Urgency + fear to force quick action.</p>
    `
  },

  learn: {
    title: "📚 Types of Scams",
    content: `
      <ul>
        <li><b>Phishing:</b> Fake login pages stealing credentials</li>
        <li><b>Lottery Scam:</b> Fake winnings requiring payment</li>
        <li><b>Job Scam:</b> Asking money before hiring</li>
        <li><b>KYC Fraud:</b> Fake verification requests</li>
      </ul>

      <div class="example-box">
        "Congratulations! You won ₹5,00,000. Pay ₹500 to claim."
      </div>

      <p><b>Pattern:</b> Greed + reward trap</p>
    `
  },

  advice: {
    title: "🛡️ Safety Tips",
    content: `
      <ul>
        <li>Never share OTP or passwords</li>
        <li>Always verify links before clicking</li>
        <li>Do not trust unknown calls or emails</li>
        <li>Use official apps/websites only</li>
      </ul>

      <div class="example-box">
        "Banks NEVER ask for OTP via phone."
      </div>

      <p><b>Golden Rule:</b> If it feels urgent or too good → it's likely a scam.</p>
    `
  },

  ai: {
    title: "🧠 How Scam Shield Works",
    content: `
      <p>Scam Shield uses AI + pattern analysis to detect fraud.</p>

      <ul>
        <li>Keyword detection (OTP, urgent, reward)</li>
        <li>Link analysis (suspicious URLs)</li>
        <li>Behavioral patterns (fear, urgency)</li>
      </ul>

      <div class="example-box">
        Example detection:
        <br>"Click now or account blocked"
        <br>→ flagged as High Risk
      </div>

      <p><b>Result:</b> You get risk level + explanation instantly.</p>
    `
  }

};

// --------- OPEN / CLOSE ---------

function openInfo(type) {
  const container = document.getElementById("infoContent");
  const box = document.getElementById("infoBox");

  const data = helpData[type];

  box.classList.remove("hidden");

  container.innerHTML = `
    <h2>${data.title}</h2>
    ${data.content}
  `;
}

function closeInfo() {
  document.getElementById("infoBox").classList.add("hidden");
}

function goPage(page) {
  window.location.href = page;
}

function generateAdvice(type) {
  switch(type) {
    case "Phishing":
      return "Do not click unknown links. Always verify website URL.";

    case "Lottery Scam":
      return "Ignore messages claiming winnings. Never pay to claim prizes.";

    case "KYC Fraud":
      return "Banks never ask KYC via phone or SMS.";

    default:
      return "Stay cautious and avoid sharing personal data.";
  }
}


function toggleAlert(id) {
  const box = document.getElementById(`more-${id}`);
  const btn = event.target;

  if (box.classList.contains("hidden")) {
    box.classList.remove("hidden");
    btn.innerText = "Show Less";
  } else {
    box.classList.add("hidden");
    btn.innerText = "Read More";
  }
}

function toggleAccordion(el) {
  const body = el.nextElementSibling;
  body.classList.toggle("hidden");
}

function toggleAnswer(btn) {
  const ans = btn.nextElementSibling;
  ans.classList.toggle("hidden");
}

function getExplanation(type) {
  switch(type) {
    case "Phishing":
      return "Attackers mimic trusted websites to steal login credentials.";

    case "Lottery Scam":
      return "Victims are tricked into paying fees for fake rewards.";

    case "KYC Fraud":
      return "Scammers impersonate banks to collect personal data.";

    default:
      return "This activity shows patterns of fraud or deception.";
  }
}

async function uploadFile() {
  stopPolling();   // 🔥 ADD THIS
  const fileInput = document.getElementById("fileInput");

  if (!fileInput.files.length) {
    alert("Select file");
    return;
  }

  const formData = new FormData();
  formData.append("file", fileInput.files[0]);

  try {
    const res = await fetch("http://127.0.0.1:5000/scan-file", {
      method: "POST",
      body: formData,
      credentials: "include"
    });

    console.log("STATUS:", res.status);

    const data = await res.json();
    console.log("DATA:", data);

    localStorage.setItem("lastScan", JSON.stringify({
    data: data,
    text: data.text || "File content"
    }));

    updateUI(data, data.text);

  } catch (err) {
    console.error("❌ REAL ERROR:", err);
    alert("Check console");
  }
}