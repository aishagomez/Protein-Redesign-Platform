import sys
from pathlib import Path

block_cipher = None

a = Analysis(
    ["cli/main.py"],
    pathex=[str(Path(".").resolve())],
    binaries=[],
    datas=[],
    hiddenimports=[
        "cli.auth",
        "cli.projects",
        "cli.pipelines",
        "cli.results",
        "cli.config",
        # Typer / Click internals
        "typer",
        "typer.main",
        "click",
        "click.core",
        # Rich
        "rich",
        "rich.console",
        "rich.table",
        "rich.live",
        "rich.panel",
        "rich.text",
        "rich.progress",
        "rich.syntax",
        # httpx
        "httpx",
        "httpx._client",
        "anyio",
        "anyio._backends._asyncio",
        "certifi",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "numpy", "pandas"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="cli",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,          # CLI → consola visible
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,            
)
