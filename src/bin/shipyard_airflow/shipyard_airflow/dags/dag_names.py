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
UCP_PREFLIGHT_NAME = 'ucp_preflight_check'
ARMADA_BUILD_DAG_NAME = 'armada_build'
DESTROY_SERVER_DAG_NAME = 'destroy_server'
DRYDOCK_BUILD_DAG_NAME = 'drydock_build'
VALIDATE_SITE_DESIGN_DAG_NAME = 'validate_site_design'
RELABEL_NODES_DAG_NAME = 'relabel_nodes'

# Steps
ACTION_XCOM = 'action_xcom'
ARMADA_TEST_RELEASES = 'armada_test_releases'
CONCURRENCY_CHECK = 'dag_concurrency_check'
CREATE_ACTION_TAG = 'create_action_tag'
DECIDE_AIRFLOW_UPGRADE = 'decide_airflow_upgrade'
DEPLOYMENT_CONFIGURATION = 'deployment_configuration'
GET_RENDERED_DOC = 'get_rendered_doc'
SKIP_UPGRADE_AIRFLOW = 'skip_upgrade_airflow'
UPGRADE_AIRFLOW = 'upgrade_airflow'
DESTROY_SERVER = 'destroy_nodes'
DEPLOYMENT_STATUS = 'deployment_status'
FINAL_DEPLOYMENT_STATUS = 'final_deployment_status'

# Define a list of critical steps, used to determine successfulness of a
# still-running DAG
CRITICAL_DAG_STEPS = [
    ARMADA_BUILD_DAG_NAME,
    SKIP_UPGRADE_AIRFLOW,
    UPGRADE_AIRFLOW,
    ARMADA_TEST_RELEASES
]
