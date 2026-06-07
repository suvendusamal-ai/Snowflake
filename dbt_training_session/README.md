# Snowflake-Native dbt One-Hour Training

This is a deliberately small training edition of the larger enterprise demo in
`snowflake_dbt_enterprise_demo/`. It is optimized for a live one-hour session:

- 15 minutes of architecture and concept framing.
- 45 minutes of live setup, model authoring, validation, deployment, Git push,
  and local `dbt docs` demonstration.

## Why this edition exists

The enterprise demo is useful as a reference implementation, but it is too
large for a first live session. This project keeps the same story:

- RAW data loaded outside dbt.
- STAGING for source cleanup.
- INTERMEDIATE for reusable joins and calculations.
- MARTS for dimensions, facts, and reporting.
- SNAPSHOTS for history.
- TESTS, MACROS, ANALYSES, and DOCS for trust and explainability.

It does that with only three RAW tables, one seed, one snapshot, two reusable
macros, one singular test, and three marts.

## Recommended repository layout

Keep this as a sibling project rather than changing the validated enterprise
demo in place:

```text
Snowflake/
  snowflake_dbt_enterprise_demo/
  snowflake_dbt_one_hour_training/
```

This keeps the training asset simple while preserving the full reference build
for later comparison.

## Files to use first

- [INSTRUCTOR_RUNBOOK.md](C:\Users\subha\OneDrive\Documents\SnowflakeMCPServer\snowflake_dbt_one_hour_training\INSTRUCTOR_RUNBOOK.md)
- [sql/00_setup_raw.sql](C:\Users\subha\OneDrive\Documents\SnowflakeMCPServer\snowflake_dbt_one_hour_training\sql\00_setup_raw.sql)
- [sql/01_live_changes.sql](C:\Users\subha\OneDrive\Documents\SnowflakeMCPServer\snowflake_dbt_one_hour_training\sql\01_live_changes.sql)
- [dbt_project.yml](C:\Users\subha\OneDrive\Documents\SnowflakeMCPServer\snowflake_dbt_one_hour_training\dbt_project.yml)
- [profiles.yml](C:\Users\subha\OneDrive\Documents\SnowflakeMCPServer\snowflake_dbt_one_hour_training\profiles.yml)

## Local docs demo

Snowflake Workspaces support `docs generate`, but Snowflake does not support
`dbt docs serve` inside dbt Projects on Snowflake. After you push this project
to Git, clone it locally and run:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
New-Item -ItemType Directory -Force .local_profiles | Out-Null
Copy-Item profiles.local.example.yml .local_profiles\profiles.yml
dbt docs generate --profiles-dir .local_profiles
dbt docs serve --profiles-dir .local_profiles --port 8081
```

Then open [http://localhost:8081](http://localhost:8081).
