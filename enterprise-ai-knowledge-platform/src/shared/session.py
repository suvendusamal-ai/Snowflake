"""Snowflake session factory — provides Snowpark session with environment config."""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Generator

from snowflake.snowpark import Session

from src.shared.config import load_environment_config


@contextmanager
def get_session(
    role: str | None = None,
    warehouse: str | None = None,
    schema: str | None = None,
) -> Generator[Session, None, None]:
    """Create a Snowpark session from environment configuration.

    Usage:
        with get_session(schema="KNOWLEDGE") as session:
            df = session.table("CHUNK_EMBEDDINGS")
    """
    config = load_environment_config()
    sf_config = config["snowflake"]

    connection_params = {
        "account": sf_config["account"],
        "user": sf_config["user"],
        "role": role or sf_config["role"],
        "warehouse": warehouse or sf_config["warehouse"],
        "database": sf_config["database"],
    }

    if schema:
        connection_params["schema"] = schema

    # Auth: prefer private key, fall back to password
    pk_path = os.environ.get("SNOWFLAKE_PRIVATE_KEY_PATH")
    if pk_path:
        with open(pk_path, "rb") as f:
            connection_params["private_key_file"] = pk_path
    else:
        password = os.environ.get("SNOWFLAKE_PASSWORD")
        if password:
            connection_params["password"] = password

    session = Session.builder.configs(connection_params).create()
    try:
        yield session
    finally:
        session.close()
