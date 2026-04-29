import json


def get_notebook_json():
    notebook = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "# 🚀 Customer Pipeline Execution Notebook\n",
                    "\n",
                    "This notebook executes the Snowflake stored procedure:\n",
                    "`RUN_CUSTOMER_PIPELINE`\n",
                    "\n",
                    "👉 Click **Run ▶** to execute the pipeline.\n"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "from snowflake.snowpark.context import get_active_session\n",
                    "\n",
                    "# Get Snowflake session\n",
                    "session = get_active_session()\n",
                    "\n",
                    "print('🚀 Calling Stored Procedure...')\n",
                    "\n",
                    "# Execute Stored Procedure\n",
                    "result = session.sql(\n",
                    "    \"CALL DEMODB.OI_ATLAS.RUN_CUSTOMER_PIPELINE()\"\n",
                    ").collect()\n",
                    "\n",
                    "print('✅ Stored Procedure Execution Result:')\n",
                    "print(result)\n"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# Verify Output Table\n",
                    "print('📊 Preview of FILTERED_CUSTOMERS table:')\n",
                    "\n",
                    "df = session.table(\"DEMODB.OI_ATLAS.FILTERED_CUSTOMERS\")\n",
                    "df.show()\n"
                ]
            }
        ],
        "metadata": {},
        "nbformat": 4,
        "nbformat_minor": 5
    }

    return json.dumps(notebook)