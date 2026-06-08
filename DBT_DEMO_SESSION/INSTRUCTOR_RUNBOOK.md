# Instructor Runbook

## Purpose

This runbook is the exact step-by-step execution guide for a one-hour,
Snowflake-native dbt training session using the project name
`dbt_demo_session`.

## Naming rules for this version

- Snowflake workspace visible name: `dbt_demo_session`
- dbt project name in `dbt_project.yml`: `dbt_demo_session`
- dbt profile key in `profiles.yml`: `dbt_demo_session`
- Workspace project root path: `/dbt_demo_session`
- Git branch name for the demo: `feat/dbt-demo-session`

## Important local-folder note

The source files on disk for this assistant session still live under:

`C:\Users\subha\OneDrive\Documents\SnowflakeMCPServer\dbt_training_session`

That is only the current local storage path.

For the actual demonstration:

- use `dbt_demo_session` as the folder name inside Snowflake Workspaces
- use `dbt_demo_session` as the folder name pushed to GitHub

## Step 0: Pre-flight checks

### Snowsight actions

1. Confirm you can log in to Snowsight.
2. Confirm you can use `ACCOUNTADMIN` or an equivalent setup role.
3. Confirm `Projects` -> `Workspaces` is visible.
4. Confirm your source files exist locally in the current authoring folder.

### Local file checks

Review:

- [sql/00_setup_raw.sql](C:\Users\subha\OneDrive\Documents\SnowflakeMCPServer\dbt_training_session\sql\00_setup_raw.sql)
- [sql/01_live_changes.sql](C:\Users\subha\OneDrive\Documents\SnowflakeMCPServer\dbt_training_session\sql\01_live_changes.sql)

Confirm the setup file contains the correct user grant:

```sql
GRANT ROLE DBT_TRAINING_ROLE TO USER suvendu;
```

Replace `suvendu` if needed.

## Step 1: Create the Snowflake demo environment

### Snowsight actions

1. Open a new SQL worksheet.
2. Paste the full contents of [sql/00_setup_raw.sql](C:\Users\subha\OneDrive\Documents\SnowflakeMCPServer\dbt_training_session\sql\00_setup_raw.sql).
3. Run the full script.

### Validation SQL

```sql
SELECT * FROM DBT_TRAINING.RAW.CUSTOMERS;
SELECT * FROM DBT_TRAINING.RAW.ORDERS;
SELECT * FROM DBT_TRAINING.RAW.ORDER_ITEMS;
```

## Step 2: Create the Snowflake Workspace

### Snowsight actions

1. Go to `Projects` -> `Workspaces`.
2. Create a new private workspace.
3. Use the visible name `dbt_demo_session`.
4. Create a top-level folder named `dbt_demo_session` if Snowflake does not
   create it for you automatically.
5. Upload the project contents from the current local source folder into that
   `dbt_demo_session` folder.
6. Confirm the folder root contains:
   `dbt_project.yml`, `profiles.yml`, `models/`, `seeds/`, `snapshots/`,
   `tests/`, `macros/`, `analyses/`, `docs/`, `sql/`.

### Important check

The project root inside the workspace must be:

```text
/dbt_demo_session
```

## Step 3: Compile the project in Snowflake

### Exact SQL

```sql
EXECUTE DBT PROJECT FROM WORKSPACE "USER$"."PUBLIC"."dbt_demo_session"
  project_root='/dbt_demo_session'
  args='compile --target dev';
```

### Expected result

- `SUCCESS = True`
- dbt runtime shows `dbt=1.9.4`

### Important YAML note

The source relationship tests in
[models/staging/sources.yml](C:\Users\subha\OneDrive\Documents\SnowflakeMCPServer\dbt_training_session\models\staging\sources.yml)
must use:

```yml
- relationships:
    to: source('raw', 'customers')
    field: customer_id
```

and not the newer `arguments:` wrapper.

## Step 4: Load the seed

### Exact SQL

```sql
EXECUTE DBT PROJECT FROM WORKSPACE "USER$"."PUBLIC"."dbt_demo_session"
  project_root='/dbt_demo_session'
  args='seed --target dev';
```

### Validation SQL

```sql
SELECT * FROM DBT_TRAINING.TRAINING_REFERENCE.SEGMENT_TARGETS;
```

## Step 5: Run the main build

### Exact SQL

```sql
EXECUTE DBT PROJECT FROM WORKSPACE "USER$"."PUBLIC"."dbt_demo_session"
  project_root='/dbt_demo_session'
  args='build --target dev';
```

### Snowsight UI equivalent

Inside the workspace, you can also use the dbt run UI and choose:

- command: `build`
- options: `--target dev`

## Step 6: Verify the analytical outputs

### Exact SQL

```sql
SELECT * FROM DBT_TRAINING.TRAINING_MARTS.FCT_ORDER_ITEMS;
SELECT * FROM DBT_TRAINING.TRAINING_MARTS.DIM_CUSTOMERS;
SELECT * FROM DBT_TRAINING.TRAINING_MARTS.RPT_SEGMENT_SUMMARY;
SELECT * FROM DBT_TRAINING.TRAINING_SNAPSHOTS.CUSTOMERS_SNAPSHOT;
```

## Step 7: Show the code files

### Snowsight actions

Open these files in the workspace:

1. `models/staging/sources.yml`
2. `models/staging/stg_orders.sql`
3. `models/intermediate/int_order_items_enriched.sql`
4. `models/marts/facts/fct_order_items.sql`
5. `snapshots/customers_snapshot.sql`
6. `tests/assert_customer_revenue_matches_fact.sql`
7. `docs/definitions.md`

## Step 8: Simulate business changes

### Exact SQL

Run only the first two sections from [sql/01_live_changes.sql](C:\Users\subha\OneDrive\Documents\SnowflakeMCPServer\dbt_training_session\sql\01_live_changes.sql):

```sql
INSERT INTO DBT_TRAINING.RAW.ORDERS
  (ORDER_ID, CUSTOMER_ID, ORDER_DATE, STATUS, UPDATED_AT)
VALUES
  (1006, 2, '2025-03-06', 'COMPLETED', CURRENT_TIMESTAMP());

INSERT INTO DBT_TRAINING.RAW.ORDER_ITEMS
  (ORDER_ID, LINE_NUMBER, PRODUCT_NAME, QUANTITY, UNIT_PRICE, UPDATED_AT)
VALUES
  (1006, 1, 'Analytics Starter', 3, 100.00, CURRENT_TIMESTAMP()),
  (1006, 2, 'Architecture Workshop', 1, 1200.00, CURRENT_TIMESTAMP());

UPDATE DBT_TRAINING.RAW.CUSTOMERS
SET STATUS = 'CHURN_RISK',
    UPDATED_AT = CURRENT_TIMESTAMP()
WHERE CUSTOMER_ID = 2;
```

## Step 9: Refresh dbt after the business change

### Exact SQL

```sql
EXECUTE DBT PROJECT FROM WORKSPACE "USER$"."PUBLIC"."dbt_demo_session"
  project_root='/dbt_demo_session'
  args='build --select fct_order_items+ --target dev';
```

```sql
EXECUTE DBT PROJECT FROM WORKSPACE "USER$"."PUBLIC"."dbt_demo_session"
  project_root='/dbt_demo_session'
  args='snapshot --target dev';
```

## Step 10: Prove the updates flowed through

### Exact SQL

```sql
SELECT *
FROM DBT_TRAINING.TRAINING_MARTS.FCT_ORDER_ITEMS
WHERE ORDER_ID = 1006;
```

```sql
SELECT *
FROM DBT_TRAINING.TRAINING_MARTS.DIM_CUSTOMERS
WHERE CUSTOMER_ID = 2;
```

```sql
SELECT *
FROM DBT_TRAINING.TRAINING_SNAPSHOTS.CUSTOMERS_SNAPSHOT
WHERE CUSTOMER_ID = 2
ORDER BY DBT_VALID_FROM;
```

## Step 11: Optional quality failure

### Exact SQL

```sql
UPDATE DBT_TRAINING.RAW.ORDERS
SET ORDER_DATE = CURRENT_DATE() + 30,
    UPDATED_AT = CURRENT_TIMESTAMP()
WHERE ORDER_ID = 1004;
```

Then run:

```sql
EXECUTE DBT PROJECT FROM WORKSPACE "USER$"."PUBLIC"."dbt_demo_session"
  project_root='/dbt_demo_session'
  args='test --select assert_no_future_orders --target dev';
```

## Step 12: Deploy the native Snowflake DBT PROJECT object

### Exact SQL

```sql
CREATE OR REPLACE DBT PROJECT DBT_TRAINING.DBT_PROJECTS.DBT_DEMO_SESSION
  FROM 'snow://workspace/user$.public."dbt_demo_session"/versions/live/dbt_demo_session'
  DEFAULT_TARGET = 'dev'
  DBT_VERSION = '1.9.4'
  COMMENT = 'One-hour Snowflake-native dbt demo session';
```

### Validation SQL

```sql
SHOW DBT PROJECTS LIKE 'DBT_DEMO_SESSION' IN SCHEMA DBT_TRAINING.DBT_PROJECTS;
```

```sql
EXECUTE DBT PROJECT DBT_TRAINING.DBT_PROJECTS.DBT_DEMO_SESSION
  ARGS = 'build --target dev'
  DBT_VERSION = '1.9.4';
```

## Step 13: Publish to GitHub from Snowflake using Git Integration

### Important prerequisite

To push from Snowflake Workspaces, do not use the `Public repository` option.
That option is read-only for push operations. Use OAuth2 or a personal access
token with write access. Snowflake documents that commit/push from Workspaces is
supported, but not when the workspace is connected as a public repository only.

### Admin SQL for GitHub OAuth API integration

Run this once if your account does not already have a GitHub API integration for
Workspaces:

```sql
CREATE OR REPLACE API INTEGRATION GITHUB_API_INTEGRATION
  API_PROVIDER = git_https_api
  API_ALLOWED_PREFIXES = ('https://github.com/')
  API_USER_AUTHENTICATION = (
    TYPE = snowflake_github_app
  )
  ENABLED = TRUE;
```

If another role created it, make sure your working role has `USAGE` on that
integration.

### Snowsight actions

1. Go to `Projects` -> `Workspaces`.
2. Choose `From Git repository`.
3. Repository URL:
   `https://github.com/suvendusamal-ai/Snowflake.git`
4. Workspace name:
   `dbt_demo_session_git`
5. API integration:
   `GITHUB_API_INTEGRATION`
6. Authentication method:
   `OAuth2`
7. Select `Sign in`, then authorize Snowflake for GitHub.
8. In GitHub permissions, allow:
   `Read access to metadata` and `Read and write access to code`
9. Under repository access, grant access to the `Snowflake` repository.
10. Select `Create`.

### Create the Git branch in Snowsight

1. Open the `dbt_demo_session_git` workspace.
2. Select `Changes`.
3. Open the branch dropdown.
4. Select `+ New`.
5. Branch name:
   `feat/dbt-demo-session`
6. Select `Create`.

### Load the validated project files into the Git workspace

1. In the `dbt_demo_session_git` workspace, create a top-level folder named
   `dbt_demo_session` if it does not already exist.
2. Upload the validated project contents into that folder.
3. Confirm the Git workspace root for the dbt project is:
   `/dbt_demo_session`

### Commit and push from Snowsight

1. Open `Changes`.
2. Review the modified and added files.
3. Optional: select the ellipsis and choose `Edit credentials` to set author
   name and email.
4. Commit message:
   `Add Snowflake-native dbt demo session`
5. Select `Push`.
6. Confirm the push.

### Result to verify

The branch `feat/dbt-demo-session` should now exist in GitHub with the folder
`dbt_demo_session`.

## Step 14: Clone the GitHub branch locally for the docs demo

### Exact PowerShell

```powershell
git clone --branch feat/dbt-demo-session https://github.com/suvendusamal-ai/Snowflake.git C:\temp\SnowflakeDocsDemo
cd C:\temp\SnowflakeDocsDemo\dbt_demo_session
```

## Step 15: Build the local docs environment

### Exact PowerShell

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python --version
```

Expected:

```text
Python 3.11.x
```

Install stable dbt versions:

```powershell
pip install -r requirements.txt
dbt --version
```

Expected:

- `dbt-core 1.9.2`
- `snowflake 1.9.2`

Create the local profiles folder:

```powershell
New-Item -ItemType Directory -Force .local_profiles | Out-Null
Copy-Item profiles.local.example.yml .local_profiles\profiles.yml
```

Edit:

`C:\temp\SnowflakeDocsDemo\dbt_demo_session\.local_profiles\profiles.yml`

Fill in:

- `account`
- `user`
- `password`

Keep:

- `role: DBT_TRAINING_ROLE`
- `database: DBT_TRAINING`
- `warehouse: DBT_TRAINING_WH`
- `schema: TRAINING`

## Step 16: Validate the local dbt connection

### Exact PowerShell

```powershell
dbt debug --profiles-dir .local_profiles
```

## Step 17: Generate and serve classic dbt docs

### Exact PowerShell

```powershell
dbt docs generate --profiles-dir .local_profiles
```

```powershell
dbt docs serve --profiles-dir .local_profiles --port 8081
```

Open:

- [http://localhost:8081](http://localhost:8081)

### 404 note

If the page loads and both `manifest.json` and `catalog.json` load, minor `404`
requests for icon assets can be ignored for the live demo.
