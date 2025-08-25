from pydantic import BaseModel, field_validator
from constant.file_constant import ALLOWED_EXTENSIONS


class FileMeta(BaseModel):
    filename: str

    @field_validator("filename")
    def validate_file_extension(cls, value: str) -> str:
        """Validate file extension and raise user-friendly error."""
        ext = value.rsplit(".", 1)[-1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
            # Raise with a clean message (no debug info needed)
            raise ValueError(f"Unsupported file type '.{ext}'. Allowed types: {allowed}")
        return value
