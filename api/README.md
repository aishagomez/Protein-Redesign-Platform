# API

Backend en FastAPI encargado de autenticacion, CRUD de recursos y orquestacion de pipelines.

## Responsabilidades

- registrar e iniciar sesion de usuarios;
- administrar proyectos y pipelines;
- importar herramientas XML al arrancar;
- lanzar y monitorear `StageExecution`;
- recibir callbacks internos de los workers;
- exponer resumen de monitoreo.

## Archivos clave

- [main.py](C:/Users/aisha/OneDrive/Escritorio/tesis/Implementación/2. Desarrollo/Segunda versión/api/main.py): arranque, routers y lifespan.
- [import_tool_from_xml.py](C:/Users/aisha/OneDrive/Escritorio/tesis/Implementación/2. Desarrollo/Segunda versión/api/import_tool_from_xml.py): importacion declarativa de herramientas.
- [routers/auth.py](C:/Users/aisha/OneDrive/Escritorio/tesis/Implementación/2. Desarrollo/Segunda versión/api/routers/auth.py): registro, login y `/auth/me`.
- [routers/orchestration.py](C:/Users/aisha/OneDrive/Escritorio/tesis/Implementación/2. Desarrollo/Segunda versión/api/routers/orchestration.py): ejecucion y seguimiento por etapas.
- [services/orchestration.py](C:/Users/aisha/OneDrive/Escritorio/tesis/Implementación/2. Desarrollo/Segunda versión/api/services/orchestration.py): logica de despacho y callbacks.

## Endpoints principales

- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`
- `GET /projects/`
- `POST /projects/`
- `GET /projects/{project_id}/pipelines/`
- `POST /projects/{project_id}/pipelines/`
- `POST /projects/{project_id}/pipelines/{pipeline_id}/run`
- `GET /executions/{pipeline_id}`
- `GET /executions/{pipeline_id}/stages`
- `POST /executions/{pipeline_id}/approve`
- `POST /executions/{pipeline_id}/retry-stage`
- `GET /monitoring/summary`

## Notas operativas

- la base de datos se recrea en cada arranque;
- las herramientas XML se cargan desde `api/examples`;
- el login usa `email` en el campo OAuth `username`;
- los callbacks internos validan `X-Internal-Token`.
