-- ============================================================================
-- 02_analysis_queries.sql
-- Core analytical queries behind the Studio Performance Analytics dashboard.
-- Run against the cleaned database produced by etl/clean_and_load.py.
-- Each block is self-contained and annotated with the business question
-- it answers -- these are also the queries etl/clean_and_load.py executes
-- programmatically to produce dashboard/data.json.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. FIRM-WIDE UTILIZATION
-- Business question: what share of paid hours are billable, overall and by
-- office, vs. each office's target utilization?
-- ----------------------------------------------------------------------------
SELECT
    o.office_id,
    o.city,
    o.region,
    ROUND(SUM(CASE WHEN t.billable_flag = 1 THEN t.hours_worked ELSE 0 END), 1)  AS billable_hours,
    ROUND(SUM(t.hours_worked), 1)                                               AS total_hours,
    ROUND(1.0 * SUM(CASE WHEN t.billable_flag = 1 THEN t.hours_worked ELSE 0 END)
          / NULLIF(SUM(t.hours_worked), 0), 3)                                  AS utilization_rate,
    ROUND(AVG(e.target_utilization), 3)                                        AS avg_target_utilization
FROM timekeeping t
JOIN employees e ON e.employee_id = t.employee_id
JOIN offices o    ON o.office_id  = e.office_id
GROUP BY o.office_id, o.city, o.region
ORDER BY utilization_rate DESC;

-- ----------------------------------------------------------------------------
-- 2. PROJECT PROFITABILITY
-- Business question: which projects are running ahead of / behind budget,
-- and what margin are they generating against contract value?
-- ----------------------------------------------------------------------------
SELECT
    p.project_id,
    p.project_name,
    c.client_name,
    i.industry_name,
    o.city AS office,
    p.status,
    p.budget_hours,
    ROUND(COALESCE(h.actual_hours, 0), 1)                                   AS actual_hours,
    ROUND(COALESCE(h.actual_hours, 0) - p.budget_hours, 1)                  AS hours_variance,
    p.budget_labor_cost,
    ROUND(COALESCE(h.actual_labor_cost, 0), 2)                              AS actual_labor_cost,
    p.contract_value,
    ROUND(p.contract_value - COALESCE(h.actual_labor_cost, 0), 2)           AS gross_margin,
    ROUND(1.0 * (p.contract_value - COALESCE(h.actual_labor_cost, 0))
          / NULLIF(p.contract_value, 0), 3)                                 AS margin_pct
FROM projects p
JOIN clients c    ON c.client_id   = p.client_id
JOIN industries i ON i.industry_id = p.industry_id
JOIN offices o    ON o.office_id   = p.office_id
LEFT JOIN (
    SELECT
        t.project_id,
        SUM(t.hours_worked)                          AS actual_hours,
        SUM(t.hours_worked * rc.cost_rate_per_hr)     AS actual_labor_cost
    FROM timekeeping t
    JOIN employees e  ON e.employee_id = t.employee_id
    JOIN rate_card rc ON rc.title      = e.title
    GROUP BY t.project_id
) h ON h.project_id = p.project_id
ORDER BY margin_pct ASC;

-- ----------------------------------------------------------------------------
-- 3. INDUSTRY MIX
-- Business question: how is the firm's labor/revenue distributed across
-- retail, hospitality, healthcare, industrial, real estate dev, and sci/tech?
-- ----------------------------------------------------------------------------
-- NOTE: avg_contract_value is computed from a pre-aggregated subquery rather
-- than SUM(p.contract_value)/COUNT(DISTINCT p.project_id) in the outer query,
-- because the LEFT JOIN to timekeeping fans a project out to one row per
-- labor entry -- summing contract_value directly against that fanned-out
-- result would multiply-count it. This is a classic BI join-fanout trap.
SELECT
    i.industry_name,
    COUNT(DISTINCT p.project_id)                                       AS project_count,
    ROUND(SUM(t.hours_worked), 1)                                      AS total_hours,
    ROUND(SUM(t.hours_worked * rc.billing_rate_per_hr), 2)             AS billed_value,
    ROUND(cv.avg_contract_value, 2)                                    AS avg_contract_value
FROM projects p
JOIN industries i ON i.industry_id = p.industry_id
LEFT JOIN timekeeping t ON t.project_id = p.project_id
LEFT JOIN employees e   ON e.employee_id = t.employee_id
LEFT JOIN rate_card rc  ON rc.title = e.title
JOIN (
    SELECT industry_id, AVG(contract_value) AS avg_contract_value
    FROM projects
    GROUP BY industry_id
) cv ON cv.industry_id = p.industry_id
GROUP BY i.industry_name, cv.avg_contract_value
ORDER BY total_hours DESC;

-- ----------------------------------------------------------------------------
-- 4. MONTHLY LABOR & REVENUE TREND
-- Business question: how are billable hours and billed value trending
-- month over month firm-wide?
-- ----------------------------------------------------------------------------
SELECT
    substr(t.work_date, 1, 7)                                         AS month,
    ROUND(SUM(CASE WHEN t.billable_flag = 1 THEN t.hours_worked ELSE 0 END), 1) AS billable_hours,
    ROUND(SUM(t.hours_worked), 1)                                     AS total_hours,
    ROUND(SUM(CASE WHEN t.billable_flag = 1
                    THEN t.hours_worked * rc.billing_rate_per_hr ELSE 0 END), 2) AS billed_value
FROM timekeeping t
JOIN employees e  ON e.employee_id = t.employee_id
JOIN rate_card rc ON rc.title      = e.title
GROUP BY month
ORDER BY month;

-- ----------------------------------------------------------------------------
-- 5. SCHEDULE PERFORMANCE
-- Business question: what share of completed projects finished on/ahead of
-- schedule vs. late, and by how many days on average?
-- ----------------------------------------------------------------------------
SELECT
    CASE WHEN julianday(actual_end_date) <= julianday(planned_end_date)
         THEN 'On Time or Early' ELSE 'Late' END          AS schedule_outcome,
    COUNT(*)                                               AS project_count,
    ROUND(AVG(julianday(actual_end_date) - julianday(planned_end_date)), 1) AS avg_days_variance
FROM projects
WHERE status = 'Complete'
GROUP BY schedule_outcome;

-- ----------------------------------------------------------------------------
-- 6. PROJECT MANAGER PERFORMANCE
-- Business question: which PMs are delivering the healthiest margins across
-- their book of projects?
-- ----------------------------------------------------------------------------
SELECT
    e.employee_id,
    e.first_name || ' ' || e.last_name                     AS project_manager,
    o.city                                                  AS home_office,
    COUNT(DISTINCT p.project_id)                            AS projects_managed,
    ROUND(AVG(
        1.0 * (p.contract_value - COALESCE(h.actual_labor_cost, 0)) / NULLIF(p.contract_value, 0)
    ), 3)                                                   AS avg_margin_pct
FROM projects p
JOIN employees e ON e.employee_id = p.project_manager_id
JOIN offices o    ON o.office_id  = e.office_id
LEFT JOIN (
    SELECT t.project_id, SUM(t.hours_worked * rc.cost_rate_per_hr) AS actual_labor_cost
    FROM timekeeping t
    JOIN employees emp ON emp.employee_id = t.employee_id
    JOIN rate_card rc  ON rc.title = emp.title
    GROUP BY t.project_id
) h ON h.project_id = p.project_id
GROUP BY e.employee_id, project_manager, home_office
HAVING COUNT(DISTINCT p.project_id) >= 1
ORDER BY avg_margin_pct DESC;

-- ----------------------------------------------------------------------------
-- 7. INDIVIDUAL UTILIZATION VS. TARGET
-- Business question: which billable staff are running under their target
-- utilization (staffing/workload risk) vs. over it (burnout risk)?
-- ----------------------------------------------------------------------------
SELECT
    e.employee_id,
    e.first_name || ' ' || e.last_name                      AS employee_name,
    e.title,
    o.city                                                    AS office,
    e.target_utilization,
    ROUND(1.0 * SUM(CASE WHEN t.billable_flag = 1 THEN t.hours_worked ELSE 0 END)
          / NULLIF(SUM(t.hours_worked), 0), 3)                AS actual_utilization,
    ROUND(
        (1.0 * SUM(CASE WHEN t.billable_flag = 1 THEN t.hours_worked ELSE 0 END)
              / NULLIF(SUM(t.hours_worked), 0)) - e.target_utilization
    , 3)                                                       AS variance_vs_target
FROM employees e
JOIN offices o ON o.office_id = e.office_id
LEFT JOIN timekeeping t ON t.employee_id = e.employee_id
WHERE e.billable_flag = 1
GROUP BY e.employee_id, employee_name, e.title, office, e.target_utilization
HAVING SUM(t.hours_worked) IS NOT NULL
ORDER BY variance_vs_target ASC;
