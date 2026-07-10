"""Snowpipe Streaming high-performance Python SDK demo.

This program reads Snowflake connection details from profile.json,
opens a streaming channel, appends sample IoT events with offset tokens,
flushes them to Snowflake, polls briefly for the committed token, and
closes the client gracefully.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

from snowflake.ingest.streaming import StreamingIngestClient


BASE_DIR = Path(__file__).resolve().parent
PROFILE_FILE = BASE_DIR / "profile.json"
SAMPLE_DATA_FILE = BASE_DIR / "sample_data" / "iot_events.json"

DATABASE = "STREAMING_DEMO"
SCHEMA = "RAW"
PIPE_NAME = "IOT_EVENTS_STREAMING"
CLIENT_NAME = "iot_demo_client"
CHANNEL_NAME = "iot_channel_1"

FLUSH_TIMEOUT_SECONDS = 30
OFFSET_POLL_ATTEMPTS = 10
OFFSET_POLL_INTERVAL_SECONDS = 1


def load_json(path: Path) -> Any:
    """Load and return JSON content from a file."""
    if not path.exists():
        raise FileNotFoundError(
            f"Required file not found: {path}\n"
            "Copy profile.example.json to profile.json and update its values."
        )

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def validate_profile(profile: dict[str, Any]) -> None:
    """Validate required profile fields and referenced private-key file."""
    required = {"account", "user", "url", "role"}
    missing = sorted(required - profile.keys())

    if missing:
        raise ValueError(f"Missing profile fields: {', '.join(missing)}")

    private_key_file = profile.get("private_key_file")
    private_key_inline = profile.get("private_key")

    if not private_key_file and not private_key_inline:
        raise ValueError(
            "Profile must contain either 'private_key_file' or 'private_key'."
        )

    if private_key_file:
        key_path = Path(private_key_file)
        if not key_path.is_absolute():
            key_path = BASE_DIR / key_path

        if not key_path.exists():
            raise FileNotFoundError(f"Private key not found: {key_path}")

        # Use an absolute path so execution is independent of the current directory.
        profile["private_key_file"] = str(key_path)


def poll_committed_offset(channel: Any) -> str | None:
    """Poll briefly for channel-status metadata to expose the committed token."""
    for attempt in range(1, OFFSET_POLL_ATTEMPTS + 1):
        token = channel.get_latest_committed_offset_token()
        if token is not None:
            return str(token)

        if attempt < OFFSET_POLL_ATTEMPTS:
            print(
                "Committed offset not visible yet; "
                f"retrying ({attempt}/{OFFSET_POLL_ATTEMPTS})..."
            )
            time.sleep(OFFSET_POLL_INTERVAL_SECONDS)

    return None


def main() -> int:
    """Run the Snowpipe Streaming demonstration."""
    profile = load_json(PROFILE_FILE)
    if not isinstance(profile, dict):
        raise ValueError("profile.json must contain a JSON object.")

    validate_profile(profile)

    events = load_json(SAMPLE_DATA_FILE)
    if not isinstance(events, list) or not events:
        raise ValueError("sample_data/iot_events.json must contain a non-empty list.")

    client: StreamingIngestClient | None = None

    try:
        client = StreamingIngestClient(
            client_name=CLIENT_NAME,
            db_name=DATABASE,
            schema_name=SCHEMA,
            pipe_name=PIPE_NAME,
            profile_json=json.dumps(profile),
        )

        channel, status = client.open_channel(channel_name=CHANNEL_NAME)
        print(f"Channel opened successfully. Initial status: {status}")

        for offset, event in enumerate(events):
            channel.append_row(row=event, offset_token=str(offset))
            print(
                f"Sent event {offset}: "
                f"{event.get('device_id', '<unknown>')} - "
                f"{event.get('event_type', '<unknown>')}"
            )

        print("\nWaiting for Snowflake commit...")
        channel.wait_for_flush(timeout_seconds=FLUSH_TIMEOUT_SECONDS)
        print("All rows successfully flushed.")

        committed_offset = poll_committed_offset(channel)
        print(f"Latest committed offset: {committed_offset}")

        return 0

    except Exception as exc:
        print(f"\nStreaming failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    finally:
        if client is not None:
            client.close()
            print("Streaming client closed.")


if __name__ == "__main__":
    raise SystemExit(main())
