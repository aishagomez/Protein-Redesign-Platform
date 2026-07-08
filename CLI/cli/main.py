import typer

from cli import auth, files, pipelines, projects, reports, results

app = typer.Typer(
    name="cli",
    help="CLI para la plataforma de pipelines bioinformaticos :D",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

app.add_typer(auth.app, name="auth", help="Autenticacion (login / register)")
app.add_typer(projects.app, name="projects", help="Gestion de proyectos")
app.add_typer(pipelines.app, name="pipelines", help="Lanzar y monitorear pipelines")
app.add_typer(files.app, name="files", help="Subir, listar y descargar archivos")
app.add_typer(results.app, name="results", help="Ver y descargar resultados")
app.add_typer(reports.app, name="reports", help="Generar y descargar reportes")

if __name__ == "__main__":
    app()
