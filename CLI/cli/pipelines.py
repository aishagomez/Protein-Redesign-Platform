import json
import time
from pathlib import Path
from typing import Optional

import typer
from rich import box
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from cli.config import client, get_token, handle_response

app = typer.Typer(no_args_is_help=True)
console = Console()

STATE_STYLE = {
    "pending": ("Pending...", "yellow"),
    "running": ("Running ;)", "blue"),
    "waiting_for_approval": ("Waiting approval", "magenta"),
    "retrying": ("Retrying...", "bright_blue"),
    "completed": ("Completed :)", "green"),
    "failed": ("Failed :(", "red"),
    "error": ("Error D:", "bold red"),
}


def _state_text(state: str) -> Text:
    label, style = STATE_STYLE.get(state, ("Unknown", "dim"))
    return Text(f"{label} {state}", style=style)


def _load_stage_order(payload: str) -> list:
    try:
        if Path(payload).exists():
            return json.loads(Path(payload).read_text())
    except Exception:
        pass

    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        typer.echo("Error: stage-order no es JSON valido ni ruta de archivo existente. Try again ;)", err=True)
        raise typer.Exit(1)


@app.command("list")
def list_pipelines(
    project_id: int = typer.Argument(..., help="ID del proyecto"),
):
    """Listar los pipelines de un proyecto."""
    token = get_token()
    with client(token) as c:
        pipelines = handle_response(c.get(f"/projects/{project_id}/pipelines/"))

    if not pipelines:
        console.print("Sin pipelines. Crea uno con: cli pipelines create")
        return

    table = Table(title=f"Pipelines - Proyecto {project_id}", box=box.ROUNDED, highlight=True)
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Version", style="magenta")
    table.add_column("Estado", no_wrap=True)
    table.add_column("Creado", style="dim")

    for pipeline in pipelines:
        table.add_row(
            str(pipeline.get("id", "")),
            pipeline.get("version", "-") or "-",
            _state_text(pipeline.get("status", "unknown")),
            pipeline.get("created_at", "")[:10],
        )
    console.print(table)


@app.command("show")
def show_pipeline(
    project_id: int = typer.Argument(..., help="ID del proyecto"),
    pipeline_id: int = typer.Argument(..., help="ID del pipeline"),
):
    """Ver detalles de un pipeline."""
    token = get_token()
    with client(token) as c:
        pipeline = handle_response(c.get(f"/projects/{project_id}/pipelines/{pipeline_id}"))

    console.print(f"\n[bold]Pipeline[/bold] : ID {pipeline['id']}")
    console.print(f"[bold]Proyecto[/bold] : {pipeline['project_id']}")
    console.print(f"[bold]Version[/bold]  : {pipeline.get('version', '-')}")
    console.print(f"[bold]Estado[/bold]   : {pipeline.get('status', '-')}")
    console.print(f"[bold]Inicio[/bold]   : {pipeline.get('started_at', '-')}")
    console.print(f"[bold]Fin[/bold]      : {pipeline.get('finished_at', '-')}")
    console.print(f"[bold]Parametros[/bold]: {json.dumps(pipeline.get('parameters') or {}, ensure_ascii=False, indent=2)}\n")


@app.command("create")
def create_pipeline(
    project_id: int = typer.Argument(..., help="ID del proyecto"),
    version: str = typer.Option(None, help="Version del pipeline (opcional)"),
    parameters: str = typer.Option("{}", help="Parametros JSON del pipeline"),
):
    """Crear un pipeline en un proyecto."""
    token = get_token()
    try:
        parameters_dict = json.loads(parameters)
    except json.JSONDecodeError:
        typer.echo("Error: --parameters no es JSON valido. Try again ;)", err=True)
        raise typer.Exit(1)

    with client(token) as c:
        pipeline = handle_response(
            c.post(
                f"/projects/{project_id}/pipelines/",
                json={"version": version, "parameters": parameters_dict},
            )
        )
    console.print(f"Pipeline creado con ID [cyan]{pipeline['id']}[/cyan] y version [bold]{pipeline.get('version', '-')}[/bold]")


@app.command("run")
def run_pipeline(
    project_id: int = typer.Argument(..., help="ID del proyecto"),
    pipeline_id: int = typer.Argument(..., help="ID del pipeline"),
    stage_order: str = typer.Option(..., "--stage-order", "-s", help="JSON array de etapas o ruta a archivo JSON"),
    pause_between_stages: bool = typer.Option(False, "--pause-between-stages", help="Pausar entre etapas"),
    watch: bool = typer.Option(True, "--watch/--no-watch", help="Monitorear en tiempo real"),
):
    """Lanzar un pipeline."""
    token = get_token()
    stage_defs = _load_stage_order(stage_order)
    if not isinstance(stage_defs, list):
        typer.echo("Error: stage-order debe ser un array JSON de etapas.", err=True)
        raise typer.Exit(1)

    with client(token) as c:
        execution = handle_response(
            c.post(
                f"/projects/{project_id}/pipelines/{pipeline_id}/run",
                json={"stage_order": stage_defs, "pause_between_stages": pause_between_stages},
            )
        )

    console.print(f"Pipeline lanzado. Pipeline ID: [cyan]{pipeline_id}[/cyan]")
    console.print(f"Estado inicial: [bold]{execution.get('status', 'unknown')}[/bold]")

    if watch:
        _monitor(token, pipeline_id)


@app.command("approve")
def approve_pipeline(
    pipeline_id: int = typer.Argument(..., help="ID del pipeline / ejecucion"),
    chosen_stage_execution_id: Optional[int] = typer.Option(None, "--stage-execution-id", help="Elegir una stage execution especifica si aplica"),
):
    """Aprobar la siguiente etapa cuando el pipeline este en waiting_for_approval."""
    token = get_token()
    payload = {}
    if chosen_stage_execution_id is not None:
        payload["chosen_stage_execution_id"] = chosen_stage_execution_id

    with client(token) as c:
        result = handle_response(c.post(f"/executions/{pipeline_id}/approve", json=payload))

    console.print(f"Pipeline [cyan]{pipeline_id}[/cyan] aprobado. Estado: [bold]{result.get('status', 'unknown')}[/bold]")


@app.command("retry")
def retry_pipeline_stage(
    pipeline_id: int = typer.Argument(..., help="ID del pipeline / ejecucion"),
    stage_order_index: int = typer.Option(..., "--stage-order-index", "-i", help="Indice de la etapa dentro del pipeline"),
    new_params: str = typer.Option("{}", "--new-params", "-p", help="JSON con nuevos parametros"),
    new_tool_id: Optional[int] = typer.Option(None, "--new-tool-id", help="Tool alternativo opcional"),
    new_tool: Optional[str] = typer.Option(None, "--new-tool", help="Nombre alternativo opcional del tool"),
):
    """Relanzar manualmente una etapa con nuevos parametros."""
    token = get_token()
    try:
        params = json.loads(new_params)
    except json.JSONDecodeError:
        typer.echo("Error: --new-params no es JSON valido. Try again ;)", err=True)
        raise typer.Exit(1)

    payload = {
        "stage_order_index": stage_order_index,
        "new_params": params,
        "new_tool_id": new_tool_id,
        "new_tool": new_tool,
    }
    with client(token) as c:
        result = handle_response(c.post(f"/executions/{pipeline_id}/retry-stage", json=payload))

    console.print(
        f"Retry solicitado para pipeline [cyan]{pipeline_id}[/cyan]. "
        f"Estado: [bold]{result.get('status', 'unknown')}[/bold]"
    )


@app.command("status")
def pipeline_status(
    pipeline_id: int = typer.Argument(..., help="ID del pipeline / ejecucion"),
    watch: bool = typer.Option(False, "--watch", "-w", help="Monitorear en tiempo real"),
):
    """Ver el estado actual del pipeline."""
    token = get_token()
    if watch:
        _monitor(token, pipeline_id)
    else:
        _print_status_once(token, pipeline_id)


def _fetch_state(token: str, pipeline_id: int, retries: int = 5) -> dict:
    return _request_json(token, f"/executions/{pipeline_id}", retries=retries)


def _fetch_stages(token: str, pipeline_id: int, retries: int = 3) -> list:
    try:
        return _request_json(token, f"/executions/{pipeline_id}/stages", retries=retries)
    except Exception:
        return []


def _build_panel(state: dict, stages: list) -> Panel:
    status = state.get("status", "unknown")
    icon, color = STATE_STYLE.get(status, ("Unknown", "dim"))

    lines = Text()
    lines.append(f"Pipeline ID : {state.get('pipeline_id', state.get('id', '?'))}\n", style="dim")
    lines.append(f"Estado      : {icon} {status}\n", style=color)
    lines.append(f"Pausa       : {state.get('pause_between_stages', False)}\n")
    lines.append(f"Inicio      : {state.get('started_at', '-')}\n")
    lines.append(f"Fin         : {state.get('finished_at', '-')}\n")

    if stages:
        lines.append("\n-- Etapas --------------------------\n", style="bold")
        for stage in stages:
            s_icon, s_color = STATE_STYLE.get(stage.get("status", ""), ("Unknown", "dim"))
            lines.append(f"  {s_icon} {stage.get('stage_name', '?'):20}", style=s_color)
            lines.append(f" {stage.get('status', '')}\n", style=s_color)

    if status == "waiting_for_approval":
        lines.append("\nAccion: ejecuta ", style="bold")
        lines.append(f"cli pipelines approve {state.get('pipeline_id', state.get('id', '?'))}", style="cyan")
        lines.append(" para continuar.\n", style="bold")

    return Panel(lines, title="Monitor de Pipeline", border_style=color)


def _print_status_once(token: str, pipeline_id: int):
    state = _fetch_state(token, pipeline_id)
    stages = _fetch_stages(token, pipeline_id)
    console.print(_build_panel(state, stages))


def _monitor(token: str, pipeline_id: int, interval: int = 5):
    console.print(f"Monitoreando pipeline [cyan]{pipeline_id}[/cyan] (Ctrl+C para salir)\n")
    terminal_states = {"completed", "failed", "error", "waiting_for_approval"}

    with Live(console=console, refresh_per_second=1) as live:
        while True:
            state = _fetch_state(token, pipeline_id)
            stages = _fetch_stages(token, pipeline_id)
            live.update(_build_panel(state, stages))

            if state.get("status") in terminal_states:
                break
            time.sleep(interval)

    console.print(_build_panel(state, stages))
    status = state.get("status")
    if status == "completed":
        console.print("\n[bold green]Pipeline completado exitosamente.[/bold green]")
        console.print("Descarga resultados con: [cyan]cli results download[/cyan]")
    elif status == "waiting_for_approval":
        console.print("\n[bold magenta]Pipeline esperando aprobacion.[/bold magenta]")
        console.print(f"Continua con: [cyan]cli pipelines approve {pipeline_id}[/cyan]")
    else:
        console.print(f"\n[bold red]Pipeline termino con estado: {status}[/bold red]")


def _request_json(token: str, path: str, retries: int = 5):
    for attempt in range(retries):
        try:
            with client(token) as c:
                return handle_response(c.get(path))
        except Exception as error:
            if attempt < retries - 1:
                time.sleep(min(2 ** attempt, 8))
            else:
                typer.echo(f"Error: no se pudo contactar la API: {error}", err=True)
                raise typer.Exit(1)
