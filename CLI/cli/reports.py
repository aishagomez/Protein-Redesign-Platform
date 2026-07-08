from pathlib import Path

import typer
from rich import box
from rich.console import Console
from rich.table import Table

from cli.config import client, get_token, handle_response

app = typer.Typer(no_args_is_help=True)
console = Console()


@app.command("project")
def show_project_report(
    project_id: int = typer.Argument(..., help="ID del proyecto"),
):
    """Mostrar resumen del reporte del proyecto."""
    token = get_token()
    with client(token) as c:
        overview = handle_response(c.get(f"/projects/{project_id}/reports/overview"))

    kpis = overview.get("kpis", {})
    table = Table(title=f"Reporte del proyecto {project_id}", box=box.ROUNDED, highlight=True)
    table.add_column("Metrica", style="bold")
    table.add_column("Valor", style="cyan")
    table.add_row("Proyecto", overview.get("project_name", "-"))
    table.add_row("Pipelines", str(kpis.get("pipelines", 0)))
    table.add_row("Completados", str(kpis.get("completed_pipelines", 0)))
    table.add_row("Fallidos", str(kpis.get("failed_pipelines", 0)))
    table.add_row("Artefactos", str(kpis.get("artifacts", 0)))
    console.print(table)


@app.command("pipeline")
def show_pipeline_report(
    project_id: int = typer.Argument(..., help="ID del proyecto"),
    pipeline_id: int = typer.Argument(..., help="ID del pipeline"),
):
    """Mostrar resumen del reporte de un pipeline."""
    token = get_token()
    with client(token) as c:
        overview = handle_response(c.get(f"/projects/{project_id}/pipelines/{pipeline_id}/reports/overview"))

    console.print(f"\n[bold]Pipeline[/bold] : {overview.get('pipeline_id', pipeline_id)}")
    console.print(f"[bold]Estado[/bold]   : {overview.get('status', '-')}")
    console.print(f"[bold]Version[/bold]  : {overview.get('version', '-') or '-'}")

    stages = overview.get("stages", [])
    if not stages:
        console.print("Sin etapas para reportar todavia.")
        return

    table = Table(title="Resumen por etapa", box=box.ROUNDED, highlight=True)
    table.add_column("Etapa", style="bold")
    table.add_column("Tool", style="cyan")
    table.add_column("Estado", no_wrap=True)
    table.add_column("Artefactos", style="green")

    for stage in stages:
        table.add_row(
            f"{stage.get('stage_order_index', 0) + 1}. {stage.get('stage_name', '-')}",
            stage.get("tool", "-"),
            stage.get("status", "-"),
            str(stage.get("artifact_count", 0)),
        )
    console.print(table)


@app.command("download-project")
def download_project_report(
    project_id: int = typer.Argument(..., help="ID del proyecto"),
    format: str = typer.Option("md", "--format", "-f", help="Formato md o json"),
    dest: Path = typer.Option(Path("./reportes"), "--dest", "-d", help="Directorio de destino"),
):
    """Descargar el reporte consolidado del proyecto."""
    _download_report(
        endpoint=f"/projects/{project_id}/reports/download",
        format=format,
        dest=dest,
    )


@app.command("download-pipeline")
def download_pipeline_report(
    project_id: int = typer.Argument(..., help="ID del proyecto"),
    pipeline_id: int = typer.Argument(..., help="ID del pipeline"),
    format: str = typer.Option("md", "--format", "-f", help="Formato md o json"),
    dest: Path = typer.Option(Path("./reportes"), "--dest", "-d", help="Directorio de destino"),
):
    """Descargar el reporte detallado de un pipeline."""
    _download_report(
        endpoint=f"/projects/{project_id}/pipelines/{pipeline_id}/reports/download",
        format=format,
        dest=dest,
    )


def _download_report(endpoint: str, format: str, dest: Path) -> None:
    token = get_token()
    dest.mkdir(parents=True, exist_ok=True)

    with client(token) as c:
        response = c.get(endpoint, params={"format": format}, follow_redirects=True)
        response.raise_for_status()
        filename = _resolve_filename(response, format)
        target = dest / filename
        target.write_bytes(response.content)

    console.print(f"Reporte descargado -> [cyan]{target.resolve()}[/cyan]")


def _resolve_filename(response, fallback_format: str) -> str:
    disposition = response.headers.get("content-disposition", "")
    marker = "filename="
    if marker in disposition:
        return disposition.split(marker, 1)[1].strip().strip('"')
    return f"report.{fallback_format}"
