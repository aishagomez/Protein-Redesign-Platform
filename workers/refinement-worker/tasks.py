import os
import shutil
import subprocess
import time
import traceback
from pathlib import Path

import requests
from billiard.exceptions import SoftTimeLimitExceeded
from celery_app import celery_app
from types import SimpleNamespace

ORCHESTRATOR_URL = os.environ.get("ORCHESTRATOR_URL", "http://api:8000")
INTERNAL_TOKEN = os.environ.get("INTERNAL_TOKEN", "123")
WORK_ROOT = Path(os.environ.get("WORK_ROOT", "/tmp/pipeline_runs"))


def _report(endpoint: str, payload: dict):
    url = f"{ORCHESTRATOR_URL}{endpoint}"
    headers = {"X-Internal-Token": INTERNAL_TOKEN}
    for attempt in range(3):
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            return
        except Exception as exc:
            print(f"[Refinement Worker] Intento {attempt + 1}/3 - error reportando a {url}: {exc}")
            if attempt < 2:
                time.sleep(2 ** attempt)


def _as_namespace(value: dict, label: str) -> SimpleNamespace:
    if not isinstance(value, dict):
        raise ValueError(f"Contrato invalido: falta '{label}'")
    return SimpleNamespace(**value)


def _load_tool_contract(tool_contract: dict):
    if not isinstance(tool_contract, dict):
        raise ValueError("El worker requiere tool_contract enviado por la API")
    tool = _as_namespace(tool_contract.get("tool"), "tool")
    runtime = _as_namespace(tool_contract.get("runtime"), "runtime")
    parameters = [
        _as_namespace(parameter, "parameter")
        for parameter in tool_contract.get("parameters", [])
    ]
    return tool, runtime, parameters


def _stage_workdir(stage_execution_id: int) -> Path:
    workdir = WORK_ROOT / f"stage_{stage_execution_id}"
    workdir.mkdir(parents=True, exist_ok=True)
    return workdir


def _copy_into_workspace(source_path: Path, destination_root: Path) -> Path:
    destination_root.mkdir(parents=True, exist_ok=True)
    destination_path = destination_root / source_path.name

    if source_path.is_dir():
        if destination_path.exists():
            shutil.rmtree(destination_path)
        shutil.copytree(source_path, destination_path)
        return destination_path

    shutil.copy2(source_path, destination_path)
    return destination_path


def _materialize_input(input_reference: str, workdir: Path) -> str:
    """
    Copia el input a un workspace estable del stage.
    Esto nos permite:
    - evitar mounts frágiles desde rutas vistas solo por el worker
    - preparar el terreno para storage remoto (ej. S3) en el futuro
    """
    source_path = Path(input_reference)
    if not source_path.exists():
        raise FileNotFoundError(f"No existe el archivo o directorio de entrada: {input_reference}")

    materialized = _copy_into_workspace(source_path, workdir / "inputs")
    return str(materialized)


def _is_missing_value(value) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    return False


def _count_pdb_residues(pdb_path: str) -> int:
    residues = set()
    with open(pdb_path, "r", encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            if not line.startswith(("ATOM", "HETATM")):
                continue
            chain_id = line[21].strip() or "_"
            residue_seq = line[22:26].strip()
            insertion_code = line[26].strip() or "_"
            if not residue_seq:
                continue
            residues.add((chain_id, residue_seq, insertion_code))
    return len(residues)


def _hydrate_atom_refine_params(normalized: dict):
    input_path = normalized.get("input")
    if _is_missing_value(normalized.get("target_id")) and input_path:
        normalized["target_id"] = Path(str(input_path)).stem

    if _is_missing_value(normalized.get("seq_length")) and input_path:
        residue_count = _count_pdb_residues(str(input_path))
        if residue_count > 0:
            normalized["seq_length"] = residue_count


def _normalize_runtime_params(tool_name: str, stage_name: str, params: dict, workdir: Path) -> dict:
    normalized = dict(params)
    requested_output_dir = normalized.get("output_dir") or str(workdir / "published_output")
    Path(requested_output_dir).mkdir(parents=True, exist_ok=True)
    runtime_output_dir = workdir / "runtime_output"
    if runtime_output_dir.exists():
        shutil.rmtree(runtime_output_dir)
    runtime_output_dir.mkdir(parents=True, exist_ok=True)

    normalized["output_dir"] = requested_output_dir
    normalized["runtime_output_dir"] = str(runtime_output_dir)

    if stage_name == "refinement" and "input" not in normalized:
        input_path = normalized.get("input_pdb_path_receptor") or normalized.get("input_pdb")
        if input_path:
            normalized["input"] = input_path

    input_reference = normalized.get("input")
    if input_reference:
        normalized["input"] = _materialize_input(str(input_reference), workdir)

    if tool_name == "atom_refine":
        _hydrate_atom_refine_params(normalized)

    return normalized


def _validate_inputs(runtime_params: dict):
    input_path = runtime_params.get("input")
    if not input_path:
        raise ValueError("No se pudo resolver el argumento posicional 'input' para la herramienta")
    if not Path(input_path).exists():
        raise FileNotFoundError(f"No existe el archivo de entrada: {input_path}")

    output_dir = runtime_params.get("output_dir")
    if not output_dir:
        raise ValueError("No se pudo resolver el directorio de salida")


def _validate_tool_specific_inputs(tool_name: str, runtime_params: dict):
    if tool_name != "atom_refine":
        return

    missing = []
    if _is_missing_value(runtime_params.get("target_id")):
        missing.append("target_id")
    if _is_missing_value(runtime_params.get("seq_length")):
        missing.append("seq_length")
    if missing:
        raise ValueError(f"ATOMRefine requiere parametros no vacios: {missing}")


def _build_template_context(runtime_params: dict) -> dict:
    context = dict(runtime_params)
    for key, value in runtime_params.items():
        if not isinstance(value, str):
            continue
        path = Path(value)
        context[f"{key}_basename"] = path.name
        context[f"{key}_stem"] = path.stem
        context[f"{key}_dirname"] = str(path.parent)
    return context


def _render_string(template: str, context: dict) -> str:
    try:
        return template.format(**context)
    except KeyError as exc:
        missing = exc.args[0]
        raise ValueError(f"Falta la variable '{missing}' para renderizar el runtime")


def _resolve_mounts(mount_specs: list[dict], runtime_params: dict, context: dict) -> tuple[list[str], dict]:
    docker_args = []
    resolved_context = dict(context)

    for mount in mount_specs:
        alias = mount.get("name")
        source_param = mount.get("source_param")
        target_template = mount.get("target")
        read_only = bool(mount.get("read_only", False))

        if not alias or not source_param or not target_template:
            raise ValueError("Cada mount del runtime debe tener name, source_param y target")

        source_value = runtime_params.get(source_param)
        if not source_value:
            raise ValueError(f"Falta el param requerido para mount '{alias}': {source_param}")

        source_path = Path(source_value)
        if not source_path.exists():
            raise FileNotFoundError(f"No existe la ruta para mount '{alias}': {source_value}")

        target_path = _render_string(target_template, resolved_context)
        volume = f"{source_path}:{target_path}"
        if read_only:
            volume += ":ro"
        docker_args.extend(["-v", volume])
        resolved_context[f"{alias}_path"] = target_path

    return docker_args, resolved_context


def _resolve_env(env_spec: dict, context: dict) -> list[str]:
    env_args = []
    for key, value in env_spec.items():
        env_args.extend(["-e", f"{key}={_render_string(str(value), context)}"])
    return env_args


def _render_command(command_template: list[str], context: dict) -> list[str]:
    if not command_template:
        raise ValueError("El runtime no tiene command_template configurado")
    return [_render_string(str(arg), context) for arg in command_template]


def _coerce_parameter_value(parameter: SimpleNamespace, runtime_params: dict):
    value = runtime_params.get(parameter.name)
    if value is None:
        value = parameter.default_value
    return value


def _append_parameter_flags(
    command: list[str],
    parameters: list[SimpleNamespace],
    runtime_params: dict,
) -> list[str]:
    rendered = list(command)
    for parameter in parameters:
        if not parameter.flag:
            continue

        value = _coerce_parameter_value(parameter, runtime_params)
        if value is None:
            continue

        if parameter.data_type == "bool":
            normalized = value if isinstance(value, bool) else str(value).strip().lower() in {"1", "true", "yes"}
            if normalized:
                rendered.append(parameter.flag)
            continue

        rendered.extend([parameter.flag, str(value)])

    return rendered


def _collect_outputs(output_dir: str) -> list[str]:
    base_path = Path(output_dir)
    if not base_path.exists():
        return []
    return sorted(str(path) for path in base_path.rglob("*") if path.is_file())


def _publish_outputs(runtime_output_dir: str, published_output_dir: str):
    source_root = Path(runtime_output_dir)
    target_root = Path(published_output_dir)
    target_root.mkdir(parents=True, exist_ok=True)

    if not source_root.exists():
        return

    for source in source_root.rglob("*"):
        if not source.is_file():
            continue
        relative_path = source.relative_to(source_root)
        destination = target_root / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def _execute_docker_runtime(runtime: SimpleNamespace, runtime_params: dict, workdir: Path, stage_execution_id: int) -> subprocess.CompletedProcess:
    if not runtime.image:
        raise ValueError("El runtime docker requiere image")

    template_context = _build_template_context(runtime_params)
    mount_args, resolved_context = _resolve_mounts(runtime.mounts or [], runtime_params, template_context)
    env_args = _resolve_env(runtime.env or {}, resolved_context)
    command = _render_command(runtime.command_template or [], resolved_context)
    command = _append_parameter_flags(command, runtime_params["_tool_parameters"], runtime_params)

    docker_command = ["docker", "run", "--rm", "--label", f"platform.stage_execution_id={stage_execution_id}"]
    parent_container = os.environ.get("HOSTNAME")
    if parent_container:
        docker_command.extend(["--volumes-from", parent_container])

    resources = runtime.resources or {}
    if resources.get("memory"):
        docker_command.append(f"--memory={resources['memory']}")
    if resources.get("cpus"):
        docker_command.append(f"--cpus={resources['cpus']}")
    if runtime.workdir:
        docker_command.extend(["-w", runtime.workdir])

    docker_command.extend(env_args)
    docker_command.extend(mount_args)
    docker_command.append(runtime.image)
    docker_command.extend(command)

    print(f"  docker command     : {' '.join(docker_command)}")

    return subprocess.run(
        docker_command,
        cwd=str(workdir),
        capture_output=True,
        text=True,
        check=True,
    )


def _execute(stage_execution_id: int, stage_name: str, tool_id: int, params: dict, tool_contract: dict) -> dict:
    tool, runtime, parameters = _load_tool_contract(tool_contract)
    if tool_id is not None and tool.id != tool_id:
        raise ValueError(f"Contrato de herramienta inconsistente: esperado id={tool_id}, recibido id={tool.id}")
    workdir = _stage_workdir(stage_execution_id)
    runtime_params = _normalize_runtime_params(tool.name, stage_name, params, workdir)
    runtime_params["_tool_parameters"] = parameters
    _validate_inputs(runtime_params)
    _validate_tool_specific_inputs(tool.name, runtime_params)

    print("=" * 60)
    print("[REFINEMENT] Ejecutando runtime declarativo")
    print(f"  stage_execution_id : {stage_execution_id}")
    print(f"  tool_id            : {tool.id}")
    print(f"  tool_name          : {tool.name}")
    print(f"  runtime_mode       : {runtime.mode}")
    print(f"  runtime_image      : {runtime.image}")
    print(f"  workdir            : {workdir}")
    print(f"  input_path         : {runtime_params['input']}")
    print(f"  runtime_output_dir : {runtime_params['runtime_output_dir']}")
    print(f"  output_dir         : {runtime_params['output_dir']}")

    if runtime.mode != "docker":
        raise ValueError(f"El refinement-worker solo soporta runtime mode='docker' por ahora, no '{runtime.mode}'")

    completed = _execute_docker_runtime(runtime, runtime_params, workdir, stage_execution_id)
    _publish_outputs(runtime_params["runtime_output_dir"], runtime_params["output_dir"])

    outputs = _collect_outputs(runtime_params["output_dir"])
    if not outputs:
        raise RuntimeError(
            f"La herramienta '{tool.name}' termino sin archivos de salida en {runtime_params['output_dir']}"
        )

    print(f"  outputs detectados : {outputs}")
    print("[REFINEMENT] Etapa completada exitosamente")
    print("=" * 60)

    return {
        "output_files": outputs,
        "metadata": {
            "tool_id": tool.id,
            "tool": tool.name,
            "runtime_mode": runtime.mode,
            "image": runtime.image,
            "workdir": str(workdir),
            "output_dir": runtime_params["output_dir"],
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        },
    }


@celery_app.task(bind=True, name="tasks.run_stage", queue="refinement", acks_late=True)
def run_stage(
    self,
    stage_execution_id: int,
    stage_name: str,
    tool_id: int | None,
    tool: str,
    params: dict,
    tool_contract: dict,
):
    print("\n[Refinement Worker] -- Tarea recibida ------------------")
    print(f"  stage_execution_id : {stage_execution_id}")
    print(f"  stage_name         : {stage_name}")
    print(f"  tool_id            : {tool_id}")
    print(f"  tool               : {tool}")
    print(f"  celery_task_id     : {self.request.id}")
    print(f"  params             : {params}")
    print("-------------------------------------------------------\n")

    _report(
        f"/internal/stages/{stage_execution_id}/started",
        {"celery_task_id": self.request.id},
    )

    try:
        if tool_id is None:
            raise ValueError("El worker requiere tool_id para resolver la herramienta real")

        result = _execute(stage_execution_id, stage_name, tool_id, params, tool_contract)

        _report(
            f"/internal/stages/{stage_execution_id}/completed",
            {
                "output_files": result["output_files"],
                "metadata": result["metadata"],
            },
        )

        print(f"[Refinement Worker] stage_execution_id={stage_execution_id} -> completed\n")
        return {"status": "completed", "stage_execution_id": stage_execution_id}

    except SoftTimeLimitExceeded:
        message = "Soft time limit excedido en refinement"
        print(f"[Refinement Worker] TIMEOUT: {message}")
        _report(
            f"/internal/stages/{stage_execution_id}/failed",
            {"error": message, "retry_type": "technical"},
        )
        raise

    except subprocess.CalledProcessError as exc:
        message = (
            f"Fallo ejecutando Docker: returncode={exc.returncode}\n"
            f"stderr: {exc.stderr}"
        )
        print(f"[Refinement Worker] ERROR: {message}")
        _report(
            f"/internal/stages/{stage_execution_id}/failed",
            {
                "error": message,
                "traceback": traceback.format_exc(),
                "retry_type": "logical",
            },
        )
        raise

    except Exception as exc:
        traceback_text = traceback.format_exc()
        message = str(exc)
        print(f"[Refinement Worker] ERROR: {message}\n{traceback_text}")
        _report(
            f"/internal/stages/{stage_execution_id}/failed",
            {"error": message, "traceback": traceback_text, "retry_type": "logical"},
        )
        raise
