import typer
from rich.console import Console
from rich.table import Table
from rich import box

from cli.config import client, handle_response, get_token

app     = typer.Typer(no_args_is_help=True)
console = Console()


@app.command("list")
def list_projects():
    token = get_token()
    with client(token) as c:
        projects = handle_response(c.get("/projects/"))

    if not projects:
        console.print("No tienes proyectos aún. Crea uno con: cli projects create")
        return

    table = Table(title="Proyectos", box=box.ROUNDED, highlight=True)
    table.add_column("ID",          style="cyan",  no_wrap=True)
    table.add_column("Nombre",      style="bold")
    table.add_column("Descripción", style="dim")
    table.add_column("Creado",      style="green")

    for p in projects:
        table.add_row(
            str(p.get("id", "")),
            p.get("name", ""),
            p.get("description", "—"),
            p.get("created_at", "")[:10],
        )
    console.print(table)


@app.command("create")
def create_project(
    name:        str = typer.Option(..., prompt=True, help="Nombre del proyecto"),
    description: str = typer.Option("",  prompt=True, help="Descripción (opcional)"),
):
    token = get_token()
    with client(token) as c:
        project = handle_response(
            c.post("/projects/", json={"name": name, "description": description})
        )
    console.print(f"Proyecto [bold]{project['name']}[/bold] creado con ID [cyan]{project['id']}[/cyan]")


@app.command("show")
def show_project(
    project_id: int = typer.Argument(..., help="ID del proyecto"),
):
    token = get_token()
    with client(token) as c:
        p = handle_response(c.get(f"/projects/{project_id}"))

    console.print(f"\n[bold]Proyecto[/bold]  : {p['name']} (ID {p['id']})")
    console.print(f"[bold]Descripción[/bold]: {p.get('description','—')}")
    console.print(f"[bold]Creado[/bold]     : {p.get('created_at','')[:19]}\n")


@app.command("delete")
def delete_project(
    project_id: int  = typer.Argument(..., help="ID del proyecto a eliminar"),
    yes:        bool = typer.Option(False, "--yes", "-y", help="Confirmar sin prompt"),
):
    if not yes:
        typer.confirm(f"¿Eliminar proyecto {project_id}?", abort=True)
    token = get_token()
    with client(token) as c:
        handle_response(c.delete(f"/projects/{project_id}"))
    console.print(f"Proyecto [cyan]{project_id}[/cyan] eliminado.")
