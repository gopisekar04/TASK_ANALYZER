const API = "http://127.0.0.1:8000/api/tasks";

function showError(msg) {
  document.getElementById("error").innerText = msg;
}

function clearError() {
  document.getElementById("error").innerText = "";
}


function appendTask(task) {
  const container = document.getElementById("taskList");

  // create table only once
  let table = container.querySelector("table");

  if (!table) {
    table = document.createElement("table");
    table.style.width = "100%";

    table.innerHTML = `
      <thead>
        <tr>
          <th>id</th>
          <th>title</th>
          <th>effort</th>
          <th>importance</th>
          <th>dependencies</th>
        </tr>
      </thead>
      <tbody></tbody>
    `;

    container.innerHTML = "";
    container.appendChild(table);
  }

  const tbody = table.querySelector("tbody");
  const row = document.createElement("tr");

  row.innerHTML = `
    <td>${task.id}</td>
    <td>${task.title}</td>
    <td>${task.estimated_hours} hr</td>
    <td>${task.importance}</td>
    <td>${task.dependencies.join(", ") || "None"}</td>
  `;

  tbody.appendChild(row);
}


document.getElementById("addTaskForm")
  .addEventListener("submit", function (e) {
    e.preventDefault();
    addTask();
  });


async function addTask() {
  clearError();
  if (!title.value || !hours.value || !importance.value) {
    return showError("Fill all required fields before submitting.");
  }


  const data = {
    task: {
      title: title.value,
      due_date: due_date.value || null,
      estimated_hours: +hours.value,
      importance: +importance.value || 5,
      dependencies: deps.value ? deps.value.split(",").map(Number) : []
    }
  };

  try {
    const res = await fetch(API + "/add/", {
      method: "POST",
      body: JSON.stringify(data)
    });

    const json = await res.json();
    if (!res.ok) throw new Error(json.error || "Failed to add task");
    const {message, id} = json

    appendTask({
      id: id,
      title: data.task.title,
      estimated_hours: data.task.estimated_hours,
      importance: data.task.importance,
      dependencies: data.task.dependencies
    });

    if (json.warnings?.length) alert(json.warnings.join("\n"));

  } catch (err) {
    showError(err.message);
  }
}

function renderResults(tasks) {
  console.log(tasks);
  
  const box = document.getElementById("result");
  box.innerHTML = "";

  const table = document.createElement("table");
  table.style.width = "100%";

  table.innerHTML = `
    <thead>
      <tr>
        <th>id</th>
        <th>title</th>
        <th>effort</th>
        <th>importance</th>
        <th>due_date</th>
        <th>priority_score</th>
        <th>Reason</th>
        <th>flag</th>
      </tr>
    </thead>
    <tbody></tbody>
  `;

  const tbody = table.querySelector("tbody");

  tasks.forEach(t => {
    const indicator = (t.priority_indicator || "").toLowerCase();

    const flag =
      indicator === "high"   ? "🔴" :
      indicator === "medium" ? "🟡" :
      indicator === "low"    ? "🟢" :
                               "⚪";

    const tr = document.createElement("tr");

    tr.innerHTML = `
      <td>${t.id ?? "-"}</td>
      <td>${t.title}</td>
      <td>${t.effort ?? "-"} hr/s</td>
      <td>${t.importance ?? "-"}</td>
      <td>${t.due_date ?? "-"}</td>
      <td>${t.priority_score ?? "-"}</td>
      <td class="reasons">${t.reasons.join(",") || "-"}</td>
      <td">${flag}</td>
    `;

    tbody.appendChild(tr);
  });

  box.appendChild(table);
}

async function analyzeTask() {
  clearError();

  let raw;
  try {
    raw = JSON.parse(bulk.value);
  } catch {
    return showError("Invalid JSON");
  }

  try {
    const mode = document.getElementById("mode").value;
    const res = await fetch(API + `/analyze/?mode=${mode}`, {
      method: "POST",
      body: JSON.stringify({ tasks: raw })
    });

    const json = await res.json();
    if (!res.ok) throw new Error(json.error || "Analysis failed");

    renderResults(json.ranked_tasks);

  } catch (err) {
    showError(err.message);
  }
}

function showEmptyMessage() {
  const box = document.getElementById("taskList");
  box.innerHTML = "<i>No tasks yet.</i>";
}

async function clearAllTasks() {
  if (!confirm("Delete ALL tasks? This cannot be undone.")) return;

  try {
    const res = await fetch(API + "/clear/", { method: "POST" });
    const json = await res.json();
    if (!res.ok) throw new Error(json.error || "Clear failed");

    document.getElementById("taskList").innerHTML = "";
    showEmptyMessage();
  } catch (e) {
    showError(e.message);
  }
}

function renderTasks(tasks) {
  const container = document.getElementById("taskList");
  container.innerHTML = "";

  if (!tasks.length) {
    return container.innerHTML = "<i>No tasks yet.</i>";
  }

  const table = document.createElement("table");
  // table.style.width = "100%";

  table.innerHTML = `
    <thead>
      <tr>
        <th>id</th>
        <th>title</th>
        <th>effort</th>
        <th>importance</th>
        <th>dependencies</th>
      </tr>
    </thead>
    <tbody></tbody>
  `;

  const tbody = table.querySelector("tbody");

  tasks.forEach(task => appendTask(task, tbody));
}


async function loadTasks() {
  try {
    const res = await fetch(API + "/list/");
    const json = await res.json();
    if (!res.ok) throw new Error(json.error || "Failed to load");

    renderTasks(json.tasks || []);
  } catch (e) {
    showError(e.message);
  }
}

loadTasks();