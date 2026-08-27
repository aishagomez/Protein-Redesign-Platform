import os
import json
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
            print(f"[Docking Worker] Attempt {attempt + 1}/3 - error reporting to {url}: {exc}")
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
    params = [
        _as_namespace(parameter, "parameter")
        for parameter in tool_contract.get("parameters", [])
    ]
    return tool, runtime, params


def _stage_dir(stage_execution_id: int) -> Path:
    stage_dir = WORK_ROOT / f"stage_{stage_execution_id}"
    stage_dir.mkdir(parents=True, exist_ok=True)
    return stage_dir


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


def _materialize_file(input_path: str, destination_root: Path) -> str:
    source = Path(input_path)
    if not source.exists():
        raise FileNotFoundError(input_path)
    return str(_copy_into_workspace(source, destination_root))


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


def _parse_constraints(constraints):
    if constraints is None:
        return None

    if isinstance(constraints, str):
        text = constraints.strip()
        return text if text else None

    if not isinstance(constraints, dict):
        raise ValueError("constraints must be a string or a dict keyed by protein id")

    lines = [
        "# Protein_name  No_of_residues_in_constraints",
        "# Res_number    Confidence_(0-10)",
        "",
    ]

    for protein_name, residues in constraints.items():
        if not isinstance(residues, list):
            raise ValueError("each protein entry in constraints must be a list")
        lines.append(f"{protein_name}  {len(residues)}")
        for residue in residues:
            if isinstance(residue, dict):
                residue_number = residue.get("residue") or residue.get("res_number")
                confidence = residue.get("confidence", 10)
            elif isinstance(residue, (list, tuple)) and len(residue) == 2:
                residue_number, confidence = residue
            else:
                residue_number, confidence = residue, 10

            if residue_number is None:
                raise ValueError("constraint residue entries require a residue number")
            lines.append(f"{residue_number}     {confidence}")
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def _write_gramm_files(runtime_params: dict, runtime_workdir: Path):
    receptor_file = Path(runtime_params["receptor_path"]).name
    ligand_file = Path(runtime_params["ligand_path"]).name
    receptor_fragment = runtime_params["receptor_fragment"]
    ligand_fragment = runtime_params["ligand_fragment"]
    receptor_id = runtime_params["receptor_id"]
    ligand_id = runtime_params["ligand_id"]
    result_file = f"{receptor_id}-{ligand_id}.res"

    rmol_content = "\n".join(
        [
            "# Filename  Fragment  ID      Filename  Fragment  ID",
            f"  {receptor_file}    {receptor_fragment}    {receptor_id}    {ligand_file}    {ligand_fragment}    {ligand_id}",
            "",
        ]
    )
    (runtime_workdir / "rmol.gr").write_text(rmol_content, encoding="utf-8")

    rpar_lines = [
        f"mmode= {runtime_params['mmode']}",
        f"eta= {runtime_params['eta']}",
        f"ro= {runtime_params['ro']}",
        f"fr= {runtime_params['fr']}",
        f"crang= {runtime_params['crang']}",
        f"ccti= {runtime_params['ccti']}",
        f"crep= {runtime_params['crep']}",
        f"maxm= {runtime_params['maxm']}",
        f"ai= {runtime_params['ai']}",
    ]
    (runtime_workdir / "rpar.gr").write_text("\n".join(rpar_lines) + "\n", encoding="utf-8")

    wlist_content = "# File_of_scan_predictions\n\n  " + result_file + "\n"
    (runtime_workdir / "wlist.gr").write_text(wlist_content, encoding="utf-8")

    wpar_lines = [
        f"mtch_l= {runtime_params['mtch_l']}",
        f"scovdw= {runtime_params['scovdw']}",
        f"scosta= {runtime_params['scosta']}",
        f"ctr= {runtime_params['ctr']}",
        f"rclusl= {runtime_params['rclusl']}",
        f"mbak= {runtime_params['mbak']}",
        f"maxmch= {runtime_params['maxmch']}",
        f"sejo= {runtime_params['sejo']}",
    ]
    (runtime_workdir / "wpar.gr").write_text("\n".join(wpar_lines) + "\n", encoding="utf-8")

    constraints_text = _parse_constraints(runtime_params.get("constraints"))
    if constraints_text:
        (runtime_workdir / "rcon.gr").write_text(constraints_text, encoding="utf-8")

    rusr_content = runtime_params.get("rusr_content")
    if rusr_content:
        (runtime_workdir / "rusr.gr").write_text(str(rusr_content).strip() + "\n", encoding="utf-8")


def _normalize(stage_name: str, params: dict, workdir: Path) -> dict:
    normalized = dict(params)
    requested_output_dir = normalized.get("output_dir") or str(workdir / "published_output")
    Path(requested_output_dir).mkdir(parents=True, exist_ok=True)

    runtime_workdir = workdir / "runtime_workdir"
    if runtime_workdir.exists():
        shutil.rmtree(runtime_workdir)
    runtime_workdir.mkdir(parents=True, exist_ok=True)

    receptor_input = normalized.get("receptor_path") or normalized.get("receptor")
    ligand_input = normalized.get("ligand_path") or normalized.get("ligand")
    if not receptor_input or not ligand_input:
        raise ValueError("Docking requires receptor_path and ligand_path")

    normalized["receptor_path"] = _materialize_file(str(receptor_input), runtime_workdir)
    normalized["ligand_path"] = _materialize_file(str(ligand_input), runtime_workdir)
    normalized["output_dir"] = requested_output_dir
    normalized["runtime_workdir"] = str(runtime_workdir)

    normalized["receptor_fragment"] = normalized.get("receptor_fragment", "*")
    normalized["ligand_fragment"] = normalized.get("ligand_fragment", "*")
    normalized["receptor_id"] = normalized.get("receptor_id") or Path(normalized["receptor_path"]).stem
    normalized["ligand_id"] = normalized.get("ligand_id") or Path(normalized["ligand_path"]).stem
    normalized["mmode"] = normalized.get("mmode", "docking")
    normalized["eta"] = normalized.get("eta", 3.5)
    normalized["ro"] = normalized.get("ro", 9)
    normalized["fr"] = normalized.get("fr", 0.0)
    normalized["crang"] = normalized.get("crang", "grid_step")
    normalized["ccti"] = normalized.get("ccti", "gray")
    normalized["crep"] = normalized.get("crep", "all")
    normalized["maxm"] = normalized.get("maxm", 30000)
    normalized["ai"] = normalized.get("ai", 10)
    normalized["mtch_l"] = normalized.get("mtch_l", 20000)
    normalized["scovdw"] = normalized.get("scovdw", 0)
    normalized["scosta"] = normalized.get("scosta", 0)
    normalized["ctr"] = normalized.get("ctr", 1 if normalized.get("constraints") else 0)
    normalized["rclusl"] = normalized.get("rclusl", 10)
    normalized["mbak"] = normalized.get("mbak", 0)
    normalized["maxmch"] = normalized.get("maxmch", 100)
    normalized["sejo"] = normalized.get("sejo", "joint")

    _write_gramm_files(normalized, runtime_workdir)
    return normalized


def _validate(runtime_params: dict):
    for key in ("receptor_path", "ligand_path", "runtime_workdir", "output_dir"):
        value = runtime_params.get(key)
        if not value:
            raise ValueError(f"Missing required runtime param: {key}")
        if key in {"receptor_path", "ligand_path"} and not Path(value).exists():
            raise FileNotFoundError(value)


def _resolve_env(env_spec: dict, context: dict) -> list[str]:
    env_args = []
    for key, value in env_spec.items():
        env_args.extend(["-e", f"{key}={_render_string(str(value), context)}"])
    return env_args


def _build_command(runtime, runtime_params):
    context = _build_template_context(runtime_params)
    if not runtime.command_template:
        raise ValueError("GRAMM runtime has no command_template configured")
    command = [_render_string(str(arg), context) for arg in runtime.command_template]
    rendered_workdir = _render_string(runtime.workdir, context) if runtime.workdir else str(runtime_params["runtime_workdir"])
    return command, rendered_workdir, context


def _run_docker(runtime, command, rendered_workdir, context, workdir, stage_execution_id):
    docker = ["docker", "run", "--rm", "--label", f"platform.stage_execution_id={stage_execution_id}"]

    parent_container = os.environ.get("HOSTNAME")
    if parent_container:
        docker.extend(["--volumes-from", parent_container])

    if runtime.resources.get("memory"):
        docker.append(f"--memory={runtime.resources['memory']}")
    if runtime.resources.get("cpus"):
        docker.append(f"--cpus={runtime.resources['cpus']}")

    if rendered_workdir:
        docker.extend(["-w", rendered_workdir])

    docker.extend(["-e", "PYTHONUNBUFFERED=1"])
    docker.extend(_resolve_env(runtime.env or {}, context))
    docker.append(runtime.image)
    docker.extend(command)

    print("[DOCKING] docker command:", " ".join(docker))

    return subprocess.run(
        docker,
        cwd=str(workdir),
        capture_output=True,
        text=True,
        check=True,
    )


def _publish_outputs(runtime_workdir: Path, output_dir: Path) -> list[str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    published = []

    for pattern in ("*.res", "*.pdb", "gramm.log"):
        for source in runtime_workdir.glob(pattern):
            if not source.is_file():
                continue
            destination = output_dir / source.name
            shutil.copy2(source, destination)
            published.append(str(destination))

    return sorted(set(published))


def _execute(stage_execution_id: int, stage_name: str, tool_id: int, params: dict, tool_contract: dict):
    tool, runtime, tool_params = _load_tool_contract(tool_contract)
    if tool_id is not None and tool.id != tool_id:
        raise ValueError(f"Inconsistent tool contract: expected id={tool_id}, received id={tool.id}")
    workdir = _stage_dir(stage_execution_id)

    runtime_params = _normalize(stage_name, params, workdir)
    runtime_params["_tool_parameters"] = tool_params
    _validate(runtime_params)

    command, rendered_workdir, context = _build_command(runtime, runtime_params)

    print("=" * 60)
    print("[DOCKING] Declarative GRAMM execution")
    print(f"  tool               : {tool.name}")
    print(f"  image              : {runtime.image}")
    print(f"  stage dir          : {workdir}")
    print(f"  runtime workdir    : {rendered_workdir}")
    print(f"  receptor_path      : {runtime_params['receptor_path']}")
    print(f"  ligand_path        : {runtime_params['ligand_path']}")
    print(f"  output_dir         : {runtime_params['output_dir']}")

    completed = _run_docker(runtime, command, rendered_workdir, context, workdir, stage_execution_id)
    outputs = _publish_outputs(Path(runtime_params["runtime_workdir"]), Path(runtime_params["output_dir"]))

    if not outputs:
        raise RuntimeError("GRAMM finished without published outputs")

    return {
        "output_files": outputs,
        "metadata": {
            "tool": tool.name,
            "image": runtime.image,
            "runtime_workdir": runtime_params["runtime_workdir"],
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "command": " ".join(command),
            "generated_files": json.dumps({
                "rmol.gr": str(Path(runtime_params["runtime_workdir"]) / "rmol.gr"),
                "rpar.gr": str(Path(runtime_params["runtime_workdir"]) / "rpar.gr"),
                "wlist.gr": str(Path(runtime_params["runtime_workdir"]) / "wlist.gr"),
                "wpar.gr": str(Path(runtime_params["runtime_workdir"]) / "wpar.gr"),
            }),
        },
    }


@celery_app.task(bind=True, name="tasks.run_stage", queue="docking", acks_late=True)
def run_stage(self, stage_execution_id, stage_name, tool_id, tool, params, tool_contract):
    print("\n[Docking Worker] task received")
    print(f"  stage_execution_id : {stage_execution_id}")
    print(f"  stage_name         : {stage_name}")
    print(f"  tool_id            : {tool_id}")
    print(f"  tool               : {tool}")
    print(f"  params             : {params}")

    _report(
        f"/internal/stages/{stage_execution_id}/started",
        {"celery_task_id": self.request.id},
    )

    try:
        if tool_id is None:
            raise ValueError("tool_id required")

        result = _execute(stage_execution_id, stage_name, tool_id, params, tool_contract)

        _report(
            f"/internal/stages/{stage_execution_id}/completed",
            result,
        )

        return {"status": "completed", "stage_execution_id": stage_execution_id}

    except SoftTimeLimitExceeded:
        _report(
            f"/internal/stages/{stage_execution_id}/failed",
            {"error": "timeout", "retry_type": "technical"},
        )
        raise

    except subprocess.CalledProcessError as exc:
        _report(
            f"/internal/stages/{stage_execution_id}/failed",
            {"error": exc.stderr, "traceback": traceback.format_exc(), "retry_type": "logical"},
        )
        raise

    except Exception as exc:
        _report(
            f"/internal/stages/{stage_execution_id}/failed",
            {"error": str(exc), "traceback": traceback.format_exc(), "retry_type": "logical"},
        )
        raise
