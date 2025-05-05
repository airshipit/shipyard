#!/bin/bash

# Core Section
export AIRFLOW__CORE__DAGS_FOLDER=~/airflow/dags
export AIRFLOW__CORE__EXECUTOR=CeleryExecutor
export AIRFLOW__CORE__FERNET_KEY=fKp7omMJ4QlTxfZzVBSiyXVgeCK-6epRjGgMpEIsjvs=
export AIRFLOW__CORE__PARALLELISM=32
export AIRFLOW__CORE__MAX_ACTIVE_TASKS_PER_DAG=1
export AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION=False
export AIRFLOW__CORE__HIDE_SENSITIVE_VAR_CONN_FIELDS=True
export AIRFLOW__CORE__KILLED_TASK_CLEANUP_TIME=60
export AIRFLOW__CORE__DAG_RUN_CONF_OVERRIDES_PARAMS=False
export AIRFLOW__CORE__LOAD_EXAMPLES=False
export AIRFLOW__CORE__SIMPLE_AUTH_MANAGER_ALL_ADMINS=True

# Database Section
export AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql+psycopg2://airflow:password@localhost:5432/airflow

# API Section
export AIRFLOW__API__AUTH_BACKENDS=airflow.api.auth.backend.default
export AIRFLOW__API__BASE_URL=http://localhost
export AIRFLOW__API__HOST=localhost
export AIRFLOW__API__PORT=8080
export AIRFLOW__API__WORKERS=4
export AIRFLOW__API__WORKER_TIMEOUT=120
export AIRFLOW__API__SSL_CERT=
export AIRFLOW__API__SSL_KEY=
export AIRFLOW__API__ACCESS_LOGFILE=-

# Logging Section
export AIRFLOW__LOGGING__BASE_LOG_FOLDER=~/airflow/logs
export AIRFLOW__LOGGING__LOG_FILENAME_TEMPLATE="{{ ti.dag_id }}/{{ ti.run_id }}/{{ ti.task_id }}/{%% if ti.map_index >= 0 %%}{{ ti.map_index }}/{%% endif %%}{{ try_number|default(ti.try_number) }}.log"
export AIRFLOW__LOGGING__LOGGING_LEVEL=DEBUG
export AIRFLOW__LOGGING__CELERY_LOGGING_LEVEL=INFO

# Celery Section
export AIRFLOW__CELERY__BROKER_URL=amqp://airflow:password@localhost:5672/
export AIRFLOW__CELERY__RESULT_BACKEND=db+postgresql://airflow:password@localhost:5432/airflow
export AIRFLOW__CELERY__WORKER_CONCURRENCY=16
export AIRFLOW__CELERY__TASK_TRACK_STARTED=True
export AIRFLOW__CELERY__TASK_TIME_LIMIT=300
export AIRFLOW__CELERY__WORKER_LOG_SERVER_PORT=8793

echo "Airflow environment variables have been set."


# cd src/bin/shipyard_airflow/; source .tox/integration/bin/activate; source ../../../tools/airflow_env_vars.sh
