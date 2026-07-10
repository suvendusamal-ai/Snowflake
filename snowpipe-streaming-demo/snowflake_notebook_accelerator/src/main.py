from connection.snowflake_connection import create_session
from notebook.notebook_deployer import (
    upload_notebook_to_stage,
    create_notebook_from_stage,
    activate_notebook
)

import warnings
warnings.filterwarnings(
    "ignore",
    message="Bad owner or permissions on.*config.toml"
)


def main():
    session = create_session()

    print("📦 Uploading notebook...")
    upload_notebook_to_stage(session)

    print("📘 Creating notebook...")
    create_notebook_from_stage(session)

    print("🚀 Activating notebook...")
    activate_notebook(session)

    session.close()


if __name__ == "__main__":
    main()