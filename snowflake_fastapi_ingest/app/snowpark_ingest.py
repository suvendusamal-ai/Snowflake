import argparse
import logging
from pathlib import Path
from typing import Iterable

from snowflake.snowpark import Session, functions as F
from snowflake.snowpark.dataframe import DataFrame

from app.config import settings

logger = logging.getLogger(__name__)


class SnowparkCSVIngestor:
    """Snowpark-based CSV ingestion and transformation.

    This class does not create stages or file formats at runtime. It assumes
    the stage and file format configured in environment variables already exist.
    """

    def __init__(self) -> None:
        self.session = Session.builder.configs(self._session_config()).create()
        self.stage_name = settings.snowflake_stage_name
        self.file_format = settings.snowflake_file_format
        self.database = settings.snowflake_database
        self.schema = settings.snowflake_schema

    def _session_config(self) -> dict[str, str]:
        return {
            "user": settings.snowflake_user,
            "password": settings.snowflake_password.get_secret_value(),
            "account": settings.snowflake_account,
            "warehouse": settings.snowflake_warehouse,
            "database": settings.snowflake_database,
            "schema": settings.snowflake_schema,
            "role": settings.snowflake_role,
            "client_session_keep_alive": "true",
        }

    def verify_stage_and_format(self) -> None:
        stage_exists = self._show_command_has_rows(
            f"SHOW STAGES LIKE '{self.stage_name}'"
        )
        file_format_exists = self._show_command_has_rows(
            f"SHOW FILE FORMATS LIKE '{self.file_format}'"
        )

        if not stage_exists:
            raise RuntimeError(
                "Configured Snowflake stage does not exist. "
                f"Create stage '{self.stage_name}' before running this program."
            )

        if not file_format_exists:
            raise RuntimeError(
                "Configured Snowflake file format does not exist. "
                f"Create file format '{self.file_format}' before running this program."
            )

        logger.info(
            "Verified stage '%s' and file format '%s' are already provisioned.",
            self.stage_name,
            self.file_format,
        )

    def _show_command_has_rows(self, sql: str) -> bool:
        result = self.session.sql(sql).collect()
        return len(result) > 0

    def upload_csv_to_stage(self, local_path: Path) -> str:
        stage_location = f"@{self.stage_name}"
        logger.info("Uploading %s to stage %s", local_path, stage_location)
        put_results = self.session.file.put(
            str(local_path),
            stage_location,
            auto_compress=False,
            overwrite=True,
        )

        if not put_results:
            raise RuntimeError("Snowflake PUT did not upload any files")

        logger.info("Uploaded %s to stage %s", local_path.name, stage_location)
        return local_path.name

    def load_csv_to_temp_table(self, stage_file_name: str, temp_table_name: str) -> DataFrame:
        stage_path = f"@{self.stage_name}/{stage_file_name}"
        logger.info("Reading staged CSV %s from stage %s", stage_file_name, self.stage_name)

        staged_df = (
            self.session.read
            .options({"FORMAT_NAME": self.file_format})
            .csv(stage_path)
        )

        logger.info(
            "Saving staged CSV data into temporary table %s with Snowpark",
            temp_table_name,
        )
        staged_df.write.mode("overwrite").save_as_table(
            temp_table_name,
            create_temp_table=True,
        )

        return self.session.table(temp_table_name)

    def transform_dataframe(self, df: DataFrame) -> DataFrame:
        logger.info("Applying Snowpark transformation logic to DataFrame")

        # Trim whitespace for all string columns and standardize case.
        string_columns = [field.name for field in df.schema.fields if field.datatype.type_name.lower() == "string"]
        transformed = df
        for column_name in string_columns:
            transformed = transformed.with_column(
                column_name,
                F.trim(F.col(column_name)).alias(column_name),
            )

        # Add a Snowflake-managed load timestamp.
        transformed = transformed.with_column("loaded_at", F.current_timestamp())

        # If any column looks like a date/timestamp, attempt a cast.
        for field in transformed.schema.fields:
            if "date" in field.name.lower() or "timestamp" in field.name.lower() or "ts" in field.name.lower():
                transformed = transformed.with_column(
                    field.name,
                    F.to_timestamp(F.col(field.name)).alias(field.name),
                )

        return transformed

    def write_table(self, df: DataFrame, target_table: str) -> None:
        qualified_table = f"{self.database}.{self.schema}.{target_table}"
        logger.info("Writing transformed data to Snowflake table %s", qualified_table)
        df.write.mode("overwrite").save_as_table(qualified_table)
        logger.info("Snowflake table %s written successfully", qualified_table)

    def ingest_csv(self, local_csv: Path, target_table: str) -> None:
        self.verify_stage_and_format()
        stage_file_name = self.upload_csv_to_stage(local_csv)
        temp_table_name = f"tmp_{target_table}_staged"
        staged_df = self.load_csv_to_temp_table(stage_file_name, temp_table_name)
        transformed_df = self.transform_dataframe(staged_df)
        self.write_table(transformed_df, target_table)

    @staticmethod
    def _quote_identifier(value: str) -> str:
        normalized = value.replace('"', '""')
        return f'"{normalized}"'


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Snowpark CSV ingestion tool that uses an existing stage and file format."
    )
    parser.add_argument(
        "csv_file",
        type=Path,
        help="Path to the local CSV file to ingest.",
    )
    parser.add_argument(
        "target_table",
        help="Snowflake target table name to overwrite with transformed data.",
    )
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = parse_arguments()

    if not args.csv_file.exists():
        raise FileNotFoundError(f"CSV file not found: {args.csv_file}")

    ingestor = SnowparkCSVIngestor()
    ingestor.ingest_csv(args.csv_file, args.target_table)
    logger.info("Snowpark ingestion complete for %s", args.csv_file)


if __name__ == "__main__":
    main()
