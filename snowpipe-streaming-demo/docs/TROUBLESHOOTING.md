# Troubleshooting

## `No suitable Python runtime found`

Cause: the requested Python version is not installed.

Check available runtimes:

```powershell
py -0p
```

For this tested Windows setup, create the environment with Python 3.11:

```powershell
py -3.11 -m venv .venv
```

## PowerShell cannot activate `.venv`

Use the PowerShell activation script, including the leading `.\`:

```powershell
.\.venv\Scripts\Activate.ps1
```

If execution policy blocks it:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

## `msgspec` wheel build fails and asks for Microsoft Visual C++ 14+

The original installation ran under Python 3.14 and attempted to build `msgspec==0.19.0` from source.

Resolution:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
```

## `PermissionError: c:/profile.json`

Do not write application files directly to the root of `C:\`.

Use the project-local file:

```text
C:\snowpipe_demo\profile.json
```

The GitHub version reads `profile.json` from the repository root.

## `ERR_PIPE_DOES_NOT_EXIST_OR_NOT_AUTHORIZED`

Check both object naming and grants:

```sql
SHOW PIPES IN SCHEMA STREAMING_DEMO.RAW;
SHOW GRANTS ON PIPE STREAMING_DEMO.RAW.IOT_EVENTS_STREAMING;
SHOW GRANTS TO ROLE STREAMING_ROLE;
```

Required runtime privileges are:

- `USAGE` on database
- `USAGE` on schema
- `INSERT` on target table
- `OPERATE` on pipe

## `MemoryThresholdExceeded`

Observed error:

```text
MemoryThresholdExceeded
System Memory Used=... (91%)
HTTP 429 Too Many Requests
```

The SDK applied client-side backpressure because Windows had very little free physical memory.

Actions that resolved the test environment:

- Closed browser and communication applications
- Removed unused startup applications
- Disabled unnecessary Dell SupportAssist components
- Set local Oracle and SQL Server services to Manual when not in use
- Increased free RAM from roughly 0.5 GB to about 2.75 GB

After system memory usage dropped to about 64%, the same program completed successfully.

Do not terminate Windows core processes such as:

- Memory Compression
- `MsMpEng`
- `explorer`
- `dwm`

## A brief `backpressure` warning appears

Example:

```text
backpressure released after 0.001 seconds
```

A short-lived warning that immediately reports release is normal flow control and does not indicate failure.

## Latest committed offset is `None`

The channel-status cache may not have refreshed immediately after the first flush.

The demo polls briefly. Also verify:

```sql
SELECT * FROM STREAMING_DEMO.RAW.IOT_EVENTS;
SHOW CHANNELS IN PIPE STREAMING_DEMO.RAW.IOT_EVENTS_STREAMING;
```

## Rows fail because of field names or data types

Input keys must match the JSON paths used by the pipe definition. Ensure the target table and pipe agree with the event structure in `sample_data/iot_events.json`.

## Security reminder

Never paste a private key into an issue, commit, screenshot, or log. Rotate the Snowflake RSA public key immediately if the private key is exposed.
