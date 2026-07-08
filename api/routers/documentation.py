import os
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import FileResponse

router = APIRouter(tags=["Documentation"])

DOCS_INDEX = {
    "user_manual.pdf": {
        "title": "User Manual",
        "description": "Guia operativa para cargar archivos, ejecutar pipelines y descargar resultados.",
        "category": "manual",
    },

}


def _docs_root() -> Path:
    return Path(os.getenv("DOCS_PATH", "./docs")).resolve()


def _resolve_doc(name: str) -> Path:
    docs_root = _docs_root()
    candidate = (docs_root / name).resolve()
    if docs_root != candidate.parent and docs_root not in candidate.parents:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Documento fuera del directorio permitido")
    if not candidate.exists() or not candidate.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento no encontrado")
    return candidate


@router.get("/documentation/entries")
def documentation_entries():
    docs_root = _docs_root()
    entries = []
    for file_name, metadata in DOCS_INDEX.items():
        path = docs_root / file_name
        if not path.exists():
            continue
        stat = path.stat()
        entries.append(
            {
                "name": file_name,
                "title": metadata["title"],
                "description": metadata["description"],
                "category": metadata["category"],
                "size": stat.st_size,
                "download_url": f"/documentation/download?name={file_name}",
            }
        )
    return entries


@router.get("/documentation/download")
def documentation_download(name: str = Query(...)):
    file_path = _resolve_doc(name)
    return FileResponse(file_path, filename=file_path.name)
