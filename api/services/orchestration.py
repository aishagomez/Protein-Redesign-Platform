import os
import shutil
import threading
import zipfile
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

import requests
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from celery_app import celery_app
from models import Pipeline, Project, StageExecution, Notification, Tool
from services.auth import is_admin_user_id
from services.access import get_pipeline_by_id_for_user, get_pipeline_for_user
from services.file_storage import GENERATED_ROOT
from tasks import run_stage

MAX_RETRIES = int(os.environ.get("MAX_RETRIES", "3"))
WORKER_TIMEOUT_SECONDS = int(os.environ.get("WORKER_TIMEOUT_SECONDS", "30"))
EMAIL_NOTIFIER_URL = os.environ.get("EMAIL_NOTIFIER_URL", "http://email-notifier:8010/send")
INTERNAL_TOKEN = os.environ.get("INTERNAL_TOKEN", "internal-secret-change-me")
NON_RETRYABLE_RESOURCE_ERRORS = (
    "no space left on device",
    "disk full",
    "not enough space",
    "errno 28",
    "returncode=137",
    "killed",
    "cannot allocate memory",
    "out of memory",
)

VALID_TRANSITIONS = {
    "created": {"pending"},
    "pending": {"running", "waiting_for_approval"},
    "running": {"completed", "failed", "waiting_for_approval", "retrying"},
    "retrying": {"pending"},
    "waiting_for_approval": {"pending", "failed"},
    "completed": set(),
    "failed": {"retrying"},
}

STAGE_QUEUES = {
    "refinement": "refinement",
    "docking": "docking",
    "interaction_optimization": "interaction_optimization",
}


def _slugify(value: str) -> str:
    return "".join(char.lower() if char.isalnum() else "_" for char in value).strip("_") or "user"


def _is_missing_value(value) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    return False


def _set_if_missing(target: dict, key: str, value):
    if _is_missing_value(target.get(key)):
        target[key] = value


def _find_final_model_pdb(output_files: list[str]) -> Optional[str]:
    for path in output_files:
        p = Path(path)
        if p.suffix.lower() == ".pdb" and "final_model" in p.stem.lower() and p.exists():
            return path
    return None


def _pick_final_model_or_first_pdb(output_files: list[str]) -> Optional[str]:
    final_model = _find_final_model_pdb(output_files)
    if final_model:
        return final_model

    complex_candidates = _pick_docking_complex_pdbs(output_files)
    if complex_candidates:
        return complex_candidates[-1]

    return _pick_primary_output_pdb(output_files)


def _inspect_scenario_contents(scenario_reference: str) -> dict:
    path = Path(scenario_reference)
    if path.is_dir():
        files = [p.name.lower() for p in path.rglob("*") if p.is_file()]
    elif path.is_file() and path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path, "r") as archive:
            files = [Path(name).name.lower() for name in archive.namelist() if not name.endswith("/")]
    else:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Ruta de escenario invalida: {scenario_reference}",
        )
    return {
        "has_pdb": any(name.endswith(".pdb") for name in files),
        "has_facea": any(name == "facea.txt" for name in files),
        # ProteinEA historically used faceC.txt, but the second protein may
        # legitimately be chain B after docking. Accept both conventional names.
        "has_facec": any(name in {"facec.txt", "faceb.txt"} for name in files),
        "has_msa": any(
            (name.endswith(".tsv") and "msa" in name)
            or (name.endswith(".txt") and ("msa" in name or "alignment" in name))
            for name in files
        ),
    }


def _warn_pause_between_stages(stage_name: str, params: dict):
    if stage_name == "interaction_optimization":
        if params.get("scenario_path") is None and params.get("msa_matrix_path") is None:
            return
        if params.get("scenario_path") is None and params.get("msa_matrix_path") is not None:
            params.setdefault("warning_message", (
                "Se usará el primer PDB disponible de la etapa anterior por defecto. "
                "Si desea usar otro PDB, ejecute con pause_between_stages=True."
            ))
    if stage_name == "docking":
        if params.get("receptor_path") is None or params.get("ligand_path") is None:
            params.setdefault("warning_message", (
                "Se usará el primer PDB disponible de las etapas de refinement anteriores. "
                "Si desea elegir otro PDB, ejecute con pause_between_stages=True."
            ))


def _validate_stage_params(stage_name: str, params: dict):
    if stage_name == "refinement":
        if not (params.get("input") or params.get("input_pdb_path_receptor")):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Etapa 'refinement' requiere params: ['input' o 'input_pdb_path_receptor']",
            )
        return

    required = {}
    if stage_name == "docking":
        receptor = params.get("receptor_path") or params.get("receptor")
        ligand = params.get("ligand_path") or params.get("ligand")
        missing = []
        if not receptor:
            missing.append("receptor_path")
        if not ligand:
            missing.append("ligand_path")
        if missing:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Etapa 'docking' requiere params: {missing}",
            )
        return

    if stage_name == "interaction_optimization":
        scenario_path = params.get("scenario_path") or params.get("input_scenario_path") or params.get("scenario_dir")
        msa_matrix_path = params.get("msa_matrix_path")
        missing = []
        if not scenario_path and not msa_matrix_path:
            missing.append("scenario_path")
        if scenario_path:
            if not params.get("partners"):
                missing.append("partners")
            if not params.get("ligand_chain"):
                missing.append("ligand_chain")
        if missing:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Etapa 'interaction_optimization' requiere params: {missing}",
            )
        return

    missing = [key for key in required.get(stage_name, []) if not params.get(key)]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Etapa '{stage_name}' requiere params: {missing}",
        )


def _validate_stage_order(stage_order: list[dict]):
    previous_stage_names: list[str] = []
    for stage_def in stage_order:
        stage_name = stage_def["stage_name"]
        params = stage_def.get("params", {})
        _warn_pause_between_stages(stage_name, params)

        if stage_name == "docking":
            receptor = params.get("receptor_path") or params.get("receptor")
            ligand = params.get("ligand_path") or params.get("ligand")
            if not receptor or not ligand:
                previous_refinements = [name for name in previous_stage_names if name == "refinement"]
                if len(previous_refinements) < 2:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail="Etapa 'docking' sin receptor/ligand explicitos requiere dos etapas 'refinement' previas",
                    )
            else:
                _validate_stage_params(stage_name, params)
        elif stage_name == "interaction_optimization":
            scenario_path = params.get("scenario_path") or params.get("input_scenario_path") or params.get("scenario_dir")
            msa_matrix_path = params.get("msa_matrix_path")
            if not scenario_path:
                if not msa_matrix_path:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail="Etapa 'interaction_optimization' requiere 'msa_matrix_path' cuando el escenario se construye desde docking",
                    )
                if "docking" not in previous_stage_names:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail="Etapa 'interaction_optimization' sin 'scenario_path' requiere una etapa 'docking' previa",
                    )
            else:
                _validate_stage_params(stage_name, params)
        else:
            _validate_stage_params(stage_name, params)

        previous_stage_names.append(stage_name)


def _validate_stage_params_with_history(stage_name: str, params: dict, previous_stage_names: list[str]):
    if stage_name == "docking":
        receptor = params.get("receptor_path") or params.get("receptor")
        ligand = params.get("ligand_path") or params.get("ligand")
        if not receptor or not ligand:
            previous_refinements = [name for name in previous_stage_names if name == "refinement"]
            if len(previous_refinements) < 2:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Etapa 'docking' sin receptor/ligand explicitos requiere dos etapas 'refinement' previas",
                )
            return

    if stage_name == "interaction_optimization":
        scenario_path = params.get("scenario_path") or params.get("input_scenario_path") or params.get("scenario_dir")
        if not scenario_path:
            if not params.get("msa_matrix_path"):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Etapa 'interaction_optimization' requiere 'msa_matrix_path' cuando el escenario se construye desde docking",
                )
            if "docking" not in previous_stage_names:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Etapa 'interaction_optimization' sin 'scenario_path' requiere una etapa 'docking' previa",
                )
            return

    _validate_stage_params(stage_name, params)


def _get_tool(db: Session, tool_id: int) -> Tool:
    tool = db.query(Tool).filter(Tool.id == tool_id, Tool.active.is_(True)).first()
    if not tool:
        raise HTTPException(status_code=404, detail=f"Herramienta {tool_id} no encontrada o inactiva")
    return tool


def _build_worker_tool_contract(tool: Tool) -> dict:
    if not tool.runtime:
        raise HTTPException(
            status_code=422,
            detail=f"La herramienta '{tool.name}' no tiene runtime profile configurado",
        )

    parameters = sorted(
        tool.parameters or [],
        key=lambda parameter: (
            parameter.position is None,
            parameter.position if parameter.position is not None else 0,
            parameter.id,
        ),
    )

    return {
        "tool": {
            "id": tool.id,
            "name": tool.name,
            "version": tool.version,
            "description": tool.description,
            "active": tool.active,
        },
        "runtime": {
            "mode": tool.runtime.mode,
            "image": tool.runtime.image,
            "workdir": tool.runtime.workdir,
            "command_template": tool.runtime.command_template or [],
            "mounts": tool.runtime.mounts or [],
            "env": tool.runtime.env or {},
            "resources": tool.runtime.resources or {},
            "notes": tool.runtime.notes,
        },
        "parameters": [
            {
                "name": parameter.name,
                "flag": parameter.flag,
                "data_type": parameter.data_type,
                "optional": parameter.optional,
                "default_value": parameter.default_value,
                "format": parameter.format,
                "position": parameter.position,
                "is_input": parameter.is_input,
                "is_output": parameter.is_output,
                "ui_label": parameter.ui_label,
                "options": parameter.options,
                "description": parameter.description,
            }
            for parameter in parameters
        ],
    }


def _transition(stage: StageExecution, new_status: str, db: Session):
    allowed = VALID_TRANSITIONS.get(stage.status, set())
    if new_status not in allowed:
        raise ValueError(
            f"Transicion invalida: {stage.status} -> {new_status} "
            f"(stage_execution_id={stage.id})"
        )
    stage.status = new_status
    stage.updated_at = datetime.now(timezone.utc)
    db.commit()


def get_next_stage(pipeline: Pipeline, db: Session) -> Optional[StageExecution]:
    stages = (
        db.query(StageExecution)
        .filter(
            StageExecution.pipeline_id == pipeline.id,
            StageExecution.status != "failed",
        )
        .order_by(StageExecution.stage_order_index, StageExecution.id.desc())
        .all()
    )

    seen = {}
    for stage in stages:
        if stage.stage_order_index not in seen:
            seen[stage.stage_order_index] = stage

    active_stages = sorted(seen.values(), key=lambda stage: stage.stage_order_index)

    for stage in active_stages:
        if stage.status == "failed":
            return None
        if stage.status in ("running", "waiting_for_approval", "retrying"):
            return None
        if stage.status == "pending":
            return stage

    return None


def _launch_stage(stage: StageExecution, db: Session):
    queue = STAGE_QUEUES.get(stage.stage_name, "pipeline")

    locked = (
        db.execute(
            select(StageExecution)
            .where(StageExecution.id == stage.id)
            .with_for_update(skip_locked=True)
        )
        .scalars()
        .first()
    )
    if not locked or locked.status != "pending":
        return

    resolved_params = _resolve_stage_params(locked, db)
    tool = _get_tool(db, locked.tool_id)
    tool_contract = _build_worker_tool_contract(tool)

    task = run_stage.apply_async(
        kwargs={
            "stage_execution_id": stage.id,
            "stage_name": stage.stage_name,
            "tool_id": stage.tool_id,
            "tool": stage.tool,
            "params": resolved_params,
            "tool_contract": tool_contract,
        },
        queue=queue,
    )

    stage.celery_task_id = task.id
    stage.updated_at = datetime.now(timezone.utc)
    db.commit()


def _resolve_stage_params(stage: StageExecution, db: Session) -> dict:
    params = dict(stage.params or {})
    _set_if_missing(params, "output_dir", _default_output_dir(stage))
    _warn_pause_between_stages(stage.stage_name, params)
    previous_stages = (
        db.query(StageExecution)
        .filter(
            StageExecution.pipeline_id == stage.pipeline_id,
            StageExecution.stage_order_index < stage.stage_order_index,
            StageExecution.status == "completed",
        )
        .order_by(StageExecution.stage_order_index.asc(), StageExecution.id.desc())
        .all()
    )

    if stage.stage_name == "docking":
        params = _hydrate_docking_params(params, previous_stages)
    elif stage.stage_name == "interaction_optimization":
        params = _hydrate_interaction_optimization_params(stage, params, previous_stages)

    stage.params = params
    db.commit()
    return params


def _default_output_dir(stage: StageExecution) -> str:
    pipeline = stage.pipeline
    project = pipeline.project if pipeline else None
    user = project.user if project else None
    username = _slugify(getattr(user, "username", "user"))
    return f"/persistent_storage/outputs/{username}/{stage.stage_name}/pipeline_{stage.pipeline_id}/stage_{stage.stage_order_index + 1}"


def _hydrate_docking_params(params: dict, previous_stages: list[StageExecution]) -> dict:
    resolved = dict(params)
    receptor = resolved.get("receptor_path") or resolved.get("receptor")
    ligand = resolved.get("ligand_path") or resolved.get("ligand")

    if receptor and ligand:
        return resolved

    refinement_stages = [stage for stage in previous_stages if stage.stage_name == "refinement"]
    pdb_outputs = [_pick_primary_output_pdb(stage.output_files or [], preferred_suffix=".refined.pdb") for stage in refinement_stages]
    pdb_outputs = [path for path in pdb_outputs if path]

    if len(pdb_outputs) < 2:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No hay suficientes salidas de refinement para alimentar docking",
        )

    _set_if_missing(resolved, "receptor_path", pdb_outputs[0])
    _set_if_missing(resolved, "ligand_path", pdb_outputs[1])
    _set_if_missing(resolved, "receptor_id", Path(pdb_outputs[0]).stem)
    _set_if_missing(resolved, "ligand_id", Path(pdb_outputs[1]).stem)
    return resolved


def _pick_previous_stage_with_pdb(previous_stages: list[StageExecution]) -> tuple[Optional[StageExecution], Optional[str]]:
    for stage in reversed(previous_stages):
        selected_pdb = _pick_final_model_or_first_pdb(stage.output_files or [])
        if selected_pdb:
            return stage, selected_pdb
    return None, None


def _hydrate_interaction_optimization_params(stage: StageExecution, params: dict, previous_stages: list[StageExecution]) -> dict:
    resolved = dict(params)
    scenario_path = resolved.get("scenario_path") or resolved.get("input_scenario_path") or resolved.get("scenario_dir")
    source_stage, selected_pdb = _pick_previous_stage_with_pdb(previous_stages)

    if scenario_path:
        scenario_info = _inspect_scenario_contents(scenario_path)
        if not scenario_info["has_facea"] or not scenario_info["has_facec"] or not scenario_info["has_msa"]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "El paquete de interaction optimization debe incluir faceA.txt, faceB.txt o faceC.txt y un archivo MSA "
                    "(por ejemplo alignment.txt o MSA_matrix.tsv). Asegure que el paquete de escenario esté completo."
                ),
            )
        if not scenario_info["has_pdb"]:
            if not selected_pdb:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=(
                        "El zip de interaction optimization no contiene un PDB y no hay una etapa previa con PDB generado. "
                        "Debe incluir un PDB en el paquete o ejecutar una etapa previa que genere al menos un PDB."
                    ),
                )
            resolved["complex_pdb_path"] = selected_pdb
        return resolved

    if not source_stage or not selected_pdb:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No se encontro una etapa previa con un PDB disponible para construir el escenario de interaction optimization",
        )

    msa_matrix_path = resolved.get("msa_matrix_path")
    if not msa_matrix_path:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Falta 'msa_matrix_path' para construir el escenario de interaction optimization",
        )

    scenario_dir, derived = _build_interaction_optimization_scenario(stage, source_stage, resolved)
    resolved.update(derived)
    resolved["scenario_path"] = str(scenario_dir)
    return resolved


def _build_interaction_optimization_scenario(stage: StageExecution, source_stage: StageExecution, params: dict) -> tuple[Path, dict]:
    complex_pdb = params.get("complex_pdb_path") or _pick_final_model_or_first_pdb(source_stage.output_files or [])
    if not complex_pdb:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "No se encontro un PDB de docking para construir el escenario de interaction optimization. "
                "Debe incluir el PDB en el zip de optimización de interacciones o proveer un stage de docking previo que genere al menos un PDB."
            ),
        )

    msa_matrix_path = Path(params["msa_matrix_path"])
    if not msa_matrix_path.exists():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"No existe el archivo MSA indicado: {msa_matrix_path}",
        )

    scenario_dir = (GENERATED_ROOT / f"pipeline_{stage.pipeline_id}" / f"stage_{stage.id}_scenario").resolve()
    if scenario_dir.exists():
        shutil.rmtree(scenario_dir)
    scenario_dir.mkdir(parents=True, exist_ok=True)

    complex_source = Path(complex_pdb)
    copied_pdb = scenario_dir / complex_source.name
    shutil.copy2(complex_source, copied_pdb)
    prepared_pdb = _prepare_interaction_optimization_complex_pdb(copied_pdb)

    chains = _extract_chain_residues(prepared_pdb)
    if len(chains) < 2:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El PDB de docking necesita al menos dos cadenas para construir el escenario de interaction optimization",
        )

    chain_map = {chain_id: residues for chain_id, residues in chains}
    requested_partners = params.get("partners")
    requested_ligand_chain = params.get("ligand_chain")

    detected_partner_chain = chains[0][0]
    detected_ligand_chain = chains[1][0]

    partners = requested_partners or f"{detected_partner_chain}_{detected_ligand_chain}"
    ligand_chain = requested_ligand_chain or partners.split("_")[-1]
    partner_chain = partners.split("_")[0]

    if partner_chain not in chain_map or ligand_chain not in chain_map:
        partner_chain = detected_partner_chain
        ligand_chain = detected_ligand_chain
        partners = f"{partner_chain}_{ligand_chain}"

    face1_name = params.get("face1_file_name") or "faceA.txt"
    face2_name = params.get("face2_file_name") or "faceC.txt"

    msa_name = params.get("msa_matrix") or msa_matrix_path.name
    shutil.copy2(msa_matrix_path, scenario_dir / msa_name)

    return scenario_dir, {
        "scenario_name": scenario_dir.name,
        "pdbfile": str(prepared_pdb),
        "partners": partners,
        "ligand_chain": ligand_chain,
        "face1_file_name": face1_name,
        "face2_file_name": face2_name,
        "msa_matrix": msa_name,
        "complex_pdb_path": str(complex_source),
        "dummy_selected_complex_pdb_path": str(complex_source),
        "prepared_complex_pdb_path": str(prepared_pdb),
        "requested_partners": requested_partners,
        "requested_ligand_chain": requested_ligand_chain,
        "generated_from_previous_stage_id": source_stage.id,
        "generated_from_previous_stage_name": source_stage.stage_name,
    }


def _pick_primary_output_pdb(output_files: list[str], preferred_suffix: str | None = None) -> Optional[str]:
    candidates = [Path(path) for path in output_files if Path(path).suffix.lower() == ".pdb" and Path(path).exists()]
    if preferred_suffix:
        for path in candidates:
            if path.name.endswith(preferred_suffix):
                return str(path)
    if candidates:
        return str(candidates[0])
    return None


def _pick_docking_complex_pdbs(output_files: list[str]) -> list[str]:
    candidates = []
    for output in output_files:
        path = Path(output)
        if path.suffix.lower() != ".pdb" or not path.exists():
            continue
        if path.name.endswith(".refined.pdb"):
            continue
        if "-" in path.stem:
            candidates.append(str(path))
    return candidates


def _pick_dummy_pdb(output_files: list[str]) -> Optional[str]:
    candidates = _pick_docking_complex_pdbs(output_files)
    if candidates:
        return candidates[0]
    return _pick_primary_output_pdb(output_files)


def _ensure_docking_final_model(stage: StageExecution, db: Session):
    output_files = list(stage.output_files or [])
    candidates = _pick_docking_complex_pdbs(output_files)
    if not candidates:
        return

    selected = Path(candidates[-1])
    if not selected.exists():
        return

    final_model_path = selected.parent / "final_model.pdb"
    lines = selected.read_text(encoding="utf-8", errors="ignore").splitlines()
    model_starts = [index for index, line in enumerate(lines) if line.startswith("MODEL")]

    if model_starts:
        start = model_starts[-1] + 1
        end = next(
            (index for index in range(start, len(lines)) if lines[index].startswith("ENDMDL")),
            len(lines),
        )
        model_lines = [
            line for line in lines[start:end]
            if line.startswith(("ATOM", "HETATM", "TER"))
        ]
        final_model_path.write_text("\n".join(model_lines) + "\nEND\n", encoding="utf-8")
    else:
        shutil.copy2(selected, final_model_path)

    if str(final_model_path) not in output_files:
        output_files.append(str(final_model_path))
        stage.output_files = output_files
        stage.output_metadata = stage.output_metadata or {}
        stage.output_metadata["final_model"] = str(final_model_path)
        db.commit()


def _extract_chain_residues(pdb_path: Path) -> list[tuple[str, list[int]]]:
    chains: dict[str, list[int]] = {}
    seen: dict[str, set[int]] = {}
    with pdb_path.open("r", encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            if not line.startswith(("ATOM", "HETATM")):
                continue
            chain_id = line[21].strip()
            residue_raw = line[22:26].strip()
            if not chain_id or not residue_raw:
                continue
            try:
                residue_number = int(residue_raw)
            except ValueError:
                continue
            if chain_id not in chains:
                chains[chain_id] = []
                seen[chain_id] = set()
            if residue_number not in seen[chain_id]:
                chains[chain_id].append(residue_number)
                seen[chain_id].add(residue_number)
    return [(chain_id, residues) for chain_id, residues in chains.items()]



def _prepare_interaction_optimization_complex_pdb(copied_pdb: Path) -> Path:
    lines = copied_pdb.read_text(encoding="utf-8", errors="ignore").splitlines()
    if not any(line.startswith("MODEL") for line in lines):
        return copied_pdb

    model_lines: list[str] = []
    inside_first_model = False
    for line in lines:
        if line.startswith("MODEL"):
            if inside_first_model:
                break
            inside_first_model = True
            continue
        if line.startswith("ENDMDL"):
            break
        if not inside_first_model:
            continue
        if line.startswith(("ATOM", "HETATM", "TER", "END")):
            model_lines.append(line)

    if not model_lines:
        return copied_pdb

    single_model_pdb = copied_pdb.with_name(f"{copied_pdb.stem}.model1.pdb")
    single_model_pdb.write_text("\n".join(model_lines) + "\n", encoding="utf-8")
    return single_model_pdb


def advance_pipeline(pipeline_id: int, db: Session):
    pipeline = db.query(Pipeline).filter(Pipeline.id == pipeline_id).first()
    if not pipeline or pipeline.status in ("completed", "failed"):
        return

    next_stage = get_next_stage(pipeline, db)

    if next_stage is None:
        active = _get_active_stages(pipeline_id, db)
        all_done = all(stage.status == "completed" for stage in active)
        any_failed = any(stage.status == "failed" for stage in active)

        if any_failed:
            pipeline.status = "failed"
            pipeline.finished_at = datetime.now(timezone.utc)
            db.commit()
            subject = "Pipeline fallido"
            message = f"Pipeline #{pipeline_id} fallo."
            _notify(db, pipeline, subject, message)
            _send_email_notification(pipeline, subject, message, status_value="error")
        elif all_done:
            pipeline.status = "completed"
            pipeline.finished_at = datetime.now(timezone.utc)
            db.commit()
            subject = "Pipeline completado"
            message = f"Pipeline #{pipeline_id} completo."
            _notify(db, pipeline, subject, message)
            _send_email_notification(pipeline, subject, message, status_value="success")
        return

    if pipeline.pause_between_stages and next_stage.stage_order_index > 0:
        _transition(next_stage, "waiting_for_approval", db)
        pipeline.status = "waiting_for_approval"
        db.commit()
        _notify(
            db,
            pipeline,
            "Aprobacion requerida",
            f"Pipeline #{pipeline_id}: etapa '{next_stage.stage_name}' espera aprobacion.",
        )
        _send_email_notification(
            pipeline,
            "Aprobacion requerida",
            f"Pipeline #{pipeline_id}: etapa '{next_stage.stage_name}' espera aprobacion.",
            status_value="warning",
        )
    else:
        _launch_stage(next_stage, db)
        pipeline.status = "pending"
        db.commit()

def _get_active_stages(pipeline_id: int, db: Session):
    stages = (
        db.query(StageExecution)
        .filter(StageExecution.pipeline_id == pipeline_id)
        .order_by(StageExecution.stage_order_index, StageExecution.id.desc())
        .all()
    )
    seen = {}
    for stage in stages:
        if stage.stage_order_index not in seen:
            seen[stage.stage_order_index] = stage
    return list(seen.values())


def _notify(db: Session, pipeline: Pipeline, subject: str, message: str):
    if not pipeline.project:
        return
    notification = Notification(
        user_id=pipeline.project.user_id,
        subject=subject,
        message=message,
    )
    db.add(notification)
    db.commit()


def _send_email_notification(
    pipeline: Pipeline,
    subject: str,
    message: str,
    status_value: str = "info",
):
    user = getattr(pipeline.project, "user", None) if pipeline.project else None
    if not user or not getattr(user, "email", None):
        return

    headers = {"X-Internal-Token": INTERNAL_TOKEN}
    payload = {
        "to_email": user.email,
        "subject": subject,
        "message": message,
        "pipeline_id": pipeline.id,
        "status": status_value,
    }

    try:
        response = requests.post(EMAIL_NOTIFIER_URL, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
    except Exception as exc:
        print(f"[EmailNotifier] No se pudo enviar correo para pipeline {pipeline.id}: {exc}")


def launch_pipeline(
    db: Session,
    project_id: int,
    pipeline_id: int,
    user_id: int,
    stage_order: list,
    pause_between_stages: bool,
) -> dict:
    pipeline = _get_pipeline_owned(db, project_id, pipeline_id, user_id)

    if pipeline.status in ("pending", "running"):
        raise HTTPException(status_code=409, detail="Pipeline ya esta en ejecucion")

    _validate_stage_order(stage_order)

    resolved_stage_defs = []
    for stage_def in stage_order:
        tool = _get_tool(db, stage_def["tool_id"])
        resolved_stage_defs.append((stage_def, tool))

    created_stages = []
    for order_index, (stage_def, tool) in enumerate(resolved_stage_defs):
        stage_execution = StageExecution(
            pipeline_id=pipeline_id,
            stage_name=stage_def["stage_name"],
            stage_order_index=order_index,
            tool_id=tool.id,
            tool=tool.name,
            tool_version=stage_def.get("tool_version") or tool.version,
            params=stage_def["params"],
            status="pending",
        )
        db.add(stage_execution)
        created_stages.append(stage_execution)

    pipeline.status = "pending"
    pipeline.pause_between_stages = pause_between_stages
    pipeline.stage_order = [stage_def["stage_name"] for stage_def, _ in resolved_stage_defs]
    pipeline.started_at = datetime.now(timezone.utc)
    pipeline.updated_at = datetime.now(timezone.utc)
    db.commit()

    for stage_execution in created_stages:
        db.refresh(stage_execution)

    advance_pipeline(pipeline_id, db)

    return {
        "pipeline_id": pipeline_id,
        "status": pipeline.status,
        "stages": [
            {
                "id": stage_execution.id,
                "stage_name": stage_execution.stage_name,
                "tool_id": stage_execution.tool_id,
                "tool": stage_execution.tool,
                "status": stage_execution.status,
            }
            for stage_execution in created_stages
        ],
    }


def approve_stage(
    db: Session,
    pipeline_id: int,
    user_id: int,
    chosen_stage_execution_id: Optional[int] = None,
    new_params: Optional[dict] = None,
) -> dict:
    pipeline = get_pipeline_by_id_for_user(db, pipeline_id, user_id)

    if pipeline.status != "waiting_for_approval":
        raise HTTPException(
            status_code=409,
            detail=f"Pipeline no esta en waiting_for_approval (status={pipeline.status})",
        )

    waiting_stage = (
        db.query(StageExecution)
        .filter(
            StageExecution.pipeline_id == pipeline_id,
            StageExecution.status == "waiting_for_approval",
        )
        .order_by(StageExecution.id.desc())
        .first()
    )
    if not waiting_stage:
        raise HTTPException(status_code=404, detail="No hay etapa esperando aprobacion")

    if chosen_stage_execution_id:
        chosen = db.query(StageExecution).filter(
            StageExecution.id == chosen_stage_execution_id,
            StageExecution.pipeline_id == pipeline_id,
        ).first()
        if not chosen:
            raise HTTPException(status_code=404, detail="StageExecution elegida no encontrada")
        if chosen.status != "completed":
            raise HTTPException(
                status_code=409,
                detail="La ejecucion elegida debe estar en status=completed",
            )

    if new_params is not None:
        previous_stage_names = [
            stage.stage_name
            for stage in (
                db.query(StageExecution)
                .filter(
                    StageExecution.pipeline_id == pipeline_id,
                    StageExecution.stage_order_index < waiting_stage.stage_order_index,
                    StageExecution.status == "completed",
                )
                .order_by(StageExecution.stage_order_index.asc(), StageExecution.id.desc())
                .all()
            )
        ]
        _validate_stage_params_with_history(waiting_stage.stage_name, new_params, previous_stage_names)
        waiting_stage.params = new_params

    waiting_stage.status = "pending"
    pipeline.status = "pending"
    db.commit()
    _launch_stage(waiting_stage, db)

    return {"pipeline_id": pipeline_id, "status": pipeline.status}


def retry_stage_manual(
    db: Session,
    pipeline_id: int,
    stage_order_index: Optional[int],
    stage_execution_id: Optional[int],
    new_params: dict,
    new_tool_id: Optional[int],
    new_tool: Optional[str],
    user_id: int,
) -> dict:
    pipeline = get_pipeline_by_id_for_user(db, pipeline_id, user_id)

    if stage_execution_id is not None:
        current = (
            db.query(StageExecution)
            .filter(
                StageExecution.id == stage_execution_id,
                StageExecution.pipeline_id == pipeline_id,
            )
            .first()
        )
    elif stage_order_index is not None:
        current = (
            db.query(StageExecution)
            .filter(
                StageExecution.pipeline_id == pipeline_id,
                StageExecution.stage_order_index == stage_order_index,
            )
            .order_by(StageExecution.id.desc())
            .first()
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Debe indicar stage_execution_id o stage_order_index para relanzar una etapa",
        )

    if not current:
        raise HTTPException(status_code=404, detail="Stage no encontrada")
    if current.status not in {"completed", "failed"}:
        raise HTTPException(
            status_code=409,
            detail=f"Solo se pueden relanzar etapas completed o failed (status={current.status})",
        )

    retry_order_index = current.stage_order_index

    previous_stage_names = [
        stage.stage_name
        for stage in (
            db.query(StageExecution)
            .filter(
                StageExecution.pipeline_id == pipeline_id,
                StageExecution.stage_order_index < retry_order_index,
                StageExecution.status == "completed",
            )
            .order_by(StageExecution.stage_order_index.asc(), StageExecution.id.desc())
            .all()
        )
    ]

    _validate_stage_params_with_history(current.stage_name, new_params, previous_stage_names)

    resolved_tool = _get_tool(db, new_tool_id) if new_tool_id else None

    new_stage = StageExecution(
        pipeline_id=pipeline_id,
        stage_name=current.stage_name,
        stage_order_index=retry_order_index,
        tool_id=resolved_tool.id if resolved_tool else current.tool_id,
        tool=(resolved_tool.name if resolved_tool else new_tool or current.tool),
        tool_version=resolved_tool.version if resolved_tool else current.tool_version,
        params=new_params,
        status="pending",
        retry_count=current.retry_count + 1,
        retry_type="manual",
    )
    db.add(new_stage)

    current.status = "failed"
    current.error_message = "Reemplazada por retry manual del usuario"

    pipeline.status = "pending"
    db.commit()
    db.refresh(new_stage)

    _launch_stage(new_stage, db)

    return {
        "new_stage_execution_id": new_stage.id,
        "stage_name": current.stage_name,
        "tool_id": new_stage.tool_id,
        "tool": new_stage.tool,
        "status": new_stage.status,
    }

def on_stage_started(db: Session, stage_execution_id: int, celery_task_id: str):
    stage = _get_stage(db, stage_execution_id)

    stage.celery_task_id = celery_task_id
    stage.status = "running"
    stage.started_at = datetime.now(timezone.utc)
    stage.updated_at = datetime.now(timezone.utc)

    pipeline = stage.pipeline
    if pipeline.status != "running":
        pipeline.status = "running"
        pipeline.updated_at = datetime.now(timezone.utc)

    db.commit()

def on_stage_completed(db: Session, stage_execution_id: int, output_files: list, metadata: dict):
    stage = _get_stage(db, stage_execution_id)
    if stage.status == "completed":
        stage.output_files = output_files or stage.output_files
        stage.output_metadata = metadata or stage.output_metadata
        if stage.stage_name == "docking":
            _ensure_docking_final_model(stage, db)
        db.commit()
        advance_pipeline(stage.pipeline_id, db)
        return
    _transition(stage, "completed", db)
    stage.output_files = output_files
    stage.output_metadata = metadata
    stage.finished_at = datetime.now(timezone.utc)
    if stage.stage_name == "docking":
        _ensure_docking_final_model(stage, db)
    db.commit()
    advance_pipeline(stage.pipeline_id, db)


def on_stage_failed(
    db: Session,
    stage_execution_id: int,
    error: str,
    retry_type: str = "logical",
):
    stage = _get_stage(db, stage_execution_id)
    normalized_error = (error or "").lower()
    if any(marker in normalized_error for marker in NON_RETRYABLE_RESOURCE_ERRORS):
        retry_type = "logical"

    if stage.retry_count < MAX_RETRIES and retry_type == "technical":
        stage.status = "retrying"
        stage.retry_count += 1
        stage.retry_type = retry_type
        stage.updated_at = datetime.now(timezone.utc)
        db.commit()

        new_stage = StageExecution(
            pipeline_id=stage.pipeline_id,
            stage_name=stage.stage_name,
            stage_order_index=stage.stage_order_index,
            tool_id=stage.tool_id,
            tool=stage.tool,
            tool_version=stage.tool_version,
            params=stage.params,
            status="pending",
            retry_count=stage.retry_count,
            retry_type="technical",
        )
        db.add(new_stage)
        stage.status = "failed"
        stage.error_message = error
        db.commit()
        db.refresh(new_stage)
        _launch_stage(new_stage, db)
    else:
        _transition(stage, "failed", db)
        stage.error_message = error
        stage.finished_at = datetime.now(timezone.utc)
        db.commit()

        pipeline = db.query(Pipeline).filter(Pipeline.id == stage.pipeline_id).first()
        if pipeline:
            pipeline.status = "failed"
            pipeline.finished_at = datetime.now(timezone.utc)
            db.commit()
            subject = "Pipeline fallido"
            message = f"Etapa '{stage.stage_name}' fallo: {error}"
            _notify(db, pipeline, subject, message)
            _send_email_notification(pipeline, subject, message, status_value="error")


def _get_stage(db: Session, stage_execution_id: int) -> StageExecution:
    stage = db.query(StageExecution).filter(StageExecution.id == stage_execution_id).first()
    if not stage:
        raise HTTPException(status_code=404, detail="StageExecution no encontrada")
    return stage


def _get_pipeline_owned(db: Session, project_id: int, pipeline_id: int, user_id: int) -> Pipeline:
    return get_pipeline_for_user(db, project_id, pipeline_id, user_id)


class PipelineWatchdog:
    """
    Escucha worker-heartbeat de Celery Events.
    Si un worker desaparece (sin heartbeat por WORKER_TIMEOUT_SECONDS),
    marca sus tareas como failed y activa retry si corresponde.

    Corre en un thread daemon separado dentro del proceso API.
    """

    def __init__(self, db_factory):
        self.db_factory = db_factory
        self.worker_last_seen: dict[str, datetime] = {}
        self._running = False
        self._thread = None

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def _run(self):
        import time

        retry_delays = [5, 10, 15, 30, 30, 30, 60, 60, 60, 60]

        for attempt, delay in enumerate(retry_delays, start=1):
            try:
                print(f"[Watchdog] Intento {attempt}: conectando al broker...")
                with celery_app.connection_for_read() as conn:
                    conn.ensure_connection(max_retries=1, timeout=5)
                    print("[Watchdog] Conectado. Escuchando eventos Celery...")
                    receiver = celery_app.events.Receiver(
                        conn,
                        handlers={
                            "worker-heartbeat": self._on_worker_heartbeat,
                            "task-failed": self._on_task_failed,
                            "task-succeeded": self._on_task_succeeded,
                            "*": self._on_any,
                        },
                    )
                    receiver.capture(limit=None, timeout=None, wakeup=True)
                    return
            except Exception as exc:
                print(f"[Watchdog] Error de conexion (intento {attempt}): {exc}")
                if not self._running:
                    print("[Watchdog] Detenido externamente.")
                    return
                print(f"[Watchdog] Reintentando en {delay}s...")
                time.sleep(delay)

        print("[Watchdog] No se pudo conectar al broker tras todos los intentos. Watchdog inactivo.")

    def _on_worker_heartbeat(self, event):
        hostname = event.get("hostname", "unknown")
        self.worker_last_seen[hostname] = datetime.now(timezone.utc)
        self._check_dead_workers()

    def _on_task_failed(self, event):
        pass

    def _on_task_succeeded(self, event):
        pass

    def _on_any(self, event):
        pass

    def _check_dead_workers(self):
        now = datetime.now(timezone.utc)
        timeout = timedelta(seconds=WORKER_TIMEOUT_SECONDS)
        dead = [
            hostname
            for hostname, last_seen in self.worker_last_seen.items()
            if now - last_seen > timeout
        ]
        if not dead:
            return

        db = self.db_factory()
        try:
            for hostname in dead:
                del self.worker_last_seen[hostname]
                running_stages = db.query(StageExecution).filter(StageExecution.status == "running").all()
                for stage in running_stages:
                    reference_time = stage.updated_at or stage.started_at
                    if reference_time and now - reference_time > timeout:
                        print(f"[Watchdog] Worker caido detectado. Stage {stage.id} marcada para retry.")
                        on_stage_failed(
                            db,
                            stage.id,
                            error=f"Worker caido (hostname={hostname})",
                            retry_type="technical",
                        )
        finally:
            db.close()


_watchdog: Optional[PipelineWatchdog] = None


def get_watchdog(db_factory) -> PipelineWatchdog:
    global _watchdog
    if _watchdog is None:
        _watchdog = PipelineWatchdog(db_factory)
    return _watchdog
