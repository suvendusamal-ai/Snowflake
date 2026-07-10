#!/usr/bin/env python3
"""Generate a valid JWT token matching .env configuration."""

import jwt
import os
from pathlib import Path

# Load .env values
env_file = Path(__file__).parent.parent / ".env"
env_vars = {}
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                env_vars[key.strip()] = value.strip()

jwt_secret_key = env_vars.get("JWT_SECRET_KEY", "supersecretjwtkey")
jwt_algorithm = env_vars.get("JWT_ALGORITHM", "HS256")
jwt_audience = env_vars.get("JWT_AUDIENCE", "my-api")
jwt_issuer = env_vars.get("JWT_ISSUER", "my-auth-service")

payload = {
    "sub": "test-user",
    "aud": jwt_audience,
    "iss": jwt_issuer,
}

token = jwt.encode(payload, jwt_secret_key, algorithm=jwt_algorithm)
print(f"Valid JWT Token:\n{token}\n")
print(f"Use it with:\n")
print(f'curl -X POST http://127.0.0.1:8000/ingest/csv \\')
print(f'  -H "Authorization: Bearer {token}" \\')
print(f'  -F "csv_file=@path/to/your/file.csv"')
print(f'\nNote: Table name will be automatically created from CSV filename (without extension)')
print(f'Example: "sales_data.csv" → table "SALES_DATA"')
