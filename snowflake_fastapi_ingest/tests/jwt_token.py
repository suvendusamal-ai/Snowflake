import jwt
import os

payload = {
    "sub": "test-user",
    "aud": "my-api",
    "iss": "my-auth-service",
}
token = jwt.encode(payload, "supersecretjwtkey", algorithm="HS256")
print(token)