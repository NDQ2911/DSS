const API_BASE = "http://localhost:8000";

const viewButtons = document.querySelectorAll("[data-view-switch]");
const views = document.querySelectorAll(".view");
const tabButtons = document.querySelectorAll("[data-tab-switch]");
const tabPanels = document.querySelectorAll(".tab-panel");

const saOptimizeBtn = document.getElementById("sa-optimize-btn");
const kmeansOptimizeBtn = document.getElementById("kmeans-optimize-btn");
const optimizationOutput = document.getElementById("optimization-output");
const floorDiagram = document.getElementById("floor-diagram");
const refreshTreeBtn = document.getElementById("refresh-tree-btn");
const refreshDashboardBtn = document.getElementById("refresh-dashboard-btn");
const clearHistoryBtn = document.getElementById("clear-history-btn");
const historyList = document.getElementById("history-list");

const metricElements = {
  totalStudents: document.querySelector('[data-metric="total-students"]'),
  studentsPlaced: document.querySelector('[data-metric="students-placed"]'),
  efficiency: document.querySelector('[data-metric="efficiency"]'),
  satisfaction: document.querySelector('[data-metric="satisfaction"]'),
  roomsFilled: document.querySelector('[data-metric="rooms-filled"]'),
  totalRooms: document.querySelector('[data-metric="total-rooms"]'),
  criticalCount: document.querySelector('[data-metric="critical-count"]'),
  capacityUsage: document.querySelector('[data-metric="capacity-usage"]'),
};



const efficiencyFills = {
  efficiency: document.querySelector('[data-fill="efficiency"]'),
  satisfaction: document.querySelector('[data-fill="satisfaction"]'),
  capacity: document.querySelector('[data-fill="capacity"]'),
};

const criticalRoomsList = document.getElementById("critical-rooms-list");
const studentGenForm = document.getElementById("student-gen-form");
const studentGenOutput = document.getElementById("student-gen-output");
const studentsTableContainer = document.getElementById("students-table-container");
const roomGenForm = document.getElementById("room-gen-form");
const roomGenOutput = document.getElementById("room-gen-output");
const roomsTableContainer = document.getElementById("rooms-table-container");

const scatterChartCtx = document.getElementById("satisfaction-scatter-chart");
const preferenceChartCtx = document.getElementById("preference-chart");
const genderChartCtx = document.getElementById("gender-chart");
const comparisonChartCtx = document.getElementById("comparison-chart");

let scatterChart, preferenceChart, genderChart, comparisonChart;
let assignmentBlocks = [];

const roomModal = document.getElementById("room-modal");
const roomModalOverlay = document.getElementById("room-modal-overlay");
const roomModalClose = document.getElementById("room-modal-close");
const roomModalTitle = document.getElementById("room-modal-title");
const roomModalMeta = document.getElementById("room-modal-meta");
const roomModalBody = document.getElementById("room-modal-body");

const jsonHeaders = { "Content-Type": "application/json" };
const HISTORY_KEY = "dss_assignment_history";

const genderLabel = (v) => {
  if (!v) return "—";
  const n = String(v).toLowerCase();
  if (n === "male" || n === "nam") return "Nam";
  if (n === "female" || n === "nu" || n === "nữ") return "Nữ";
  return v;
};

const genderBadge = (v) => {
  const l = genderLabel(v);
  const c = l === "Nam" ? "badge-male" : l === "Nữ" ? "badge-female" : "";
  return `<span class="badge ${c}">${l}</span>`;
};

const boolBadge = (v) => v ? `<span class="badge badge-yes">Có</span>` : `<span class="badge badge-no">Không</span>`;

function switchView(t) {
  views.forEach(v => v.classList.toggle("active", v.dataset.view === t));
  viewButtons.forEach(b => b.classList.toggle("active", b.dataset.viewSwitch === t));
}

function switchTab(t) {
  tabPanels.forEach(p => p.classList.toggle("active", p.dataset.tab === t));
  tabButtons.forEach(b => b.classList.toggle("active", b.dataset.tabSwitch === t));
}

viewButtons.forEach(b => b.addEventListener("click", () => switchView(b.dataset.viewSwitch)));
tabButtons.forEach(b => b.addEventListener("click", () => switchTab(b.dataset.tabSwitch)));

function setStatus(el, msg, type = "info") {
  el.textContent = msg;
  el.dataset.state = type;
}

async function fetchJSON(path, opts = {}) {
  const res = await fetch(`${API_BASE}${path}`, opts);
  if (!res.ok) {
    let d = "Yêu cầu thất bại";
    try { const p = await res.json(); d = p.detail || JSON.stringify(p); } catch { }
    throw new Error(d);
  }
  return res.json();
}

function getHistory() {
  try {
    return JSON.parse(localStorage.getItem(HISTORY_KEY) || "[]");
  } catch {
    return [];
  }
}

function saveHistory(history) {
  localStorage.setItem(HISTORY_KEY, JSON.stringify(history.slice(-20)));
}

function addToHistory(algo, cost, studentsPlaced, roomsFilled, runtimeMs) {
  const history = getHistory();
  history.push({
    id: Date.now(),
    algo,
    cost: cost ?? 0,
    studentsPlaced: studentsPlaced ?? 0,
    roomsFilled: roomsFilled ?? 0,
    runtimeMs: runtimeMs ?? 0,
    timestamp: new Date().toISOString(),
  });
  saveHistory(history);
  renderHistory();
  updateComparisonChart();
}

function renderHistory() {
  if (!historyList) return;
  const history = getHistory();
  if (!history.length) {
    historyList.innerHTML = "<p class='muted'>Chưa có lịch sử xếp phòng</p>";
    return;
  }
  historyList.innerHTML = history.slice().reverse().map(item => `
    <div class="history-item">
      <span class="algo-badge ${item.algo === 'SA' ? 'sa' : 'kmeans'}">${item.algo}</span>
      <div class="metrics">
        <span>Chi phí: <strong>${(item.cost ?? 0).toFixed(2)}</strong></span>
        <span>Sinh viên: <strong>${item.studentsPlaced ?? 0}</strong></span>
        <span>Phòng: <strong>${item.roomsFilled ?? 0}</strong></span>
        <span>Thời gian: <strong>${(item.runtimeMs ?? 0).toFixed(0)}ms</strong></span>
      </div>
      <span class="timestamp">${new Date(item.timestamp).toLocaleString("vi-VN")}</span>
    </div>
  `).join("");
}

function updateComparisonChart() {
  const history = getHistory();
  const saRuns = history.filter(h => h.algo === "SA");
  const kmeansRuns = history.filter(h => h.algo === "KMeans");

  const labels = ["Chi phí TB", "Sinh viên TB", "Thời gian TB (ms)"];
  const saData = [
    saRuns.length ? saRuns.reduce((s, h) => s + (h.cost ?? 0), 0) / saRuns.length : 0,
    saRuns.length ? saRuns.reduce((s, h) => s + (h.studentsPlaced ?? 0), 0) / saRuns.length : 0,
    saRuns.length ? saRuns.reduce((s, h) => s + (h.runtimeMs ?? 0), 0) / saRuns.length : 0,
  ];
  const kmeansData = [
    kmeansRuns.length ? kmeansRuns.reduce((s, h) => s + (h.cost ?? 0), 0) / kmeansRuns.length : 0,
    kmeansRuns.length ? kmeansRuns.reduce((s, h) => s + (h.studentsPlaced ?? 0), 0) / kmeansRuns.length : 0,
    kmeansRuns.length ? kmeansRuns.reduce((s, h) => s + (h.runtimeMs ?? 0), 0) / kmeansRuns.length : 0,
  ];

  const init = () => {
    if (!comparisonChartCtx || !window.Chart) {
      setTimeout(updateComparisonChart, 100);
      return;
    }
    if (comparisonChart) {
      comparisonChart.data.datasets[0].data = saData;
      comparisonChart.data.datasets[1].data = kmeansData;
      comparisonChart.update();
      return;
    }
    comparisonChart = new window.Chart(comparisonChartCtx, {
      type: "bar",
      data: {
        labels,
        datasets: [
          { label: "Simulated Annealing", data: saData, backgroundColor: "#3b82f6", borderRadius: 4 },
          { label: "KMeans", data: kmeansData, backgroundColor: "#10b981", borderRadius: 4 },
        ],
      },
      options: {
        responsive: true,
        plugins: { legend: { position: "bottom" } },
        scales: {
          y: { beginAtZero: true, grid: { color: "#f3f4f6" } },
          x: { grid: { display: false } },
        },
      },
    });
  };
  init();
}

clearHistoryBtn?.addEventListener("click", () => {
  localStorage.removeItem(HISTORY_KEY);
  renderHistory();
  updateComparisonChart();
});

function getSatisfactionClass(score) {
  if (score < 2) return "satisfaction-high";
  if (score < 4) return "satisfaction-medium";
  return "satisfaction-low";
}

function renderFloorDiagram(blocks) {
  if (!floorDiagram) return;
  if (!blocks?.length) {
    floorDiagram.innerHTML = "<p class='muted'>Chưa có dữ liệu</p>";
    return;
  }

  const floorMap = new Map();
  blocks.forEach(block => {
    block.rooms.forEach(room => {
      const key = `${block.building}-T${room.floor}`;
      if (!floorMap.has(key)) {
        floorMap.set(key, { building: block.building, floor: room.floor, rooms: [] });
      }
      floorMap.get(key).rooms.push(room);
    });
  });

  const sortedFloors = Array.from(floorMap.values()).sort((a, b) => {
    if (a.building !== b.building) return a.building.localeCompare(b.building);
    return a.floor - b.floor;
  });

  floorDiagram.innerHTML = "";
  sortedFloors.forEach((floorData, idx) => {
    const row = document.createElement("div");
    row.className = "floor-row";

    const label = document.createElement("div");
    label.className = "floor-label";
    label.textContent = `${floorData.building} - Tầng ${floorData.floor}`;
    row.appendChild(label);

    const roomsContainer = document.createElement("div");
    roomsContainer.className = "floor-rooms";

    floorData.rooms.forEach(room => {
      const cell = document.createElement("div");
      const satClass = room.occupancy > 0 ? getSatisfactionClass(room.conflict_score) : "empty";
      cell.className = `room-cell ${satClass}`;
      cell.textContent = room.room_code.split("-").pop();

      const tooltip = document.createElement("div");
      tooltip.className = "tooltip";
      if (idx === 0) tooltip.classList.add("tooltip-bottom");
      const studentNames = room.students?.slice(0, 3).map(s => s.name).join(", ") || "Trống";
      tooltip.textContent = `${room.room_code}: ${room.occupancy}/${room.capacity} - ${studentNames}`;
      cell.appendChild(tooltip);

      cell.addEventListener("click", () => openRoomModal({ ...room, building: floorData.building }));
      roomsContainer.appendChild(cell);
    });

    row.appendChild(roomsContainer);
    floorDiagram.appendChild(row);
  });
}

function updateScatterChart(blocks) {
  if (!scatterChartCtx || !window.Chart) {
    setTimeout(() => updateScatterChart(blocks), 100);
    return;
  }

  const dataPoints = [];
  let roomIndex = 0;
  let stats = { low: 0, medium: 0, high: 0 };

  blocks.forEach(block => {
    block.rooms.forEach(room => {
      if (room.occupancy > 0) {
        const score = room.conflict_score;
        if (score <= 2) stats.low++;
        else if (score <= 4) stats.medium++;
        else stats.high++;

        dataPoints.push({
          x: roomIndex++,
          y: score,
          roomCode: room.room_code,
          building: block.building,
          occupancy: room.occupancy,
          capacity: room.capacity
        });
      }
    });
  });

  const elLow = document.getElementById("stat-low");
  const elMed = document.getElementById("stat-medium");
  const elHigh = document.getElementById("stat-high");
  if (elLow) elLow.textContent = stats.low;
  if (elMed) elMed.textContent = stats.medium;
  if (elHigh) elHigh.textContent = stats.high;

  const pointColors = dataPoints.map(p => p.y <= 2 ? "#10b981" : p.y <= 4 ? "#f59e0b" : "#ef4444");

  if (scatterChart) {
    scatterChart.data.datasets[0].data = dataPoints;
    scatterChart.data.datasets[0].pointBackgroundColor = pointColors;
    scatterChart.data.datasets[0].backgroundColor = pointColors;
    scatterChart.update();
    return;
  }

  scatterChart = new window.Chart(scatterChartCtx, {
    type: "line",
    data: {
      datasets: [{
        label: "Điểm xung đột",
        data: dataPoints,
        borderColor: "#64748b", // Darker slate for higher contrast
        borderWidth: 3, // Thicker line
        pointBackgroundColor: pointColors,
        backgroundColor: pointColors,
        pointBorderColor: "#fff",
        pointBorderWidth: 3, // Thicker point border
        pointRadius: 8,
        pointHoverRadius: 12,
        showLine: true,
        tension: 0.3, // Slightly less curve for "sharper" feel
        fill: false,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      parsing: { xAxisKey: "x", yAxisKey: "y" },
      interaction: {
        mode: 'nearest',
        axis: 'x',
        intersect: false
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: 'rgba(255, 255, 255, 0.95)',
          titleColor: '#1e293b',
          bodyColor: '#475569',
          borderColor: '#e2e8f0',
          borderWidth: 1,
          padding: 10,
          displayColors: true,
          callbacks: {
            title: (ctx) => {
              const p = ctx[0].raw;
              return `${p.building} - ${p.roomCode}`;
            },
            label: (ctx) => {
              const p = ctx.raw;
              return [`Xung đột: ${p.y.toFixed(2)}`, `Sức chứa: ${p.occupancy}/${p.capacity}`];
            },
            labelColor: (ctx) => {
              const val = ctx.raw.y;
              const col = val <= 2 ? "#10b981" : val <= 4 ? "#f59e0b" : "#ef4444";
              return { borderColor: col, backgroundColor: col };
            }
          },
        },
      },
      scales: {
        x: {
          type: "linear",
          title: { display: false },
          grid: { display: false },
          ticks: { display: false }
        },
        y: {
          title: { display: true, text: "Điểm xung đột" },
          beginAtZero: true,
          suggestedMax: 5,
          grid: { color: "#f1f5f9", drawBorder: false },
          ticks: { stepSize: 1 }
        },
      },
    },
  });
}

function updatePreferenceChart(prefs) {
  const labels = ["Hướng nội", "Giờ ngủ", "Sạch sẽ", "Chịu ồn"];
  const values = [
    prefs.introversion ?? 0,
    prefs.sleep ?? 0,
    prefs.cleanliness ?? 0,
    prefs.noise ?? 0,
  ];

  const init = () => {
    if (!preferenceChartCtx || !window.Chart) {
      setTimeout(() => updatePreferenceChart(prefs), 100);
      return;
    }
    if (preferenceChart) {
      preferenceChart.data.datasets[0].data = values;
      preferenceChart.update();
      return;
    }
    preferenceChart = new window.Chart(preferenceChartCtx, {
      type: "bar",
      data: {
        labels,
        datasets: [{
          label: "Điểm TB (1-5)",
          data: values,
          backgroundColor: ["#6366f1", "#8b5cf6", "#a855f7", "#d946ef"],
          borderRadius: 4,
        }],
      },
      options: {
        indexAxis: "y",
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
          x: { beginAtZero: true, max: 5, grid: { color: "#f3f4f6" } },
          y: { grid: { display: false } },
        },
      },
    });
  };
  init();
}

function updateGenderChart(maleRatio, femaleRatio) {
  const labels = ["Nam", "Nữ"];
  const values = [Math.round(maleRatio * 100), Math.round(femaleRatio * 100)];
  const colors = ["#3b82f6", "#ec4899"];

  const init = () => {
    if (!genderChartCtx || !window.Chart) {
      setTimeout(() => updateGenderChart(maleRatio, femaleRatio), 100);
      return;
    }
    if (genderChart) {
      genderChart.data.datasets[0].data = values;
      genderChart.update();
      return;
    }
    genderChart = new window.Chart(genderChartCtx, {
      type: "pie",
      data: {
        labels,
        datasets: [{ data: values, backgroundColor: colors, borderWidth: 0 }],
      },
      options: {
        responsive: true,
        plugins: {
          legend: { position: "bottom", labels: { padding: 15, usePointStyle: true } },
          tooltip: { callbacks: { label: (ctx) => `${ctx.label}: ${ctx.raw}%` } },
        },
      },
    });
  };
  init();
}

function openRoomModal(room) {
  if (!roomModal) return;
  roomModalTitle.textContent = `${room.room_code} — ${room.building || ""}`;
  roomModalMeta.textContent = `Tầng ${room.floor} • ${room.occupancy}/${room.capacity} người • Xung đột: ${room.conflict_score}`;
  roomModalBody.innerHTML = "";

  if (!room.students?.length) {
    roomModalBody.innerHTML = "<p class='muted'>Chưa có sinh viên</p>";
  } else {
    room.students.forEach(s => {
      const prefs = s.preferences || {};
      const tags = [
        { l: "Hướng nội", k: "introversion" },
        { l: "Giờ ngủ", k: "sleep_schedule" },
        { l: "Sạch sẽ", k: "cleanliness" },
        { l: "Chịu ồn", k: "noise_tolerance" },
      ].map(p => `<li>${p.l}: ${prefs[p.k] ?? "?"}/5</li>`).join("");

      const smokingText = s.smoking ? "Có" : "Không";
      const smokingItem = `<li>Hút thuốc: ${smokingText}</li>`;

      const row = document.createElement("div");
      row.className = "student-row";
      row.innerHTML = `
        <div class="left">
          <strong>${s.name}</strong>
          <span class="muted">${s.major ?? "—"} • ${genderLabel(s.gender)} • Năm ${s.year ?? "?"}</span>
          <ul class="preference-tags">${tags}${smokingItem}</ul>
        </div>
      `;
      roomModalBody.appendChild(row);
    });
  }

  roomModal.setAttribute("aria-hidden", "false");
  roomModalClose?.focus();
}

function closeRoomModal() {
  roomModal?.setAttribute("aria-hidden", "true");
}

if (roomModalClose) roomModalClose.addEventListener("click", closeRoomModal);
if (roomModalOverlay) roomModalOverlay.addEventListener("click", closeRoomModal);
document.addEventListener("keydown", e => {
  if (e.key === "Escape" && roomModal?.getAttribute("aria-hidden") === "false") closeRoomModal();
});

function renderAssignmentTree(data) {
  assignmentBlocks = data?.blocks ?? [];
  renderFloorDiagram(assignmentBlocks);
  updateScatterChart(assignmentBlocks);
}

function updateMetrics(summary) {
  const total = summary.total_students ?? 0;
  const placed = summary.students_placed ?? 0;
  const avgConflict = summary.avg_conflict_score ?? 0;
  const roomsFilled = summary.rooms_filled ?? 0;
  const totalRooms = summary.total_rooms ?? 0;
  const totalCapacity = summary.total_capacity ?? 0;
  const criticalCount = summary.critical_rooms?.length ?? 0;

  const efficiency = total > 0 ? (placed / total * 100) : 0;
  const satisfaction = Math.max(0, 100 - (avgConflict / 7) * 100);
  const capacityUsage = totalCapacity > 0 ? (placed / totalCapacity * 100) : 0;

  metricElements.totalStudents.textContent = total;
  metricElements.studentsPlaced && (metricElements.studentsPlaced.textContent = placed);
  metricElements.efficiency && (metricElements.efficiency.textContent = `${efficiency.toFixed(1)}%`);
  metricElements.satisfaction && (metricElements.satisfaction.textContent = `${satisfaction.toFixed(1)}%`);
  metricElements.roomsFilled.textContent = roomsFilled;
  metricElements.totalRooms.textContent = totalRooms;
  metricElements.criticalCount && (metricElements.criticalCount.textContent = criticalCount);
  metricElements.capacityUsage && (metricElements.capacityUsage.textContent = `${capacityUsage.toFixed(1)}%`);

  efficiencyFills.efficiency && (efficiencyFills.efficiency.style.width = `${efficiency}%`);
  efficiencyFills.satisfaction && (efficiencyFills.satisfaction.style.width = `${satisfaction}%`);
  efficiencyFills.capacity && (efficiencyFills.capacity.style.width = `${capacityUsage}%`);

  const prefs = summary.preference_insights || {};
  updatePreferenceChart(prefs);

  const maleRatio = summary.male_ratio ?? 0.5;
  updateGenderChart(maleRatio, 1 - maleRatio);

  criticalRoomsList.innerHTML = "";
  if (!summary.critical_rooms?.length) {
    criticalRoomsList.innerHTML = "<li class='muted'>Không có phòng cần lưu ý 🎉</li>";
  } else {
    summary.critical_rooms.forEach(room => {
      const li = document.createElement("li");
      li.innerHTML = `<strong>${room.room_code}</strong><span>Điểm: ${room.score.toFixed(2)} • ${room.occupancy}/${room.capacity}</span>`;
      li.style.cursor = "pointer";
      li.addEventListener("click", () => {
        for (const block of assignmentBlocks) {
          const r = block.rooms.find(rm => rm.room_code === room.room_code);
          if (r) { openRoomModal({ ...r, building: block.building }); return; }
        }
      });
      criticalRoomsList.appendChild(li);
    });
  }
}

async function loadAssignmentTree() {
  floorDiagram && (floorDiagram.innerHTML = "<p class='muted'>Đang tải…</p>");
  try {
    const data = await fetchJSON("/analytics/assignment-map");
    renderAssignmentTree(data);
  } catch (e) {
    floorDiagram && (floorDiagram.innerHTML = `<p class='error'>${e.message}</p>`);
  }
}

async function loadDashboard() {
  try {
    const summary = await fetchJSON("/analytics/summary");
    updateMetrics(summary);
  } catch (e) {
    criticalRoomsList.innerHTML = `<li class='error'>${e.message}</li>`;
  }
}

async function runOptimization(method) {
  saOptimizeBtn?.classList.remove("active");
  kmeansOptimizeBtn?.classList.remove("active");
  if (method === "SA") saOptimizeBtn?.classList.add("active");
  else kmeansOptimizeBtn?.classList.add("active");

  setStatus(optimizationOutput, `Đang xếp phòng theo ${method}…`);
  try {
    const endpoint = method === "SA" ? "/assignments/optimize" : "/assignments/kmeans-optimize";
    const payload = method === "SA" ? { initial_temperature: 1000, cooling_rate: 0.95, iterations: 3000 } : {};
    const result = await fetchJSON(endpoint, { method: "POST", headers: jsonHeaders, body: JSON.stringify(payload) });

    let cost = 0, runtimeMs = 0, studentsPlaced = 0, roomsFilled = 0;
    if (method === "SA") {
      cost = result.best_cost ?? 0;
      runtimeMs = result.runtime_ms ?? 0;
      optimizationOutput.innerHTML = `<p>✓ Hoàn thành • Chi phí: <strong>${cost.toFixed(2)}</strong> • ${runtimeMs.toFixed(0)}ms</p>`;
    } else {
      const total = Object.values(result.assignments || {}).reduce((s, ids) => s + (Array.isArray(ids) ? ids.length : 0), 0);
      studentsPlaced = total;
      optimizationOutput.innerHTML = `<p>✓ Hoàn thành • Đã xếp: <strong>${total}</strong> sinh viên</p>`;
    }

    await loadAssignmentTree();
    await loadDashboard();

    const summary = await fetchJSON("/analytics/summary");
    addToHistory(method, summary.avg_conflict_score ?? cost, summary.students_placed ?? studentsPlaced, summary.rooms_filled ?? roomsFilled, runtimeMs);
  } catch (e) {
    const msg = e.message?.includes("Unable to place") ? "Không đủ phòng. Hãy tạo thêm phòng." : e.message;
    setStatus(optimizationOutput, msg, "error");
  }
}

saOptimizeBtn?.addEventListener("click", () => runOptimization("SA"));
kmeansOptimizeBtn?.addEventListener("click", () => runOptimization("KMeans"));

refreshTreeBtn?.addEventListener("click", loadAssignmentTree);
refreshDashboardBtn?.addEventListener("click", loadDashboard);
function renderStudentsTable(students) {
  if (!studentsTableContainer) return;
  if (!students?.length) {
    studentsTableContainer.innerHTML = "<p class='muted'>Chưa có</p>";
    return;
  }
  const rows = students.map(s => `
    <tr>
      <td>${s.id}</td>
      <td>${s.name}</td>
      <td>${genderBadge(s.gender)}</td>
      <td>${s.major || "—"}</td>
      <td>${s.introversion_score || "—"}</td>
      <td>${s.sleep_schedule_score || "—"}</td>
      <td>${s.cleanliness_score || "—"}</td>
      <td>${s.noise_tolerance || "—"}</td>
      <td>${boolBadge(s.smoking)}</td>
    </tr>
  `).join("");
  studentsTableContainer.innerHTML = `
    <div class="table-scroll">
      <table class="data-table">
        <thead><tr><th>ID</th><th>Tên</th><th>GT</th><th>Ngành</th><th>HN</th><th>Ngủ</th><th>SS</th><th>Ồn</th><th>Thuốc</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </div>
    <p class="muted" style="margin-top:0.5rem;font-size:0.75rem;">${Math.min(80, students.length)}/${students.length} sinh viên</p>
  `;
}

function renderRoomsTable(rooms) {
  if (!roomsTableContainer) return;
  if (!rooms?.length) {
    roomsTableContainer.innerHTML = "<p class='muted'>Chưa có</p>";
    return;
  }
  const rows = rooms.slice(0, 80).map(r => `
    <tr><td>${r.room_code || r.id}</td><td>${r.building}</td><td>${r.floor}</td><td>${r.capacity}</td><td>${genderBadge(r.gender_restriction)}</td></tr>
  `).join("");
  roomsTableContainer.innerHTML = `
    <div class="table-scroll">
      <table class="data-table">
        <thead><tr><th>Mã</th><th>Tòa</th><th>Tầng</th><th>SL</th><th>GT</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </div>
    <p class="muted" style="margin-top:0.5rem;font-size:0.75rem;">${Math.min(80, rooms.length)}/${rooms.length} phòng</p>
  `;
}

async function loadStudentsList() {
  try {
    const students = await fetchJSON("/students/");
    renderStudentsTable(students);
  } catch (e) {
    studentsTableContainer && (studentsTableContainer.innerHTML = `<p class="error">${e.message}</p>`);
  }
}

async function loadRoomsList() {
  try {
    const rooms = await fetchJSON("/rooms/");
    renderRoomsTable(rooms);
  } catch (e) {
    roomsTableContainer && (roomsTableContainer.innerHTML = `<p class="error">${e.message}</p>`);
  }
}

studentGenForm?.addEventListener("submit", async e => {
  e.preventDefault();
  setStatus(studentGenOutput, "Đang tạo…");
  const fd = new FormData(studentGenForm);
  const payload = {
    count: Number(fd.get("count")),
    male_ratio: Number(fd.get("male_ratio")),
    smoking_ratio: Number(fd.get("smoking_ratio")),
    clear_existing: fd.get("clear_existing") === "true",
  };
  try {
    const s = await fetchJSON("/generators/students", { method: "POST", headers: jsonHeaders, body: JSON.stringify(payload) });
    setStatus(studentGenOutput, `✓ Đã tạo ${s.created} sinh viên (Nam ${(s.male_ratio * 100).toFixed(0)}%)`);
    await loadStudentsList();
    await loadDashboard();
  } catch (e) {
    setStatus(studentGenOutput, e.message, "error");
  }
});

roomGenForm?.addEventListener("submit", async e => {
  e.preventDefault();
  setStatus(roomGenOutput, "Đang tạo…");
  const fd = new FormData(roomGenForm);
  const caps = (fd.get("capacity_choices") || "6,8,10").split(",").map(v => Number(v.trim())).filter(v => [6, 8, 10].includes(v));
  const payload = {
    target_students: fd.get("target_students") ? Number(fd.get("target_students")) : null,
    blocks: 6,
    floors_per_block: Number(fd.get("floors_per_block")),
    rooms_per_floor: Number(fd.get("rooms_per_floor")),
    capacity_choices: caps.length ? caps : [6, 8, 10],
    clear_existing: fd.get("clear_existing") === "true",
    gender_strategy: fd.get("gender_strategy"),
  };
  try {
    const s = await fetchJSON("/generators/rooms", { method: "POST", headers: jsonHeaders, body: JSON.stringify(payload) });
    setStatus(roomGenOutput, `✓ Đã tạo ${s.rooms_created} phòng • Sức chứa: ${s.total_capacity}`);
    await loadRoomsList();
    await loadDashboard();
  } catch (e) {
    setStatus(roomGenOutput, e.message, "error");
  }
});

loadAssignmentTree();
loadDashboard();
loadStudentsList();
loadRoomsList();
renderHistory();
updateComparisonChart();
