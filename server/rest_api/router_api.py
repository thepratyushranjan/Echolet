import os
import asyncio
from fastapi import UploadFile, APIRouter, File, HTTPException
from pydantic import ValidationError
from constant.file_constant import CHUNK_SIZE, MAX_FILE_SIZE, UPLOAD_DIR, ALLOWED_EXTENSIONS
from validation.pydentic_model import FileMeta
from services.upload_processor import process_file

router = APIRouter()


@router.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    print("research-agent/upload/")
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
        
        # Start background processing for allowed text/document types
        try:
            ext = os.path.splitext(file.filename)[1].lower().lstrip('.')
            if ext in ALLOWED_EXTENSIONS:
                asyncio.create_task(asyncio.to_thread(process_file, file_path))
        except Exception as e:
            # log but do not fail the upload
            print(f"Failed to start background processing for {file_path}: {e}")

        return {
            "filename": file.filename,
            "size": f"{size / (1024 * 1024):.2f} MB",
            "path": file_path,
            "status": "Uploaded successfully",
        }
    except HTTPException:
        raise
    except Exception as e:
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail="Internal server error")
