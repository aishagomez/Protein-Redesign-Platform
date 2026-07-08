from pathlib import Path

import typer
from rich import box
from rich.console import Console
from rich.table import Table

from cli.config import client, get_token, handle_response

app = typer.Typer(no_args_is_help=True)
console = Console()


@app.command("list")
def list_project_files(
    project_id: int = typer.Argument(..., help="ID del proyecto"),
):
    """Listar archivos subidos al proyecto."""
    token = get_token()
    with client(token) as c:
        files = handle_response(c.get(f"/projects/{project_id}/files"))

    if not files:
        console.print("No hay archivos subidos en este proyecto todavia.")
        return

    table = Table(title=f"Archivos del proyecto {project_id}", box=box.ROUNDED, highlight=True)
    table.add_column("Nombre", style="bold")
    table.add_column("Ruta relativa", style="cyan")
    table.add_column("Tamano", style="green", no_wrap=True)

    for entry in files:
        table.add_row(
            entry.get("name", "-"),
            entry.get("relative_path", "-"),
            _format_size(entry.get("size")),
        )
    console.print(table)


@app.command("upload")
def upload_project_file(
    project_id: int = typer.Argument(..., help="ID del proyecto"),
    source: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        resolve_path=True,
        help="Archivo a subir",
    ),
    target_subdir: str = typer.Option("shared_inputs", "--target-subdir", "-t", help="Subdirectorio logico dentro del proyecto"),
):
    """Subir un archivo al proyecto."""
    token = get_token()
    with client(token) as c:
        with source.open("rb") as handle:
            response = c.post(
                f"/projects/{project_id}/files/upload",
                params={"target_subdir": target_subdir} if target_subdir else None,
                files={"upload": (source.name, handle)},
            )
        uploaded = handle_response(response)

    console.print(
        f"Archivo [bold]{uploaded.get('name', source.name)}[/bold] subido a "
        f"[cyan]{uploaded.get('relative_path', 'ruta desconocida')}[/cyan]"
    )


@app.command("download")
def download_project_file(
    project_id: int = typer.Argument(..., help="ID del proyecto"),
    path: str = typer.Argument(..., help="Ruta relativa del archivo dentro del proyecto"),
    dest: Path = typer.Option(Path("./archivos_proyecto"), "--dest", "-d", help="Directorio de destino"),
):
    """Descargar un archivo subido al proyecto."""
    token = get_token()
    dest.mkdir(parents=True, exist_ok=True)
    target = dest / Path(path).name

    with client(token) as c:
        response = c.get(
            f"/projects/{project_id}/files/download",
            params={"path": path},
            follow_redirects=True,
        )
        response.raise_for_status()
        target.write_bytes(response.content)

    console.print(f"Descargado -> [cyan]{target.resolve()}[/cyan]")


@app.command("outputs")
def list_project_outputs(
    project_id: int = typer.Argument(..., help="ID del proyecto"),
):
    """Listar outputs descargables agrupados por etapa."""
    token = get_token()
    with client(token) as c:
        outputs = handle_response(c.get(f"/projects/{project_id}/outputs"))

    if not outputs:
        console.print("No hay outputs disponibles para este proyecto todavia.")
        return

    table = Table(title=f"Outputs del proyecto {project_id}", box=box.ROUNDED, highlight=True)
    table.add_column("Pipeline", style="cyan", no_wrap=True)
    table.add_column("Etapa", style="bold")
    table.add_column("Estado", no_wrap=True)
    table.add_column("Artefactos", style="green")

    for entry in outputs:
        artifact_names = ", ".join(artifact.get("name", "-") for artifact in entry.get("artifacts", [])) or "-"
        table.add_row(
            str(entry.get("pipeline_id", "-")),
            f"{entry.get('stage_order_index', 0) + 1}. {entry.get('stage_name', '-')}",
            entry.get("status", "-"),
            artifact_names,
        )
    console.print(table)


def _format_size(size: int | None) -> str:
    if not isinstance(size, (int, float)):
        return "n/a"
    if size < 1024:
        return f"{int(size)} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size / (1024 * 1024):.1f} MB"
