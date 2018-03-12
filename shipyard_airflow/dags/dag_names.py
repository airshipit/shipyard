# Copyright 2018 AT&T Intellectual Property.  All other rights reserved.
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

# Subdags
ALL_PREFLIGHT_CHECKS_DAG_NAME = 'preflight'
ARMADA_BUILD_DAG_NAME = 'armada_build'
DAG_CONCURRENCY_CHECK_DAG_NAME = 'dag_concurrency_check'
DECKHAND_GET_DESIGN_VERSION = 'deckhand_get_design_version'
GET_DEPLOY_CONF_DAG_NAME = 'dag_deployment_configuration'
DRYDOCK_BUILD_DAG_NAME = 'drydock_build'
VALIDATE_SITE_DESIGN_DAG_NAME = 'validate_site_design'
DESTROY_SERVER_DAG_NAME = 'destroy_server'

# Steps
ACTION_XCOM = 'action_xcom'
DECIDE_AIRFLOW_UPGRADE = 'decide_airflow_upgrade'
UPGRADE_AIRFLOW = 'upgrade_airflow'
SKIP_UPGRADE_AIRFLOW = 'skip_upgrade_airflow'
