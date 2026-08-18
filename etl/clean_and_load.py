"""
clean_and_load.py

ETL step: takes the raw, intentionally-messy timekeeping export plus the
clean reference tables, applies data-quality rules, loads everything into
a SQLite database against sql/01_schema.sql, then runs the analytical
queries in sql/02_analysis_queries.sql (reimplemented here in Python/SQL)
to produce dashboard/data.json for the front-end.

Run:  python3 clean_and_load.py
"""

import csv
import json
import re
import sqlite3
from collections import defaultdict
from datetime import datetime

DATA_DIR = "../data"
SQL_DIR = "../sql"
DASHBOARD_DIR = "../dashboard"
DB_PATH = f"{DATA_DIR}/studio_analytics.db"

MAX_PLAUSIBLE_DAILY_HOURS = 16.0


# ---------------------------------------------------------------------------
# Cleaning helpers
# ---------------------------------------------------------------------------

def parse_messy_date(raw):
    raw = raw.strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y"):
        try:
            return datetime.strptime(raw, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def parse_messy_hours(raw):
    if raw is None:
        return None, "missing"
    s = raw.strip()
    if s == "":
        return None, "missing"
    s = re.sub(r"[hH]$", "", s).strip()
    try:
        val = float(s)
    except ValueError:
        return None, "unparseable"
    if val < 0:
        return None, "negative"
    if val > MAX_PLAUSIBLE_DAILY_HOURS:
        return None, "implausible_outlier"
    return round(val, 2), None


def normalize_category(raw):
    return raw.strip().title() if raw else raw


# ---------------------------------------------------------------------------
# Load + clean
# ---------------------------------------------------------------------------

def load_csv(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def clean_timekeeping(raw_rows, valid_employee_ids, valid_project_ids):
    stats = defaultdict(int)
    stats["raw_rows"] = len(raw_rows)

    seen = set()
    cleaned = []

    for row in raw_rows:
        emp_id = row["employee_id"].strip()
        proj_id = row["project_id"].strip()

        if not emp_id.isdigit() or int(emp_id) not in valid_employee_ids:
            stats["dropped_orphan_employee"] += 1
            continue
        if not proj_id.isdigit() or int(proj_id) not in valid_project_ids:
            stats["dropped_orphan_project"] += 1
            continue

        work_date = parse_messy_date(row["work_date"])
        if work_date is None:
            stats["dropped_bad_date"] += 1
            continue

        hours, err = parse_messy_hours(row["hours_worked"])
        if err:
            stats[f"dropped_hours_{err}"] += 1
            continue

        category = normalize_category(row["task_category"])
        billable = int(row["billable_flag"])

        dedupe_key = (int(emp_id), int(proj_id), work_date, hours, category)
        if dedupe_key in seen:
            stats["dropped_duplicate"] += 1
            continue
        seen.add(dedupe_key)

        cleaned.append({
            "employee_id": int(emp_id),
            "project_id": int(proj_id),
            "work_date": work_date,
            "hours_worked": hours,
            "task_category": category,
            "billable_flag": billable,
        })

    stats["clean_rows"] = len(cleaned)
    stats["total_dropped"] = stats["raw_rows"] - stats["clean_rows"]
    return cleaned, stats


# ---------------------------------------------------------------------------
# Load into SQLite
# ---------------------------------------------------------------------------

def build_database():
    offices = load_csv(f"{DATA_DIR}/offices.csv")
    industries = load_csv(f"{DATA_DIR}/industries.csv")
    rate_card = load_csv(f"{DATA_DIR}/rate_card.csv")
    clients = load_csv(f"{DATA_DIR}/clients.csv")
    employees = load_csv(f"{DATA_DIR}/employees.csv")
    projects = load_csv(f"{DATA_DIR}/projects.csv")
    raw_timekeeping = load_csv(f"{DATA_DIR}/timekeeping_raw.csv")

    valid_employee_ids = {int(e["employee_id"]) for e in employees}
    valid_project_ids = {int(p["project_id"]) for p in projects}

    cleaned_tk, stats = clean_timekeeping(raw_timekeeping, valid_employee_ids, valid_project_ids)

    conn = sqlite3.connect(DB_PATH)
    with open(f"{SQL_DIR}/01_schema.sql") as f:
        conn.executescript(f.read())

    conn.executemany(
        "INSERT INTO offices VALUES (:office_id, :city, :state, :region, :is_hq)", offices
    )
    conn.executemany(
        "INSERT INTO industries VALUES (:industry_id, :industry_name)", industries
    )
    conn.executemany(
        "INSERT INTO rate_card VALUES (:title, :cost_rate_per_hr, :billing_rate_per_hr)", rate_card
    )
    conn.executemany(
        "INSERT INTO clients VALUES (:client_id, :client_name, :industry_id, :client_tier)", clients
    )
    conn.executemany(
        """INSERT INTO employees VALUES
           (:employee_id, :first_name, :last_name, :office_id, :title, :department,
            :hire_date, :employment_type, :target_utilization, :billable_flag)""",
        employees,
    )
    conn.executemany(
        """INSERT INTO projects VALUES
           (:project_id, :project_name, :client_id, :industry_id, :office_id, :project_type,
            :project_manager_id, :start_date, :planned_end_date,
            NULLIF(:actual_end_date, ''), :status, :budget_hours, :budget_labor_cost, :contract_value)""",
        projects,
    )
    conn.executemany(
        """INSERT INTO timekeeping (employee_id, project_id, work_date, hours_worked, task_category, billable_flag)
           VALUES (:employee_id, :project_id, :work_date, :hours_worked, :task_category, :billable_flag)""",
        cleaned_tk,
    )
    conn.commit()
    return conn, stats


# ---------------------------------------------------------------------------
# Analytical queries -> dashboard JSON
# ---------------------------------------------------------------------------

def rows_as_dicts(cur):
    cols = [c[0] for c in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


def run_analysis(conn):
    cur = conn.cursor()
    out = {}

    cur.execute("""
        SELECT o.office_id, o.city, o.region,
               ROUND(SUM(CASE WHEN t.billable_flag=1 THEN t.hours_worked ELSE 0 END),1) AS billable_hours,
               ROUND(SUM(t.hours_worked),1) AS total_hours,
               ROUND(1.0*SUM(CASE WHEN t.billable_flag=1 THEN t.hours_worked ELSE 0 END)/NULLIF(SUM(t.hours_worked),0),3) AS utilization_rate,
               ROUND(AVG(e.target_utilization),3) AS avg_target_utilization
        FROM timekeeping t
        JOIN employees e ON e.employee_id=t.employee_id
        JOIN offices o ON o.office_id=e.office_id
        GROUP BY o.office_id, o.city, o.region
        ORDER BY utilization_rate DESC
    """)
    out["utilization_by_office"] = rows_as_dicts(cur)

    cur.execute("""
        SELECT p.project_id, p.project_name, c.client_name, i.industry_name, o.city AS office, p.status,
               p.budget_hours, ROUND(COALESCE(h.actual_hours,0),1) AS actual_hours,
               ROUND(COALESCE(h.actual_hours,0)-p.budget_hours,1) AS hours_variance,
               p.budget_labor_cost, ROUND(COALESCE(h.actual_labor_cost,0),2) AS actual_labor_cost,
               p.contract_value, ROUND(p.contract_value-COALESCE(h.actual_labor_cost,0),2) AS gross_margin,
               ROUND(1.0*(p.contract_value-COALESCE(h.actual_labor_cost,0))/NULLIF(p.contract_value,0),3) AS margin_pct
        FROM projects p
        JOIN clients c ON c.client_id=p.client_id
        JOIN industries i ON i.industry_id=p.industry_id
        JOIN offices o ON o.office_id=p.office_id
        LEFT JOIN (
            SELECT t.project_id, SUM(t.hours_worked) AS actual_hours,
                   SUM(t.hours_worked*rc.cost_rate_per_hr) AS actual_labor_cost
            FROM timekeeping t
            JOIN employees e ON e.employee_id=t.employee_id
            JOIN rate_card rc ON rc.title=e.title
            GROUP BY t.project_id
        ) h ON h.project_id=p.project_id
        ORDER BY margin_pct ASC
    """)
    out["projects"] = rows_as_dicts(cur)

    cur.execute("""
        SELECT i.industry_name, COUNT(DISTINCT p.project_id) AS project_count,
               ROUND(SUM(t.hours_worked),1) AS total_hours,
               ROUND(SUM(t.hours_worked*rc.billing_rate_per_hr),2) AS billed_value,
               ROUND(cv.avg_contract_value,2) AS avg_contract_value
        FROM projects p
        JOIN industries i ON i.industry_id=p.industry_id
        LEFT JOIN timekeeping t ON t.project_id=p.project_id
        LEFT JOIN employees e ON e.employee_id=t.employee_id
        LEFT JOIN rate_card rc ON rc.title=e.title
        JOIN (
            SELECT industry_id, AVG(contract_value) AS avg_contract_value
            FROM projects GROUP BY industry_id
        ) cv ON cv.industry_id = p.industry_id
        GROUP BY i.industry_name, cv.avg_contract_value
        ORDER BY total_hours DESC
    """)
    out["industry_mix"] = rows_as_dicts(cur)

    cur.execute("""
        SELECT substr(t.work_date,1,7) AS month,
               ROUND(SUM(CASE WHEN t.billable_flag=1 THEN t.hours_worked ELSE 0 END),1) AS billable_hours,
               ROUND(SUM(t.hours_worked),1) AS total_hours,
               ROUND(SUM(CASE WHEN t.billable_flag=1 THEN t.hours_worked*rc.billing_rate_per_hr ELSE 0 END),2) AS billed_value
        FROM timekeeping t
        JOIN employees e ON e.employee_id=t.employee_id
        JOIN rate_card rc ON rc.title=e.title
        GROUP BY month
        ORDER BY month
    """)
    out["monthly_trend"] = rows_as_dicts(cur)

    cur.execute("""
        SELECT CASE WHEN julianday(actual_end_date)<=julianday(planned_end_date) THEN 'On Time or Early' ELSE 'Late' END AS schedule_outcome,
               COUNT(*) AS project_count,
               ROUND(AVG(julianday(actual_end_date)-julianday(planned_end_date)),1) AS avg_days_variance
        FROM projects
        WHERE status='Complete'
        GROUP BY schedule_outcome
    """)
    out["schedule_performance"] = rows_as_dicts(cur)

    cur.execute("""
        SELECT e.employee_id, e.first_name || ' ' || e.last_name AS project_manager, o.city AS home_office,
               COUNT(DISTINCT p.project_id) AS projects_managed,
               ROUND(AVG(1.0*(p.contract_value-COALESCE(h.actual_labor_cost,0))/NULLIF(p.contract_value,0)),3) AS avg_margin_pct
        FROM projects p
        JOIN employees e ON e.employee_id=p.project_manager_id
        JOIN offices o ON o.office_id=e.office_id
        LEFT JOIN (
            SELECT t.project_id, SUM(t.hours_worked*rc.cost_rate_per_hr) AS actual_labor_cost
            FROM timekeeping t
            JOIN employees emp ON emp.employee_id=t.employee_id
            JOIN rate_card rc ON rc.title=emp.title
            GROUP BY t.project_id
        ) h ON h.project_id=p.project_id
        GROUP BY e.employee_id, project_manager, home_office
        ORDER BY avg_margin_pct DESC
    """)
    out["pm_performance"] = rows_as_dicts(cur)

    cur.execute("""
        SELECT p.status, COUNT(*) AS project_count
        FROM projects p
        GROUP BY p.status
    """)
    out["status_breakdown"] = rows_as_dicts(cur)

    # firm-wide summary headline numbers
    cur.execute("SELECT COUNT(*) FROM employees")
    headcount = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM projects")
    project_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM offices")
    office_count = cur.fetchone()[0]
    cur.execute("""
        SELECT ROUND(1.0*SUM(CASE WHEN billable_flag=1 THEN hours_worked ELSE 0 END)/NULLIF(SUM(hours_worked),0),3)
        FROM timekeeping
    """)
    firm_utilization = cur.fetchone()[0]
    cur.execute("""
        SELECT ROUND(SUM(contract_value),2) FROM projects WHERE status IN ('Active','Complete')
    """)
    total_contract_value = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM timekeeping")
    clean_entry_count = cur.fetchone()[0]

    out["summary"] = {
        "headcount": headcount,
        "project_count": project_count,
        "office_count": office_count,
        "firm_utilization": firm_utilization,
        "total_contract_value": total_contract_value,
        "clean_timekeeping_entries": clean_entry_count,
    }

    return out


def main():
    conn, stats = build_database()
    print("=== ETL cleaning summary ===")
    for k, v in stats.items():
        print(f"  {k}: {v:,}")

    results = run_analysis(conn)
    results["etl_stats"] = dict(stats)

    with open(f"{DASHBOARD_DIR}/data.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nwrote dashboard data -> {DASHBOARD_DIR}/data.json")
    print(f"database written -> {DB_PATH}")

    conn.close()


if __name__ == "__main__":
    main()
