import httpx
import typer
from rich.console import Console
from rich.panel import Panel

from cli.config import client, handle_response, save_config, load_config, get_base_url

app     = typer.Typer(no_args_is_help=True)
console = Console()


@app.command("register")
def register(
    username: str = typer.Option(..., prompt=True,               help="Nombre de usuario"),
    email:    str = typer.Option(..., prompt=True,               help="Correo electrónico"),
    password: str = typer.Option(..., prompt=True, hide_input=True, help="Contraseña"),
):
    with client() as c:
        data = handle_response(
            c.post("/auth/register", json={"username": username, "email": email, "password": password})
        )
    console.print(Panel(f"Usuario [bold]{username}[/bold] registrado. Ya puedes hacer login. ;)", style="green"))


@app.command("login")
def login(
    email: str = typer.Option(..., prompt=True,               help="Correo electrónico"),
    password: str = typer.Option(..., prompt=True, hide_input=True, help="Contraseña"),
    url:      str = typer.Option(None,                           help="URL base de la API (opcional)"),
):
    cfg = load_config()
    base = url or cfg.get("base_url", get_base_url())

    with httpx.Client(base_url=base, timeout=30.0) as c:
        data = handle_response(
            c.post(
                "/auth/login",
                data={"username": email, "password": password},
            )
        )

    token = data.get("access_token") or data.get("token")
    if not token:
        typer.echo("Error: la API no devolvió un token. :(", err=True)
        raise typer.Exit(1)

    save_config({"token": token, "username": email, "base_url": base})
    console.print(Panel(f"Bienvenido, [bold]{email}[/bold]!", style="green"))


@app.command("logout")
def logout():
    save_config({})
    console.print("Sesión cerrada, vuelve pronto. :)")


@app.command("whoami")
def whoami():
    cfg = load_config()
    username = cfg.get("username", "desconocido")
    base     = cfg.get("base_url", get_base_url())
    token    = cfg.get("token")
    status   = "autenticado" if token else "sin sesión"
    console.print(Panel(
        f"Usuario : [bold]{username}[/bold]\nServidor: {base}\nEstado  : {status}",
        title="Sesión actual",
    ))
