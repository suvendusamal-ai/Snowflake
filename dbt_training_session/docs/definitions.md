{% docs training_architecture %}

This one-hour workshop uses a compact but complete dbt flow:

1. `RAW` tables are loaded outside dbt.
2. `STAGING` models standardize source data.
3. `INTERMEDIATE` models centralize reusable joins and calculations.
4. `MARTS` publish business-ready facts, dimensions, and reporting views.
5. `SNAPSHOTS` preserve mutable customer history.
6. `SEEDS` store small business-owned reference data in Git.

The lineage should be easy to explain live in under one minute.

{% enddocs %}
