import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models import Pipeline, Project, StageExecution
from services.access import get_pipeline_for_user, get_project_for_user

REPORTS_ROOT = Path(os.environ.get("PERSISTENT_STORAGE_ROOT", "/persistent_storage")).resolve() / "reports"
TEXT_METRIC_PATTERNS = {
    "tm_score_a": re.compile(r"tmscoa=\s*([-+]?\d*\.?\d+)", re.IGNORECASE),
    "tm_score_b": re.compile(r"tmscob=\s*([-+]?\d*\.?\d+)", re.IGNORECASE),
    "energy": re.compile(r"energy=\s*([-+]?\d*\.?\d+)", re.IGNORECASE),
    "rmsd": re.compile(r"rmsd\s*[:=]\s*([-+]?\d*\.?\d+)", re.IGNORECASE),
    "coverage": re.compile(r"coverage\s*[:=]\s*([-+]?\d*\.?\d+)", re.IGNORECASE),
    "seq_id": re.compile(r"seq[-_ ]?id\s*[:=]\s*([-+]?\d*\.?\d+)", re.IGNORECASE),
}
TRACKED_NUMERIC_METRICS = {
    "duration_seconds",
    "artifact_count",
    "output_size_bytes",
    "energy",
    "total_score",
    "fitness",
    "tm_score_a",
    "tm_score_b",
    "coverage",
    "seq_id",
    "rmsd",
    "atom_count",
    "residue_count",
    "chain_count",
}
METRIC_DIRECTIONS = {
    "duration_seconds": "lower",
    "artifact_count": "higher",
    "output_size_bytes": "higher",
    "energy": "lower",
    "total_score": "lower",
    "fitness": "higher",
    "tm_score_a": "higher",
    "tm_score_b": "higher",
    "coverage": "higher",
    "seq_id": "higher",
    "rmsd": "lower",
    "atom_count": "higher",
    "residue_count": "higher",
    "chain_count": "higher",
}
METRIC_LABELS = {
    "duration_seconds": "Duration (s)",
    "artifact_count": "Artifacts",
    "output_size_bytes": "Output Size (bytes)",
    "energy": "Energy",
    "total_score": "Total Score",
    "fitness": "Fitness",
    "tm_score_a": "TM-score A",
    "tm_score_b": "TM-score B",
    "coverage": "Coverage",
    "seq_id": "Seq ID",
    "rmsd": "RMSD",
    "atom_count": "Atom Count",
    "residue_count": "Residue Count",
    "chain_count": "Chain Count",
}


def _project_owned(db: Session, project_id: int, user_id: int) -> Project:
    return get_project_for_user(db, project_id, user_id)


def _pipeline_owned(db: Session, project_id: int, pipeline_id: int, user_id: int) -> Pipeline:
    return get_pipeline_for_user(db, project_id, pipeline_id, user_id)


def _latest_stages(stages: list[StageExecution]) -> list[StageExecution]:
    latest_by_index = {}
    for stage in sorted(stages, key=lambda item: (item.stage_order_index, item.id), reverse=True):
        latest_by_index.setdefault(stage.stage_order_index, stage)
    return sorted(latest_by_index.values(), key=lambda item: item.stage_order_index)


def _serialize_stage(stage: StageExecution) -> dict:
    artifact_stats = _collect_stage_artifact_stats(stage.output_files or [])
    duration_seconds = _duration_seconds(stage.started_at, stage.finished_at)
    metadata_metrics = _extract_metadata_metrics(stage.output_metadata or {})
    scientific_metrics = _merge_metric_sources(artifact_stats["scientific_metrics"], metadata_metrics)
    return {
        "id": stage.id,
        "stage_name": stage.stage_name,
        "stage_order_index": stage.stage_order_index,
        "tool": stage.tool,
        "tool_version": stage.tool_version,
        "status": stage.status,
        "retry_count": stage.retry_count,
        "retry_type": stage.retry_type,
        "error_message": stage.error_message,
        "started_at": _iso(stage.started_at),
        "finished_at": _iso(stage.finished_at),
        "updated_at": _iso(stage.updated_at),
        "duration_seconds": duration_seconds,
        "params": stage.params or {},
        "output_files": stage.output_files or [],
        "artifact_count": len(stage.output_files or []),
        "output_size_bytes": artifact_stats["total_size_bytes"],
        "artifact_extensions": artifact_stats["artifact_extensions"],
        "scientific_metrics": scientific_metrics,
        "output_metadata": stage.output_metadata or {},
    }


def _pipeline_summary(pipeline: Pipeline) -> dict:
    all_stages = list(pipeline.stage_executions or [])
    active_stages = _latest_stages(all_stages)
    serialized_stages = [_serialize_stage(stage) for stage in active_stages]
    completed_count = sum(1 for stage in serialized_stages if stage["status"] == "completed")
    failed_count = sum(1 for stage in serialized_stages if stage["status"] == "failed")
    total_artifacts = sum(stage["artifact_count"] for stage in serialized_stages)
    total_output_size = sum(stage["output_size_bytes"] for stage in serialized_stages)
    stage_duration_total = sum(stage["duration_seconds"] or 0 for stage in serialized_stages)

    summary = {
        "pipeline_id": pipeline.id,
        "project_id": pipeline.project_id,
        "project_name": pipeline.project.name if pipeline.project else None,
        "version": pipeline.version,
        "status": pipeline.status,
        "pause_between_stages": pipeline.pause_between_stages,
        "stage_order": pipeline.stage_order or [],
        "started_at": _iso(pipeline.started_at),
        "finished_at": _iso(pipeline.finished_at),
        "created_at": _iso(pipeline.created_at),
        "updated_at": _iso(pipeline.updated_at),
        "parameters": pipeline.parameters or {},
        "kpis": {
            "total_stages": len(serialized_stages),
            "completed_stages": completed_count,
            "failed_stages": failed_count,
            "artifact_count": total_artifacts,
            "total_output_size_bytes": total_output_size,
            "duration_seconds": _duration_seconds(pipeline.started_at, pipeline.finished_at) or stage_duration_total,
        },
        "stages": serialized_stages,
        "history": [_serialize_stage(stage) for stage in sorted(all_stages, key=lambda item: (item.stage_order_index, item.id))],
    }
    summary["comparison"] = _build_pipeline_comparison(summary)
    summary["visualizations"] = _build_pipeline_visualizations(summary)
    return summary


def get_project_reports_overview(db: Session, project_id: int, user_id: int) -> dict:
    project = _project_owned(db, project_id, user_id)
    pipelines = db.query(Pipeline).filter(Pipeline.project_id == project_id).order_by(Pipeline.id.desc()).all()
    pipeline_summaries = [_pipeline_summary(pipeline) for pipeline in pipelines]
    overview = {
        "project_id": project.id,
        "project_name": project.name,
        "description": project.description,
        "created_at": _iso(project.created_at),
        "kpis": {
            "pipelines": len(pipeline_summaries),
            "completed_pipelines": sum(1 for item in pipeline_summaries if item["status"] == "completed"),
            "failed_pipelines": sum(1 for item in pipeline_summaries if item["status"] == "failed"),
            "artifacts": sum(item["kpis"]["artifact_count"] for item in pipeline_summaries),
            "total_output_size_bytes": sum(item["kpis"]["total_output_size_bytes"] for item in pipeline_summaries),
        },
        "pipelines": pipeline_summaries,
    }
    overview["comparison"] = _build_project_comparison(pipeline_summaries)
    overview["visualizations"] = _build_project_visualizations(overview, pipeline_summaries)
    return overview


def get_pipeline_report(db: Session, project_id: int, pipeline_id: int, user_id: int) -> dict:
    pipeline = _pipeline_owned(db, project_id, pipeline_id, user_id)
    return _pipeline_summary(pipeline)


def generate_project_report_file(db: Session, project_id: int, user_id: int, fmt: str) -> Path:
    overview = get_project_reports_overview(db, project_id, user_id)
    project = _project_owned(db, project_id, user_id)
    return _write_report_file(
        REPORTS_ROOT / f"user_{project.user_id}" / f"project_{project_id}",
        f"project_{project_id}_report",
        fmt,
        overview,
        _render_project_markdown,
    )


def generate_pipeline_report_file(db: Session, project_id: int, pipeline_id: int, user_id: int, fmt: str) -> Path:
    report = get_pipeline_report(db, project_id, pipeline_id, user_id)
    pipeline = _pipeline_owned(db, project_id, pipeline_id, user_id)
    return _write_report_file(
        REPORTS_ROOT / f"user_{pipeline.project.user_id}" / f"project_{project_id}" / f"pipeline_{pipeline_id}",
        f"pipeline_{pipeline_id}_report",
        fmt,
        report,
        _render_pipeline_markdown,
    )


def _build_project_comparison(pipelines: list[dict]) -> dict:
    rows = []
    for pipeline in pipelines:
        rows.append(
            {
                "pipeline_id": pipeline["pipeline_id"],
                "status": pipeline["status"],
                "version": pipeline["version"],
                "duration_seconds": pipeline["kpis"]["duration_seconds"],
                "artifact_count": pipeline["kpis"]["artifact_count"],
                "output_size_bytes": pipeline["kpis"]["total_output_size_bytes"],
                "completed_stages": pipeline["kpis"]["completed_stages"],
                "docking_energy_min": _pipeline_metric_value(pipeline, "energy", reducer="min"),
                "docking_tm_score_best": _pipeline_metric_value(pipeline, "tm_score_a", reducer="max"),
                "fitness_best": _pipeline_metric_value(pipeline, "fitness", reducer="max"),
                "total_score_best": _pipeline_metric_value(pipeline, "total_score", reducer="min"),
                "pdb_atoms_total": _pipeline_metric_value(pipeline, "atom_count", reducer="sum"),
            }
        )

    metric_specs = [
        ("duration_seconds", "lower"),
        ("artifact_count", "higher"),
        ("output_size_bytes", "higher"),
        ("docking_energy_min", "lower"),
        ("docking_tm_score_best", "higher"),
        ("fitness_best", "higher"),
        ("total_score_best", "lower"),
        ("pdb_atoms_total", "higher"),
    ]
    _decorate_ranking_rows(rows, metric_specs)

    fastest = _pick_extreme(rows, "duration_seconds", min)
    richest_outputs = _pick_extreme(rows, "output_size_bytes", max)
    best_energy = _pick_extreme(rows, "docking_energy_min", min)
    best_tm = _pick_extreme(rows, "docking_tm_score_best", max)
    best_fitness = _pick_extreme(rows, "fitness_best", max)
    best_total_score = _pick_extreme(rows, "total_score_best", min)

    return {
        "ranked_pipelines": rows,
        "table_rows": rows,
        "automatic_rankings": _build_automatic_rankings(rows, metric_specs, "pipeline_id"),
        "highlights": {
            "fastest_pipeline_id": fastest["pipeline_id"] if fastest else None,
            "largest_output_pipeline_id": richest_outputs["pipeline_id"] if richest_outputs else None,
            "best_energy_pipeline_id": best_energy["pipeline_id"] if best_energy else None,
            "best_tm_score_pipeline_id": best_tm["pipeline_id"] if best_tm else None,
            "best_fitness_pipeline_id": best_fitness["pipeline_id"] if best_fitness else None,
            "best_total_score_pipeline_id": best_total_score["pipeline_id"] if best_total_score else None,
        },
    }


def _build_project_visualizations(overview: dict, pipelines: list[dict]) -> dict:
    labels = [f"Pipeline {pipeline['pipeline_id']}" for pipeline in pipelines]
    datasets = {
        "status_distribution": [
            {"label": "completed", "value": overview["kpis"]["completed_pipelines"]},
            {"label": "failed", "value": overview["kpis"]["failed_pipelines"]},
            {"label": "other", "value": max(overview["kpis"]["pipelines"] - overview["kpis"]["completed_pipelines"] - overview["kpis"]["failed_pipelines"], 0)},
        ],
        "pipeline_duration_seconds": [
            {"label": label, "value": pipeline["kpis"]["duration_seconds"] or 0}
            for label, pipeline in zip(labels, pipelines)
        ],
        "pipeline_artifact_count": [
            {"label": label, "value": pipeline["kpis"]["artifact_count"]}
            for label, pipeline in zip(labels, pipelines)
        ],
        "pipeline_output_size_bytes": [
            {"label": label, "value": pipeline["kpis"]["total_output_size_bytes"]}
            for label, pipeline in zip(labels, pipelines)
        ],
        "pipeline_docking_energy": [
            {"label": label, "value": _pipeline_metric_value(pipeline, "energy", reducer="min")}
            for label, pipeline in zip(labels, pipelines)
        ],
        "pipeline_tm_score": [
            {"label": label, "value": _pipeline_metric_value(pipeline, "tm_score_a", reducer="max")}
            for label, pipeline in zip(labels, pipelines)
        ],
        "pipeline_fitness": [
            {"label": label, "value": _pipeline_metric_value(pipeline, "fitness", reducer="max")}
            for label, pipeline in zip(labels, pipelines)
        ],
        "pipeline_total_score": [
            {"label": label, "value": _pipeline_metric_value(pipeline, "total_score", reducer="min")}
            for label, pipeline in zip(labels, pipelines)
        ],
    }
    datasets["graphs"] = [
        {"id": "status_distribution", "title": "Pipeline Status Distribution", "type": "pie", "data_key": "status_distribution"},
        {"id": "pipeline_duration_seconds", "title": "Pipeline Duration", "type": "bar", "data_key": "pipeline_duration_seconds"},
        {"id": "pipeline_artifact_count", "title": "Pipeline Artifact Count", "type": "bar", "data_key": "pipeline_artifact_count"},
        {"id": "pipeline_output_size_bytes", "title": "Pipeline Output Size", "type": "bar", "data_key": "pipeline_output_size_bytes"},
        {"id": "pipeline_docking_energy", "title": "Best Docking Energy", "type": "bar", "data_key": "pipeline_docking_energy"},
        {"id": "pipeline_tm_score", "title": "Best TM-score", "type": "bar", "data_key": "pipeline_tm_score"},
        {"id": "pipeline_fitness", "title": "Best Fitness", "type": "bar", "data_key": "pipeline_fitness"},
        {"id": "pipeline_total_score", "title": "Best Total Score", "type": "bar", "data_key": "pipeline_total_score"},
    ]
    return datasets


def _build_pipeline_comparison(summary: dict) -> dict:
    stages = summary["stages"]
    table_rows = []
    previous_metrics = None

    for stage in stages:
        metrics = _collect_stage_comparable_metrics(stage)
        table_rows.append(
            {
                "stage_execution_id": stage["id"],
                "stage_order_index": stage["stage_order_index"],
                "stage_name": stage["stage_name"],
                "tool": stage["tool"],
                "status": stage["status"],
                "metrics": metrics,
                "relative_vs_previous_percent": _relative_metric_map(metrics, previous_metrics or {}),
                "ranking": {},
            }
        )
        previous_metrics = metrics

    metric_specs = [
        (metric_name, METRIC_DIRECTIONS[metric_name])
        for metric_name in _ordered_metric_names(table_rows)
        if metric_name in METRIC_DIRECTIONS
    ]
    _decorate_stage_table_rows(table_rows, metric_specs)

    return {
        "stage_durations": [
            {
                "stage_name": stage["stage_name"],
                "stage_order_index": stage["stage_order_index"],
                "duration_seconds": stage["duration_seconds"],
            }
            for stage in stages
        ],
        "stage_output_sizes": [
            {
                "stage_name": stage["stage_name"],
                "stage_order_index": stage["stage_order_index"],
                "output_size_bytes": stage["output_size_bytes"],
            }
            for stage in stages
        ],
        "stage_scientific_metrics": [
            {
                "stage_name": stage["stage_name"],
                "stage_order_index": stage["stage_order_index"],
                "metrics": stage["scientific_metrics"],
            }
            for stage in stages
        ],
        "stage_metrics_table": table_rows,
        "automatic_rankings": _build_stage_rankings(table_rows, metric_specs),
    }


def _build_pipeline_visualizations(summary: dict) -> dict:
    stages = summary["stages"]
    datasets = {
        "stage_duration_seconds": [
            {"label": f"{stage['stage_order_index'] + 1}. {stage['stage_name']}", "value": stage["duration_seconds"] or 0}
            for stage in stages
        ],
        "stage_output_size_bytes": [
            {"label": f"{stage['stage_order_index'] + 1}. {stage['stage_name']}", "value": stage["output_size_bytes"]}
            for stage in stages
        ],
        "stage_artifact_count": [
            {"label": f"{stage['stage_order_index'] + 1}. {stage['stage_name']}", "value": stage["artifact_count"]}
            for stage in stages
        ],
        "stage_atom_count": [
            {"label": f"{stage['stage_order_index'] + 1}. {stage['stage_name']}", "value": stage["scientific_metrics"].get("atom_count")}
            for stage in stages
        ],
        "stage_residue_count": [
            {"label": f"{stage['stage_order_index'] + 1}. {stage['stage_name']}", "value": stage["scientific_metrics"].get("residue_count")}
            for stage in stages
        ],
        "stage_energy": [
            {"label": f"{stage['stage_order_index'] + 1}. {stage['stage_name']}", "value": stage["scientific_metrics"].get("energy")}
            for stage in stages
        ],
        "stage_tm_score": [
            {"label": f"{stage['stage_order_index'] + 1}. {stage['stage_name']}", "value": stage["scientific_metrics"].get("tm_score_a")}
            for stage in stages
        ],
        "stage_total_score": [
            {"label": f"{stage['stage_order_index'] + 1}. {stage['stage_name']}", "value": stage["scientific_metrics"].get("total_score")}
            for stage in stages
        ],
        "stage_fitness": [
            {"label": f"{stage['stage_order_index'] + 1}. {stage['stage_name']}", "value": stage["scientific_metrics"].get("fitness")}
            for stage in stages
        ],
    }
    datasets["graphs"] = [
        {"id": "stage_duration_seconds", "title": "Stage Duration", "type": "bar", "data_key": "stage_duration_seconds"},
        {"id": "stage_output_size_bytes", "title": "Stage Output Size", "type": "bar", "data_key": "stage_output_size_bytes"},
        {"id": "stage_artifact_count", "title": "Stage Artifact Count", "type": "bar", "data_key": "stage_artifact_count"},
        {"id": "stage_atom_count", "title": "Stage Atom Count", "type": "bar", "data_key": "stage_atom_count"},
        {"id": "stage_residue_count", "title": "Stage Residue Count", "type": "bar", "data_key": "stage_residue_count"},
        {"id": "stage_energy", "title": "Stage Energy", "type": "line", "data_key": "stage_energy"},
        {"id": "stage_tm_score", "title": "Stage TM-score", "type": "line", "data_key": "stage_tm_score"},
        {"id": "stage_total_score", "title": "Stage Total Score", "type": "line", "data_key": "stage_total_score"},
        {"id": "stage_fitness", "title": "Stage Fitness", "type": "line", "data_key": "stage_fitness"},
    ]
    return datasets


def _collect_stage_artifact_stats(output_files: list[str]) -> dict:
    total_size = 0
    extension_counts: dict[str, int] = {}
    aggregated_metrics: dict[str, float] = {}
    metric_counts: dict[str, int] = {}

    for output in output_files:
        path = Path(output)
        if not path.exists() or not path.is_file():
            continue

        total_size += path.stat().st_size
        extension = path.suffix.lower() or "<no_ext>"
        extension_counts[extension] = extension_counts.get(extension, 0) + 1

        metrics = _extract_artifact_metrics(path)
        for key, value in metrics.items():
            if value is None:
                continue
            aggregated_metrics[key] = aggregated_metrics.get(key, 0.0) + value
            metric_counts[key] = metric_counts.get(key, 0) + 1

    scientific_metrics = {}
    for key, total in aggregated_metrics.items():
        if key in {"tm_score_a", "tm_score_b", "coverage", "seq_id", "fitness"}:
            scientific_metrics[key] = round(total / metric_counts[key], 4)
        elif key in {"energy", "total_score", "rmsd"}:
            scientific_metrics[key] = round(total / metric_counts[key], 4)
        else:
            scientific_metrics[key] = int(total) if float(total).is_integer() else round(total, 4)

    return {
        "total_size_bytes": total_size,
        "artifact_extensions": extension_counts,
        "scientific_metrics": scientific_metrics,
    }


def _extract_artifact_metrics(path: Path) -> dict:
    suffix = path.suffix.lower()
    if suffix == ".pdb":
        return _extract_pdb_metrics(path)
    if suffix == ".sc":
        return _extract_score_file_metrics(path)
    if suffix == ".json":
        return _extract_json_metrics(path)
    if suffix in {".gr", ".txt", ".log", ".out", ".csv", ".tsv"}:
        return _extract_text_metrics(path)
    return {}


def _extract_pdb_metrics(path: Path) -> dict:
    atom_count = 0
    hetatm_count = 0
    residues = set()
    chains = set()
    model_count = 0
    pose_headers = []
    pose_metrics = {}

    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped.startswith("label "):
                pose_headers = stripped.split()
                continue
            if stripped.startswith("pose ") and pose_headers:
                pose_values = stripped.split()
                for index, header in enumerate(pose_headers[1:], start=1):
                    if index >= len(pose_values):
                        break
                    try:
                        pose_metrics[header] = float(pose_values[index])
                    except ValueError:
                        continue

            if line.startswith("MODEL"):
                model_count += 1
            if not line.startswith(("ATOM", "HETATM")):
                continue

            chain_id = line[21].strip() or "_"
            residue_id = line[22:26].strip() or "0"
            residues.add((chain_id, residue_id))
            chains.add(chain_id)
            if line.startswith("ATOM"):
                atom_count += 1
            else:
                hetatm_count += 1

    metrics = {
        "atom_count": atom_count,
        "hetatm_count": hetatm_count,
        "residue_count": len(residues),
        "chain_count": len(chains),
        "model_count": model_count or 1,
    }
    if "total" in pose_metrics:
        metrics["total_score"] = pose_metrics["total"]
        metrics["energy"] = pose_metrics["total"]
    return metrics


def _extract_text_metrics(path: Path) -> dict:
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return {}

    metrics = {}
    for metric_name, pattern in TEXT_METRIC_PATTERNS.items():
        matches = [float(match) for match in pattern.findall(content)]
        if not matches:
            continue
        if metric_name == "energy":
            metrics[metric_name] = min(matches)
        elif metric_name in {"tm_score_a", "tm_score_b", "coverage", "seq_id"}:
            metrics[metric_name] = max(matches)
        else:
            metrics[metric_name] = matches[-1]
    return metrics


def _extract_score_file_metrics(path: Path) -> dict:
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except Exception:
        return {}

    headers = None
    values = None
    for line in lines:
        stripped = line.strip()
        if not stripped.startswith("SCORE:"):
            continue
        payload = stripped.split()[1:]
        if headers is None:
            headers = payload
            continue
        values = payload
        break

    if not headers or not values:
        return _extract_text_metrics(path)

    metrics = {}
    for header, raw_value in zip(headers, values):
        try:
            value = float(raw_value)
        except ValueError:
            continue
        if header == "total_score":
            metrics["total_score"] = value
        if header == "dG_separated":
            metrics["energy"] = value
            metrics["fitness"] = value
        if header == "complex_normalized" and "fitness" not in metrics:
            metrics["fitness"] = value
        if header == "dSASA_int":
            metrics["coverage"] = value
        if header == "rmsd":
            metrics["rmsd"] = value
    return metrics or _extract_text_metrics(path)


def _extract_json_metrics(path: Path) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return {}
    return _extract_metadata_metrics(payload)


def _pipeline_metric_value(summary: dict, metric_name: str, reducer: str) -> float | int | None:
    values = []
    for stage in summary.get("stages", []):
        value = stage.get("scientific_metrics", {}).get(metric_name)
        if value is not None:
            values.append(value)
    if not values:
        return None
    if reducer == "min":
        return min(values)
    if reducer == "max":
        return max(values)
    if reducer == "sum":
        return sum(values)
    return values[-1]


def _pick_extreme(rows: list[dict], metric_name: str, picker):
    valid_rows = [row for row in rows if row.get(metric_name) is not None]
    if not valid_rows:
        return None
    return picker(valid_rows, key=lambda item: item[metric_name])


def _merge_metric_sources(primary: dict, secondary: dict) -> dict:
    merged = dict(primary)
    for key, value in secondary.items():
        if key not in merged and value is not None:
            merged[key] = value
    return merged


def _extract_metadata_metrics(payload: Any, prefix: str = "") -> dict[str, float]:
    metrics = {}
    if isinstance(payload, dict):
        for key, value in payload.items():
            compound_key = f"{prefix}.{key}" if prefix else str(key)
            metrics.update(_extract_metadata_metrics(value, compound_key))
        return metrics
    if isinstance(payload, list):
        for index, item in enumerate(payload):
            metrics.update(_extract_metadata_metrics(item, f"{prefix}[{index}]"))
        return metrics
    if isinstance(payload, bool):
        return metrics
    if isinstance(payload, (int, float)):
        normalized_name = _normalize_metric_name(prefix)
        if normalized_name:
            metrics[normalized_name] = float(payload)
        return metrics
    return metrics


def _normalize_metric_name(raw_name: str) -> str | None:
    candidate = raw_name.lower()
    aliases = {
        "energy": ["energy", "dg_separated", "dg_cross"],
        "total_score": ["total_score", "score_total", "pose_total"],
        "fitness": ["fitness", "objective", "score"],
        "tm_score_a": ["tm_score", "tm_score_a", "tmscore", "tm_a"],
        "tm_score_b": ["tm_score_b", "tm_b"],
        "coverage": ["coverage", "dsasa_int"],
        "seq_id": ["seq_id", "sequence_identity"],
        "rmsd": ["rmsd"],
    }
    for normalized, names in aliases.items():
        if any(name in candidate for name in names):
            return normalized
    return None


def _decorate_ranking_rows(rows: list[dict], metric_specs: list[tuple[str, str]]):
    for metric_name, direction in metric_specs:
        valid = [row for row in rows if row.get(metric_name) is not None]
        if not valid:
            continue
        reverse = direction == "higher"
        ordered = sorted(valid, key=lambda item: item[metric_name], reverse=reverse)
        best_value = ordered[0][metric_name]
        for rank_index, row in enumerate(ordered, start=1):
            row[f"{metric_name}_rank"] = rank_index
            row[f"{metric_name}_delta_vs_best_percent"] = _percent_change(row[metric_name], best_value)


def _build_automatic_rankings(rows: list[dict], metric_specs: list[tuple[str, str]], id_field: str) -> list[dict]:
    rankings = []
    for metric_name, direction in metric_specs:
        valid = [row for row in rows if row.get(metric_name) is not None]
        if not valid:
            continue
        reverse = direction == "higher"
        ordered = sorted(valid, key=lambda item: item[metric_name], reverse=reverse)
        best_value = ordered[0][metric_name]
        rankings.append(
            {
                "metric": metric_name,
                "label": METRIC_LABELS.get(metric_name, metric_name),
                "direction": direction,
                "ranking": [
                    {
                        id_field: row[id_field],
                        "rank": index,
                        "value": row[metric_name],
                        "delta_vs_best_percent": _percent_change(row[metric_name], best_value),
                    }
                    for index, row in enumerate(ordered, start=1)
                ],
            }
        )
    return rankings


def _collect_stage_comparable_metrics(stage: dict) -> dict:
    comparable = {
        "duration_seconds": stage.get("duration_seconds"),
        "artifact_count": stage.get("artifact_count"),
        "output_size_bytes": stage.get("output_size_bytes"),
    }
    for metric_name, value in (stage.get("scientific_metrics") or {}).items():
        if metric_name in TRACKED_NUMERIC_METRICS:
            comparable[metric_name] = value
    return {key: value for key, value in comparable.items() if value is not None}


def _ordered_metric_names(table_rows: list[dict]) -> list[str]:
    seen = []
    for row in table_rows:
        for metric_name in row.get("metrics", {}):
            if metric_name not in seen:
                seen.append(metric_name)
    return seen


def _decorate_stage_table_rows(rows: list[dict], metric_specs: list[tuple[str, str]]):
    for metric_name, direction in metric_specs:
        valid = [row for row in rows if row["metrics"].get(metric_name) is not None]
        if not valid:
            continue
        reverse = direction == "higher"
        ordered = sorted(valid, key=lambda item: item["metrics"][metric_name], reverse=reverse)
        best_value = ordered[0]["metrics"][metric_name]
        for rank_index, row in enumerate(ordered, start=1):
            row["ranking"][metric_name] = {
                "rank": rank_index,
                "delta_vs_best_percent": _percent_change(row["metrics"][metric_name], best_value),
            }


def _build_stage_rankings(rows: list[dict], metric_specs: list[tuple[str, str]]) -> list[dict]:
    rankings = []
    for metric_name, direction in metric_specs:
        valid = [row for row in rows if row["metrics"].get(metric_name) is not None]
        if not valid:
            continue
        reverse = direction == "higher"
        ordered = sorted(valid, key=lambda item: item["metrics"][metric_name], reverse=reverse)
        best_value = ordered[0]["metrics"][metric_name]
        rankings.append(
            {
                "metric": metric_name,
                "label": METRIC_LABELS.get(metric_name, metric_name),
                "direction": direction,
                "ranking": [
                    {
                        "stage_execution_id": row["stage_execution_id"],
                        "stage_order_index": row["stage_order_index"],
                        "stage_name": row["stage_name"],
                        "rank": index,
                        "value": row["metrics"][metric_name],
                        "delta_vs_best_percent": _percent_change(row["metrics"][metric_name], best_value),
                    }
                    for index, row in enumerate(ordered, start=1)
                ],
            }
        )
    return rankings


def _relative_metric_map(current_metrics: dict, reference_metrics: dict) -> dict:
    relative = {}
    for metric_name, value in current_metrics.items():
        if metric_name not in reference_metrics:
            continue
        relative[metric_name] = _percent_change(value, reference_metrics[metric_name])
    return relative


def _percent_change(current: float | int | None, reference: float | int | None) -> float | None:
    if current is None or reference is None:
        return None
    if float(reference) == 0:
        return None
    return round(((float(current) - float(reference)) / abs(float(reference))) * 100.0, 4)


def _write_report_file(scope_dir: Path, basename: str, fmt: str, payload: dict, renderer) -> Path:
    normalized_fmt = fmt.lower()
    if normalized_fmt not in {"md", "json"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Formato de reporte no soportado")
    scope_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    destination = scope_dir / f"{basename}_{timestamp}.{normalized_fmt}"
    if normalized_fmt == "json":
        destination.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")
    else:
        destination.write_text(renderer(payload), encoding="utf-8")
    return destination


def _render_project_markdown(payload: dict) -> str:
    lines = [
        f"# Project Report: {payload['project_name']}",
        "",
        f"- Project ID: {payload['project_id']}",
        f"- Created At: {payload['created_at'] or 'n/a'}",
        f"- Pipelines: {payload['kpis']['pipelines']}",
        f"- Completed Pipelines: {payload['kpis']['completed_pipelines']}",
        f"- Failed Pipelines: {payload['kpis']['failed_pipelines']}",
        f"- Published Artifacts: {payload['kpis']['artifacts']}",
        f"- Total Output Size (bytes): {payload['kpis']['total_output_size_bytes']}",
        "",
        "## Cross-pipeline comparison",
        "",
        "| Pipeline | Status | Duration (s) | Artifacts | Output Size | Energy | TM-score | Fitness | Total Score |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]

    for row in payload["comparison"]["table_rows"]:
        lines.append(
            f"| #{row['pipeline_id']} | {row['status']} | {row['duration_seconds'] or 0} | {row['artifact_count']} | {row['output_size_bytes']} | {row['docking_energy_min'] if row['docking_energy_min'] is not None else 'n/a'} | {row['docking_tm_score_best'] if row['docking_tm_score_best'] is not None else 'n/a'} | {row['fitness_best'] if row['fitness_best'] is not None else 'n/a'} | {row['total_score_best'] if row['total_score_best'] is not None else 'n/a'} |"
        )

    lines.extend(["", "## Automatic rankings", ""])
    for ranking in payload["comparison"]["automatic_rankings"]:
        lines.append(f"### {ranking['label']}")
        for item in ranking["ranking"]:
            lines.append(
                f"- Pipeline #{item['pipeline_id']}: rank {item['rank']}, value={item['value']}, delta_vs_best={item['delta_vs_best_percent'] if item['delta_vs_best_percent'] is not None else 'n/a'}%"
            )
        lines.append("")

    lines.extend(
        [
            "## Visualization datasets",
            "",
            "The JSON report includes table rows, automatic rankings, relative deltas and graph-ready datasets for duration, artifact count, output size, energy, TM-score, fitness and total score.",
            "",
        ]
    )
    return "\n".join(lines) + "\n"


def _render_pipeline_markdown(payload: dict) -> str:
    lines = [
        f"# Pipeline Report: #{payload['pipeline_id']}",
        "",
        f"- Project: {payload['project_name']}",
        f"- Status: {payload['status']}",
        f"- Version: {payload['version'] or 'n/a'}",
        f"- Started At: {payload['started_at'] or 'n/a'}",
        f"- Finished At: {payload['finished_at'] or 'n/a'}",
        f"- Completed stages: {payload['kpis']['completed_stages']}/{payload['kpis']['total_stages']}",
        f"- Artifacts: {payload['kpis']['artifact_count']}",
        f"- Total Output Size (bytes): {payload['kpis']['total_output_size_bytes']}",
        f"- Duration (s): {payload['kpis']['duration_seconds'] or 0}",
        "",
        "## Stage comparison",
        "",
        "| Stage | Status | Tool | Duration (s) | Artifacts | Output Size | Energy | TM-score | Fitness | Total Score |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]

    for stage in payload["stages"]:
        metrics = stage["scientific_metrics"]
        lines.append(
            f"| {stage['stage_order_index'] + 1}. {stage['stage_name']} | {stage['status']} | {stage['tool']} | {stage['duration_seconds'] or 0} | {stage['artifact_count']} | {stage['output_size_bytes']} | {metrics.get('energy', 'n/a')} | {metrics.get('tm_score_a', 'n/a')} | {metrics.get('fitness', 'n/a')} | {metrics.get('total_score', 'n/a')} |"
        )

    lines.extend(["", "## Comparable metrics and relative deltas", ""])
    for row in payload["comparison"]["stage_metrics_table"]:
        lines.extend(
            [
                f"### Stage {row['stage_order_index'] + 1}: {row['stage_name']}",
                f"- Status: {row['status']}",
                f"- Tool: {row['tool']}",
            ]
        )
        if row["metrics"]:
            lines.append("- Comparable metrics:")
            for key, value in row["metrics"].items():
                ranking = row["ranking"].get(key, {})
                delta_vs_previous = row["relative_vs_previous_percent"].get(key)
                lines.append(
                    f"  - {key}: value={value}, rank={ranking.get('rank', 'n/a')}, delta_vs_best={ranking.get('delta_vs_best_percent', 'n/a')}%, delta_vs_previous={delta_vs_previous if delta_vs_previous is not None else 'n/a'}%"
                )
        lines.append("")

    lines.extend(["## Automatic rankings", ""])
    for ranking in payload["comparison"]["automatic_rankings"]:
        lines.append(f"### {ranking['label']}")
        for item in ranking["ranking"]:
            lines.append(
                f"- Stage {item['stage_order_index'] + 1} ({item['stage_name']}): rank {item['rank']}, value={item['value']}, delta_vs_best={item['delta_vs_best_percent'] if item['delta_vs_best_percent'] is not None else 'n/a'}%"
            )
        lines.append("")

    lines.extend(
        [
            "## Visualization datasets",
            "",
            "The JSON report includes table rows, automatic rankings, relative deltas and graph-ready datasets for stage duration, output size, artifact count, atom count, residue count, energy, TM-score, fitness and total score.",
            "",
        ]
    )
    return "\n".join(lines) + "\n"


def _duration_seconds(started_at, finished_at) -> float | None:
    if not started_at or not finished_at:
        return None
    return round((finished_at - started_at).total_seconds(), 3)


def _iso(value) -> str | None:
    return value.isoformat() if value else None
