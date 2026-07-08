from celery import Celery

celery_app = Celery(
    "docking_worker",
    broker="amqp://user:password@broker:5672//",
    include=["tasks"],
)

celery_app.conf.update(
    result_backend="rpc://",
    broker_connection_retry_on_startup=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_time_limit=6 * 3600,
    task_soft_time_limit=6 * 3600 - 60,
    worker_send_task_events=True,
    task_send_sent_event=True,
    task_routes={
        "tasks.run_stage": {"queue": "docking"},
    },
)
