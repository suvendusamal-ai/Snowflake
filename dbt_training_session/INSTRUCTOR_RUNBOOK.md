# Instructor Runbook

## Delivery goal

Teach what dbt is, why teams use it, and how Snowflake-native development works
without overwhelming the room. The live build should feel small, deliberate,
and complete.

## Architect recommendation

Use this training project as a new sibling folder and a new dbt project name.
Do not trim the enterprise demo in place. That keeps the validated enterprise
artifact intact and gives you a clean, purpose-built workshop repo.

## One-hour agenda

### 0-15 min: Presentation

#### Slide 1: What problem dbt solves

Talking points:

- SQL transformations become code, not ad hoc worksheet history.
- dbt gives modular models, dependency management, documentation, and tests.
- Analysts and engineers stay close to SQL while getting software discipline.

#### Slide 2: Where dbt sits in a Snowflake stack

Talking points:

- Ingestion lands source-shaped data in `RAW`.
- dbt transforms inside Snowflake; compute stays in the warehouse.
- BI and downstream consumers read curated marts, not raw tables.

#### Slide 3: Core dbt building blocks

Talking points:

- `ref()` builds a DAG and manages dependencies.
- `source()` declares governed entry points.
- YAML adds tests, descriptions, lineage, and ownership.
- Macros and seeds remove repetition and keep reference data in version control.

#### Slide 4: The folder story

Talking points:

- `models/staging`: rename, cast, standardize.
- `models/intermediate`: reusable business logic.
- `models/marts`: publish facts, dimensions, and reporting tables.
- `snapshots`: preserve record history.
- `tests`, `macros`, `analyses`, `docs`: trust, reuse, learning, and explainability.

#### Slide 5: Why Snowflake-native dbt matters

Talking points:

- Development happens in Snowflake Workspaces.
- Deployment creates a native schema object: `DBT PROJECT`.
- Execution can happen from Snowsight, SQL, CLI, and tasks.
- The project object becomes a governed Snowflake asset, not just a folder on a laptop.

#### Slide 6: Training architecture

Talking points:

- Three RAW tables: customers, orders, order_items.
- One seed: segment targets.
- One snapshot: customer status history.
- Two marts plus one report are enough to show the full dbt lifecycle.

## 15-60 min: Live build and demo

### 15-20 min: Create the Snowflake objects and load sample data

Run in Snowsight worksheet:

```sql
-- Paste the entire file:
-- snowflake_dbt_one_hour_training/sql/00_setup_raw.sql
```

Presenter notes:

- Emphasize that `RAW` is loaded outside dbt on purpose.
- Show the schemas that will receive staging, marts, seeds, and snapshots.

### 20-25 min: Create a private Workspace and initialize the dbt project

Why private first:

- Snowflake Git-synced workspaces do not support empty repositories.
- Because this training flow requires validating the project before Git upload,
  start in a private Workspace, then push to Git afterward.

Snowsight steps:

1. Open `Projects` -> `Workspaces`.
2. Create a private workspace named `DBT One Hour Training`.
3. Add the files from this local folder with the project root at the workspace root.
4. Confirm `dbt_project.yml` and `profiles.yml` are at the root.

Presenter notes:

- Call out that this is the Snowflake-native IDE experience.
- Mention that `profiles.yml` is still required in Workspaces.

### 25-35 min: Validate the project in Workspace

Run in the Workspace terminal or command runner:

```text
dbt compile --target dev
dbt seed --target dev
dbt build --target dev
dbt snapshot --target dev
dbt docs generate --target dev
```

Optional worksheet validation using native SQL execution from the workspace:

```sql
EXECUTE DBT PROJECT FROM WORKSPACE user$.public."DBT One Hour Training"
  ARGS = 'build --target dev'
  DBT_VERSION = '1.10.15';
```

Presenter notes:

- `compile` proves the DAG resolves.
- `seed` shows how business-owned reference data becomes governed tables.
- `build` shows models and tests in dependency order.
- `snapshot` shows history preservation.
- `docs generate` prepares classic dbt docs artifacts, even though they cannot
  be served from inside Snowflake Workspaces.

### 35-40 min: Show the code folder by folder

Open these files in order:

1. `models/staging/sources.yml`
2. `models/staging/stg_orders.sql`
3. `models/intermediate/int_order_items_enriched.sql`
4. `models/marts/facts/fct_order_items.sql`
5. `snapshots/customers_snapshot.sql`
6. `tests/assert_customer_revenue_matches_fact.sql`
7. `docs/definitions.md`

Presenter notes:

- Keep each file explanation under one minute.
- Focus on why the folder exists, not every line.

### 40-45 min: Demonstrate a business change

Run:

```sql
-- Paste the first two sections of:
-- snowflake_dbt_one_hour_training/sql/01_live_changes.sql
```

Then rerun:

```text
dbt build --select fct_order_items+ --target dev
dbt snapshot --target dev
```

Presenter notes:

- New order demonstrates incremental-style rebuild behavior.
- Customer status update demonstrates slowly changing history.
- If time allows, run the optional future-date update and then:

```text
dbt test --select assert_no_future_orders --target dev
```

This gives you a quick, memorable data quality failure.

### 45-50 min: Deploy a native Snowflake DBT PROJECT object

Snowsight path:

1. In the workspace, choose `Deploy project`.
2. Set object name: `DBT_ONE_HOUR_TRAINING`.
3. Set default target: `dev`.
4. Pin dbt version: `1.10.15`.
5. Deploy.

SQL equivalent:

```sql
CREATE OR REPLACE DBT PROJECT DBT_TRAINING.DBT_PROJECTS.DBT_ONE_HOUR_TRAINING
  FROM 'snow://workspace/user$.public."DBT One Hour Training"/versions/live'
  DEFAULT_TARGET = 'dev'
  DBT_VERSION = '1.10.15'
  COMMENT = 'One-hour Snowflake-native dbt training project';
```

Validate the object:

```sql
SHOW DBT PROJECTS LIKE 'DBT_ONE_HOUR_TRAINING';

EXECUTE DBT PROJECT DBT_TRAINING.DBT_PROJECTS.DBT_ONE_HOUR_TRAINING
  ARGS = 'build --target dev'
  DBT_VERSION = '1.10.15';
```

Presenter notes:

- This is the key Snowflake-native moment.
- The project is now a governed Snowflake object with versions and executable SQL.

### 50-55 min: Upload to Git only after validation and deployment

From the repository root on localhost:

```powershell
git checkout -b feat/dbt-one-hour-training
git add snowflake_dbt_one_hour_training
git commit -m "Add one-hour Snowflake-native dbt training project"
git push -u origin feat/dbt-one-hour-training
```

If the remote is not configured:

```powershell
git remote add origin https://github.com/suvendusamal-ai/Snowflake.git
git push -u origin feat/dbt-one-hour-training
```

Presenter notes:

- Explain why Git comes after validation here: the session is teaching
  Snowflake-native development first, Git second.

### 55-60 min: Clone locally and show classic dbt docs

In a fresh local shell:

```powershell
git clone https://github.com/suvendusamal-ai/Snowflake.git C:\temp\Snowflake
cd C:\temp\Snowflake\snowflake_dbt_one_hour_training
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
New-Item -ItemType Directory -Force .local_profiles | Out-Null
Copy-Item profiles.local.example.yml .local_profiles\profiles.yml
dbt docs generate --profiles-dir .local_profiles
dbt docs serve --profiles-dir .local_profiles --port 8081
```

Open [http://localhost:8081](http://localhost:8081).

Presenter notes:

- Say explicitly that classic dbt docs are local here because Snowflake
  supports `docs generate` but not `docs serve`.
- Trace lineage from `rpt_segment_summary` back to RAW and the seed.

## What to pre-stage vs type live

### Pre-stage

- [sql/00_setup_raw.sql](C:\Users\subha\OneDrive\Documents\SnowflakeMCPServer\snowflake_dbt_one_hour_training\sql\00_setup_raw.sql)
- [profiles.yml](C:\Users\subha\OneDrive\Documents\SnowflakeMCPServer\snowflake_dbt_one_hour_training\profiles.yml)
- [seeds/segment_targets.csv](C:\Users\subha\OneDrive\Documents\SnowflakeMCPServer\snowflake_dbt_one_hour_training\seeds\segment_targets.csv)
- [docs/definitions.md](C:\Users\subha\OneDrive\Documents\SnowflakeMCPServer\snowflake_dbt_one_hour_training\docs\definitions.md)
- [models/marts/schema.yml](C:\Users\subha\OneDrive\Documents\SnowflakeMCPServer\snowflake_dbt_one_hour_training\models\marts\schema.yml)

Reason:

- These are verbose, low-drama files that consume time without teaching much.

### Type live

- `models/staging/sources.yml`
- `models/staging/stg_orders.sql`
- `models/intermediate/int_order_items_enriched.sql`
- `models/marts/facts/fct_order_items.sql`
- `snapshots/customers_snapshot.sql`
- `tests/assert_customer_revenue_matches_fact.sql`
- `tests/assert_no_future_orders.sql`

Reason:

- These files best demonstrate `source`, `ref`, incremental logic, tests, and snapshots.

## Success criteria

- `dbt build`, `dbt snapshot`, and `dbt docs generate` succeed in Workspace.
- `DBT PROJECT` is deployed and can execute with SQL.
- Git push happens only after native validation and deployment.
- Local clone serves classic docs successfully.
