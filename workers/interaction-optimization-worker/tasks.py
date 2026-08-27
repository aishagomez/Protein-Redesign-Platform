import os
import shutil
import subprocess
import time
import traceback
import zipfile
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
            print(f"[Interaction Optimization Worker] Attempt {attempt + 1}/3 - error reporting to {url}: {exc}")
            if attempt < 2:
                time.sleep(2 ** attempt)


def _as_namespace(value: dict, label: str) -> SimpleNamespace:
    if not isinstance(value, dict):
        raise ValueError(f"Invalid contract: missing '{label}'")
    return SimpleNamespace(**value)


def _load_tool_contract(tool_contract: dict):
    if not isinstance(tool_contract, dict):
        raise ValueError("Worker requires tool_contract sent by the API")
    tool = _as_namespace(tool_contract.get("tool"), "tool")
    runtime = _as_namespace(tool_contract.get("runtime"), "runtime")
    parameters = [
        _as_namespace(parameter, "parameter")
        for parameter in tool_contract.get("parameters", [])
    ]
    return tool, runtime, parameters


def _stage_workdir(stage_execution_id: int) -> Path:
    workdir = WORK_ROOT / f"stage_{stage_execution_id}"
    if workdir.exists():
        shutil.rmtree(workdir, ignore_errors=True)
    workdir.mkdir(parents=True, exist_ok=True)
    return workdir


def _cleanup_stage_workdir(stage_execution_id: int):
    workdir = WORK_ROOT / f"stage_{stage_execution_id}"
    if workdir.exists():
        shutil.rmtree(workdir, ignore_errors=True)


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


def _materialize_scenario(scenario_reference: str, workdir: Path) -> Path:
    source_path = Path(scenario_reference)
    if not source_path.exists():
        raise FileNotFoundError(f"Scenario path does not exist: {scenario_reference}")
    if source_path.is_dir():
        return _copy_into_workspace(source_path, workdir / "scenarios")
    print(f"Scenario path is a file: {source_path}")
    if source_path.is_file() and source_path.suffix.lower() == ".zip":
        extraction_root = workdir / "scenarios" / source_path.stem
        extraction_root.mkdir(parents=True, exist_ok=True)
        print(f"Extracting scenario zip {source_path} to {extraction_root}!!!!!!!!!!!!!!!!!!!!!!!!!")
        with zipfile.ZipFile(source_path, "r") as archive:
            archive.extractall(extraction_root)

        child_directories = sorted(path for path in extraction_root.iterdir() if path.is_dir())
        child_files = sorted(path for path in extraction_root.iterdir() if path.is_file())
        print(child_files)
        if len(child_directories) == 1 and not child_files:
            return child_directories[0]
        return _find_scenario_directory(extraction_root)

    raise ValueError(
        f"Scenario path must be a directory or .zip file: {scenario_reference}"
    )


def _find_scenario_directory(directory: Path) -> Path:
    """Return the deepest extracted directory that looks like a scenario folder."""

    def _looks_like_scenario_dir(path: Path) -> bool:
        if not path.is_dir():
            return False
        file_names = {child.name.lower() for child in path.iterdir() if child.is_file()}
        has_face = any(name.startswith("face") and name.endswith(".txt") for name in file_names)
        has_msa = any(
            (name.endswith(".tsv") and "msa" in name)
            or (name.endswith(".txt") and ("msa" in name or "alignment" in name))
            for name in file_names
        )
        return has_face and has_msa

    normalized = directory
    while True:
        entries = sorted(normalized.iterdir())
        subdirs = [entry for entry in entries if entry.is_dir()]
        files = [entry for entry in entries if entry.is_file()]
        if len(subdirs) == 1 and not files:
            normalized = subdirs[0]
            continue
        break

    if _looks_like_scenario_dir(normalized):
        return normalized

    for subdir in sorted(directory.rglob("*")):
        if _looks_like_scenario_dir(subdir):
            return subdir

    return directory


def _coerce_bool_string(value, default: str) -> str:
    if value is None:
        return default
    if isinstance(value, bool):
        return "True" if value else "False"
    normalized = str(value).strip().lower()
    return "True" if normalized in {"1", "true", "yes"} else "False"


def _coerce_csv_string(value, default: str) -> str:
    if value is None:
        return default
    if isinstance(value, (list, tuple)):
        return ",".join(str(item) for item in value)
    return str(value)


def _detect_default_pdbfile(scenario_dir: Path) -> str:
    pdb_files = sorted(path for path in scenario_dir.iterdir() if path.is_file() and path.suffix.lower() == ".pdb")
    if not pdb_files:
        raise ValueError(f"No .pdb file found inside scenario directory: {scenario_dir}")
    preferred = [path for path in pdb_files if "final_model" in path.stem.lower()]
    return (preferred[0] if preferred else pdb_files[0]).name


def _copy_pdb_into_scenario(source: Path, scenario_dir: Path) -> str:
    if not source.exists() or not source.is_file() or source.suffix.lower() != ".pdb":
        raise FileNotFoundError(f"PDB source does not exist: {source}")
    target = scenario_dir / source.name
    if source.resolve() != target.resolve():
        shutil.copy2(source, target)
    return target.name


def _resolve_interaction_optimization_pdbfile(normalized: dict, scenario_dir: Path) -> str:
    pdbfile_param = normalized.get("pdbfile")
    if pdbfile_param:
        explicit_path = Path(str(pdbfile_param))
        if explicit_path.exists():
            return _copy_pdb_into_scenario(explicit_path, scenario_dir)

        scenario_relative = scenario_dir / str(pdbfile_param)
        if scenario_relative.exists() and scenario_relative.is_file():
            return scenario_relative.name

    for key in ("complex_pdb_path", "prepared_complex_pdb_path", "dummy_selected_complex_pdb_path"):
        candidate = normalized.get(key)
        if candidate and Path(str(candidate)).exists():
            copied_name = _copy_pdb_into_scenario(Path(str(candidate)), scenario_dir)
            print(f"Using previous-stage PDB from {key}: {candidate} -> {scenario_dir / copied_name}")
            return copied_name

    return _detect_default_pdbfile(scenario_dir)


def _detect_default_file(scenario_dir: Path, pattern: str, fallback: str) -> str:
    matches = sorted(path.name for path in scenario_dir.rglob(pattern) if path.is_file())
    if matches:
        return matches[0]

    extra_matches = sorted(
        path.name
        for path in scenario_dir.rglob("*")
        if path.is_file()
        and path.suffix.lower() in {".tsv", ".txt"}
        and ("msa" in path.name.lower() or "alignment" in path.name.lower())
    )
    return extra_matches[0] if extra_matches else fallback


def _detect_face2_file(scenario_dir: Path, face1_file_name: str) -> str:
    candidates = sorted(path.name for path in scenario_dir.glob("face*.txt") if path.is_file())
    for candidate in candidates:
        if candidate != face1_file_name:
            return candidate
    return "faceC.txt"


def _normalize_runtime_params(stage_name: str, params: dict, workdir: Path) -> dict:
    normalized = dict(params)
    requested_output_dir = normalized.get("output_dir") or str(workdir / "published_output")
    Path(requested_output_dir).mkdir(parents=True, exist_ok=True)
    runtime_output_dir = workdir / "runtime_output"
    if runtime_output_dir.exists():
        shutil.rmtree(runtime_output_dir)
    runtime_output_dir.mkdir(parents=True, exist_ok=True)

    normalized["output_dir"] = requested_output_dir
    normalized["runtime_output_dir"] = str(runtime_output_dir)

    if stage_name == "interaction_optimization":
        scenario_reference = (
            normalized.get("scenario_path")
            or normalized.get("input_scenario_path")
            or normalized.get("scenario_dir")
        )
        if not scenario_reference:
            raise ValueError("Interaction optimization requires 'scenario_path' or equivalent input directory")

        materialized_scenario = _materialize_scenario(str(scenario_reference), workdir)
        scenario_name = normalized.get("scenario_name") or materialized_scenario.name

        normalized["scenario_path"] = str(materialized_scenario)
        normalized["scenario_name"] = scenario_name
        normalized["scenario_root"] = str(materialized_scenario.parent)
        normalized["algorithm"] = str(normalized.get("algorithm") or "sea")
        
        normalized["pdbfile"] = _resolve_interaction_optimization_pdbfile(normalized, materialized_scenario)
        
        normalized["partners"] = str(normalized.get("partners") or "")
        normalized["ligand_chain"] = str(normalized.get("ligand_chain") or "")
        normalized["gen"] = int(normalized.get("gen", 5))
        normalized["popsize"] = int(normalized.get("popsize", 5))
        normalized["mutp"] = normalized.get("mutp", 1)
        normalized["fitness_idxs"] = _coerce_csv_string(normalized.get("fitness_idxs"), "2,3")
        normalized["fitness_weights"] = _coerce_csv_string(normalized.get("fitness_weights"), "-1,1")
        normalized["checkpoint"] = _coerce_bool_string(normalized.get("checkpoint"), "False")
        normalized["checks"] = int(normalized.get("checks", 2))
        normalized["mobj"] = _coerce_bool_string(normalized.get("mobj"), "False")
        normalized["randomseed"] = int(normalized.get("randomseed", 15))
        normalized["face1_file_name"] = str(
            normalized.get("face1_file_name") or _detect_default_file(materialized_scenario, "face*.txt", "faceA.txt")
        )
        normalized["face2_file_name"] = str(
            normalized.get("face2_file_name") or _detect_face2_file(materialized_scenario, normalized["face1_file_name"])
        )
        normalized["msa_matrix"] = str(
            normalized.get("msa_matrix") or _detect_default_file(materialized_scenario, "MSA*.tsv", "MSA_matrix.tsv")
        )

    return normalized


def _validate_inputs(runtime_params: dict):
    scenario_path = runtime_params.get("scenario_path")
    if not scenario_path:
        raise ValueError("Could not resolve 'scenario_path' for interaction optimization")
    if not Path(scenario_path).exists():
        raise FileNotFoundError(f"Scenario directory not found: {scenario_path}")

    if not runtime_params.get("partners"):
        raise ValueError("Interaction optimization requires 'partners'")
    if not runtime_params.get("ligand_chain"):
        raise ValueError("Interaction optimization requires 'ligand_chain'")


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
        raise ValueError(f"Missing runtime variable '{exc.args[0]}'")


def _resolve_mounts(mount_specs: list[dict], runtime_params: dict, context: dict) -> tuple[list[str], dict]:
    docker_args = []
    resolved_context = dict(context)

    for mount in mount_specs:
        alias = mount.get("name")
        source_param = mount.get("source_param")
        target_template = mount.get("target")
        read_only = bool(mount.get("read_only", False))

        if not alias or not source_param or not target_template:
            raise ValueError("Each mount requires name, source_param and target")

        source_value = runtime_params.get(source_param)
        if not source_value:
            raise ValueError(f"Missing param for mount '{alias}': {source_param}")

        source_path = Path(source_value)
        if not source_path.exists():
            raise FileNotFoundError(f"Mount source does not exist for '{alias}': {source_value}")

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
        raise ValueError("Runtime has no command_template configured")
    return [_render_string(str(arg), context) for arg in command_template]


def _coerce_parameter_value(parameter: SimpleNamespace, runtime_params: dict):
    value = runtime_params.get(parameter.name)
    if value is None:
        value = parameter.default_value
    return value


def _append_parameter_flags(command: list[str], parameters: list[SimpleNamespace], runtime_params: dict) -> list[str]:
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
        raise ValueError("Docker runtime requires an image")

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
        raise ValueError(f"Inconsistent tool contract: expected id={tool_id}, received id={tool.id}")
    workdir = _stage_workdir(stage_execution_id)
    runtime_params = _normalize_runtime_params(stage_name, params, workdir)
    runtime_params["_tool_parameters"] = parameters
    _validate_inputs(runtime_params)

    print("=" * 60)
    print("[INTERACTION OPTIMIZATION] Executing declarative runtime")
    print(f"  stage_execution_id : {stage_execution_id}")
    print(f"  tool_id            : {tool.id}")
    print(f"  tool_name          : {tool.name}")
    print(f"  runtime_mode       : {runtime.mode}")
    print(f"  runtime_image      : {runtime.image}")
    print(f"  workdir            : {workdir}")
    print(f"  scenario_path      : {runtime_params['scenario_path']}")
    print(f"  scenario_name      : {runtime_params['scenario_name']}")
    print(f"  runtime_output_dir : {runtime_params['runtime_output_dir']}")
    print(f"  output_dir         : {runtime_params['output_dir']}")

    if runtime.mode != "docker":
        raise ValueError(f"Interaction optimization worker only supports runtime mode='docker' for now, not '{runtime.mode}'")

    completed = _execute_docker_runtime(runtime, runtime_params, workdir, stage_execution_id)
    _publish_outputs(runtime_params["runtime_output_dir"], runtime_params["output_dir"])

    outputs = _collect_outputs(runtime_params["output_dir"])
    if not outputs:
        raise RuntimeError(
            f"Tool '{tool.name}' finished without output files in {runtime_params['output_dir']}"
        )

    return {
        "output_files": outputs,
        "metadata": {
            "tool_id": tool.id,
            "tool": tool.name,
            "runtime_mode": runtime.mode,
            "image": runtime.image,
            "workdir": str(workdir),
            "scenario_path": runtime_params["scenario_path"],
            "scenario_name": runtime_params["scenario_name"],
            "output_dir": runtime_params["output_dir"],
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        },
    }


def _is_resource_exhaustion(message: str) -> bool:
    normalized = (message or "").lower()
    markers = [
        "no space left on device",
        "disk full",
        "not enough space",
        "errno 28",
        "returncode=137",
        "killed",
        "cannot allocate memory",
        "out of memory",
    ]
    return any(marker in normalized for marker in markers)


@celery_app.task(bind=True, name="tasks.run_stage", queue="interaction_optimization", acks_late=True)
def run_stage(
    self,
    stage_execution_id: int,
    stage_name: str,
    tool_id: int | None,
    tool: str,
    params: dict,
    tool_contract: dict,
):
    print("\n[Interaction Optimization Worker] -- Task received ------------------")
    print(f"  stage_execution_id : {stage_execution_id}")
    print(f"  stage_name         : {stage_name}")
    print(f"  tool_id            : {tool_id}")
    print(f"  tool               : {tool}")
    print(f"  celery_task_id     : {self.request.id}")
    print(f"  params             : {params}")
    print("-----------------------------------------------------\n")

    _report(f"/internal/stages/{stage_execution_id}/started", {"celery_task_id": self.request.id})

    try:
        if tool_id is None:
            raise ValueError("Worker requires tool_id to resolve the real tool")

        result = _execute(stage_execution_id, stage_name, tool_id, params, tool_contract)

        _report(
            f"/internal/stages/{stage_execution_id}/completed",
            {"output_files": result["output_files"], "metadata": result["metadata"]},
        )

        print(f"[Interaction Optimization Worker] stage_execution_id={stage_execution_id} -> completed\n")
        return {"status": "completed", "stage_execution_id": stage_execution_id}

    except SoftTimeLimitExceeded:
        message = "Soft time limit exceeded in interaction optimization"
        print(f"[Interaction Optimization Worker] TIMEOUT: {message}")
        _report(f"/internal/stages/{stage_execution_id}/failed", {"error": message, "retry_type": "technical"})
        raise

    except subprocess.CalledProcessError as exc:
        message = f"Docker execution failed: returncode={exc.returncode}\nstderr: {exc.stderr}"
        print(f"[Interaction Optimization Worker] ERROR: {message}")
        retry_type = "logical" if _is_resource_exhaustion(message) else "logical"
        _report(
            f"/internal/stages/{stage_execution_id}/failed",
            {"error": message, "traceback": traceback.format_exc(), "retry_type": retry_type},
        )
        raise

    except Exception as exc:
        traceback_text = traceback.format_exc()
        message = str(exc)
        print(f"[Interaction Optimization Worker] ERROR: {message}\n{traceback_text}")
        retry_type = "logical" if _is_resource_exhaustion(message) else "logical"
        _report(
            f"/internal/stages/{stage_execution_id}/failed",
            {"error": message, "traceback": traceback_text, "retry_type": retry_type},
        )
        raise
'''    finally:
        _cleanup_stage_workdir(stage_execution_id)
'''
