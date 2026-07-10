from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

    sqlserver_conn: str
    sqlite_path: str

    snowflake_user: str
    snowflake_password: str
    snowflake_account: str
    snowflake_warehouse: str
    snowflake_database: str

    snowflake_schema: str = "oi_atlas"

    CORTEX_MODEL: str = "snowflake-arctic"

    # Toggle demo vs LLM mode
    USE_LLM: bool = False


settings = Settings()