const API_BASE = "http://localhost:8000";

const viewButtons = document.querySelectorAll("[data-view-switch]");
const views = document.querySelectorAll(".view");
const tabButtons = document.querySelectorAll("[data-tab-switch]");
const tabPanels = document.querySelectorAll(".tab-panel");

const optimizeForm = document.getElementById("optimize-form");
const optimizationOutput = document.getElementById("optimization-output");
const assignmentTreeEl = document.getElementById("assignment-tree");
const blockTabsEl = document.getElementById("block-tabs");
const refreshTreeBtn = document.getElementById("refresh-tree-btn");
const refreshDashboardBtn = document.getElementById("refresh-dashboard-btn");

const metricElements = {
  totalStudents: document.querySelector('[data-metric="total-students"]'),
  avgConflict: document.querySelector('[data-metric="avg-conflict"]'),
  roomsFilled: document.querySelector('[data-metric="rooms-filled"]'),
  totalRooms: document.querySelector('[data-metric="total-rooms"]'),
  totalCapacity: document.querySelector('[data-metric="total-capacity"]'),
};
const preferenceElements = {
  introversion: document.querySelector('[data-pref="introversion"]'),
  sleep: document.querySelector('[data-pref="sleep"]'),
  cleanliness: document.querySelector('[data-pref="cleanliness"]'),
  noise: document.querySelector('[data-pref="noise"]'),
  smoking: document.querySelector('[data-pref="smoking"]'),
};
const criticalRoomsList = document.getElementById("critical-rooms-list");

const studentGenForm = document.getElementById("student-gen-form");
const studentGenOutput = document.getElementById("student-gen-output");
const roomGenForm = document.getElementById("room-gen-form");
const roomGenOutput = document.getElementById("room-gen-output");
const kmeansOptimizeBtn = document.getElementById("kmeans-optimize-btn");

const conflictChartCtx = document.getElementById("conflict-chart");
let conflictChart;
let assignmentBlocks = [];
let activeBlockIndex = 0;
let assignmentGeneratedAt = null;
// Modal elements for room details
const roomModal = document.getElementById("room-modal");
const roomModalOverlay = document.getElementById("room-modal-overlay");
const roomModalClose = document.getElementById("room-modal-close");
const roomModalTitle = document.getElementById("room-modal-title");
const roomModalMeta = document.getElementById("room-modal-meta");
const roomModalBody = document.getElementById("room-modal-body");

const jsonHeaders = { "Content-Type": "application/json" };

const genderLabel = (value) => {
  if (!value) return "Any";
  const normalized = String(value).toLowerCase();
  if (normalized === "male" || normalized === "nam") return "Nam";
  if (normalized === "female" || normalized === "nu" || normalized === "nữ") return "Nữ";
  return value;
};

function switchView(target) {
  views.forEach((view) => {
    view.classList.toggle("active", view.dataset.view === target);
  });
  viewButtons.forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.viewSwitch === target);
  });
}

function openRoomModal(room) {
  if (!roomModal) return;
  const buildingLabel = room.building ? ` — ${room.building}` : "";
  roomModalTitle.textContent = `${room.room_code}${buildingLabel}`;
  const conflictScore = Number(room.conflict_score ?? 0).toFixed(2);
  roomModalMeta.textContent = `Floor ${room.floor} • ${room.occupancy}/${room.capacity} occupants • Gender: ${room.gender ? genderLabel(room.gender) : "Any"} • Conflict ${conflictScore}`;
  roomModalBody.innerHTML = "";

  if (!room.students?.length) {
    roomModalBody.innerHTML = `<p class='muted'>No students assigned</p>`;
  } else {
    room.students.forEach((s) => {
      const prefs = s.preferences || {};
      const preferenceTags = [
        { label: "Introversion", key: "introversion" },
        { label: "Sleep", key: "sleep_schedule" },
        { label: "Cleanliness", key: "cleanliness" },
        { label: "Noise", key: "noise_tolerance" },
      ];
      const preferenceHtml = preferenceTags
        .map((pref) => `<li>${pref.label}: ${prefs[pref.key] ?? "?"}/5</li>`)
        .join("");

      const row = document.createElement("div");
      row.className = "student-row";
      row.innerHTML = `
        <div class="left">
          <strong>${s.name}</strong>
          <span class="muted">${s.major ?? "Undeclared"} • ${genderLabel(s.gender)} • Year ${s.year ?? "?"}</span>
          <ul class="preference-tags">${preferenceHtml}</ul>
        </div>
        <div class="right">
          <span>${s.smoking ? "Smoker" : "Non-smoker"}</span>
        </div>
      `;
      roomModalBody.appendChild(row);
    });
  }

  roomModal.setAttribute("aria-hidden", "false");
  // trap focus to modal close button for simplicity
  roomModalClose.focus();
}

function closeRoomModal() {
  if (!roomModal) return;
  roomModal.setAttribute("aria-hidden", "true");
}

async function getRoomDetailsByCode(roomCode) {
  if (!roomCode) return null;
  if (!assignmentBlocks.length) {
    try {
      const data = await fetchJSON(`/analytics/assignment-map`);
      renderAssignmentTree(data);
    } catch (error) {
      throw new Error(`Unable to load assignments: ${error.message}`);
    }
  }
  for (const block of assignmentBlocks) {
    const room = block.rooms.find((r) => r.room_code === roomCode);
    if (room) {
      return { block, room };
    }
  }
  return null;
}

async function showRoomInsights(roomCode) {
  try {
    const details = await getRoomDetailsByCode(roomCode);
    if (!details) {
      throw new Error("Room details not found. Try refreshing assignments.");
    }
    openRoomModal({ ...details.room, building: details.block.building });
  } catch (error) {
    window.alert(error.message);
  }
}

// modal event bindings
if (roomModalClose) roomModalClose.addEventListener("click", closeRoomModal);
if (roomModalOverlay) roomModalOverlay.addEventListener("click", closeRoomModal);
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && roomModal && roomModal.getAttribute("aria-hidden") === "false") {
    closeRoomModal();
  }
});

function switchTab(target) {
  tabPanels.forEach((panel) => {
    panel.classList.toggle("active", panel.dataset.tab === target);
  });
  tabButtons.forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.tabSwitch === target);
  });
}

viewButtons.forEach((btn) => {
  btn.addEventListener("click", () => switchView(btn.dataset.viewSwitch));
});

tabButtons.forEach((btn) => {
  btn.addEventListener("click", () => switchTab(btn.dataset.tabSwitch));
});

function setStatus(el, message, type = "info") {
  el.textContent = message;
  el.dataset.state = type;
}

async function fetchJSON(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, options);
  if (!response.ok) {
    let detail = "Request failed";
    try {
      const payload = await response.json();
      detail = payload.detail || JSON.stringify(payload);
    } catch (err) {
      /* ignore */
    }
    throw new Error(detail);
  }
  return response.json();
}

function renderAssignmentTree(data) {
  assignmentBlocks = data?.blocks ?? [];
  assignmentGeneratedAt = data?.generated_at ?? null;

  if (blockTabsEl) {
    blockTabsEl.innerHTML = "";
  }
  assignmentTreeEl.innerHTML = "";

  if (!assignmentBlocks.length) {
    assignmentTreeEl.innerHTML = "<p class='muted'>No assignments stored yet. Run the optimizer to generate assignments.</p>";
    return;
  }

  activeBlockIndex = Math.min(activeBlockIndex, assignmentBlocks.length - 1);
  renderBlockTabs();
  renderSelectedBlock();
}

function renderBlockTabs() {
  if (!blockTabsEl) return;
  blockTabsEl.innerHTML = "";
  assignmentBlocks.forEach((block, index) => {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = block.building;
    button.classList.toggle("active", index === activeBlockIndex);
    button.setAttribute("role", "tab");
    button.setAttribute("aria-selected", index === activeBlockIndex ? "true" : "false");
    button.addEventListener("click", () => {
      if (activeBlockIndex === index) return;
      activeBlockIndex = index;
      renderBlockTabs();
      renderSelectedBlock();
    });
    blockTabsEl.appendChild(button);
  });
}

function renderSelectedBlock() {
  if (!assignmentBlocks.length) return;
  const block = assignmentBlocks[activeBlockIndex];
  if (!block) return;

  assignmentTreeEl.innerHTML = "";
  const blockCard = document.createElement("article");
  blockCard.className = "block-card";
  blockCard.innerHTML = `
    <header>
      <div>
        <h3>${block.building}</h3>
        <p>${block.rooms.length} rooms</p>
      </div>
      <span>${assignmentGeneratedAt ? new Date(assignmentGeneratedAt).toLocaleString() : ""}</span>
    </header>
  `;

  const roomsContainer = document.createElement("div");
  roomsContainer.className = "rooms-grid";

  block.rooms.forEach((room) => {
    const roomCard = document.createElement("div");
    roomCard.className = "room-card";
    roomCard.tabIndex = 0;
    roomCard.setAttribute("role", "button");
    roomCard.setAttribute("aria-label", `Open ${room.room_code} details`);
    roomCard.innerHTML = `
      <div class="room-meta">
        <strong>${room.room_code}</strong>
        <span>Floor ${room.floor}</span>
      </div>
      <p class="room-info">
        ${room.occupancy}/${room.capacity} occupants • Gender: ${room.gender ? genderLabel(room.gender) : "Any"} • Conflict ${room.conflict_score}
      </p>
    `;

    if (room.students?.length) {
      const list = document.createElement("ul");
      list.className = "room-students";
      room.students.forEach((student) => {
        const item = document.createElement("li");
        item.innerHTML = `
          <strong>${student.name}</strong>
          <span>${genderLabel(student.gender)} • ${student.major ?? "Undeclared"} • Year ${student.year ?? "?"}</span>
        `;
        list.appendChild(item);
      });
      roomCard.appendChild(list);
    } else {
      const empty = document.createElement("p");
      empty.className = "muted";
      empty.textContent = "No students assigned";
      roomCard.appendChild(empty);
    }

    // click / enter to open details modal
    roomCard.addEventListener("click", () => openRoomModal(room));
    roomCard.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") openRoomModal(room);
    });

    roomsContainer.appendChild(roomCard);
  });

  blockCard.appendChild(roomsContainer);
  assignmentTreeEl.appendChild(blockCard);
}

function updateMetrics(summary) {
  metricElements.totalStudents.textContent = summary.total_students ?? 0;
  metricElements.avgConflict.textContent = summary.avg_conflict_score?.toFixed(2) ?? "0";
  metricElements.roomsFilled.textContent = summary.rooms_filled ?? 0;
  metricElements.totalRooms.textContent = summary.total_rooms ?? 0;
  metricElements.totalCapacity.textContent = summary.total_capacity ?? 0;

  const prefs = summary.preference_insights || {};
  if (preferenceElements.introversion) {
    preferenceElements.introversion.textContent = (prefs.introversion ?? 0).toFixed(2);
    preferenceElements.sleep.textContent = (prefs.sleep ?? 0).toFixed(2);
    preferenceElements.cleanliness.textContent = (prefs.cleanliness ?? 0).toFixed(2);
    preferenceElements.noise.textContent = (prefs.noise ?? 0).toFixed(2);
    const smokingRatio = prefs.smoking_ratio ?? 0;
    preferenceElements.smoking.textContent = `${(smokingRatio * 100).toFixed(1)}%`;
  }

  criticalRoomsList.innerHTML = "";
  if (!summary.critical_rooms?.length) {
    criticalRoomsList.innerHTML = "<li class='muted'>No critical rooms 🎉</li>";
  } else {
    summary.critical_rooms.forEach((room) => {
      const item = document.createElement("li");
      const button = document.createElement("button");
      button.type = "button";
      button.innerHTML = `
        <strong>${room.room_code}</strong>
        <span>score ${room.score.toFixed(2)} • ${room.occupancy}/${room.capacity}</span>
      `;
      button.addEventListener("click", () => showRoomInsights(room.room_code));
      item.appendChild(button);
      criticalRoomsList.appendChild(item);
    });
  }
}

function updateConflictChart(distribution = []) {
  const labels = distribution.map((bucket) => bucket.label);
  const values = distribution.map((bucket) => bucket.rooms);

  const initChart = () => {
    if (!conflictChartCtx || !window.Chart) {
      setTimeout(() => updateConflictChart(distribution), 100);
      return;
    }
    if (conflictChart) {
      conflictChart.data.labels = labels;
      conflictChart.data.datasets[0].data = values;
      conflictChart.update();
      return;
    }
    conflictChart = new window.Chart(conflictChartCtx, {
      type: "bar",
      data: {
        labels,
        datasets: [
          {
            label: "Rooms",
            data: values,
            backgroundColor: "rgba(99, 102, 241, 0.7)",
            borderRadius: 8,
          },
        ],
      },
      options: {
        responsive: true,
        scales: {
          y: { beginAtZero: true, ticks: { precision: 0 } },
        },
      },
    });
  };

  initChart();
}

async function loadAssignmentTree() {
  assignmentTreeEl.innerHTML = "<p class='muted'>Loading assignments…</p>";
  if (blockTabsEl) {
    blockTabsEl.innerHTML = "";
  }
  try {
    const data = await fetchJSON(`/analytics/assignment-map`);
    renderAssignmentTree(data);
  } catch (error) {
    assignmentTreeEl.innerHTML = `<p class='error'>${error.message}</p>`;
  }
}

async function loadDashboard() {
  setStatus(refreshDashboardBtn, "Refreshing…");
  try {
    const summary = await fetchJSON(`/analytics/summary`);
    updateMetrics(summary);
    updateConflictChart(summary.conflict_distribution);
    setStatus(refreshDashboardBtn, "Refresh Dashboard");
  } catch (error) {
    setStatus(refreshDashboardBtn, "Failed", "error");
    criticalRoomsList.innerHTML = `<li class='error'>${error.message}</li>`;
  }
}

optimizeForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  setStatus(optimizationOutput, "Running optimization…");
  const formData = new FormData(optimizeForm);
  const payload = {
    initial_temperature: Number(formData.get("initial_temperature")),
    cooling_rate: Number(formData.get("cooling_rate")),
    iterations: Number(formData.get("iterations")),
  };

  try {
    const result = await fetchJSON(`/assignments/optimize`, {
      method: "POST",
      headers: jsonHeaders,
      body: JSON.stringify(payload),
    });
    optimizationOutput.innerHTML = `
      <p>Best Cost: <strong>${result.best_cost.toFixed(2)}</strong></p>
      <p>Iterations: ${result.iterations} • Runtime: ${result.runtime_ms.toFixed(2)} ms</p>
    `;
    await loadAssignmentTree();
    await loadDashboard();
  } catch (error) {
    const message = error.message?.includes("Unable to place all students")
      ? "Allocation failed: not enough compatible rooms. Please generate more rooms (at least 5% buffer) or adjust trait settings."
      : error.message;
    setStatus(optimizationOutput, message, "error");
  }
});

if (kmeansOptimizeBtn) {
  kmeansOptimizeBtn.addEventListener("click", async () => {
    setStatus(optimizationOutput, "Running KMeans optimization…");
    try {
      const result = await fetchJSON(`/assignments/kmeans-optimize`, {
        method: "POST",
        headers: jsonHeaders,
        body: JSON.stringify({}),
      });
      const totalAssigned = Object.values(result.assignments || {}).reduce(
        (sum, ids) => sum + (Array.isArray(ids) ? ids.length : 0),
        0
      );
      optimizationOutput.innerHTML = `
        <p>Strategy: <strong>${result.strategy || "kmeans"}</strong></p>
        <p>Total assigned students: <strong>${totalAssigned}</strong></p>
      `;
      await loadAssignmentTree();
      await loadDashboard();
    } catch (error) {
      setStatus(optimizationOutput, error.message, "error");
    }
  });
}

refreshTreeBtn.addEventListener("click", loadAssignmentTree);
refreshDashboardBtn.addEventListener("click", loadDashboard);

studentGenForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  setStatus(studentGenOutput, "Generating students…");
  const formData = new FormData(studentGenForm);
  const payload = {
    count: Number(formData.get("count")),
    male_ratio: Number(formData.get("male_ratio")),
    smoking_ratio: Number(formData.get("smoking_ratio")),
    clear_existing: formData.get("clear_existing") === "true",
  };

  try {
    const summary = await fetchJSON(`/generators/students`, {
      method: "POST",
      headers: jsonHeaders,
      body: JSON.stringify(payload),
    });
    setStatus(
      studentGenOutput,
      `Created ${summary.created} students • Total: ${summary.total_students} (♂ ${(summary.male_ratio * 100).toFixed(
        1
      )}%, ♀ ${(summary.female_ratio * 100).toFixed(1)}%)`
    );
    await loadDashboard();
  } catch (error) {
    setStatus(studentGenOutput, error.message, "error");
  }
});

roomGenForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  setStatus(roomGenOutput, "Generating rooms…");
  const formData = new FormData(roomGenForm);
  const capacityChoices = (formData.get("capacity_choices") || "6,8,10")
    .split(",")
    .map((value) => Number(value.trim()))
    .filter((value) => [6, 8, 10].includes(value));

  const payload = {
    target_students: formData.get("target_students") ? Number(formData.get("target_students")) : null,
    blocks: Number(formData.get("blocks")),
    floors_per_block: Number(formData.get("floors_per_block")),
    rooms_per_floor: Number(formData.get("rooms_per_floor")),
    capacity_choices: capacityChoices.length ? capacityChoices : [6, 8, 10],
    clear_existing: formData.get("clear_existing") === "true",
    gender_strategy: formData.get("gender_strategy"),
  };

  try {
    const summary = await fetchJSON(`/generators/rooms`, {
      method: "POST",
      headers: jsonHeaders,
      body: JSON.stringify(payload),
    });
    setStatus(
      roomGenOutput,
      `Created ${summary.rooms_created} rooms • Capacity ${summary.total_capacity} (target ${summary.target_capacity})`
    );
    await loadAssignmentTree();
    await loadDashboard();
  } catch (error) {
    setStatus(roomGenOutput, error.message, "error");
  }
});

// Initial load
loadAssignmentTree();
loadDashboard();
