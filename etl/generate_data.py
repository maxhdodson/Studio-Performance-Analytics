"""
generate_data.py

Synthetic (but realistic) data generator for a mid-size, employee-owned
architecture + engineering firm modeled on the operating profile of a
national retail/hospitality/healthcare A&E studio (multi-office, project-based,
timekeeping-driven).

All company, client, and employee names below are fictional. No real client
or personnel data is used anywhere in this project.

Output: raw CSVs in ../data/, intentionally messy in the timekeeping file
(inconsistent date formats, stray whitespace/casing, duplicate entries,
a handful of orphaned/negative/blank values) so the ETL step has real
cleaning work to do -- mirroring the kind of raw timekeeping data a BI
analyst actually receives.
"""

import csv
import random
from datetime import date, timedelta

random.seed(42)

OUT_DIR = "../data"

# ---------------------------------------------------------------------------
# Reference data
# ---------------------------------------------------------------------------

OFFICES = [
    # office_id, city, state, region, is_hq
    (1, "Bentonville", "AR", "South", 1),
    (2, "Springfield", "MO", "Midwest", 0),
    (3, "Fort Worth", "TX", "South", 0),
    (4, "Boston", "MA", "Northeast", 0),
    (5, "Franklin", "MA", "Northeast", 0),
    (6, "Baltimore", "MD", "Northeast", 0),
    (7, "Mexico City", "MX", "International", 0),
]

# relative headcount weighting per office (Bentonville = HQ, largest)
OFFICE_WEIGHTS = [0.34, 0.13, 0.12, 0.15, 0.08, 0.10, 0.08]

INDUSTRIES = [
    (1, "Retail"),
    (2, "Hospitality"),
    (3, "Healthcare"),
    (4, "Industrial"),
    (5, "Real Estate Development"),
    (6, "Science & Tech"),
]

TITLES = [
    # title, department, billable_target, weight
    ("Project Architect", "Architecture", 0.75, 10),
    ("Design Architect", "Architecture", 0.70, 6),
    ("Architectural Designer", "Architecture", 0.80, 10),
    ("Structural Engineer", "Engineering", 0.75, 6),
    ("MEP Engineer", "Engineering", 0.75, 7),
    ("Civil Engineer", "Engineering", 0.75, 4),
    ("Interior Designer", "Interior Design", 0.78, 7),
    ("BIM/CAD Technician", "Architecture", 0.82, 9),
    ("Construction Administrator", "Project Delivery", 0.72, 6),
    ("Project Manager", "Project Delivery", 0.65, 8),
    ("Senior Project Manager", "Project Delivery", 0.55, 4),
    ("Studio Director", "Leadership", 0.35, 3),
    ("Business Development Manager", "Operations", 0.20, 2),
    ("Marketing Coordinator", "Operations", 0.10, 2),
    ("Accounting Specialist", "Operations", 0.05, 2),
    ("Operations/BI Analyst", "Operations", 0.15, 2),
]

FIRST_NAMES = [
    "James","Maria","David","Ashley","Michael","Jennifer","Robert","Linda","William","Elizabeth",
    "Carlos","Priya","Wei","Fatima","John","Sarah","Daniel","Laura","Kevin","Megan",
    "Andres","Grace","Omar","Nicole","Brian","Rachel","Tyler","Hannah","Jorge","Emily",
    "Steven","Amanda","Marcus","Olivia","Diego","Sofia","Ethan","Chloe","Nathan","Victoria",
    "Ricardo","Alicia","Trevor","Brittany","Xavier","Paige","Miguel","Samantha","Derek","Kayla",
]
LAST_NAMES = [
    "Whitfield","Nguyen","Martinez","Coleman","Sullivan","Patel","Kowalski","Reyes","Bennett","Foster",
    "Alvarado","Chen","O'Brien","Larsen","Ibarra","Simmons","Delgado","Sato","Marsh","Herrera",
    "Doyle","Castillo","Fitzgerald","Osei","Vargas","Rowland","Mendez","Blackwood","Torres","Keating",
    "Nakamura","Guerrero","Winslow","Ramos","Beckett","Salinas","Hartley","Ochoa","Preston","Lindqvist",
]

PROJECT_TYPES_BY_INDUSTRY = {
    1: ["New Store Prototype", "Store Remodel Program", "Store Rollout", "Tenant Improvement", "Store Refresh"],
    2: ["New Restaurant Prototype", "Restaurant Remodel", "Hotel Renovation", "Restaurant Rollout"],
    3: ["Clinic Buildout", "Medical Office Renovation", "Urgent Care Prototype"],
    4: ["Distribution Center", "Warehouse Expansion", "Fulfillment Center Buildout"],
    5: ["Ground-Up Development", "Mixed-Use Development", "Corporate HQ Buildout"],
    6: ["Lab Buildout", "R&D Facility Renovation", "Tech Campus Expansion"],
}

CLIENT_NAMES_BY_INDUSTRY = {
    1: ["Northgate Mart", "CopperLeaf Grocers", "Trailhead Outfitters", "Summit Home & Hardware",
        "Basecamp Supply Co.", "Ridgeline Pharmacy", "Cardinal Variety Stores", "Prairie Fresh Market",
        "Union Square Goods", "Bluebonnet General Store"],
    2: ["Basecamp Coffee Co.", "Harvest Table Kitchen", "Redwood Grill", "Golden Skillet",
        "Fernwood Hospitality Group", "Route 9 Diner Co.", "Sable Hotel Collective"],
    3: ["Meridian Health Partners", "Cascade Family Clinics", "BrightPath Urgent Care",
        "Northstar Medical Group", "Willowbrook Health"],
    4: ["Atlas Logistics", "Pioneer Distribution Group", "Vantage Supply Chain", "Ironwood Freight"],
    5: ["Cobalt Real Estate Partners", "Highline Development Group", "Anchor Point Ventures"],
    6: ["Nimbus Technologies", "Vertex Labs", "Quanta Research Group"],
}

TASK_CATEGORIES = [
    "Design", "Construction Documents", "Construction Admin", "Site Visit",
    "Client Meetings", "Internal Coordination", "Business Development", "PTO/Holiday",
]
# billable weighting -- last two categories are non-billable
NONBILLABLE = {"Internal Coordination", "Business Development", "PTO/Holiday"}

STATUS_WEIGHTS = [("Active", 0.55), ("Complete", 0.35), ("On Hold", 0.06), ("Cancelled", 0.04)]

# Loaded cost rate (fully-burdened $/hr the firm pays) vs. standard billing
# rate ($/hr charged to clients) by title -- a simplified rate card typical
# of an A/E firm, used to translate raw hours into actual labor cost/revenue.
RATE_CARD = {
    "Project Architect":            (72, 155),
    "Design Architect":             (78, 170),
    "Architectural Designer":       (48, 115),
    "Structural Engineer":          (75, 160),
    "MEP Engineer":                 (74, 158),
    "Civil Engineer":               (73, 155),
    "Interior Designer":            (58, 130),
    "BIM/CAD Technician":           (45, 105),
    "Construction Administrator":   (55, 120),
    "Project Manager":              (68, 145),
    "Senior Project Manager":       (85, 175),
    "Studio Director":              (95, 195),
    "Business Development Manager": (60, 0),   # non-billable role
    "Marketing Coordinator":        (40, 0),
    "Accounting Specialist":        (42, 0),
    "Operations/BI Analyst":        (46, 0),
}


def weighted_choice(pairs):
    items, weights = zip(*pairs)
    return random.choices(items, weights=weights, k=1)[0]


def gen_offices():
    rows = []
    for oid, city, state, region, is_hq in OFFICES:
        rows.append({"office_id": oid, "city": city, "state": state, "region": region, "is_hq": is_hq})
    return rows


def gen_employees(n=220):
    rows = []
    office_ids = [o[0] for o in OFFICES]
    titles, depts, targets, weights = zip(*TITLES)
    used_names = set()
    for eid in range(1, n + 1):
        office_id = random.choices(office_ids, weights=OFFICE_WEIGHTS, k=1)[0]
        idx = random.choices(range(len(TITLES)), weights=weights, k=1)[0]
        title, dept, target, _ = TITLES[idx]

        while True:
            fn = random.choice(FIRST_NAMES)
            ln = random.choice(LAST_NAMES)
            if (fn, ln) not in used_names:
                used_names.add((fn, ln))
                break

        hire_year = random.choices([2019, 2020, 2021, 2022, 2023, 2024, 2025],
                                    weights=[10, 10, 14, 16, 18, 18, 14], k=1)[0]
        hire_month = random.randint(1, 12)
        hire_day = random.randint(1, 28)
        hire_date = date(hire_year, hire_month, hire_day)
        if hire_date > date(2026, 6, 1):
            hire_date = date(2025, 6, 1)

        employment_type = random.choices(["Full-Time", "Contract"], weights=[92, 8], k=1)[0]
        billable = 0 if dept in ("Leadership", "Operations") and random.random() < 0.6 else 1

        rows.append({
            "employee_id": eid,
            "first_name": fn,
            "last_name": ln,
            "office_id": office_id,
            "title": title,
            "department": dept,
            "hire_date": hire_date.isoformat(),
            "employment_type": employment_type,
            "target_utilization": target,
            "billable_flag": billable,
        })
    return rows


def gen_clients():
    rows = []
    cid = 1
    for industry_id, names in CLIENT_NAMES_BY_INDUSTRY.items():
        for name in names:
            tier = random.choices(["Strategic", "Regional", "Emerging"], weights=[30, 45, 25], k=1)[0]
            rows.append({"client_id": cid, "client_name": name, "industry_id": industry_id, "client_tier": tier})
            cid += 1
    return rows


def gen_projects(clients, employees, n=72):
    rows = []
    pm_pool = [e for e in employees if e["title"] in ("Project Manager", "Senior Project Manager")]
    office_ids = [o[0] for o in OFFICES]

    for pid in range(1, n + 1):
        client = random.choice(clients)
        industry_id = client["industry_id"]
        ptype = random.choice(PROJECT_TYPES_BY_INDUSTRY[industry_id])
        office_id = random.choices(office_ids, weights=OFFICE_WEIGHTS, k=1)[0]
        pm = random.choice(pm_pool)

        start_year = random.choices([2024, 2025, 2026], weights=[25, 55, 20], k=1)[0]
        start_month = random.randint(1, 12)
        start_day = random.randint(1, 28)
        start_date = date(start_year, start_month, start_day)
        if start_date > date(2026, 8, 1):
            start_date = date(2026, 7, 1)

        duration_weeks = random.randint(8, 52)
        planned_end = start_date + timedelta(weeks=duration_weeks)

        status = weighted_choice(STATUS_WEIGHTS)
        # bias status by how far in the past planned_end is
        if planned_end > date(2026, 8, 15):
            status = random.choices(["Active", "On Hold"], weights=[90, 10], k=1)[0]
        else:
            status = random.choices(["Complete", "Cancelled"], weights=[92, 8], k=1)[0]

        actual_end = ""
        if status == "Complete":
            drift_days = random.randint(-10, 35)
            actual_end = (planned_end + timedelta(days=drift_days)).isoformat()
        elif status == "Cancelled":
            actual_end = (start_date + timedelta(weeks=random.randint(2, duration_weeks // 2 + 1))).isoformat()

        budget_hours = round(duration_weeks * random.uniform(18, 45))
        avg_rate = random.uniform(95, 165)  # blended billing rate assumption
        budget_labor_cost = round(budget_hours * avg_rate, 2)
        contract_value = round(budget_labor_cost * random.uniform(1.35, 1.75), 2)

        rows.append({
            "project_id": pid,
            "project_name": f"{client['client_name']} - {ptype} #{pid}",
            "client_id": client["client_id"],
            "industry_id": industry_id,
            "office_id": office_id,
            "project_type": ptype,
            "project_manager_id": pm["employee_id"],
            "start_date": start_date.isoformat(),
            "planned_end_date": planned_end.isoformat(),
            "actual_end_date": actual_end,
            "status": status,
            "budget_hours": budget_hours,
            "budget_labor_cost": budget_labor_cost,
            "contract_value": contract_value,
        })
    return rows


def messy_date(d):
    """Return the date in one of several inconsistent human-entered formats."""
    fmt = random.choices(
        ["iso", "us_slash", "us_slash_short", "clean"],
        weights=[55, 20, 15, 10], k=1
    )[0]
    if fmt == "iso":
        return d.isoformat()
    if fmt == "us_slash":
        return f"{d.month:02d}/{d.day:02d}/{d.year}"
    if fmt == "us_slash_short":
        return f"{d.month}/{d.day}/{d.year % 100:02d}"
    return d.isoformat()


def messy_hours(h):
    """Occasionally corrupt an hours value to simulate real timesheet entry errors."""
    roll = random.random()
    if roll < 0.02:
        return ""  # blank / missing
    if roll < 0.035:
        return str(-abs(h))  # negative entry error
    if roll < 0.05:
        return f"{h}h"  # stray unit suffix
    if roll < 0.06:
        return " " + str(h) + " "  # stray whitespace
    if roll < 0.07:
        return str(round(h * 4, 1))  # fat-finger multiple (e.g. 32 instead of 8)
    return str(h)


def messy_category(cat):
    roll = random.random()
    if roll < 0.15:
        return cat.upper()
    if roll < 0.30:
        return cat.lower()
    if roll < 0.35:
        return " " + cat + " "
    return cat


def gen_timekeeping(employees, projects, target_rows=6500):
    rows = []
    active_projects = [p for p in projects]
    emp_by_id = {e["employee_id"]: e for e in employees}
    billable_employees = [e for e in employees if e["billable_flag"] == 1]

    entry_id = 1
    while len(rows) < target_rows:
        proj = random.choice(active_projects)
        p_start = date.fromisoformat(proj["start_date"])
        p_end_str = proj["actual_end_date"] or proj["planned_end_date"]
        p_end = date.fromisoformat(p_end_str)
        if p_end <= p_start:
            p_end = p_start + timedelta(days=30)
        span_days = (p_end - p_start).days
        if span_days <= 0:
            continue
        work_date = p_start + timedelta(days=random.randint(0, span_days))
        if work_date > date(2026, 8, 15):
            continue

        # staff assigned tend to be from the project's office, weighted
        office_pool = [e for e in billable_employees if e["office_id"] == proj["office_id"]]
        emp = random.choice(office_pool) if office_pool and random.random() < 0.85 else random.choice(billable_employees)

        category = random.choice(TASK_CATEGORIES)
        base_hours = round(random.choices([1, 2, 3, 4, 6, 8], weights=[10, 15, 20, 20, 20, 15], k=1)[0] * random.uniform(0.5, 1.0), 1)
        billable = 0 if category in NONBILLABLE else 1

        rows.append({
            "entry_id": entry_id,
            "employee_id": emp["employee_id"],
            "project_id": proj["project_id"],
            "work_date": messy_date(work_date),
            "hours_worked": messy_hours(base_hours),
            "task_category": messy_category(category),
            "billable_flag": billable,
        })
        entry_id += 1

        # inject occasional exact-duplicate row (data entry / double sync error)
        if random.random() < 0.02:
            dup = dict(rows[-1])
            dup["entry_id"] = entry_id
            rows.append(dup)
            entry_id += 1

        # inject rare orphan record (bad employee_id / project_id reference)
        if random.random() < 0.005:
            rows.append({
                "entry_id": entry_id,
                "employee_id": 9999,
                "project_id": proj["project_id"],
                "work_date": messy_date(work_date),
                "hours_worked": messy_hours(base_hours),
                "task_category": messy_category(category),
                "billable_flag": billable,
            })
            entry_id += 1

    random.shuffle(rows)
    for i, r in enumerate(rows, start=1):
        r["entry_id"] = i
    return rows


def write_csv(path, rows, fieldnames):
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows):,} rows -> {path}")


def main():
    offices = gen_offices()
    employees = gen_employees(220)
    clients = gen_clients()
    projects = gen_projects(clients, employees, 72)
    timekeeping = gen_timekeeping(employees, projects, 6500)

    write_csv(f"{OUT_DIR}/offices.csv", offices, list(offices[0].keys()))
    write_csv(f"{OUT_DIR}/employees.csv", employees, list(employees[0].keys()))
    write_csv(f"{OUT_DIR}/clients.csv", clients, list(clients[0].keys()))
    write_csv(f"{OUT_DIR}/projects.csv", projects, list(projects[0].keys()))
    write_csv(f"{OUT_DIR}/timekeeping_raw.csv", timekeeping, list(timekeeping[0].keys()))

    industries_path = f"{OUT_DIR}/industries.csv"
    with open(industries_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["industry_id", "industry_name"])
        writer.writerows(INDUSTRIES)
    print(f"wrote {len(INDUSTRIES)} rows -> {industries_path}")

    rate_card_path = f"{OUT_DIR}/rate_card.csv"
    with open(rate_card_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["title", "cost_rate_per_hr", "billing_rate_per_hr"])
        for title, (cost_rate, bill_rate) in RATE_CARD.items():
            writer.writerow([title, cost_rate, bill_rate])
    print(f"wrote {len(RATE_CARD)} rows -> {rate_card_path}")


if __name__ == "__main__":
    main()
