# CLI

Cli para la plataforma de pipelines bioinformaticos.

## Instalación

Desde la carpeta `bio-cli`:

```bash
python -m venv .venv
source .venv/bin/activate 
python -m pip install -e .
bio-cli --help
```

En Windows (powershell), activa el entorno con:

```bash
.\.venv\Scripts\Activate.ps1
```

---

## Uso

```bash
bio-cli --help
```

### Autenticacion

```bash
bio-cli auth register
bio-cli auth login
bio-cli auth whoami
bio-cli auth logout
```

### Proyectos

```bash
bio-cli projects list
bio-cli projects create
bio-cli projects show 3
bio-cli projects delete 3
```

### Archivos

```bash
# Listar archivos subidos
bio-cli files list 1

# Subir un archivo al proyecto
bio-cli files upload 1 ./inputs/receptor.pdb

# Descargar un archivo del proyecto
bio-cli files download 1 shared_inputs/receptor.pdb --dest ./descargas

# Ver outputs disponibles por proyecto
bio-cli files outputs 1
```

### Pipelines

```bash
# Listar pipelines de un proyecto
bio-cli pipelines list 1

# Crear pipeline
bio-cli pipelines create 1

# Lanzar y monitorear en tiempo real
bio-cli pipelines run 1 2 --stage-order ./stage_order.json

# Solo ver estado
bio-cli pipelines status 2

# Monitorear pipeline ya lanzado
bio-cli pipelines status 2 --watch

# Aprobar la siguiente etapa si el pipeline queda en pausa
bio-cli pipelines approve 2

# Retry manual de una etapa
bio-cli pipelines retry 2 --stage-order-index 2 --new-params "{\"maxm\": 20000}"
```

### Resultados

```bash
# Ver tabla de resultados
bio-cli results show 2

# Ver detalle por etapa
bio-cli results stages 2

# Descargar todos los outputs
bio-cli results download 2 --dest ./mis_resultados

# Descargar solo una etapa
bio-cli results download 2 --stage interaction_optimization --dest ./interaction_optimization
```

### Reportes

```bash
# Ver resumen del proyecto
bio-cli reports project 1

# Ver resumen de un pipeline
bio-cli reports pipeline 1 2

# Descargar reporte del proyecto
bio-cli reports download-project 1 --format md --dest ./reportes

# Descargar reporte del pipeline
bio-cli reports download-pipeline 1 2 --format json --dest ./reportes
```

---

## Variables de entorno

| Variable | Default | Descripcion |
|---|---|---|
| `bio-cli_URL` | `http://localhost:8000` | URL base de la API |
| `bio-cli_URL` | `http://localhost:8000` | Alias legacy |

Tambien puedes cambiarla al hacer login:

```bash
bio-cli auth login --url http://mi-servidor:8000
```

---

## Estructura del proyecto

```text
cli/
|-- cli/
|   |-- __init__.py
|   |-- main.py
|   |-- config.py
|   |-- auth.py
|   |-- projects.py
|   |-- pipelines.py
|   |-- files.py
|   |-- results.py
|   `-- reports.py
|-- cli.spec
|-- build.bat
|-- build.sh
`-- pyproject.toml
```
