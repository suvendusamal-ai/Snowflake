# Speaker Script: One-Hour Session

## 0:00-2:00 Opening

"Today I'm going to show dbt on Snowflake in a very practical way. I'll assume
some of you come from a Databricks background, so I'll translate the concepts
as we go."

"The main idea is simple: raw data lands first, then dbt turns that raw data
into clean, trusted, business-ready analytical models."

## 2:00-5:00 What dbt solves

"Without dbt, SQL logic often lives in worksheets, notebooks, or scattered job
scripts. That makes it hard to test, document, and reuse."

"dbt makes SQL transformations behave more like software. We get modular models,
dependencies, tests, docs, lineage, and version control."

## 5:00-8:00 Where dbt fits

"In this demo, Snowflake stores the data and runs the transformations."

"RAW is our landing layer. If you think in Databricks terms, this is similar to
source or bronze-like data."

"dbt then builds the curated analytical layers on top, similar to the cleaner
silver and gold layers."

## 8:00-12:00 Core concepts

"The most important dbt ideas are `source`, `ref`, tests, seeds, and snapshots."

"`source` tells dbt where trusted raw input starts."

"`ref` links one model to another, so dbt builds a dependency graph."

"Tests let us validate assumptions like uniqueness, not-null rules, and valid
relationships."

"Seeds are tiny CSV files stored in Git and loaded as tables."

"Snapshots preserve historical changes when source records change over time."

## 12:00-15:00 Snowflake-native angle

"The special part of this demo is that the development happens in Snowflake
Workspaces and the final deployment becomes a native Snowflake `DBT PROJECT`
object."

"So we are not just running SQL from a laptop. We are using Snowflake as the
development and execution platform."

## 15:00-20:00 Create the RAW layer

"I'll start by running a setup script that creates a small warehouse, a demo
database, the raw schemas, and sample data."

"This is important: dbt is not loading the operational data here. dbt starts
after the raw data already exists."

"That separation is healthy. Ingestion and transformation are related, but they
are not the same responsibility."

## 20:00-25:00 Workspace setup

"Now I'm opening a Snowflake Workspace. This is our development area for the dbt
project."

"If you use Databricks notebooks or files as a development surface, this is the
Snowflake-native equivalent for this demo."

"I've uploaded a small dbt project with folders for staging, intermediate,
marts, tests, snapshots, docs, and macros."

## 25:00-30:00 Compile and seed

"First I'll run `compile`. This does not build tables yet. It just checks that
dbt understands the project."

"Next I'll run `seed`. This loads a tiny business-owned reference file into
Snowflake."

"This is useful when you have small configuration or target tables that should
live in Git and be version-controlled."

## 30:00-35:00 Build

"Now I'll run `build`. This is the main execution step."

"It builds models and runs tests in dependency order."

"In simple terms, this is where raw data becomes trusted analytical data."

"If you come from Databricks, think of this as materializing the curated layers
after validating the transformation graph."

## 35:00-40:00 Show the project files

"Let me quickly show the key folders."

"In `models/staging`, we do simple cleanup and standardization."

"In `models/intermediate`, we combine reusable business logic."

"In `models/marts`, we publish the business-facing fact, dimension, and report."

"In `snapshots`, we preserve history."

"In `tests`, `macros`, and `docs`, we make the project trustworthy and easier
to understand."

## 40:00-45:00 Show the built outputs

"Now I'll query the outputs."

"This fact table stores measurable business events."

"This dimension table gives customer context."

"This reporting view summarizes performance by segment."

"And this snapshot table keeps historical versions of customer records."

## 45:00-50:00 Simulate a business change

"Next I'll simulate two real changes: a new order arrives, and a customer status
changes."

"This is where dbt becomes operational instead of static."

"I'll rerun the relevant part of the project and then rerun the snapshot."

"Now I can prove that the fact table picked up the new transaction, and the
snapshot preserved the old and new customer states."

## 50:00-54:00 Deploy native Snowflake DBT PROJECT

"So far we were developing in a workspace. Now I'll deploy this as a native
Snowflake `DBT PROJECT` object."

"This is the Snowflake-native moment."

"The transformation project is now a managed Snowflake object that Snowflake can
execute directly."

## 54:00-56:00 Git publish

"After validation and deployment, I push the project to GitHub from Snowflake
Workspace using Snowflake Git Integration."

"That gives us version control, collaboration, and reproducibility."

"The order matters here: first validate in Snowflake, then deploy, then publish
the approved code to Git from within Snowflake."

## 56:00-60:00 Local docs and lineage

"Finally, I clone the project fresh and open classic dbt docs locally."

"This gives us a visual lineage map."

"I'll start from the report, trace it back to the fact, then back to staging,
and finally back to the raw source tables."

"This is where non-technical users often understand the value very quickly,
because they can literally see how business outputs are produced."

## Closing

"The key takeaway is that dbt on Snowflake gives us modular SQL transformation,
testing, documentation, lineage, and repeatable deployment in a platform-native
way."

"For Databricks users, the mindset is familiar: raw data lands first, then we
build cleaner and more trusted layers on top. The difference here is the dbt
workflow and the Snowflake-native execution model."
