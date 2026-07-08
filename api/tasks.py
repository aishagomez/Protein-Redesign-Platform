"""
Worker Celery — completamente desacoplado de la DB y de la orquestación.

Contrato:
  - Recibe: stage_execution_id, stage_name, tool, params, tool_contract
  - Ejecuta: el proceso científico (stub → reemplazar con binario real)
  - Reporta: éxito o fallo al orquestador vía HTTP callback
  - NO toca la DB directamente
  - NO decide qué etapa sigue
  - Celery Events emite worker-heartbeat automáticamente (cada ~2s)
"""

import os
import time
import traceback
import requests
from billiard.exceptions import SoftTimeLimitExceeded
from celery_app import celery_app, STAGE_TIMEOUT_HOURS

# URL del orquestador — configurable por variable de entorno
ORCHESTRATOR_URL = os.environ.get("ORCHESTRATOR_URL", "http://api:8000")
INTERNAL_TOKEN = os.environ.get("INTERNAL_TOKEN", "123")


def _report(endpoint: str, payload: dict):
    """Llama al orquestador para reportar un evento. Fire-and-forget con retry básico."""
    url = f"{ORCHESTRATOR_URL}{endpoint}"
    headers = {"X-Internal-Token": INTERNAL_TOKEN}
    for attempt in range(3):
        try:
            r = requests.post(url, json=payload, headers=headers, timeout=10)
            r.raise_for_status()
            return
        except Exception as e:
            if attempt == 2:
                print(f"[Worker] No se pudo reportar a {url}: {e}")
            time.sleep(2 ** attempt)


def _run_tool(stage_name: str, tool: str, params: dict) -> dict:
    """
    Ejecuta la herramienta científica.
    Retorna {"output_files": [...], "metadata": {...}}
    TODO: reemplazar stubs con subprocess reales.
    """
    if stage_name == "refinement":
        # subprocess.run(["GNNrefine",
        #     "--receptor", params["input_pdb_path_receptor"],
        #     "--ligand",   params.get("input_pdb_path_ligand", ""),
        # ], check=True)
        output = params.get("input_pdb_path_receptor", "").replace(".pdb", "_refined.pdb")
        return {"output_files": [output], "metadata": {"tool": tool}}

    elif stage_name == "docking":
        # subprocess.run(["GRAMM",
        #     "--receptor", params["receptor_path"],
        #     "--ligand",   params["ligand_path"],
        # ], check=True)
        output = params.get("receptor_path", "").replace(".pdb", "_docked.pdb")
        return {"output_files": [output], "metadata": {"tool": tool}}

    elif stage_name == "evolution":
        # subprocess.run(["evo_algorithm",
        #     "--input", params["input_pdb"],
        # ], check=True)
        output = params.get("input_pdb", "").replace(".pdb", "_evolved.pdb")
        return {"output_files": [output], "metadata": {"tool": tool}}

    else:
        raise ValueError(f"Etapa desconocida: {stage_name}")


@celery_app.task(
    bind=True,
    name="tasks.run_stage",
    # El worker no impone timeout propio — el watchdog del orquestador detecta workers caídos
    # vía Celery Events (worker-heartbeat). task_time_limit sigue como hard kill de seguridad.
    acks_late=True,
)
def run_stage(
    self,
    stage_execution_id: int,
    stage_name: str,
    tool_id: int | None,
    tool: str,
    params: dict,
    tool_contract: dict | None = None,
):
    """
    Tarea genérica. Ejecuta cualquier etapa del pipeline.
    Reporta inicio y fin al orquestador vía HTTP.
    NO toca la DB. NO decide la siguiente etapa.
    """
    _report(
        f"/internal/stages/{stage_execution_id}/started",
        {"celery_task_id": self.request.id},
    )

    try:
        result = _run_tool(stage_name, tool, params)

        _report(
            f"/internal/stages/{stage_execution_id}/completed",
            {
                "output_files": result["output_files"],
                "metadata": result.get("metadata", {}),
            },
        )
        return {"status": "completed", "stage_execution_id": stage_execution_id}

    except SoftTimeLimitExceeded:
        _report(
            f"/internal/stages/{stage_execution_id}/failed",
            {
                "error": f"Soft time limit excedido ({STAGE_TIMEOUT_HOURS}h)",
                "retry_type": "technical",
            },
        )
        raise

    except Exception as exc:
        _report(
            f"/internal/stages/{stage_execution_id}/failed",
            {
                "error": str(exc),
                "traceback": traceback.format_exc(),
                "retry_type": "logical",
            },
        )
        raise
