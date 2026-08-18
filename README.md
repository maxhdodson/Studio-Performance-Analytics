# Studio Performance Analytics

A self-directed business intelligence project built for my application to HFA's
Business Intelligence Specialist I role. It models the kind of multi-office,
project-based analytics problem an employee-owned architecture & engineering
studio like HFA actually has: turning raw project timekeeping into staff
utilization, project profitability, and portfolio-level insight leadership
can act on.

**All company, client, and personnel data in this project is synthetic.**
It does not use or reference any real HFA data. The scenario (a ~220-person,
7-office A&E firm doing retail, hospitality, healthcare, industrial, real
estate development, and science/tech work) is modeled on HFA's public profile
and office footprint, not on internal information.

## Why this project

HFA is a 100%-employee-owned architecture and engineering studio with offices
in Bentonville, Springfield, Fort Worth, Boston, Franklin, Baltimore, and
Mexico City, delivering design and project management for national retail,
hospitality, healthcare, and industrial clients. A firm that shape is exactly
the kind of business where BI work matters most: dozens of concurrent
projects, hundreds of staff logging hours across offices, and leadership that
needs a fast, trustworthy read on where labor, budget, and schedule risk are
concentrated.

That is the same problem I worked on as a data analyst contractor for
Hedgerow, where I cleaned and modeled 2,000+ raw timekeeping records across
300+ employees and 30+ projects in Power BI. This project extends that
experience end-to-end -- schema design, ETL, SQL analysis, and a dashboard --
against a scenario built specifically around HFA's business.

## The problem

Studio leadership needs answers to five questions every month, and the raw
data to answer them arrives messy:

1. Are we staffed efficiently? Which offices are running under or over their
   utilization target?
2. Which projects are profitable, and which are quietly eating their budget?
3. How is our work distributed across industries, and where's the growth?
4. Are we delivering projects on schedule?
5. Which project managers are consistently delivering healthy margins?

The raw timekeeping export has the problems every real timekeeping export
has: inconsistent date formats, hours logged with stray units or extra
whitespace, a handful of negative or impossibly large entries, duplicate
syncs, and a few orphaned records pointing at employees that don't exist in
the roster.

## Approach

```
generate_data.py          synthetic but realistic source data
      |
      v
timekeeping_raw.csv   <-- intentionally messy (see Data Quality below)
offices / employees / clients / projects / rate_card.csv  <-- clean reference data
      |
      v
clean_and_load.py          ETL: parses/validates/dedupes raw timekeeping,
      |                     loads everything into SQLite against 01_schema.sql
      v
studio_analytics.db        relational database (6 tables, indexed)
      |
      v
02_analysis_queries.sql    7 analytical queries answering the 5 questions above
      |                     (re-implemented in Python inside clean_and_load.py
      |                      so the pipeline runs in one command)
      v
dashboard/data.json  -->   build.py embeds it into dashboard/index.html
      |
      v
dashboard/index.html       interactive dashboard (Chart.js), opens standalone
```

Everything runs from the command line with no external services:

```bash
cd etl
python3 generate_data.py       # writes ../data/*.csv
python3 clean_and_load.py      # cleans + loads SQLite, writes ../dashboard/data.json
cd ../dashboard
python3 build.py               # embeds data.json into index.html
```

`dashboard/index.html` is then a single self-contained file -- open it
directly in a browser, no server required.

## Tech stack

- **Python** for synthetic data generation and the ETL/cleaning pipeline
- **SQL (SQLite)** for the relational schema and all analytical logic --
  joins, aggregations, window-style variance calculations, and a documented
  join-fanout fix in the industry-mix query
- **Chart.js** for the dashboard's visualizations
- **Vanilla JS** for dashboard interactivity (search, sort, filter) -- no
  framework, kept dependency-free so the file is portable

## Data model

Six tables: `offices`, `industries`, `rate_card`, `clients`, `employees`,
`projects`, and the `timekeeping` fact table (grain: one row per labor entry,
~6,100 rows after cleaning). `rate_card` holds a simplified loaded-cost vs.
billing rate by title, which is what turns raw hours into actual labor cost
and billed value in the profitability queries -- see `sql/01_schema.sql` and
`sql/02_analysis_queries.sql` for the full DDL and annotated queries.

## Data quality / ETL

Of 6,500 raw timekeeping rows, 404 (6.2%) were removed by the cleaning
pipeline, with every removal reason logged and surfaced on the dashboard
itself:

| Issue | Rows |
|---|---|
| Blank/missing hours | 126 |
| Negative hours (entry error) | 99 |
| Exact duplicate entries (double sync) | 122 |
| Orphaned employee reference | 39 |
| Implausible single-day entry (>16h) | 18 |

Dates arriving in three different formats (`2025-01-14`, `01/14/2025`,
`1/14/25`) are normalized to ISO before loading, and task categories with
inconsistent casing/whitespace are normalized as well. This mirrors the kind
of real-world cleanup I did with Hedgerow's raw timekeeping exports.

## What the data shows

- **Utilization varies more across offices than firm-wide averages suggest.**
  Bentonville (HQ) runs highest at 64.9% billable utilization; Springfield
  runs lowest at 59.8% -- a 5-point gap that a single firm-wide number would
  hide entirely.
- **Margin performance is uneven even though no tracked project is
  unprofitable.** Gross margin across projects ranges from ~47% to over 99%,
  and only 3 of 72 projects ran over their budgeted hours -- but those 3
  concentrate almost all of the firm's schedule and cost risk.
- **Retail and hospitality dominate the portfolio** (22 and 18 projects
  respectively, well ahead of healthcare, industrial, real estate
  development, and science/tech), consistent with HFA's retail-heavy client
  base.
- **Schedule slippage is the biggest risk signal in the data**: of 50
  completed projects, 36 finished late (by an average of ~21 days), while 14
  finished on time or early (by an average of 6 days ahead). That's a
  clearer leading indicator than budget variance alone.
- **Project manager performance varies widely** even among PMs with similar
  project counts, which the PM performance table on the dashboard surfaces
  directly rather than burying in a firm-wide average.

## What I'd build next

- Bring in project-phase-level budgets (schematic design, design
  development, construction documents, construction admin) instead of a
  single whole-project budget, since that's where A&E firms actually manage
  risk
- Add a forecast-at-completion metric (actual burn rate projected against
  remaining scope) rather than only backward-looking variance
- Rebuild the same data model as a live Power BI report with DAX measures,
  since that's HFA's actual BI tooling -- the SQL and schema here translate
  directly

## Files

```
hfa-bi-project/
  README.md                  this file
  sql/01_schema.sql           relational schema
  sql/02_analysis_queries.sql annotated analytical queries
  etl/generate_data.py        synthetic data generator
  etl/clean_and_load.py       cleaning pipeline + SQLite load + JSON export
  data/                       generated CSVs + studio_analytics.db
  dashboard/build.py          embeds data.json into a standalone index.html
  dashboard/index.html        the dashboard itself
```
