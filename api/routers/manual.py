import os
from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter(tags=["Manual"])

@router.get("/manual/user-guide")
def user_guide():
    base_path = Path(os.getenv("DOCS_PATH", "./docs"))
    manual_path = base_path / "user_manual.pdf"
    return FileResponse(manual_path, filename="user_manual.pdf")
