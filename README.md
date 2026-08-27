# Plataforma de Pipelines Bioinformaticos

Sistema para componer, ejecutar y monitorear pipelines bioinformaticos por etapas. La plataforma integra una API FastAPI, una interfaz web React/Vite, una CLI Typer, PostgreSQL, RabbitMQ, workers Celery y runtimes cientificos aislados en Docker.


## Modulos del repositorio

- [api](api/README.md): backend FastAPI, modelos, routers, autenticacion y orquestacion.
- [frontend](frontend/README.md): consola web en React + Vite.
- [CLI](CLI/README.md): cliente de linea de comandos.
- [workers](workers/README.md): workers Celery por etapa cientifica.
- [docs](docs/user_manual.md): manual de usuario y ejemplos de `stage_order`.
- [email-notifier](email-notifier/): servicio interno para notificaciones por correo.
- [observability](observability/): componentes auxiliares de observabilidad.
- [persistent_storage](persistent_storage/): volumen local para uploads, runs, outputs, reportes y escenarios generados.

## Arquitectura

Servicios principales definidos en [docker-compose.yml](docker-compose.yml):

| Servicio | Responsabilidad |
| --- | --- |
| `db` | PostgreSQL 15 para datos de la aplicacion. |
| `broker` | RabbitMQ con UI de administracion. |
| `api` | API REST, autenticacion, CRUD, orquestador y documentacion. |
| `frontend` | Interfaz web React/Vite. |
| `refinement-worker` | Ejecuta `gnn_refine`. |
| `docking-worker` | Ejecuta `gramm`. |
| `interaction-optimization-worker` | Ejecuta `protein_ea`. |
| `gnnrefine-runtime` | Imagen cientifica para refinamiento. |
| `gramm-runtime` | Imagen cientifica para docking. |
| `protein-ea-runtime` | Imagen cientifica para optimización de interacciones. |
| `email-notifier` | Envio interno de notificaciones. |
| `pgadmin` | Administracion visual de PostgreSQL. |

Los workers no consultan PostgreSQL directamente. Reciben desde la API un `tool_contract`, preparan un workspace en `persistent_storage/runs`, ejecutan el runtime Docker correspondiente, publican salidas en `persistent_storage/outputs` y reportan el resultado a la API mediante callbacks internos.

## Flujo de ejecucion

1. La API arranca, crea las tablas actuales e importa herramientas XML desde [api/examples](api/examples/).
2. El usuario se registra o inicia sesion.
3. El usuario crea un proyecto.
4. El usuario crea un pipeline y define el `stage_order`.
5. El orquestador crea registros `StageExecution` y despacha cada etapa a su cola Celery.
6. Cada worker ejecuta su runtime cientifico y publica artefactos.
7. Si el pipeline usa `pause_between_stages`, queda en `waiting_for_approval` antes de avanzar.
8. Al completar el pipeline, los outputs y reportes quedan disponibles desde la web y la CLI.

## Herramientas importadas

En estos documentos se puede configurar los recursos de cada herramienta.

- [gnnrefine.xml](api/examples/gnnrefine.xml): `gnn_refine`
- [gramm.xml](api/examples/gramm.xml): `gramm`
- [protein_ea.xml](api/examples/protein_ea.xml): `protein_ea`
- [atomrefine.xmx](api/examples/atomrefine.xml): `atom_refine`

## Requisitos

- Docker y Docker Compose.
- Puertos libres: `5432`, `5672`, `8000`, `5173`, `15672` y `5050`.

## Puesta en marcha

```bash
docker compose up --build
```

Una vez levantado el stack:

- API: `http://localhost:8000`
- Frontend: `http://localhost:5173`
- RabbitMQ UI: `http://localhost:15672`
- pgAdmin: `http://localhost:5050`

Para reconstruir solo un servicio:

```bash
docker compose build api
docker compose up -d api
```

## Uso desde la web

1. Abre `http://localhost:5173`.
2. Crea una cuenta o inicia sesion.
3. Crea un proyecto en `Projects`.
4. Sube entradas desde `My Files / Outputs` o desde el compositor.
5. Crea un pipeline, agrega etapas y pulsa `Launch execution`.
6. Revisa el progreso en el detalle del pipeline.
7. Descarga artefactos desde `Execution detail` o `My Files / Outputs`.
8. Exporta reportes desde `Reports`.

El manual completo esta en [docs/user_manual.md](docs/user_manual.md) y tambien se sirve desde la seccion `Documentation` del frontend.

## Uso desde CLI

La CLI vive en [CLI](CLI/README.md). Comandos principales:

```bash
cli auth register
cli auth login
cli projects list
cli projects create
cli files upload 1 ./inputs/receptor.pdb
cli files outputs 1
cli pipelines create 1
cli pipelines run 1 2 --stage-order ./docs/example_rde.json --watch
cli pipelines approve 2
cli pipelines retry 2 --stage-order-index 2 --new-params "{\"maxm\": 20000}"
cli results show 2
cli results download 2 --dest ./resultados
cli reports download-pipeline 1 2 --format json --dest ./reportes
```

La variable `cli_URL` permite cambiar la URL base de la API. Por defecto apunta a `http://localhost:8000`.

## Ejemplos de stage_order

Hay ejemplos listos en [docs](docs/):

- [example_r.json](docs/example_r.json): solo refinamiento.
- [example_rd.json](docs/example_rd.json): refinamiento y docking.
- [example_rde.json](docs/example_rde.json): refinamiento, docking y optimización de interacciones.

Tambien existen scripts de humo:

```bash
python use_test.py
python use_test_r+d.py
python use_test_r+d+e.py
```

Ejecutalos con la plataforma levantada.

## Almacenamiento persistente

`persistent_storage` se monta dentro de los contenedores como `/persistent_storage`.

```text
persistent_storage/
|-- uploads/     # entradas subidas por usuario/proyecto
|-- runs/        # workspaces temporales por etapa
|-- outputs/     # artefactos publicados por etapa
|-- reports/     # reportes exportados
`-- generated/   # escenarios o archivos intermedios generados
```

Los outputs siguen una ruta similar a:

```text
/persistent_storage/outputs/<usuario>/<stage>/pipeline_<id>/stage_<orden>
```

## Endpoints relevantes

- `POST /auth/register`
- `POST /auth/login`
- `GET /projects/`
- `POST /projects/{project_id}/pipelines/{pipeline_id}/run`
- `GET /executions/{pipeline_id}`
- `GET /executions/{pipeline_id}/stages`
- `POST /executions/{pipeline_id}/approve`
- `POST /executions/{pipeline_id}/retry-stage`
- `GET /projects/{project_id}/files`
- `POST /projects/{project_id}/files/upload`
- `GET /projects/{project_id}/outputs`
- `GET /projects/{project_id}/reports/overview`
- `GET /projects/{project_id}/pipelines/{pipeline_id}/reports/overview`
- `GET /monitoring/summary`
- `GET /documentation/entries`

## Estructura resumida

```text
.
|-- api/
|-- CLI/
|-- docs/
|-- email-notifier/
|-- frontend/
|-- observability/
|-- persistent_storage/
|-- workers/
|-- docker-compose.yml
|-- use_test.py
|-- use_test_r+d.py
`-- use_test_r+d+e.py
```
