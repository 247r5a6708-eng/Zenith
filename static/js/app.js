/* ── Zenith · app.js ─────────────────────────────────────────────── */

function getCsrf() {
  return document.cookie.split(";")
    .map(c => c.trim())
    .find(c => c.startsWith("csrftoken="))
    ?.split("=")[1] || "";
}

async function api(url, data) {
  const r = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-CSRFToken": getCsrf() },
    body: JSON.stringify(data),
  });
  return r.json();
}

/* ── Live count refresh ──────────────────────────────────────────── */
function _refreshAll(res) {
  if (res.current_streak !== undefined)
    document.querySelectorAll(".live-streak").forEach(el => el.textContent = res.current_streak);
  if (res.shields !== undefined)
    document.querySelectorAll(".live-shields").forEach(el => el.textContent = res.shields);

  // Today-count on home and today pages
  const done  = res.today_done  ?? res.tasks_completed;
  const total = res.today_total ?? res.tasks_total;
  if (done !== undefined && total !== undefined) {
    document.querySelectorAll(".live-today-count").forEach(el => {
      el.textContent = `${done}/${total}`;
    });
    // Specific element on home page
    const countEl = document.getElementById("today-count");
    if (countEl) countEl.textContent = `${done}/${total}`;
  }
}

/* ── Regular task toggle ─────────────────────────────────────────── */
async function toggleTask(taskId, cb) {
  const done = cb.checked;
  const row  = cb.closest(".task-row");
  const res  = await api("/tracker/api/task/complete/", { task_id: taskId, completed: done });
  if (res.success) {
    row.classList.toggle("done", done);
    _refreshAll(res);
    if (res.fully_completed) showBanner();
  } else {
    cb.checked = !done;
    showToast("Error updating task.");
  }
}

/* ── Weekly task toggle ──────────────────────────────────────────── */
async function toggleWeekly(wtId, cb) {
  const done = cb.checked;
  const row  = cb.closest(".task-row");
  const res  = await api("/tracker/api/weekly/complete/", { wt_id: wtId, completed: done });
  if (res.success) {
    row.classList.toggle("done", done);
    _refreshAll(res);
    if (res.fully_completed) showBanner();
  } else {
    cb.checked = !done;
    showToast("Error updating weekly task.");
  }
}

/* ── Range task toggle ───────────────────────────────────────────── */
async function toggleRange(rtId, cb) {
  const done = cb.checked;
  const row  = cb.closest(".task-row");
  const res  = await api("/tracker/api/range/complete/", { rt_id: rtId, completed: done });
  if (res.success) {
    row.classList.toggle("done", done);
    _refreshAll(res);
    if (res.fully_completed) showBanner();
  } else {
    cb.checked = !done;
    showToast("Error updating task.");
  }
}

/* ── Delete task (one-time) ──────────────────────────────────────── */
async function deleteTask(taskId, btn) {
  showConfirm("Delete this task?", async () => {
    const res = await api("/tracker/api/task/delete/", { task_id: taskId });
    if (res.success) {
      const el = btn.closest(".tg-item") || btn.closest(".task-row");
      el?.remove();
      showToast("Task deleted.");
    } else {
      showToast("Could not delete task.");
    }
  });
}

/* ── Delete range task ───────────────────────────────────────────── */
async function deleteRangeTask(rtId, btn) {
  showConfirm("Delete this date-range task? This stops the whole series.", async () => {
    const res = await api("/tracker/api/range/delete/", { rt_id: rtId });
    if (res.success) {
      const el = btn.closest(".tg-item") || btn.closest(".range-row");
      el?.remove();
      showToast("Range task deleted.");
    } else {
      showToast("Could not delete task.");
    }
  });
}

/* ── Shield ──────────────────────────────────────────────────────── */
async function useShield() {
  const res = await api("/tracker/api/shield/use/", {});
  if (res.success) {
    _refreshAll(res);
    showToast("🛡️ Shield used! Streak protected.");
  } else {
    showToast(res.error || "Shield not available.");
  }
}

/* ── Inline confirm dialog (replaces browser confirm()) ─────────── */
function showConfirm(msg, onOk) {
  let overlay = document.getElementById("_confirm-overlay");
  if (!overlay) {
    overlay = document.createElement("div");
    overlay.id = "_confirm-overlay";
    overlay.style.cssText = `
      position:fixed;inset:0;z-index:9000;background:rgba(0,0,0,.55);
      display:flex;align-items:center;justify-content:center;
    `;
    const box = document.createElement("div");
    box.id = "_confirm-box";
    box.style.cssText = `
      background:var(--s2);border:1px solid var(--b2);border-radius:16px;
      padding:28px 32px;max-width:380px;width:90%;text-align:center;
    `;
    box.innerHTML = `
      <p id="_confirm-msg" style="font-size:14px;color:var(--tx);margin-bottom:20px;line-height:1.6;"></p>
      <div style="display:flex;gap:10px;justify-content:center;">
        <button id="_confirm-cancel" style="padding:8px 20px;border-radius:8px;border:1px solid var(--b2);background:transparent;color:var(--tm);font-size:13px;cursor:pointer;">Cancel</button>
        <button id="_confirm-ok" style="padding:8px 20px;border-radius:8px;border:none;background:var(--tx);color:var(--bg);font-size:13px;cursor:pointer;font-weight:600;">Delete</button>
      </div>
    `;
    overlay.appendChild(box);
    document.body.appendChild(overlay);
    document.getElementById("_confirm-cancel").addEventListener("click", () => {
      overlay.style.display = "none";
    });
    overlay.addEventListener("click", e => {
      if (e.target === overlay) overlay.style.display = "none";
    });
  }
  document.getElementById("_confirm-msg").textContent = msg;
  overlay.style.display = "flex";
  const okBtn = document.getElementById("_confirm-ok");
  const newBtn = okBtn.cloneNode(true);
  okBtn.parentNode.replaceChild(newBtn, okBtn);
  newBtn.addEventListener("click", () => {
    overlay.style.display = "none";
    onOk();
  });
}

/* ── Toast ───────────────────────────────────────────────────────── */
function showToast(msg) {
  let t = document.getElementById("_toast");
  if (!t) {
    t = document.createElement("div");
    t.id = "_toast";
    Object.assign(t.style, {
      position:"fixed", bottom:"28px", left:"50%",
      transform:"translateX(-50%)",
      background:"var(--s3)", border:"1px solid var(--b2)",
      color:"var(--tx)", padding:"10px 20px",
      borderRadius:"50px", fontSize:"13px",
      zIndex:"9999", transition:"opacity .3s",
      pointerEvents:"none", whiteSpace:"nowrap",
    });
    document.body.appendChild(t);
  }
  t.textContent = msg;
  t.style.opacity = "1";
  clearTimeout(t._tid);
  t._tid = setTimeout(() => { t.style.opacity = "0"; }, 2800);
}

/* ── Banner ──────────────────────────────────────────────────────── */
function showBanner() {
  const b = document.getElementById("complete-banner");
  if (b) b.classList.add("show");
}

/* ── Heatmap ─────────────────────────────────────────────────────── */
// Format a Date as YYYY-MM-DD using its LOCAL calendar date, not UTC.
// (toISOString() converts to UTC first, which shifts the date back a day
// for any timezone ahead of UTC — e.g. IST — causing every cell to look
// up the wrong key and silently fail to match the server's data.)
function toLocalISODate(d) {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

function renderHeatmap(jsonData) {
  const gridEl  = document.getElementById("hm-grid");
  const monthEl = document.getElementById("hm-months");
  if (!gridEl) return;

  const today = new Date(); today.setHours(0,0,0,0);
  const start = new Date(today);
  start.setDate(today.getDate() - 364);
  const dow = start.getDay();
  start.setDate(start.getDate() - (dow === 0 ? 6 : dow - 1));

  const months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
  const weeks = [];
  let week = [], lastMonth = -1;
  const monthPos = [];
  const cur = new Date(start);

  while (cur <= today) {
    const ds = toLocalISODate(cur);
    const info = jsonData[ds] || { shade:0, tc:0, tt:0 };
    week.push({ ds, ...info });
    if (cur.getMonth() !== lastMonth) {
      monthPos.push({ m: cur.getMonth(), wi: weeks.length });
      lastMonth = cur.getMonth();
    }
    if (week.length === 7) { weeks.push(week); week = []; }
    cur.setDate(cur.getDate() + 1);
  }
  while (week.length > 0 && week.length < 7) week.push({ ds: null, shade: -1 });
  if (week.length) weeks.push(week);

  if (monthEl) monthPos.forEach(({ m, wi }) => {
    const s = document.createElement("span");
    s.textContent = months[m];
    s.style.left = (wi * 15) + "px";
    monthEl.appendChild(s);
  });

  weeks.forEach(wk => {
    const col = document.createElement("div");
    col.className = "hm-week";
    wk.forEach(day => {
      const cell = document.createElement("div");
      if (!day.ds || day.shade === -1) {
        cell.className = "hm-cell empty";
      } else {
        cell.className = "hm-cell";
        cell.setAttribute("data-s", day.shade);
        if (day.su) cell.classList.add("shield");
        const tip = document.createElement("span");
        tip.className = "tip";
        tip.textContent = day.tt > 0 ? `${day.ds}: ${day.tc}/${day.tt} tasks` : day.ds;
        cell.appendChild(tip);
      }
      col.appendChild(cell);
    });
    gridEl.appendChild(col);
  });
}

/* ── Task type tabs on tasks page ────────────────────────────────── */
function initTaskTabs() {
  const tabs = document.querySelectorAll(".task-tab-btn");
  if (!tabs.length) return;
  tabs.forEach(tab => {
    tab.addEventListener("click", () => {
      tabs.forEach(t => t.classList.remove("active"));
      tab.classList.add("active");
      document.querySelectorAll(".task-tab-panel").forEach(p => p.style.display = "none");
      const panel = document.getElementById("panel-" + tab.dataset.tab);
      if (panel) panel.style.display = "block";

      // Update hidden task_type input
      const input = document.getElementById("task-type-val");
      if (input) input.value = tab.dataset.tab;
    });
  });
}

/* ── Shade selector ──────────────────────────────────────────────── */
function initShadeSelector() {
  document.querySelectorAll(".shade-opt").forEach(opt => {
    opt.addEventListener("click", () => {
      opt.closest(".shade-row").querySelectorAll(".shade-opt").forEach(o => o.classList.remove("sel"));
      opt.classList.add("sel");
      // Find shade input in the same form
      const form = opt.closest("form");
      const inp = form ? form.querySelector("[name='shade']") : document.getElementById("shade-val");
      if (inp) inp.value = opt.dataset.v;
    });
  });
}

/* ── Home live refresh ───────────────────────────────────────────── */
async function refreshHomeStats() {
  try {
    const r = await fetch("/tracker/api/home/stats/", { headers: { "X-CSRFToken": getCsrf() } });
    const data = await r.json();
    _refreshAll(data);
  } catch(e) {}
}

/* ── Init ────────────────────────────────────────────────────────── */
document.addEventListener("DOMContentLoaded", () => {
  const hd = document.getElementById("heatmap-data");
  if (hd) { try { renderHeatmap(JSON.parse(hd.textContent)); } catch(e) {} }
  initShadeSelector();
  initTaskTabs();

  document.querySelectorAll(".stat-card").forEach((c, i) => {
    c.style.animationDelay = (i * 60) + "ms";
    c.classList.add("fade-in");
  });

  // On home page, refresh stats every 30s (in case user has today page open)
  if (document.getElementById("hm-grid")) {
    setInterval(refreshHomeStats, 30000);
  }
});