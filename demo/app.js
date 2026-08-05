import { ARG_FIELDS, validateRows, summarize } from "./validate.js";

const STORAGE_KEY = "vidroidcall_items_v1";

const form = document.getElementById("item-form");
const idInput = document.getElementById("f-id");
const utteranceInput = document.getElementById("f-utterance");
const languageInput = document.getElementById("f-language");
const intentInput = document.getElementById("f-intent");
const riskInput = document.getElementById("f-risk");
const splitInput = document.getElementById("f-split");
const notesInput = document.getElementById("f-notes");
const argFieldset = document.getElementById("arg-fields");
const formErrors = document.getElementById("form-errors");
const dashboard = document.getElementById("dashboard");
const tableBody = document.querySelector("#item-table tbody");
const itemCount = document.getElementById("item-count");
const importInput = document.getElementById("import-input");
const importStatus = document.getElementById("import-status");

let items = loadItems();

function loadItems() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function saveItems() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
}

function nextId() {
  let max = 0;
  for (const it of items) {
    const m = /^VDC(\d+)$/.exec(it.id || "");
    if (m) max = Math.max(max, parseInt(m[1], 10));
  }
  return `VDC${String(max + 1).padStart(4, "0")}`;
}

function renderIntentOptions() {
  intentInput.innerHTML = Object.keys(ARG_FIELDS)
    .map((intent) => `<option value="${intent}">${intent}</option>`)
    .join("");
}

function renderArgFields() {
  const intent = intentInput.value;
  const fields = ARG_FIELDS[intent] || [];
  argFieldset.innerHTML = '<legend>Arguments theo intent</legend>';
  if (!fields.length) {
    argFieldset.innerHTML += "<p class=\"hint\">Intent này không cần argument.</p>";
    return;
  }
  for (const f of fields) {
    const div = document.createElement("div");
    div.className = "field";
    div.innerHTML = `<label for="arg-${f.key}">${f.label}</label>
      <input id="arg-${f.key}" data-arg="${f.key}" data-type="${f.type}">`;
    argFieldset.appendChild(div);
  }
}

function collectArguments() {
  const intent = intentInput.value;
  const args = {};
  for (const f of ARG_FIELDS[intent] || []) {
    const el = document.getElementById(`arg-${f.key}`);
    const raw = el ? el.value.trim() : "";
    if (!raw) continue;
    if (intent === "clarify" && f.key === "missing") {
      args.missing = raw.split(",").map((s) => s.trim()).filter(Boolean);
    } else if (f.type === "number") {
      args[f.key] = Number(raw);
    } else {
      args[f.key] = raw;
    }
  }
  return args;
}

function buildCandidate() {
  return {
    id: idInput.value.trim(),
    utterance: utteranceInput.value.trim(),
    language: languageInput.value,
    intent: intentInput.value,
    arguments: collectArguments(),
    risk_level: riskInput.value,
    split: splitInput.value,
    notes: notesInput.value.trim(),
  };
}

function renderDashboard() {
  const summary = summarize(items);
  const errors = validateRows(items);
  const asList = (obj) => Object.entries(obj).map(([k, v]) => `<li>${k}: ${v}</li>`).join("") || "<li>(chưa có)</li>";
  dashboard.innerHTML = `
    <div class="stat-grid">
      <div class="stat"><strong>${summary.n}</strong><span>câu</span></div>
      <div class="stat"><strong>${summary.unique_utterance_rate}</strong><span>tỉ lệ utterance duy nhất</span></div>
      <div class="stat ${errors.length ? "stat-bad" : "stat-good"}"><strong>${errors.length}</strong><span>lỗi validate hiện tại</span></div>
    </div>
    <div class="stat-columns">
      <div><h3>Intent</h3><ul>${asList(summary.intent_counts)}</ul></div>
      <div><h3>Split</h3><ul>${asList(summary.split_counts)}</ul></div>
      <div><h3>Risk</h3><ul>${asList(summary.risk_counts)}</ul></div>
    </div>
    ${errors.length ? `<details><summary>Xem ${errors.length} lỗi</summary><ul>${errors.map((e) => `<li>${e}</li>`).join("")}</ul></details>` : ""}
  `;
}

function renderTable() {
  itemCount.textContent = items.length;
  tableBody.innerHTML = items.map((it) => `
    <tr>
      <td>${it.id}</td>
      <td>${it.utterance}</td>
      <td>${it.intent}</td>
      <td>${it.split}</td>
      <td>${it.risk_level}</td>
      <td><code>${JSON.stringify(it.arguments)}</code></td>
      <td><button type="button" data-delete="${it.id}">Xoá</button></td>
    </tr>
  `).join("");
}

function renderAll() {
  renderDashboard();
  renderTable();
  idInput.value = nextId();
}

form.addEventListener("submit", (e) => {
  e.preventDefault();
  const candidate = buildCandidate();
  const lineNo = items.length + 1;
  const errors = validateRows([...items, candidate]).filter((msg) => msg.startsWith(`Dong ${lineNo}:`));
  if (errors.length) {
    formErrors.innerHTML = `<ul>${errors.map((e) => `<li>${e}</li>`).join("")}</ul>`;
    return;
  }
  formErrors.innerHTML = "";
  items.push(candidate);
  saveItems();
  form.reset();
  languageInput.value = "vi";
  riskInput.value = "medium";
  splitInput.value = "train";
  renderArgFields();
  renderAll();
  utteranceInput.focus();
});

intentInput.addEventListener("change", renderArgFields);

tableBody.addEventListener("click", (e) => {
  const id = e.target.getAttribute("data-delete");
  if (!id) return;
  items = items.filter((it) => it.id !== id);
  saveItems();
  renderAll();
});

document.getElementById("export-btn").addEventListener("click", () => {
  const text = items.map((it) => JSON.stringify({
    id: it.id,
    utterance: it.utterance,
    language: it.language,
    intent: it.intent,
    arguments: it.arguments,
    risk_level: it.risk_level,
    split: it.split,
    notes: it.notes,
  })).join("\n") + (items.length ? "\n" : "");
  const blob = new Blob([text], { type: "application/x-ndjson" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `vidroidcall_export_${new Date().toISOString().slice(0, 10)}.jsonl`;
  a.click();
  URL.revokeObjectURL(a.href);
});

document.getElementById("reset-btn").addEventListener("click", () => {
  if (!confirm("Xoá toàn bộ dữ liệu đã nhập trong trình duyệt này?")) return;
  items = [];
  saveItems();
  renderAll();
  importStatus.textContent = "";
});

importInput.addEventListener("change", async () => {
  const file = importInput.files[0];
  if (!file) return;
  const text = await file.text();
  const existingIds = new Set(items.map((it) => it.id));
  let added = 0;
  let skipped = 0;
  let malformed = 0;
  for (const line of text.split("\n")) {
    if (!line.trim()) continue;
    let obj;
    try {
      obj = JSON.parse(line);
    } catch {
      malformed += 1;
      continue;
    }
    if (existingIds.has(obj.id)) {
      skipped += 1;
      continue;
    }
    items.push(obj);
    existingIds.add(obj.id);
    added += 1;
  }
  saveItems();
  renderAll();
  const errors = validateRows(items);
  importStatus.textContent = `Đã nhập ${added} dòng, bỏ qua ${skipped} trùng id, ${malformed} dòng lỗi JSON. Hiện có ${errors.length} lỗi validate tổng thể (xem Dashboard).`;
  importInput.value = "";
});

renderIntentOptions();
renderArgFields();
renderAll();
