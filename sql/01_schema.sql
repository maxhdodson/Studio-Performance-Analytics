-- ============================================================================
-- 01_schema.sql
-- Relational schema for the Studio Performance Analytics project.
-- Modeled on a multi-office, project-based architecture & engineering firm.
-- SQLite-compatible; portable to Postgres/SQL Server with minor type changes.
-- ============================================================================

DROP TABLE IF EXISTS timekeeping;
DROP TABLE IF EXISTS projects;
DROP TABLE IF EXISTS employees;
DROP TABLE IF EXISTS clients;
DROP TABLE IF EXISTS industries;
DROP TABLE IF EXISTS offices;
DROP TABLE IF EXISTS rate_card;

CREATE TABLE offices (
    office_id     INTEGER PRIMARY KEY,
    city          TEXT NOT NULL,
    state         TEXT NOT NULL,
    region        TEXT NOT NULL,
    is_hq         INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE industries (
    industry_id   INTEGER PRIMARY KEY,
    industry_name TEXT NOT NULL
);

-- Simplified rate card: fully-burdened cost vs. standard billing rate by title.
CREATE TABLE rate_card (
    title                TEXT PRIMARY KEY,
    cost_rate_per_hr     REAL NOT NULL,
    billing_rate_per_hr  REAL NOT NULL
);

CREATE TABLE clients (
    client_id     INTEGER PRIMARY KEY,
    client_name   TEXT NOT NULL,
    industry_id   INTEGER NOT NULL REFERENCES industries(industry_id),
    client_tier   TEXT NOT NULL CHECK (client_tier IN ('Strategic','Regional','Emerging'))
);

CREATE TABLE employees (
    employee_id        INTEGER PRIMARY KEY,
    first_name          TEXT NOT NULL,
    last_name           TEXT NOT NULL,
    office_id            INTEGER NOT NULL REFERENCES offices(office_id),
    title                TEXT NOT NULL,
    department           TEXT NOT NULL,
    hire_date            TEXT NOT NULL,
    employment_type      TEXT NOT NULL CHECK (employment_type IN ('Full-Time','Contract')),
    target_utilization   REAL NOT NULL,
    billable_flag        INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE projects (
    project_id          INTEGER PRIMARY KEY,
    project_name        TEXT NOT NULL,
    client_id           INTEGER NOT NULL REFERENCES clients(client_id),
    industry_id         INTEGER NOT NULL REFERENCES industries(industry_id),
    office_id           INTEGER NOT NULL REFERENCES offices(office_id),
    project_type        TEXT NOT NULL,
    project_manager_id  INTEGER NOT NULL REFERENCES employees(employee_id),
    start_date          TEXT NOT NULL,
    planned_end_date    TEXT NOT NULL,
    actual_end_date     TEXT,
    status               TEXT NOT NULL CHECK (status IN ('Active','Complete','On Hold','Cancelled')),
    budget_hours         REAL NOT NULL,
    budget_labor_cost    REAL NOT NULL,
    contract_value        REAL NOT NULL
);

-- Cleaned timekeeping fact table (populated by the ETL step from the raw,
-- messy CSV -- see etl/clean_and_load.py). Grain: one row per labor entry.
CREATE TABLE timekeeping (
    entry_id        INTEGER PRIMARY KEY,
    employee_id     INTEGER NOT NULL REFERENCES employees(employee_id),
    project_id      INTEGER NOT NULL REFERENCES projects(project_id),
    work_date       TEXT NOT NULL,        -- normalized to YYYY-MM-DD
    hours_worked    REAL NOT NULL,        -- cleaned, validated numeric
    task_category   TEXT NOT NULL,        -- normalized casing/whitespace
    billable_flag   INTEGER NOT NULL
);

CREATE INDEX idx_timekeeping_employee ON timekeeping(employee_id);
CREATE INDEX idx_timekeeping_project ON timekeeping(project_id);
CREATE INDEX idx_timekeeping_date ON timekeeping(work_date);
CREATE INDEX idx_projects_office ON projects(office_id);
CREATE INDEX idx_projects_industry ON projects(industry_id);
