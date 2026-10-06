const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

const state = {
  weekOf: new URLSearchParams(window.location.search).get("week_of"),
  review: null,
};

function formatDate(iso) {
  const [year, month, day] = iso.split("-").map(Number);
  return `${day} ${MONTHS[month - 1]} ${year}`;
}

function formatHours(value) {
  return Number(value).toFixed(1);
}

function cell(text, className) {
  const td = document.createElement("td");
  td.textContent = text;
  if (className) td.className = className;
  return td;
}

function emptyRow(columns, message) {
  const tr = document.createElement("tr");
  const td = cell(message, "empty");
  td.colSpan = columns;
  tr.appendChild(td);
  return tr;
}

function renderTotals(totals) {
  document.getElementById("total-hours").textContent = formatHours(totals.hours);
  document.getElementById("billable-hours").textContent = formatHours(totals.billable_hours);
  document.getElementById("non-billable-hours").textContent = formatHours(totals.non_billable_hours);
}

function renderLawyers(rows) {
  const body = document.getElementById("lawyer-rows");
  body.replaceChildren();
  if (rows.length === 0) {
    body.appendChild(emptyRow(4, "No time logged this week."));
    return;
  }
  for (const row of rows) {
    const tr = document.createElement("tr");
    tr.append(
      cell(row.lawyer),
      cell(formatHours(row.hours), "num"),
      cell(formatHours(row.billable_hours), "num"),
      cell(formatHours(row.non_billable_hours), "num"),
    );
    body.appendChild(tr);
  }
}

function renderMatters(matters) {
  const body = document.getElementById("matter-rows");
  body.replaceChildren();
  const entries = Object.entries(matters);
  if (entries.length === 0) {
    body.appendChild(emptyRow(4, "No matter time logged this week."));
    return;
  }
  for (const [name, info] of entries) {
    const tr = document.createElement("tr");
    tr.append(
      cell(name),
      cell(info.client),
      cell(formatHours(info.hours), "num"),
      cell(formatHours(info.billable_hours), "num"),
    );
    body.appendChild(tr);
  }
}

function renderIdle(matters) {
  const list = document.getElementById("idle-matters");
  list.replaceChildren();
  if (matters.length === 0) {
    const li = document.createElement("li");
    li.className = "empty";
    li.textContent = "Every open matter had activity this week.";
    list.appendChild(li);
    return;
  }
  for (const matter of matters) {
    const li = document.createElement("li");
    li.textContent = `${matter.matter} (${matter.client})`;
    list.appendChild(li);
  }
}

function showError(message) {
  const el = document.getElementById("error");
  el.textContent = message;
  el.hidden = !message;
}

async function loadReview() {
  const url = state.weekOf ? `/api/review?week_of=${encodeURIComponent(state.weekOf)}` : "/api/review";
  try {
    const response = await fetch(url);
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      throw new Error(body.detail || `Request failed (${response.status})`);
    }
    const review = await response.json();
    state.review = review;
    showError("");
    document.getElementById("week-label").textContent =
      `${formatDate(review.week_start)} – ${formatDate(review.week_end)}`;
    renderTotals(review.totals);
    renderLawyers(review.hours_by_lawyer);
    renderMatters(review.hours_by_matter);
    renderIdle(review.idle_matters);
  } catch (err) {
    showError(`Could not load the weekly review: ${err.message}`);
  }
}

function goToWeek(weekOf) {
  state.weekOf = weekOf;
  const params = new URLSearchParams(window.location.search);
  params.set("week_of", weekOf);
  window.history.replaceState(null, "", `?${params}`);
  loadReview();
}

document.getElementById("prev-week").addEventListener("click", () => {
  if (state.review) goToWeek(state.review.previous_week);
});

document.getElementById("next-week").addEventListener("click", () => {
  if (state.review) goToWeek(state.review.next_week);
});

loadReview();
