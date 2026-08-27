# Manual de Usuario - Plataforma de Pipelines Bioinformáticos

## Flujo de Trabajo Básico

1. **Registro e Inicio de Sesión**: Crea una cuenta y autentícate.
2. **Crear Proyecto**: Organiza tus trabajos en proyectos.
3. **Subir Archivos**: Carga archivos de entrada (PDB, MSA, etc.).
4. **Crear Pipeline**: Define las etapas y parámetros.
5. **Ejecutar Pipeline**: Lanza la ejecución y monitorea progreso.
6. **Descargar Resultados**: Obtén los archivos generados.
7. **Exportar Reportes**: Descarga resúmenes en `md` o `json`.

## Uso de la GUI

La interfaz grafica web está disponible, por defecto, en `http://localhost:5173`.
Desde ella se puede registrar usuarios, iniciar sesion, crear proyectos,
componer ejecuciónes por etapas, monitorear estados, descargar archivos y
consultar reportes sin usar comandos de consola.

### Acceso e Inicio de Sesión

1. Abre el frontend en el navegador.
2. Si aun no tienes usuario, entra a `Crear cuenta`.
3. Completa `Username`, `Email`, `Password` y `Confirm password`.
4. Vuelve al login e ingresa con email y contraseña.

Cuando la autenticación es correcta, la aplicacion carga la consola principal.
El menu lateral muestra las secciones disponibles:

- `Dashboard`
- `Projects`
- `My Files / Outputs`
- `Reports`
- `Documentation`
- `Tools`
- `Monitoring` solo para usuarios administradores
- `About Us`

### Dashboard

El `Dashboard` resume la actividad del sistema. En esta pantalla puedes:

- Ver KPIs de pipelines activos, ejecuciónes en curso, fallos recientes y
  herramientas disponibles.
- Revisar la tabla `Pipeline executions` con pipelines recientes.
- Abrir un pipeline con el botón `Open`.
- Consultar fallos recientes y herramientas importadas.

Para usuarios no administradores, algunos datos de observabilidad profunda se
muestran de forma limitada y se consultan completamente desde la vista admin.

### Projects

La pantalla `Projects` permite administrar proyectos y pipelines.

Para crear un proyecto:

1. Entra a `Projects`.
2. En el panel `Create project`, escribe `Name` y, opcionalmente,
   `Description`.
3. Pulsa `Create project`.

Para crear un pipeline dentro de un proyecto:

1. Busca el proyecto en `Project inventory`.
2. Escribe una version en `Pipeline version`, por ejemplo `v1`.
3. Pulsa `Add pipeline`.
4. Abre el pipeline desde la lista para entrar al detalle.

También puedes eliminar un pipeline desde `Project inventory`. El primer clic
activa la confirmacion y el segúndo clic en `Confirm delete` ejecuta el borrado.

### Detalle de Pipeline y Compositor de Ejecución

Al abrir un pipeline se muestra la vista `Pipeline #<id>`, que contiene el
estado de la ejecución, el compositor de etapas y el detalle de cada etapa.

#### Revisar Estado

En `Pipeline state` se observa:

- Versión del pipeline.
- Estado actual (`pending`, `running`, `waiting_for_approval`, `completed` o
  `failed`).
- Si la ejecución usa pausa entre etapas.
- Lista de etapas ejecutadas o en ejecución.

Selecciona una etapa para ver su informacion en `Execution detail`.

#### Componer y Lanzar una Ejecución

Para lanzar un pipeline desde la GUI:

1. Entra al detalle del pipeline.
2. En `Execution composer`, pulsa `Add stage`.
3. Selecciona la `Phase`: `Refinement`, `Docking`, `Interaction Optimization` u otra fase
   disponible según las herramientas importadas.
4. Selecciona la `Tool` correspondiente.
5. Completa los parámetros principales. Los parámetros avanzados aparecen en
   `Advanced parameters`.
6. Para parámetros de tipo archivo, selecciona un archivo ya subido o usa
   `Upload file` dentro del campo. Los directorios se cargan como `.zip`.
7. Repite `Add stage` para agregar las etapas necesarias.
8. Si quieres revisar manualmente entre etapas, activa `Pause between stages`.
9. Pulsa `Launch execution`.

Los parámetros `output_dir` y otros parámetros marcados como salida no se
rellenan manualmente. La plataforma los asigna de forma automatica. Algunos
parámetros de docking y optimización de interacciones también se resuelven desde salidas previas,
por ejemplo receptor, ligando o escenario intermedio.

#### Aprobar una Etapa Pausada

Si se activó `Pause between stages`, el pipeline puede quedar en
`waiting_for_approval`.

1. Selecciona la etapa pausada en `Pipeline state`.
2. En `Execution detail`, revisa los datos y artefactos disponibles.
3. Pulsa `Approve next stage`.

Después de aprobar, la plataforma continua con la siguiente etapa definida en
el compositor.

#### Reintentar una Etapa

En `Manual controls` puedes relanzar una etapa con parámetros nuevos:

1. Escoge la etapa en `Stage to retry`.
2. Escribe los parámetros nuevos en caso de necesitarlo.


### My Files / Outputs

La pantalla `My Files / Outputs` centraliza entradas subidas y salidas
generadas.

Para subir archivos de entrada:

1. Selecciona el proyecto en `Project scope`.
2. Pulsa `Upload file`.
3. Selecciona el archivo local.

Los archivos subidos desde esta pantalla se guardan como entradas compartidas
del proyecto (`shared_inputs`) y quedan disponibles para los formularios de
parámetros del compositor.

Para descargar entradas:

1. En `Uploaded inputs`, ubica el archivo.
2. Haz clic sobre el elemento para descargarlo.

Para descargar salidas:

1. En `Available outputs`, abre el grupo del pipeline y etapa deseada.
2. Haz clic sobre el artefacto. La tarjeta muestra el tipo de archivo y el
   tamaño.

### Reports

La pantalla `Reports` permite inspeccionar y exportar reportes.

1. Selecciona el `Project`.
2. Selecciona el `Pipeline`.
3. Revisa el resumen del proyecto y el resumen del pipeline.
4. Usa `Download MD` o `Download JSON` en `Project report` o
   `Pipeline report`.

La vista tambien incluye:

- Comparacion entre pipelines del proyecto.
- Indicadores cientificos destacados, como mejor energia de docking o mejor
  TM-score cuando están disponibles.
- Visualizaciones simples de duracion, TM-score, tamaño de salidas, atomos y
  energia.
- Resumen de etapas con estado, herramienta, duracion, artefactos y metricas
  cientificas extraidas.

### Documentation

La pantalla `Documentation` lista documentos servidos por el modulo de
documentacion del backend. Desde aqui puedes abrir o descargar el manual de
usuario y otras referencias incluidas en `docs`.

### Tools

La pantalla `Tools` muestra las herramientas importadas desde XML:

- Nombre de la herramienta.
- Tipo de servicio o fase.
- Versión.
- Descripción.
- Runtime usado.
- Parámetros disponibles y tipos de dato.

Esta vista sirve para confirmar que una herramienta está cargada antes de
usarla en el compositor de ejecución.

### Monitoring

La pantalla `Monitoring` está disponible para usuarios administradores. Muestra
herramientas disponibles y pipelines activos desde la perspectiva del sistema.
Usala para revisar salud operativa y estado general de ejecuciónes.

### Recomendaciones de Uso en la GUI

- Sube primero los archivos de entrada desde `My Files / Outputs` o desde el
  campo de archivo del compositor.
- Verifica que las herramientas aparezcan en `Tools` antes de crear una
  ejecución.
- Usa `Pause between stages` cuando necesites inspeccionar salidas intermedias
  antes de continuar.
- Descarga artefactos desde `Execution detail` si estás revisando una etapa
  especifica, o desde `My Files / Outputs` si quieres navegar todas las salidas
  del proyecto.
- Revisa `Reports` al finalizar para comparar pipelines y exportar resultados.

## Autenticación

### Registro

- Ve a la interfaz web o usa la CLI.
- Proporciona: nombre de usuario, email y contraseña.

### Inicio de Sesión

- Usa email y contraseña.
- El token JWT se guarda automaticamente para sesiones posteriores.

### CLI: Autenticación

```bash
bio-cli auth register
bio-cli auth login
bio-cli auth whoami
bio-cli auth logout
```

## Gestión de Proyectos

Los proyectos organizan tus pipelines y archivos.

### Crear Proyecto

- Web: Navega a `Projects` > `Create`.
- CLI:

```bash
bio-cli projects create --name "Mi Proyecto" --description "Descripción opcional"
```

### Listar Proyectos

```bash
bio-cli projects list
```

### Ver Detalles de Proyecto

```bash
bio-cli projects show <project_id>
```

### Eliminar Proyecto

```bash
bio-cli projects delete <project_id> --yes
```

## Gestión de Archivos

### Subida de Archivos

- Web: En `My Files / Outputs`, usa `Upload file`.
- CLI:

```bash
bio-cli files upload <project_id> ./inputs/receptor.pdb
bio-cli files upload <project_id> ./inputs/MSA.tsv --target-subdir shared_inputs
```

Los archivos se almacenan por usuario y proyecto. Tipos comunes:

- PDB para estructuras moleculares.
- Archivos MSA para optimización de interacciones.
- Otros inputs específicos de herramientas.

### Ver Archivos Subidos

```bash
bio-cli files list <project_id>
bio-cli files outputs <project_id>
```

### Descargar Archivo de Proyecto

```bash
bio-cli files download <project_id> shared_inputs/receptor.pdb --dest ./descargas
```

## Creación y Ejecución de Pipelines

### Crear Pipeline

```bash
bio-cli pipelines create <project_id> --version "v1.0" --parameters "{}"
```

### Definir Etapas

Las etapas se ejecutan en secuencia. Algunos parámetros se resuelven automaticamente desde etapas previas.

#### Refinement

- Input: PDB subido al proyecto.
- Output: PDB refinado.

#### Docking

- Input: receptor y ligando refinados.
- Nota: `receptor_path` y `ligand_path` se resuelven automaticamente si vienes de refinement.

#### Interaction Optimization

- Input: complejo seleccionado desde docking + MSA.
- Nota: el escenario intermedio se construye automaticamente.

### Ejecutar Pipeline

```bash
bio-cli pipelines run <project_id> <pipeline_id> --stage-order .\example_rde.json --watch
```

También puedes pasar la configuración inline:

```bash
bio-cli pipelines run <project_id> <pipeline_id> --stage-order "[{\"stage_name\":\"refinement\",\"tool_id\":1,\"tool\":
\"gnn_refine\",\"params\":{}}]"
```

### Monitoreo

```bash
bio-cli pipelines status <pipeline_id> --watch
```

Estados frecuentes:

- `pending`
- `running`
- `waiting_for_approval`
- `completed`
- `failed`

### Aprobar la Siguiente Etapa

Si el pipeline fue lanzado con pausa entre etapas:

```bash
bio-cli pipelines approve <pipeline_id>
```

### Retry Manual de una Etapa

```bash
bio-cli pipelines retry <pipeline_id> --stage-order-index 2 --new-params "{\"maxm\": 20000}"
```

## Resultados y Descargas

### Ver Resultados

```bash
bio-cli results show <pipeline_id>
bio-cli results stages <pipeline_id>
```

### Descargar Outputs

```bash
bio-cli results download <pipeline_id> --dest ./resultados
bio-cli results download <pipeline_id> --stage interaction_optimization --dest ./interaction_optimization
```

Los outputs se generan en rutas del estilo:

`/persistent_storage/outputs/<user>/<stage>/pipeline_<id>/stage_<order>`

## Reportes

### Ver Resumen del Proyecto

```bash
bio-cli reports project <project_id>
```

### Ver Resumen de un Pipeline

```bash
bio-cli reports pipeline <project_id> <pipeline_id>
```

### Descargar Reportes

```bash
bio-cli reports download-project <project_id> --format md --dest ./reportes
bio-cli reports download-pipeline <project_id> <pipeline_id> --format json --dest ./reportes
```

## Uso Avanzado

### Parámetros Avanzados

- En la web, se agrupan separadamente.
- En CLI, se incluyen en el JSON de etapas o en `--new-params`.

### Pausas Entre Etapas

- Sirven para aprobación manual y revision intermedia.

### Logs y Debugging

- La web muestra un resumen más limpio del estado.
- Para fallos profundos, revisa logs de API y workers.

## Notas Técnicas

- La plataforma usa Celery para workers asincronos.
- Los archivos se almacenan en `/persistent_storage`.
- API REST por defecto en `http://localhost:8000`.
- Frontend por defecto en `http://localhost:5173`.
- CLI requiere Python 3.10+ y dependencias instaladas.
