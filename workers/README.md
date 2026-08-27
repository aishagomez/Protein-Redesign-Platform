# Workers

Workers Celery especializados por etapa cientifica.

## Workers disponibles

- [refinement-worker](C:/Users/aisha/OneDrive/Escritorio/tesis/Implementación/2. Desarrollo/Segunda versión/workers/refinement-worker): ejecuta `gnn_refine`.
- [docking-worker](C:/Users/aisha/OneDrive/Escritorio/tesis/Implementación/2. Desarrollo/Segunda versión/workers/docking-worker): ejecuta `gramm`.
- [interaction-optimization-worker](C:/Users/aisha/OneDrive/Escritorio/tesis/Implementación/2. Desarrollo/Segunda versión/workers/interaction-optimization-worker): ejecuta `protein_ea`.

## Patrón comun

Cada worker:

1. recibe una `StageExecution`;
2. recibe desde la API el `tool_contract` con herramienta, runtime y parametros declarativos;
3. prepara un workspace en `persistent_storage/runs`;
4. ejecuta el runtime Docker;
5. publica archivos en `persistent_storage/outputs`;
6. reporta `started`, `completed` o `failed` a la API.

## Dependencias operativas

- RabbitMQ
- acceso al socket Docker del host
- `persistent_storage` montado

## Observaciones

- los tres workers dependen del contrato declarativo de `tool_runtimes` y `tool_parameters`, pero no consultan PostgreSQL directamente;
- el worker de optimización de interacciones exige `scenario_path`, `partners` y `ligand_chain`;
- los resultados finales se toman del directorio `output_dir` publicado por cada etapa.
