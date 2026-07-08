from celery import Celery

celery_app = Celery(
    "pipeline",
    broker="amqp://user:password@broker:5672//",
    include=["tasks"],
)

STAGE_TIMEOUT_HOURS = 6
STAGE_TIMEOUT_SECONDS = int(STAGE_TIMEOUT_HOURS * 3600)

celery_app.conf.update(
    result_backend="rpc://",
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,

    # Hard kill de seguridad (el watchdog actúa antes vía Events)
    task_time_limit=STAGE_TIMEOUT_SECONDS,
    task_soft_time_limit=STAGE_TIMEOUT_SECONDS - 60,

    # CRÍTICO: habilitar eventos para que el orquestador detecte workers caídos
    worker_send_task_events=True,
    task_send_sent_event=True,

    task_routes={
        "tasks.run_stage": {"queue": "pipeline"},  # cola única genérica
        # O mantener colas por etapa si los workers están en servidores separados:
        # "tasks.run_stage": {"queue": "pipeline"},
    },
)