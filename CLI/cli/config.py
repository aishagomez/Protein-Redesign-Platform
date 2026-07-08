"""
Configuración global y cliente HTTP compartido.
"""
import os
import json
from pathlib import Path
from typing import Optional

import httpx
import typer

CONFIG_DIR  = Path(typer.get_app_dir("cli"))
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_BASE_URL = os.getenv("CLI_URL") or os.getenv("cli_URL", "http://localhost:8000")


def load_config() -> dict:
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return {}


def save_config(data: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(data, indent=2))


def get_token() -> str:
    cfg = load_config()
    token = cfg.get("token")
    if not token:
        typer.echo("Error: no has iniciado sesión :(. Usa: cli auth login.", err=True)
        raise typer.Exit(1)
    return token


def get_base_url() -> str:
    return load_config().get("base_url", DEFAULT_BASE_URL)


def client(token: Optional[str] = None) -> httpx.Client:
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return httpx.Client(
        base_url=get_base_url(),
        headers=headers,
        timeout=30.0,
    )


def handle_response(response: httpx.Response) -> dict:
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError:
        try:
            detail = response.json().get("detail", response.text)
        except Exception:
            detail = response.text
        typer.echo(f"Error {response.status_code}: {detail}. Try again ;)", err=True)
        raise typer.Exit(1)
    return response.json()
