from pathlib import Path

from fastapi import HTTPException, status
from fastapi import UploadFile


ALLOWED_CONTENT_TYPES = {"text/csv", "application/vnd.ms-excel", "text/plain", "application/octet-stream"}


def get_bearer_token(authorization: str | None) -> str:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing.",
        )

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header must be a Bearer token.",
        )

    return parts[1]


def validate_csv_file(upload_file: UploadFile) -> None:
    if not upload_file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File extension must be .csv.",
        )


def write_upload_to_disk(upload_file: UploadFile, temp_dir: Path) -> Path:
    temp_path = temp_dir / Path(upload_file.filename).name
    contents = upload_file.file.read()
    temp_path.write_bytes(contents)
    return temp_path
