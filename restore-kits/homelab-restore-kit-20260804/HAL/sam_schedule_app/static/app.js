let currentDate = new Date().toISOString().slice(0, 10);
let currentData = null;
let currentFilter = "";

const $ = (id) => document.getElementById(id);

function toast(message, ms = 2600) {
  const el = $("toast");
  el.textContent = message;
  el.hidden = false;
  clearTimeout(window.toastTimer);
  window.toastTimer = setTimeout(() => { el.hidden = true; }, ms);
}

async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await res.json();
  if (!res.ok || data.status === "error") {
    throw new Error(data.error || data.detail || `Request failed: ${res.status}`);
  }
  return data;
}

function cellState(itemId, cellName) {
  return !!(currentData?.completed?.[itemId]?.[cellName]);
}

function cellText(item, cellName) {
  const value = item[cellName] || {};
  if (cellName === "training") return value.display || value.raw || "";
  return value.needed ? (value.display || "Needed") : "";
}

function cellNeeded(item, cellName) {
  const value = item[cellName] || {};
  return cellName === "training" ? !!value.needed : !!value.needed;
}

function makeCell(item, cellName) {
  const td = document.createElement("td");
  const itemId = String(item.id);
  const needed = cellNeeded(item, cellName);
  const done = cellState(itemId, cellName);
  td.className = `action-cell ${needed ? "needed" : "empty"} ${done ? "done" : ""}`;
  if (cellName === "farrier" && needed) td.classList.add("farrier-needed");
  if (cellName === "vet" && needed) td.classList.add("vet-needed");
  td.textContent = cellText(item, cellName);
  td.title = td.textContent;
  if (!needed) return td;
  td.addEventListener("click", async () => {
    const wasDone = cellState(itemId, cellName);
    if (wasDone) {
      const ok = confirm(`Undo completion for ${item.horse} / ${cellName}?`);
      if (!ok) return;
    }
    try {
      await api("/api/cell", {
        method: "POST",
        body: JSON.stringify({ date: currentDate, item_id: itemId, cell: cellName, completed: !wasDone }),
      });
      await loadSchedule(false);
    } catch (err) {
      toast(err.message, 5000);
    }
  });
  return td;
}

function makeRow(item) {
  const tr = document.createElement("tr");
  const horse = document.createElement("td");
  horse.className = "horse";
  horse.textContent = item.horse || "";
  horse.title = item.registered_name ? `${item.horse} (${item.registered_name})` : item.horse;
  tr.appendChild(horse);
  tr.appendChild(makeCell(item, "training"));
  tr.appendChild(makeCell(item, "farrier"));
  tr.appendChild(makeCell(item, "vet"));
  return tr;
}

function filteredItems() {
  const items = currentData?.payload?.items || [];
  if (!currentFilter) return items;
  if (currentFilter === "__unassigned__") {
    return items.filter((item) => !(item.training || {}).trainer);
  }
  return items.filter((item) => (item.training || {}).trainer === currentFilter);
}

function renderTables() {
  const items = filteredItems();
  const midpoint = Math.ceil(items.length / 2);
  const left = items.slice(0, midpoint);
  const right = items.slice(midpoint);
  const leftBody = $("leftTable").querySelector("tbody");
  const rightBody = $("rightTable").querySelector("tbody");
  leftBody.innerHTML = "";
  rightBody.innerHTML = "";
  left.forEach((item) => leftBody.appendChild(makeRow(item)));
  right.forEach((item) => rightBody.appendChild(makeRow(item)));
}

function renderFilter() {
  const select = $("trainerFilter");
  const chosen = select.value || currentFilter;
  const active = (currentData?.trainers || []).filter((t) => t.active);
  const seen = new Set();
  select.innerHTML = `<option value="">All Trainers</option><option value="__unassigned__">Freewalk / Unassigned</option>`;
  active.forEach((trainer) => {
    if (!seen.has(trainer.name)) {
      seen.add(trainer.name);
      const option = document.createElement("option");
      option.value = trainer.name;
      option.textContent = trainer.name;
      select.appendChild(option);
    }
  });
  (currentData?.odoo_trainers || []).forEach((name) => {
    if (!seen.has(name)) {
      seen.add(name);
      const option = document.createElement("option");
      option.value = name;
      option.textContent = name;
      select.appendChild(option);
    }
  });
  select.value = [...select.options].some((o) => o.value === chosen) ? chosen : "";
  currentFilter = select.value;
}

function render() {
  if (!currentData) return;
  $("scheduleDate").textContent = `${currentData.payload.day_name}, ${currentData.date}`;
  $("statusText").textContent = `Updated: ${currentData.updated_at || "unknown"}`;
  $("commitText").textContent = currentData.committed_at ? `Committed: ${currentData.committed_at}` : "Not committed";
  renderFilter();
  renderTables();
}

async function loadSchedule(showToast = true) {
  currentData = await api(`/api/schedule?date=${encodeURIComponent(currentDate)}`);
  render();
  if (showToast) toast("Schedule loaded");
}

async function updateNow() {
  $("updateBtn").disabled = true;
  try {
    currentData = await api("/api/update", { method: "POST", body: JSON.stringify({ date: currentDate }) });
    render();
    toast("Schedule updated from Herald/Odoo");
  } catch (err) {
    toast(err.message, 6000);
  } finally {
    $("updateBtn").disabled = false;
  }
}

async function commitNow() {
  const ok = confirm("Commit today's completed schedule to Archivist?");
  if (!ok) return;
  $("commitBtn").disabled = true;
  try {
    const result = await api("/api/commit", { method: "POST", body: JSON.stringify({ date: currentDate }) });
    await loadSchedule(false);
    toast(`Committed to Archivist (${result.herald.completed_items} completed rows)`, 5000);
  } catch (err) {
    toast(err.message, 7000);
  } finally {
    $("commitBtn").disabled = false;
  }
}

document.addEventListener("DOMContentLoaded", () => {
  $("trainerFilter").addEventListener("change", (ev) => {
    currentFilter = ev.target.value;
    renderTables();
  });
  $("updateBtn").addEventListener("click", updateNow);
  $("commitBtn").addEventListener("click", commitNow);
  loadSchedule(false).catch((err) => toast(err.message, 8000));
  setInterval(() => loadSchedule(false).catch(() => {}), 120000);
});
