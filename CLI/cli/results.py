import typer
import shutil
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.syntax import Syntax
from rich import box
import json

from cli.config import client, handle_response, get_token

app     = typer.Typer(no_args_is_help=True)
console = Console()


@app.command("show")
def show_results(
    pipeline_id: int = typer.Argument(..., help="ID del pipeline / ejecución"),
):
    token  = get_token()
    with client(token) as c:
        state  = handle_response(c.get(f"/executions/{pipeline_id}"))
        stages = handle_response(c.get(f"/executions/{pipeline_id}/stages"))

    status = state.get("status", "unknown")
    console.print(f"\nPipeline [cyan]{pipeline_id}[/cyan] — Estado: [bold]{status}[/bold]\n")

    if not stages:
        console.print("Sin información de etapas.")
        return

    table = Table(title="Resultados por etapa", box=box.ROUNDED, highlight=True)
    table.add_column("Etapa",   style="bold")
    table.add_column("Estado",  no_wrap=True)
    table.add_column("Inicio",  style="dim")
    table.add_column("Fin",     style="dim")
    table.add_column("Output",  style="cyan", overflow="fold")

    for s in stages:
        s_status = s.get("status", "—")
        icon = {"completed": "Completed :)", "failed": "Failed :(", "running": "Running ;)", "pending": "Pending..."}.get(s_status, "Unknown")
        outputs = s.get("output_files") or []
        if isinstance(outputs, str):
            outputs = [outputs]
        output = ", ".join(Path(path).name for path in outputs) if outputs else "—"
        table.add_row(
            s.get("stage_name", "?"),
            f"{icon} {s_status}",
            (s.get("started_at")  or "—")[:19],
            (s.get("finished_at") or "—")[:19],
            str(output)[:80],
        )
    console.print(table)

    metrics = state.get("metrics") or state.get("result")
    if metrics:
        console.print("\n[bold]Métricas finales:[/bold]")
        console.print(Syntax(json.dumps(metrics, indent=2, ensure_ascii=False), "json", theme="monokai"))


@app.command("stages")
def show_stages(
    pipeline_id: int = typer.Argument(..., help="ID del pipeline / ejecución"),
):
    token = get_token()
    with client(token) as c:
        stages = handle_response(c.get(f"/executions/{pipeline_id}/stages"))

    if not stages:
        console.print("Sin etapas registradas.")
        return

    for s in stages:
        status = s.get("status", "?")
        icon   = {"completed": "Completed :)", "failed": "Failed :(", "running": "Running ;)", "pending": "Pending..."}.get(status, "Unknown")
        console.rule(f"{icon} {s.get('stage_name','?')} [{status}]")
        console.print(f"  Inicio : {s.get('started_at','—')}")
        console.print(f"  Fin    : {s.get('finished_at','—')}")
        outputs = s.get("output_files") or []
        if isinstance(outputs, str):
            outputs = [outputs]
        if outputs:
            console.print(f"  Output files: {', '.join(Path(path).name for path in outputs)}")
        console.print()


@app.command("download")
def download_results(
    pipeline_id: int  = typer.Argument(..., help="ID del pipeline / ejecución"),
    dest:        Path = typer.Option(
        Path("./resultados"),
        "--dest", "-d",
        help="Directorio de destino",
    ),
    stage:       str  = typer.Option(None, "--stage", "-s", help="Filtrar por etapa específica"),
):

    token = get_token()
    with client(token) as c:
        stages = handle_response(c.get(f"/executions/{pipeline_id}/stages"))

    if stage:
        stages = [s for s in stages if s.get("stage_name") == stage]

    if not stages:
        console.print("No hay etapas para descargar.")
        return

    dest.mkdir(parents=True, exist_ok=True)
    downloaded = 0

    for s in stages:
        stage_name  = s.get("stage_name", "unknown")
        output_paths = s.get("output_files") or []
        if isinstance(output_paths, str):
            output_paths = [output_paths]

        if not output_paths:
            console.print(f"Etapa [bold]{stage_name}[/bold] sin archivos de salida — omitida.")
            continue

        for output_path in output_paths:
            if not isinstance(output_path, str):
                continue

            downloaded_one = False
            try:
                with client(token) as c:
                    r = c.get(
                        f"/executions/stages/{s['id']}/artifacts/download",
                        params={"path": output_path},
                        follow_redirects=True,
                    )
                if r.status_code == 200:
                    target = dest / stage_name / Path(output_path).name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(r.content)
                    console.print(f"Descargado [green]{stage_name}[/green] -> {target}")
                    downloaded += 1
                    downloaded_one = True
            except Exception:
                downloaded_one = False

            if downloaded_one:
                continue

            src = Path(output_path)
            if src.exists():
                target = dest / stage_name / Path(output_path).name
                target.parent.mkdir(parents=True, exist_ok=True)
                if src.is_dir():
                    shutil.copytree(src, target, dirs_exist_ok=True)
                else:
                    shutil.copy2(src, target)
                console.print(f"Copiado [green]{stage_name}[/green] -> {target}")
                downloaded += 1
            else:
                console.print(f"Ruta no encontrada localmente: {output_path}")

    if downloaded:
        console.print(f"\n{downloaded} archivo(s) descargado(s) en [cyan]{dest.resolve()}[/cyan]")
    else:
        console.print("\nNo se pudo descargar ningún archivo. Verifica que el servidor esté activo.")
