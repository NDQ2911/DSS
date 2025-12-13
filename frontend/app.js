const API_BASE = "http://localhost:8000";

const viewButtons = document.querySelectorAll("[data-view-switch]");
const views = document.querySelectorAll(".view");
const tabButtons = document.querySelectorAll("[data-tab-switch]");
const tabPanels = document.querySelectorAll(".tab-panel");

const optimizeForm = document.getElementById("optimize-form");
const optimizationOutput = document.getElementById("optimization-output");
const assignmentTreeEl = document.getElementById("assignment-tree");
const refreshTreeBtn = document.getElementById("refresh-tree-btn");
const refreshDashboardBtn = document.getElementById("refresh-dashboard-btn");

const metricElements = {
  totalStudents: document.querySelector('[data-metric="total-students"]'),
  avgConflict: document.querySelector('[data-metric="avg-conflict"]'),
  roomsFilled: document.querySelector('[data-metric="rooms-filled"]'),
  totalRooms: document.querySelector('[data-metric="total-rooms"]'),
  totalCapacity: document.querySelector('[data-metric="total-capacity"]'),
};
const criticalRoomsList = document.getElementById("critical-rooms-list");

const studentGenForm = document.getElementById("student-gen-form");
const studentGenOutput = document.getElementById("student-gen-output");
const roomGenForm = document.getElementById("room-gen-form");
const roomGenOutput = document.getElementById("room-gen-output");

const conflictChartCtx = document.getElementById("conflict-chart");
let conflictChart;

const jsonHeaders = { "Content-Type": "application/json" };

function switchView(target) {
  views.forEach((view) => {
    view.classList.toggle("active", view.dataset.view === target);
  });
  viewButtons.forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.viewSwitch === target);
  });
}

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
  assignmentTreeEl.innerHTML = "";
  const blocks = data?.blocks || [];
  if (blocks.length === 0) {
    assignmentTreeEl.innerHTML = "<p class='muted'>No assignments stored yet. Run the optimizer to generate assignments.</p>";
    return;
  }

  blocks.forEach((block) => {
    const blockCard = document.createElement("article");
    blockCard.className = "block-card";
    blockCard.innerHTML = `
      <header>
        <div>
          <h3>${block.building}</h3>
          <p>${block.rooms.length} rooms</p>
        </div>
        <span>${data.generated_at ? new Date(data.generated_at).toLocaleString() : ""}</span>
      </header>
    `;

    const roomsContainer = document.createElement("div");
    roomsContainer.className = "rooms-grid";

    block.rooms.forEach((room) => {
      const roomCard = document.createElement("div");
      roomCard.className = "room-card";
      roomCard.innerHTML = `
        <div class="room-meta">
          <strong>${room.room_code}</strong>
          <span>Floor ${room.floor}</span>
        </div>
        <p class="room-info">
          ${room.occupancy}/${room.capacity} occupants • Gender: ${room.gender ?? "Any"} • Conflict ${room.conflict_score}
        </p>
      `;

      if (room.students?.length) {
        const list = document.createElement("ul");
        list.className = "room-students";
        room.students.forEach((student) => {
          const item = document.createElement("li");
          item.innerHTML = `
            <strong>${student.name}</strong>
            <span>${student.gender} • ${student.major ?? "Undeclared"} • Year ${student.year ?? "?"}</span>
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

      roomsContainer.appendChild(roomCard);
    });

    blockCard.appendChild(roomsContainer);
    assignmentTreeEl.appendChild(blockCard);
  });
}

function updateMetrics(summary) {
  metricElements.totalStudents.textContent = summary.total_students ?? 0;
  metricElements.avgConflict.textContent = summary.avg_conflict_score?.toFixed(2) ?? "0";
  metricElements.roomsFilled.textContent = summary.rooms_filled ?? 0;
  metricElements.totalRooms.textContent = summary.total_rooms ?? 0;
  metricElements.totalCapacity.textContent = summary.total_capacity ?? 0;

  criticalRoomsList.innerHTML = "";
  if (!summary.critical_rooms?.length) {
    criticalRoomsList.innerHTML = "<li class='muted'>No critical rooms 🎉</li>";
  } else {
    summary.critical_rooms.forEach((room) => {
      const item = document.createElement("li");
      item.innerHTML = `
        <strong>${room.room_code}</strong>
        <span>score ${room.score.toFixed(2)} • ${room.occupancy}/${room.capacity}</span>
      `;
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
    setStatus(optimizationOutput, error.message, "error");
  }
});

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
