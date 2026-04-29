from pathlib import Path
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    jwt_secret_key: SecretStr
    jwt_algorithm: str = Field("HS256", env="JWT_ALGORITHM")
    jwt_audience: str
    jwt_issuer: str

    snowflake_user: str
    snowflake_password: SecretStr
    snowflake_account: str
    snowflake_warehouse: str
    snowflake_database: str
    snowflake_schema: str
    snowflake_role: str
    snowflake_stage_name: str = Field("csv_ingest_stage", env="SNOWFLAKE_STAGE_NAME")
    snowflake_file_format: str = Field("csv_file_format", env="SNOWFLAKE_FILE_FORMAT")
    snowflake_transform_procedure: str | None = Field(None, env="SNOWFLAKE_TRANSFORM_PROCEDURE")

    app_env: str = Field("production", env="APP_ENV")
    log_level: str = Field("INFO", env="LOG_LEVEL")

    temp_upload_dir: Path = Field(Path.cwd(), env="TEMP_UPLOAD_DIR")

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
