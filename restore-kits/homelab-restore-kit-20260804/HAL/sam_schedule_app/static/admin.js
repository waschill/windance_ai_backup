const $ = (id) => document.getElementById(id);

function toast(message, ms = 2400) {
  const el = $("toast");
  el.textContent = message;
  el.hidden = false;
  clearTimeout(window.toastTimer);
  window.toastTimer = setTimeout(() => { el.hidden = true; }, ms);
}

async function api(path, options = {}) {
  const res = await fetch(path, { headers: { "Content-Type": "application/json" }, ...options });
  const data = await res.json();
  if (!res.ok || data.status === "error") throw new Error(data.error || data.detail || "Request failed");
  return data;
}

function clearForm() {
  $("trainerId").value = "";
  $("trainerName").value = "";
  $("trainerSort").value = "100";
  $("trainerActive").checked = true;
}

function render(items) {
  const list = $("trainerList");
  list.innerHTML = "";
  items.forEach((trainer) => {
    const card = document.createElement("div");
    card.className = `trainer-card ${trainer.active ? "" : "inactive"}`;
    const label = document.createElement("div");
    label.innerHTML = `<strong>${trainer.name}</strong><br><small>Sort ${trainer.sort_order} • ${trainer.active ? "Active" : "Inactive"}</small>`;
    const edit = document.createElement("button");
    edit.textContent = "Edit";
    edit.onclick = () => {
      $("trainerId").value = trainer.id;
      $("trainerName").value = trainer.name;
      $("trainerSort").value = trainer.sort_order;
      $("trainerActive").checked = !!trainer.active;
      $("trainerName").focus();
    };
    const del = document.createElement("button");
    del.textContent = "Delete";
    del.onclick = async () => {
      if (!confirm(`Delete trainer ${trainer.name}?`)) return;
      const data = await api("/api/trainers/delete", { method: "POST", body: JSON.stringify({ id: trainer.id }) });
      render(data.items);
      toast("Trainer deleted");
    };
    card.append(label, edit, del);
    list.appendChild(card);
  });
}

async function load() {
  const data = await api("/api/trainers");
  render(data.items);
}

document.addEventListener("DOMContentLoaded", () => {
  $("clearBtn").addEventListener("click", clearForm);
  $("trainerForm").addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const payload = {
      id: $("trainerId").value || null,
      name: $("trainerName").value,
      sort_order: Number($("trainerSort").value || 100),
      active: $("trainerActive").checked,
    };
    try {
      const data = await api("/api/trainers", { method: "POST", body: JSON.stringify(payload) });
      render(data.items);
      clearForm();
      toast("Trainer saved");
    } catch (err) {
      toast(err.message, 5000);
    }
  });
  load().catch((err) => toast(err.message, 5000));
});
