"""
build.py

Assembles the final, self-contained dashboard/index.html by embedding
dashboard/data.json directly into the page (as a JS const) so the dashboard
opens standalone via double-click -- no local server, no fetch()/CORS issues.

Run this after etl/clean_and_load.py has produced data.json.
"""

import json

with open("data.json") as f:
    data = json.load(f)

DATA_JSON = json.dumps(data)

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Studio Performance Analytics</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.4/chart.umd.min.js"></script>
<style>
  :root {
    --navy: #1b2a4a;
    --navy-light: #2c3e63;
    --charcoal: #23262b;
    --copper: #c1652f;
    --copper-light: #e08a52;
    --gold: #b9974a;
    --bg: #f6f4f0;
    --card: #ffffff;
    --border: #e6e2d8;
    --muted: #6b7280;
    --green: #2f7a4f;
    --red: #b23b3b;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    background: var(--bg);
    color: var(--charcoal);
  }
  header {
    background: linear-gradient(120deg, var(--navy) 0%, var(--navy-light) 100%);
    color: #fff;
    padding: 28px 40px 24px;
  }
  header .eyebrow {
    text-transform: uppercase;
    letter-spacing: 0.12em;
    font-size: 11px;
    color: var(--copper-light);
    font-weight: 600;
    margin-bottom: 6px;
  }
  header h1 {
    margin: 0 0 6px;
    font-size: 26px;
    font-weight: 700;
    letter-spacing: -0.01em;
  }
  header p {
    margin: 0;
    color: #c7cfe0;
    font-size: 14px;
    max-width: 760px;
    line-height: 1.5;
  }
  main {
    max-width: 1240px;
    margin: 0 auto;
    padding: 28px 40px 60px;
  }
  .kpi-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    margin-bottom: 28px;
  }
  .kpi-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 18px 20px;
    box-shadow: 0 1px 2px rgba(0,0,0,0.03);
  }
  .kpi-card .label {
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--muted);
    font-weight: 600;
    margin-bottom: 8px;
  }
  .kpi-card .value {
    font-size: 28px;
    font-weight: 700;
    color: var(--navy);
  }
  .kpi-card .sub {
    font-size: 12.5px;
    color: var(--muted);
    margin-top: 4px;
  }
  .grid-2 {
    display: grid;
    grid-template-columns: 1.3fr 1fr;
    gap: 16px;
    margin-bottom: 16px;
  }
  .grid-3 {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 16px;
    margin-bottom: 16px;
  }
  .panel {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 18px 20px 12px;
    box-shadow: 0 1px 2px rgba(0,0,0,0.03);
  }
  .panel h2 {
    font-size: 14.5px;
    margin: 0 0 2px;
    color: var(--navy);
    font-weight: 700;
  }
  .panel .panel-sub {
    font-size: 12px;
    color: var(--muted);
    margin-bottom: 12px;
  }
  .chart-wrap { position: relative; height: 240px; }
  .chart-wrap.tall { height: 320px; }
  section.block { margin-top: 8px; margin-bottom: 28px; }
  section.block > h3 {
    font-size: 16px;
    color: var(--navy);
    margin: 0 0 4px;
  }
  section.block > .desc {
    font-size: 13px;
    color: var(--muted);
    margin-bottom: 14px;
    max-width: 820px;
    line-height: 1.5;
  }
  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
  }
  th {
    text-align: left;
    background: #f0eee7;
    color: var(--navy);
    font-weight: 700;
    padding: 8px 10px;
    position: sticky;
    top: 0;
    cursor: pointer;
    user-select: none;
    white-space: nowrap;
  }
  th:hover { background: #e6e2d8; }
  td {
    padding: 7px 10px;
    border-bottom: 1px solid var(--border);
    white-space: nowrap;
  }
  tr:hover td { background: #faf9f6; }
  .table-wrap { max-height: 420px; overflow: auto; border: 1px solid var(--border); border-radius: 8px; }
  .pill {
    display: inline-block;
    padding: 2px 9px;
    border-radius: 999px;
    font-size: 11px;
    font-weight: 700;
  }
  .pill.Active { background: #e5f0ea; color: var(--green); }
  .pill.Complete { background: #e6eaf3; color: var(--navy); }
  .pill.On-Hold, .pill.OnHold { background: #fbeee0; color: var(--copper); }
  .pill.Cancelled { background: #f6e4e4; color: var(--red); }
  .margin-neg { color: var(--red); font-weight: 700; }
  .margin-pos { color: var(--green); font-weight: 700; }
  .controls { display:flex; gap:10px; margin-bottom:10px; flex-wrap:wrap; align-items:center; }
  input[type=text] {
    padding: 7px 10px;
    border: 1px solid var(--border);
    border-radius: 6px;
    font-size: 13px;
    width: 240px;
  }
  select {
    padding: 7px 10px;
    border: 1px solid var(--border);
    border-radius: 6px;
    font-size: 13px;
    background: #fff;
  }
  .etl-strip {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    margin-top: 10px;
  }
  .etl-chip {
    background: #f0eee7;
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 12.5px;
    color: var(--charcoal);
  }
  .etl-chip b { color: var(--navy); }
  footer {
    text-align: center;
    color: var(--muted);
    font-size: 12px;
    padding: 20px 0 40px;
  }
  @media (max-width: 1000px) {
    .kpi-grid { grid-template-columns: repeat(2, 1fr); }
    .grid-2, .grid-3 { grid-template-columns: 1fr; }
  }
</style>
</head>
<body>

<header>
  <div class="eyebrow">Studio Performance Analytics &middot; Prototype</div>
  <h1>Multi-Office Project &amp; Labor Intelligence Dashboard</h1>
  <p>A business intelligence prototype modeling how a multi-office, project-based architecture &amp; engineering
     studio could track staff utilization, project profitability, and industry mix from raw timekeeping data.
     Built end-to-end: SQL data model &rarr; Python ETL/cleaning &rarr; analytical SQL &rarr; this dashboard.
     All company, client, and personnel data below is synthetic.</p>
</header>

<main>

  <div class="kpi-grid" id="kpiGrid"></div>

  <div class="grid-2">
    <div class="panel">
      <h2>Utilization by Office</h2>
      <div class="panel-sub">Billable hours as a share of total hours logged, vs. each office's blended target</div>
      <div class="chart-wrap"><canvas id="chartUtilization"></canvas></div>
    </div>
    <div class="panel">
      <h2>Work Mix by Industry</h2>
      <div class="panel-sub">Share of billed value by client industry</div>
      <div class="chart-wrap"><canvas id="chartIndustry"></canvas></div>
    </div>
  </div>

  <div class="panel" style="margin-bottom:16px;">
    <h2>Firm-Wide Labor &amp; Billed Value Trend</h2>
    <div class="panel-sub">Monthly billable hours and billed value across all offices</div>
    <div class="chart-wrap tall"><canvas id="chartTrend"></canvas></div>
  </div>

  <div class="grid-2">
    <div class="panel">
      <h2>Schedule Performance</h2>
      <div class="panel-sub">Completed projects: on time/early vs. late</div>
      <div class="chart-wrap"><canvas id="chartSchedule"></canvas></div>
    </div>
    <div class="panel">
      <h2>Project Status Mix</h2>
      <div class="panel-sub">Current pipeline across all 72 tracked projects</div>
      <div class="chart-wrap"><canvas id="chartStatus"></canvas></div>
    </div>
  </div>

  <section class="block">
    <h3>Project Profitability</h3>
    <div class="desc">Every tracked project, ranked by gross margin (contract value less actual labor cost at loaded
      rates). Search or sort to find at-risk projects &mdash; negative or thin margins typically mean actual hours
      ran well over budget.</div>
    <div class="controls">
      <input type="text" id="projectSearch" placeholder="Search project, client, office...">
      <select id="statusFilter">
        <option value="">All statuses</option>
        <option value="Active">Active</option>
        <option value="Complete">Complete</option>
        <option value="On Hold">On Hold</option>
        <option value="Cancelled">Cancelled</option>
      </select>
    </div>
    <div class="table-wrap">
      <table id="projectsTable">
        <thead>
          <tr>
            <th data-key="project_name">Project</th>
            <th data-key="client_name">Client</th>
            <th data-key="industry_name">Industry</th>
            <th data-key="office">Office</th>
            <th data-key="status">Status</th>
            <th data-key="budget_hours">Budget Hrs</th>
            <th data-key="actual_hours">Actual Hrs</th>
            <th data-key="hours_variance">Hrs Var</th>
            <th data-key="contract_value">Contract Value</th>
            <th data-key="gross_margin">Gross Margin</th>
            <th data-key="margin_pct">Margin %</th>
          </tr>
        </thead>
        <tbody id="projectsBody"></tbody>
      </table>
    </div>
  </section>

  <section class="block">
    <h3>Project Manager Performance</h3>
    <div class="desc">Average margin delivered across each PM's book of projects.</div>
    <div class="table-wrap" style="max-height:280px;">
      <table id="pmTable">
        <thead>
          <tr>
            <th data-key="project_manager">Project Manager</th>
            <th data-key="home_office">Home Office</th>
            <th data-key="projects_managed">Projects</th>
            <th data-key="avg_margin_pct">Avg Margin %</th>
          </tr>
        </thead>
        <tbody id="pmBody"></tbody>
      </table>
    </div>
  </section>

  <section class="block">
    <h3>Data Quality &amp; ETL Summary</h3>
    <div class="desc">The raw timekeeping export is real-world messy: inconsistent date formats, stray units on
      hours, whitespace/casing inconsistencies, duplicate syncs, and a small number of orphaned references. The
      cleaning pipeline below is what makes the numbers above trustworthy.</div>
    <div class="etl-strip" id="etlStrip"></div>
  </section>

</main>

<footer>
  Studio Performance Analytics &mdash; a self-directed BI portfolio project. Synthetic data, built with SQLite, Python, and Chart.js.
</footer>

<script>
const DATA = __DATA_JSON__;

function fmtNum(n, decimals=0) {
  if (n === null || n === undefined) return "—";
  return Number(n).toLocaleString(undefined, {minimumFractionDigits: decimals, maximumFractionDigits: decimals});
}
function fmtPct(n) {
  if (n === null || n === undefined) return "—";
  return (n*100).toFixed(1) + "%";
}
function fmtMoney(n) {
  if (n === null || n === undefined) return "—";
  return "$" + Number(n).toLocaleString(undefined, {maximumFractionDigits:0});
}

const NAVY = "#1b2a4a";
const COPPER = "#c1652f";
const GOLD = "#b9974a";
const GREEN = "#2f7a4f";
const RED = "#b23b3b";
const SLATE = "#8a93a6";
const PALETTE = ["#1b2a4a","#c1652f","#b9974a","#5b7f9e","#7a5c8e","#3e8060"];

// ---------- KPI cards ----------
const s = DATA.summary;
const etl = DATA.etl_stats;
const kpis = [
  {label:"Firm-Wide Utilization", value: fmtPct(s.firm_utilization), sub: `${fmtNum(s.headcount)} employees across ${s.office_count} offices`},
  {label:"Active + Complete Contract Value", value: fmtMoney(s.total_contract_value), sub: `${s.project_count} tracked projects`},
  {label:"Clean Timekeeping Entries", value: fmtNum(s.clean_timekeeping_entries), sub: `from ${fmtNum(etl.raw_rows)} raw entries (${fmtNum(etl.total_dropped)} removed)`},
  {label:"Offices Tracked", value: fmtNum(s.office_count), sub: "Bentonville HQ + 6 satellite studios"},
];
document.getElementById("kpiGrid").innerHTML = kpis.map(k => `
  <div class="kpi-card">
    <div class="label">${k.label}</div>
    <div class="value">${k.value}</div>
    <div class="sub">${k.sub}</div>
  </div>`).join("");

// ---------- Utilization by office ----------
new Chart(document.getElementById("chartUtilization"), {
  type: "bar",
  data: {
    labels: DATA.utilization_by_office.map(r => r.city),
    datasets: [
      {label: "Actual Utilization", data: DATA.utilization_by_office.map(r => (r.utilization_rate*100).toFixed(1)), backgroundColor: NAVY, borderRadius: 4},
      {label: "Target", data: DATA.utilization_by_office.map(r => (r.avg_target_utilization*100).toFixed(1)), backgroundColor: COPPER, borderRadius: 4},
    ]
  },
  options: {
    responsive: true, maintainAspectRatio: false,
    scales: { y: { beginAtZero: true, max: 100, ticks: { callback: v => v + "%" } } },
    plugins: { legend: { position: "bottom", labels: { boxWidth: 12, font: {size: 11} } } }
  }
});

// ---------- Industry mix (donut, billed value) ----------
new Chart(document.getElementById("chartIndustry"), {
  type: "doughnut",
  data: {
    labels: DATA.industry_mix.map(r => r.industry_name),
    datasets: [{ data: DATA.industry_mix.map(r => r.billed_value), backgroundColor: PALETTE }]
  },
  options: {
    responsive: true, maintainAspectRatio: false,
    plugins: {
      legend: { position: "bottom", labels: { boxWidth: 10, font: {size: 10.5} } },
      tooltip: { callbacks: { label: ctx => `${ctx.label}: ${fmtMoney(ctx.raw)}` } }
    }
  }
});

// ---------- Monthly trend (dual axis) ----------
new Chart(document.getElementById("chartTrend"), {
  type: "line",
  data: {
    labels: DATA.monthly_trend.map(r => r.month),
    datasets: [
      {label: "Billable Hours", data: DATA.monthly_trend.map(r => r.billable_hours), borderColor: NAVY, backgroundColor: NAVY, yAxisID: "y", tension: 0.25, pointRadius: 2},
      {label: "Billed Value ($)", data: DATA.monthly_trend.map(r => r.billed_value), borderColor: COPPER, backgroundColor: COPPER, yAxisID: "y1", tension: 0.25, pointRadius: 2},
    ]
  },
  options: {
    responsive: true, maintainAspectRatio: false,
    interaction: { mode: "index", intersect: false },
    scales: {
      y: { type: "linear", position: "left", title: { display: true, text: "Hours" } },
      y1: { type: "linear", position: "right", title: { display: true, text: "Billed Value ($)" }, grid: { drawOnChartArea: false } },
    },
    plugins: { legend: { position: "bottom" } }
  }
});

// ---------- Schedule performance ----------
new Chart(document.getElementById("chartSchedule"), {
  type: "doughnut",
  data: {
    labels: DATA.schedule_performance.map(r => `${r.schedule_outcome} (avg ${r.avg_days_variance>0?"+":""}${r.avg_days_variance}d)`),
    datasets: [{ data: DATA.schedule_performance.map(r => r.project_count), backgroundColor: [GREEN, RED] }]
  },
  options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: "bottom", labels: {font:{size:11}} } } }
});

// ---------- Status mix ----------
const statusOrder = ["Active","Complete","On Hold","Cancelled"];
const statusSorted = statusOrder.map(st => DATA.status_breakdown.find(r => r.status===st)).filter(Boolean);
new Chart(document.getElementById("chartStatus"), {
  type: "pie",
  data: {
    labels: statusSorted.map(r => r.status),
    datasets: [{ data: statusSorted.map(r => r.project_count), backgroundColor: [GREEN, NAVY, GOLD, RED] }]
  },
  options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: "bottom" } } }
});

// ---------- Projects table ----------
let sortKey = "margin_pct", sortDir = 1;
function renderProjects() {
  const q = document.getElementById("projectSearch").value.toLowerCase();
  const statusF = document.getElementById("statusFilter").value;
  let rows = DATA.projects.filter(r =>
    (!statusF || r.status === statusF) &&
    (!q || (r.project_name+r.client_name+r.office).toLowerCase().includes(q))
  );
  rows.sort((a,b) => (a[sortKey] > b[sortKey] ? 1 : -1) * sortDir);
  document.getElementById("projectsBody").innerHTML = rows.map(r => `
    <tr>
      <td>${r.project_name}</td>
      <td>${r.client_name}</td>
      <td>${r.industry_name}</td>
      <td>${r.office}</td>
      <td><span class="pill ${r.status.replace(' ','-')}">${r.status}</span></td>
      <td>${fmtNum(r.budget_hours)}</td>
      <td>${fmtNum(r.actual_hours)}</td>
      <td>${fmtNum(r.hours_variance)}</td>
      <td>${fmtMoney(r.contract_value)}</td>
      <td class="${r.gross_margin<0?'margin-neg':'margin-pos'}">${fmtMoney(r.gross_margin)}</td>
      <td class="${r.margin_pct<0?'margin-neg':'margin-pos'}">${fmtPct(r.margin_pct)}</td>
    </tr>`).join("");
}
document.getElementById("projectSearch").addEventListener("input", renderProjects);
document.getElementById("statusFilter").addEventListener("change", renderProjects);
document.querySelectorAll("#projectsTable th").forEach(th => {
  th.addEventListener("click", () => {
    const key = th.dataset.key;
    sortDir = (sortKey === key) ? -sortDir : 1;
    sortKey = key;
    renderProjects();
  });
});
renderProjects();

// ---------- PM table ----------
document.getElementById("pmBody").innerHTML = DATA.pm_performance.map(r => `
  <tr>
    <td>${r.project_manager}</td>
    <td>${r.home_office}</td>
    <td>${r.projects_managed}</td>
    <td class="${r.avg_margin_pct<0?'margin-neg':'margin-pos'}">${fmtPct(r.avg_margin_pct)}</td>
  </tr>`).join("");

// ---------- ETL summary chips ----------
const etlLabels = {
  raw_rows: "Raw rows",
  dropped_hours_missing: "Dropped (blank hours)",
  dropped_hours_negative: "Dropped (negative hours)",
  dropped_hours_implausible_outlier: "Dropped (implausible &gt;16h entry)",
  dropped_hours_unparseable: "Dropped (unparseable hours)",
  dropped_duplicate: "Dropped (duplicate sync)",
  dropped_orphan_employee: "Dropped (orphan employee ref)",
  dropped_orphan_project: "Dropped (orphan project ref)",
  dropped_bad_date: "Dropped (unparseable date)",
  clean_rows: "Clean rows loaded",
  total_dropped: "Total removed",
};
document.getElementById("etlStrip").innerHTML = Object.entries(etlLabels)
  .filter(([k]) => etl[k] !== undefined)
  .map(([k,label]) => `<div class="etl-chip"><b>${fmtNum(etl[k])}</b> &nbsp;${label}</div>`).join("");
</script>

</body>
</html>
"""

with open("index.html", "w") as f:
    f.write(HTML_TEMPLATE.replace("__DATA_JSON__", DATA_JSON))

print("wrote index.html")
