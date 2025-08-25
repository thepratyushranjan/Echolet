import os
from fastapi import UploadFile, APIRouter, File, HTTPException
from pydantic import ValidationError
from constant.file_constant import CHUNK_SIZE, MAX_FILE_SIZE, UPLOAD_DIR
from validation.pydentic_model import FileMeta

router = APIRouter()


@router.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a file with validation on type and size.
    Saves file in chunks to prevent memory issues.
    """
    try:
        try:
            FileMeta(filename=file.filename)
        except ValidationError as e:
            error_msg = e.errors()[0].get("msg", "Invalid file")
            raise HTTPException(status_code=400, detail=error_msg)

        # Ensure upload directory exists
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        file_path = os.path.join(UPLOAD_DIR, file.filename)

        size = 0
        try:
            with open(file_path, "wb") as f:
                while chunk := await file.read(CHUNK_SIZE):
                    size += len(chunk)
                    if size > MAX_FILE_SIZE:
                        raise HTTPException(
                            status_code=400,
                            detail=f"File too large. Max allowed size is {MAX_FILE_SIZE // (1024 * 1024)} MB"
                        )
                    f.write(chunk)
        except HTTPException:
            # Cleanup partially written file
            if os.path.exists(file_path):
                os.remove(file_path)
            raise

        return {
            "filename": file.filename,
            "size": f"{size / (1024 * 1024):.2f} MB",
            "path": file_path,
            "status": "Uploaded successfully",
        }
    except HTTPException:
        # Re-raise HTTP exceptions to be handled by FastAPI
        raise
    except Exception as e:
        # Cleanup partially written file if any unexpected error occurs
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail="Internal server error")
