# Copyright 2017 The Openstack-Helm Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

{{ include "airflow.conf.airflow_values_skeleton" .Values.conf.airflow | trunc 0 }}
{{ include "airflow.conf.airflow" .Values.conf.airflow}}

{{- define "airflow.conf.airflow_values_skeleton" -}}

{{- if not .core -}}{{- set . "core" dict -}}{{- end -}}
{{- if not .webserver -}}{{- set . "webserver" dict -}}{{- end -}}
{{- if not .email -}}{{- set . "email" dict -}}{{- end -}}
{{- if not .smtp -}}{{- set . "smtp" dict -}}{{- end -}}
{{- if not .celery -}}{{- set . "celery" dict -}}{{- end -}}
{{- if not .scheduler -}}{{- set . "scheduler" dict -}}{{- end -}}
{{- if not .mesos -}}{{- set . "mesos" dict -}}{{- end -}}

{{- end -}}

{{- define "airflow.conf.airflow" -}}

[core]
# The home folder for airflow, is ~/airflow
{{ if not .core.airflow_home }}#{{ end }}airflow_home = {{ .core.airflow_home | default "<None>" }}

# The folder where your airflow pipelines live, most likely a
# subfolder in a code repository
{{ if not .core.dags_folder }}#{{ end }}dags_folder = {{ .core.dags_folder | default "<None>" }}

# The folder where airflow should store its log files. This location
{{ if not .core.base_log_folder }}#{{ end }}base_log_folder = {{ .core.base_log_folder | default "<None>" }}

# Airflow can store logs remotely in AWS S3 or Google Cloud Storage. Users
# must supply a remote location URL (starting with either 's3://...' or
# 'gs://...') and an Airflow connection id that provides access to the storage
# location.
{{ if not .core.remote_base_log_folder }}#{{ end }}remote_base_log_folder = {{ .core.remote_base_log_folder | default "<None>" }}
{{ if not .core.remote_log_conn_id }}#{{ end }}remote_log_conn_id = {{ .core.remote_log_conn_id | default "<None>" }}
# Use server-side encryption for logs stored in S3
{{ if not .core.encrypt_s3_logs }}#{{ end }}encrypt_s3_logs = {{ .core.encrypt_s3_logs | default "<None>" }}
# deprecated option for remote log storage, use remote_base_log_folder instead!
# s3_log_folder =

# The executor class that airflow should use. Choices include
# SequentialExecutor, LocalExecutor, CeleryExecutor
{{ if not .core.executor }}#{{ end }}executor = {{ .core.executor | default "<None>" }}

# The SqlAlchemy connection string to the metadata database.
# SqlAlchemy supports many different database engine, more information
# their website
{{ if not .core.sql_alchemy_conn }}#{{ end }}sql_alchemy_conn = {{ .core.sql_alchemy_conn | default "<None>" }}

# The SqlAlchemy pool size is the maximum number of database connections
# in the pool.
{{ if not .core.sql_alchemy_pool_size }}#{{ end }}sql_alchemy_pool_size = {{ .core.sql_alchemy_pool_size | default "<None>" }}

# The SqlAlchemy pool recycle is the number of seconds a connection
# can be idle in the pool before it is invalidated. This config does
# not apply to sqlite.
{{ if not .core.sql_alchemy_pool_recycle }}#{{ end }}sql_alchemy_pool_recycle = {{ .core.sql_alchemy_pool_recycle | default "<None>" }}

# The amount of parallelism as a setting to the executor. This defines
# the max number of task instances that should run simultaneously
# on this airflow installation
{{ if not .core.parallelism }}#{{ end }}parallelism = {{ .core.parallelism | default "<None>" }}

# The number of task instances allowed to run concurrently by the scheduler
{{ if not .core.dag_concurrency }}#{{ end }}dag_concurrency = {{ .core.dag_concurrency | default "<None>" }}

# Are DAGs paused by at creation
{{ if not .core.dags_are_paused_at_creation }}#{{ end }}dags_are_paused_at_creation = {{ .core.dags_are_paused_at_creation | default "<None>" }}

# When not using pools, tasks are run in the  pool",
# whose size is guided by this config element
{{ if not .core.non_pooled_task_slot_count }}#{{ end }}non_pooled_task_slot_count = {{ .core.non_pooled_task_slot_count | default "<None>" }}

# The maximum number of active DAG runs per DAG
{{ if not .core.max_active_runs_per_dag }}#{{ end }}max_active_runs_per_dag = {{ .core.max_active_runs_per_dag | default "<None>" }}

# Whether to load the examples that ship with Airflow. It's good to
# get started, but you probably want to set this to False in a production
# environment
{{ if not .core.load_examples }}#{{ end }}load_examples = {{ .core.load_examples | default "<None>" }}

# Where your Airflow plugins are stored
{{ if not .core.plugins_folder }}#{{ end }}plugins_folder = {{ .core.plugins_folder | default "<None>" }}

# Secret key to save connection passwords in the db
{{ if not .core.fernet_key }}#{{ end }}fernet_key = {{ .core.fernet_key | default "<None>" }}

# Whether to disable pickling dags
{{ if not .core.donot_pickle }}#{{ end }}donot_pickle = {{ .core.donot_pickle | default "<None>" }}

# How long before timing out a python file import while filling the DagBag
{{ if not .core.dagbag_import_timeout }}#{{ end }}dagbag_import_timeout = {{ .core.dagbag_import_timeout | default "<None>" }}

# The class to use for running task instances in a subprocess
{{ if not .core.task_runner }}#{{ end }}task_runner = {{ .core.task_runner | default "<None>" }}

# If set, tasks without a `run_as_user` argument will be run with this user
# Can be used to de-elevate a sudo user running Airflow when executing tasks
{{ if not .core.default_impersonation }}#{{ end }}default_impersonation = {{ .core.default_impersonation | default "<None>" }}

# What security module to use (for example kerberos):
{{ if not .core.security }}#{{ end }}security = {{ .core.security | default "<None>" }}

# Turn unit test mode on (overwrites many configuration options with test
# values at runtime)
{{ if not .core.unit_test_mode }}#{{ end }}unit_test_mode = {{ .core.unit_test_mode | default "<None>" }}

[cli]
# In what way should the cli access the API. The LocalClient will use the
# database directly, while the json_client will use the api running on the
# webserver
{{ if not .cli.api_client }}#{{ end }}api_client = {{ .cli.api_client | default "<None>" }}
{{ if not .cli.endpoint_url }}#{{ end }}endpoint_url = {{ .cli.endpoint_url | default "<None>" }}

[api]
# How to authenticate users of the API
{{ if not .api.auth_backend }}#{{ end }}auth_backend = {{ .api.auth_backend | default "<None>" }}

[operators]
# The default owner assigned to each new operator, unless
# provided explicitly or passed via `default_args`
{{ if not .operators.default_owner }}#{{ end }}default_owner = {{ .operators.default_owner | default "<None>" }}
{{ if not .operators.default_cpus }}#{{ end }}default_cpus = {{ .operators.default_cpus | default "<None>" }}
{{ if not .operators.default_ram }}#{{ end }}default_ram = {{ .operators.default_ram | default "<None>" }}
{{ if not .operators.default_disk }}#{{ end }}default_disk = {{ .operators.default_disk | default "<None>" }}
{{ if not .operators.default_gpus }}#{{ end }}default_gpus = {{ .operators.default_gpus | default "<None>" }}

[webserver]
# The base url of your website as airflow cannot guess what domain or
# cname you are using. This is use in automated emails that
# airflow sends to point links to the right web server
{{ if not .webserver.base_url }}#{{ end }}base_url = {{ .webserver.base_url | default "<None>" }}

# The ip specified when starting the web server
{{ if not .webserver.web_server_host }}#{{ end }}web_server_host = {{ .webserver.web_server_host | default "<None>" }}

# The port on which to run the web server
{{ if not .webserver.web_server_port }}#{{ end }}web_server_port = {{ .webserver.web_server_port | default "<None>" }}

# Paths to the SSL certificate and key for the web server. When both are
# provided SSL will be enabled. This does not change the web server port.
{{ if not .webserver.web_server_ssl_cert }}#{{ end }}web_server_ssl_cert = {{ .webserver.web_server_ssl_cert | default "<None>" }}
{{ if not .webserver.web_server_ssl_key }}#{{ end }}web_server_ssl_key = {{ .webserver.web_server_ssl_key | default "<None>" }}

# The time the gunicorn webserver waits before timing out on a worker
{{ if not .webserver.web_server_worker_timeout }}#{{ end }}web_server_worker_timeout = {{ .webserver.web_server_worker_timeout | default "<None>" }}

# Number of workers to refresh at a time. When set to 0, worker refresh is
# disabled. When nonzero, airflow periodically refreshes webserver workers by
# bringing up new ones and killing old ones.
{{ if not .webserver.worker_refresh_batch_size }}#{{ end }}worker_refresh_batch_size = {{ .webserver.worker_refresh_batch_size | default "<None>" }}

# Number of seconds to wait before refreshing a batch of workers.
{{ if not .webserver.worker_refresh_interval }}#{{ end }}worker_refresh_interval = {{ .webserver.worker_refresh_interval | default "<None>" }}

# Secret key used to run your flask app
{{ if not .webserver.secret_key }}#{{ end }}secret_key = {{ .webserver.secret_key | default "<None>" }}

# Number of workers to run the Gunicorn web server
{{ if not .webserver.workers }}#{{ end }}workers = {{ .webserver.workers | default "<None>" }}

# The worker class gunicorn should use. Choices include
# sync ), eventlet, gevent
{{ if not .webserver.worker_class }}#{{ end }}worker_class = {{ .webserver.worker_class | default "<None>" }}

# Log files for the gunicorn webserver. '-' means log to stderr.
{{ if not .webserver.access_logfile }}#{{ end }}access_logfile = {{ .webserver.access_logfile | default "<None>" }}
{{ if not .webserver.error_logfile }}#{{ end }}error_logfile = {{ .webserver.error_logfile | default "<None>" }}

# Expose the configuration file in the web server
{{ if not .webserver.expose_config }}#{{ end }}expose_config = {{ .webserver.expose_config | default "<None>" }}

# Set to true to turn on authentication : http://pythonhosted.org/airflow/installation.html#web-authentication
{{ if not .webserver.authenticate }}#{{ end }}authenticate = {{ .webserver.authenticate | default "<None>" }}

# Filter the list of dags by owner name (requires authentication to be enabled)
{{ if not .webserver.filter_by_owner }}#{{ end }}filter_by_owner = {{ .webserver.filter_by_owner | default "<None>" }}

# Filtering mode. Choices include user ) and ldapgroup.
# Ldap group filtering requires using the ldap backend
#
# Note that the ldap server needs the "memberOf" overlay to be set up
# in order to user the ldapgroup mode.
{{ if not .webserver.owner_mode }}#{{ end }}owner_mode = {{ .webserver.owner_mode | default "<None>" }}

# Default DAG orientation. Valid values are:
# LR (Left->Right), TB (Top->Bottom), RL (Right->Left), BT (Bottom->Top)
{{ if not .webserver.dag_orientation }}#{{ end }}dag_orientation = {{ .webserver.dag_orientation | default "<None>" }}

# Puts the webserver in demonstration mode; blurs the names of Operators for
# privacy.
{{ if not .webserver.demo_mode }}#{{ end }}demo_mode = {{ .webserver.demo_mode | default "<None>" }}

# The amount of time (in secs) webserver will wait for initial handshake
# while fetching logs from other worker machine
{{ if not .webserver.log_fetch_timeout_sec }}#{{ end }}log_fetch_timeout_sec = {{ .webserver.log_fetch_timeout_sec | default "<None>" }}

# By, the webserver shows paused DAGs. Flip this to hide paused
# DAGs by
{{ if not .webserver.hide_paused_dags_by_default }}#{{ end }}hide_paused_dags_by_default = {{ .webserver.hide_paused_dags_by_default | default "<None>" }}

[email]
{{ if not .email.email_backend }}#{{ end }}email_backend = {{ .email.email_backend | default "<None>" }}

[smtp]
# If you want airflow to send emails on retries, failure, and you want to
# the airflow.utils.send_email function, you have to configure an smtp
# server here
{{ if not .smtp.smtp_host }}#{{ end }}smtp_host = {{ .smtp.smtp_host | default "<None>" }}
{{ if not .smtp.smtp_starttls }}#{{ end }}smtp_smtp_starttls = {{ .smtp.smtp_starttls | default "<None>" }}
smtp_ssl = {{ .smtp.smtp_ssl | default "<None>" }}
{{ if not .smtp.smtp_user }}#{{ end }}smtp_user = {{ .smtp.smtp_user | default "<None>" }}
{{ if not .smtp.smtp_port }}#{{ end }}smtp_port = {{ .smtp.smtp_port | default "<None>" }}
{{ if not .smtp.smtp_password }}#{{ end }}smtp_password = {{ .smtp.smtp_password | default "<None>" }}
{{ if not .smtp.smtp_mail_from }}#{{ end }}smtp_mail_from = {{ .smtp.smtp_mail_from | default "<None>" }}

[celery]
# This section only applies if you are using the CeleryExecutor in
# [core] section above

# The app name that will be used by celery
{{ if not .celery.celery_app_name }}#{{ end }}celery_app_name = {{ .celery.celery_app_name | default "<None>" }}

# The concurrency that will be used when starting workers with the
# "airflow worker" command. This defines the number of task instances that
# a worker will take, so size up your workers based on the resources on
# your worker box and the nature of your tasks
{{ if not .celery.celeryd_concurrency }}#{{ end }}celeryd_concurrency = {{ .celery.celeryd_concurrency | default "<None>" }}

# When you start an airflow worker, airflow starts a tiny web server
# subprocess to serve the workers local log files to the airflow main
# web server, who then builds pages and sends them to users. This defines
# the port on which the logs are served. It needs to be unused, and open
# visible from the main web server to connect into the workers.
{{ if not .celery.worker_log_server_port }}#{{ end }}worker_log_server_port = {{ .celery.worker_log_server_port | default "<None>" }}

# The Celery broker URL. Celery supports RabbitMQ, Redis and experimentally
# a sqlalchemy database. Refer to the Celery documentation for more
# information.
{{ if not .celery.broker_url }}#{{ end }}broker_url = {{ .celery.broker_url | default "<None>" }}

# Another key Celery setting
{{ if not .celery.celery_result_backend }}#{{ end }}celery_result_backend = {{ .celery.celery_result_backend | default "<None>" }}

# Celery Flower is a sweet UI for Celery. Airflow has a shortcut to start
# it `airflow flower`. This defines the IP that Celery Flower runs on
{{ if not .celery.flower_host }}#{{ end }}flower_host = {{ .celery.flower_host | default "<None>" }}

# This defines the port that Celery Flower runs on
{{ if not .celery.flower_port }}#{{ end }}flower_port = {{ .celery.flower_port | default "<None>" }}

# Default queue that tasks get assigned to and that worker listen on.
{{ if not .celery.default_queue }}#{{ end }}default_queue = {{ .celery.default_queue | default "<None>" }}

[scheduler]
# Task instances listen for external kill signal (when you clear tasks
# from the CLI or the UI), this defines the frequency at which they should
# listen (in seconds).
{{ if not .scheduler.job_heartbeat_sec }}#{{ end }}job_heartbeat_sec = {{ .scheduler.job_heartbeat_sec | default "<None>" }}

# The scheduler constantly tries to trigger new tasks (look at the
# scheduler section in the docs for more information). This defines
# how often the scheduler should run (in seconds).
{{ if not .scheduler.scheduler_heartbeat_sec }}#{{ end }}scheduler_heartbeat_sec = {{ .scheduler.scheduler_heartbeat_sec | default "<None>" }}

# after how much time should the scheduler terminate in seconds
# -1 indicates to run continuously (see also num_runs)
{{ if not .scheduler.run_duration }}#{{ end }}run_duration = {{ .scheduler.run_duration | default "<None>" }}

# after how much time a new DAGs should be picked up from the filesystem
{{ if not .scheduler.min_file_process_interval }}#{{ end }}min_file_process_interval = {{ .scheduler.min_file_process_interval | default "<None>" }}

{{ if not .scheduler.dag_dir_list_interval }}#{{ end }}dag_dir_list_interval = {{ .scheduler.dag_dir_list_interval | default "<None>" }}

# How often should stats be printed to the logs
{{ if not .scheduler.print_stats_interval }}#{{ end }}print_stats_interval = {{ .scheduler.print_stats_interval | default "<None>" }}

{{ if not .scheduler.child_process_log_directory }}#{{ end }}child_process_log_directory = {{ .scheduler.child_process_log_directory | default "<None>" }}

# Local task jobs periodically heartbeat to the DB. If the job has
# not heartbeat in this many seconds, the scheduler will mark the
# associated task instance as failed and will re-schedule the task.
{{ if not .scheduler.scheduler_zombie_task_threshold }}#{{ end }}scheduler_zombie_task_threshold = {{ .scheduler.scheduler_zombie_task_threshold | default "<None>" }}

# Turn off scheduler catchup by setting this to False.
# Default behavior is unchanged and
# Command Line Backfills still work, but the scheduler
# will not do scheduler catchup if this is False,
# however it can be set on a per DAG basis in the
# DAG definition (catchup)
{{ if not .scheduler.catchup_by_default }}#{{ end }}catchup_by_default = {{ .scheduler.catchup_by_default | default "<None>" }}

# Statsd (https://github.com/etsy/statsd) integration settings
# statsd_on = False
# statsd_host = localhost
# statsd_port = 8125
# statsd_prefix = airflow

# The scheduler can run multiple threads in parallel to schedule dags.
# This defines how many threads will run. However airflow will never
# use more threads than the amount of cpu cores available.
{{ if not .scheduler.max_threads }}#{{ end }}max_threads = {{ .scheduler.max_threads | default "<None>" }}

{{ if not .scheduler.authenticate }}#{{ end }}authenticate = {{ .scheduler.authenticate | default "<None>" }}

[mesos]
# Mesos master address which MesosExecutor will connect to.
{{ if not .mesos.master }}#{{ end }}master = {{ .mesos.master | default "<None>" }}

# The framework name which Airflow scheduler will register itself as on mesos
{{ if not .mesos.framework_name }}#{{ end }}framework_name = {{ .mesos.framework_name | default "<None>" }}

# Number of cpu cores required for running one task instance using
# 'airflow run <dag_id> <task_id> <execution_date> --local -p <pickle_id>'
# command on a mesos slave
{{ if not .mesos.task_cpu }}#{{ end }}task_cpu = {{ .mesos.task_cpu | default "<None>" }}

# Memory in MB required for running one task instance using
# 'airflow run <dag_id> <task_id> <execution_date> --local -p <pickle_id>'
# command on a mesos slave
{{ if not .mesos.task_memory }}#{{ end }}task_memory = {{ .mesos.task_memory | default "<None>" }}

# Enable framework checkpointing for mesos
# See http://mesos.apache.org/documentation/latest/slave-recovery/
{{ if not .mesos.checkpoint }}#{{ end }}checkpoint = {{ .mesos.checkpoint | default "<None>" }}

# Failover timeout in milliseconds.
# When checkpointing is enabled and this option is set, Mesos waits
# until the configured timeout for
# the MesosExecutor framework to re-register after a failover. Mesos
# shuts down running tasks if the
# MesosExecutor framework fails to re-register within this timeframe.
# failover_timeout = 604800

# Enable framework authentication for mesos
# See http://mesos.apache.org/documentation/latest/configuration/
{{ if not .mesos.authenticate }}#{{ end }}authenticate = {{ .mesos.authenticate | default "<None>" }}

# Mesos credentials, if authentication is enabled
#_principal = admin
#_secret = admin

[kerberos]
#ccache = /tmp/airflow_krb5_ccache
# gets augmented with fqdn
#principal = airflow
#reinit_frequency = 3600
#kinit_path = kinit
#keytab = airflow.keytab

[github_enterprise]
#api_rev = v3

[admin]
# UI to hide sensitive variable fields when set to True
{{ if not .admin.hide_sensitive_variable_fields }}#{{ end }}hide_sensitive_variable_fields = {{ .admin.hide_sensitive_variable_fields | default "<None>" }}

{{- end -}}
