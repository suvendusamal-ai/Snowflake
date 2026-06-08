# Snowflake-Native dbt One-Hour Training

This is a compact training edition of the larger enterprise dbt demo. It is
designed for a live one-hour walkthrough under the project name
`dbt_demo_session`:

- 15 minutes of concepts and architecture
- 45 minutes of Snowflake-native execution, deployment, Git publish, and
  classic local dbt docs

## What this project demonstrates

- RAW data loaded outside dbt
- STAGING cleanup models
- INTERMEDIATE reusable logic
- MARTS facts, dimensions, and reporting
- SNAPSHOTS for history
- TESTS, MACROS, ANALYSES, DOCS, and lineage

## Start here

- [INSTRUCTOR_RUNBOOK.md](C:\Users\subha\OneDrive\Documents\SnowflakeMCPServer\dbt_training_session\INSTRUCTOR_RUNBOOK.md)
- [SPEAKER_SCRIPT_1H.md](C:\Users\subha\OneDrive\Documents\SnowflakeMCPServer\dbt_training_session\SPEAKER_SCRIPT_1H.md)
- [sql/00_setup_raw.sql](C:\Users\subha\OneDrive\Documents\SnowflakeMCPServer\dbt_training_session\sql\00_setup_raw.sql)
- [sql/01_live_changes.sql](C:\Users\subha\OneDrive\Documents\SnowflakeMCPServer\dbt_training_session\sql\01_live_changes.sql)

## Local docs prerequisites

For the local `dbt docs` demo, use:

- Python `3.11`
- `dbt-core==1.9.2`
- `dbt-snowflake==1.9.2`

The `requirements.txt` file is pinned accordingly.

## Local docs demo

After the Git push, use a fresh clone and run:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
New-Item -ItemType Directory -Force .local_profiles | Out-Null
Copy-Item profiles.local.example.yml .local_profiles\profiles.yml
dbt debug --profiles-dir .local_profiles
dbt docs generate --profiles-dir .local_profiles
dbt docs serve --profiles-dir .local_profiles --port 8081
```

Then open [http://localhost:8081](http://localhost:8081).
