# Copyright 2017 AT&T Intellectual Property.  All other rights reserved.
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
""" Tests for the action_helper.py module """

from shipyard_airflow.control.helpers import action_helper
import yaml


def test_determine_lifecycle():
    dag_statuses = [
        {'input': 'queued', 'expected': 'Pending'},
        {'input': 'ShUTdown', 'expected': 'Failed'},
        {'input': 'RUNNING', 'expected': 'Processing'},
        {'input': 'None', 'expected': 'Pending'},
        {'input': None, 'expected': 'Pending'},
        {'input': 'bogusBroken', 'expected': 'Unknown (bogusBroken)'},
    ]
    for status_pair in dag_statuses:
        assert(status_pair['expected'] ==
               action_helper.determine_lifecycle(status_pair['input']))


def test_get_step():
    # Set up actions helper
    action_id = '01CPV581B0CM8C9CA0CFRNVPPY'  # id in db
    actions = yaml.safe_load("""
---
  - id: 01CPV581B0CM8C9CA0CFRNVPPY
    name: update_software
    parameters: {}
    dag_id: update_software
    dag_execution_date: 2018-09-07T23:18:04
    user: admin
    datetime: 2018-09-07 23:18:04.38546+00
    context_marker: 10447c79-b02c-4dfd-a9e8-1362842f029d
...
""")
    action_helper.ActionsHelper._get_action_db = lambda \
            self, action_id: actions[0]

    tasks = yaml.safe_load("""
---
  - task_id: armada_get_status
    dag_id: update_software.armada_build
    execution_date: 2018-09-07 23:18:04
    start_date: 2018-09-07 23:18:55.950298
    end_date: 2018-09-07 23:18:58.159597
    duration: 2.209299
    state: success
    try_number: 1
    hostname: airflow-worker-0.airflow-worker-discovery.ucp.svc.cluster.local
    unixname: airflow
    job_id: 11
    pool:
    queue: default
    priority_weight: 3
    operator: ArmadaGetStatusOperator
    queued_dttm:
    pid: 249
    max_tries: 0
  - task_id: armada_get_status
    dag_id: update_software.armada_build
    execution_date: 2018-09-07 23:18:04
    start_date: 2018-09-07 23:18:55.950298
    end_date: 2018-09-07 23:18:58.159597
    duration: 2.209299
    state: success
    try_number: 2
    hostname: airflow-worker-1.airflow-worker-discovery.ucp.svc.cluster.local
    unixname: airflow
    job_id: 12
    pool:
    queue: default
    priority_weight: 3
    operator: ArmadaGetStatusOperator
    queued_dttm:
    pid: 249
    max_tries: 0
  - task_id: armada_post_apply
    dag_id: update_software.armada_build
    execution_date: 2018-09-07 23:18:04
    start_date: 2018-09-07 23:48:25.884615
    end_date: 2018-09-07 23:48:50.552757
    duration: 24.668142
    state: success
    try_number: 2
    hostname: airflow-worker-0.airflow-worker-discovery.ucp.svc.cluster.local
    unixname: airflow
    job_id: 13
    pool:
    queue: default
    priority_weight: 2
    operator: ArmadaPostApplyOperator
    queued_dttm:
    pid: 329
    max_tries: 3
  - task_id: armada_get_releases
    dag_id: update_software.armada_build
    execution_date: 2018-09-07 23:18:04
    start_date: 2018-09-07 23:48:59.024696
    end_date: 2018-09-07 23:49:01.471963
    duration: 2.447267
    state: success
    try_number: 1
    hostname: airflow-worker-0.airflow-worker-discovery.ucp.svc.cluster.local
    unixname: airflow
    job_id: 14
    pool:
    queue: default
    priority_weight: 1
    operator: ArmadaGetReleasesOperator
    queued_dttm:
    pid: 365
    max_tries: 0
  - task_id: armada_build
    dag_id: update_software
    execution_date: 2018-09-07 23:18:04
    start_date: 2018-09-07 23:18:47.447987
    end_date: 2018-09-07 23:49:02.397515
    duration: 1814.949528
    state: success
    try_number: 1
    hostname: airflow-worker-0.airflow-worker-discovery.ucp.svc.cluster.local
    unixname: airflow
    job_id: 9
    pool:
    queue: default
    priority_weight: 5
    operator: SubDagOperator
    queued_dttm: 2018-09-07 23:18:45.772501
    pid: 221
    max_tries: 0
...
""")
    action_helper.ActionsHelper._get_tasks_db = lambda \
            self, dag_id, execution_date: tasks
    actions_helper = action_helper.ActionsHelper(action_id=action_id)

    # Retrieve step
    step_id = 'armada_get_status'  # task_id in db

    # test backward compatibility with no additional param
    step = actions_helper.get_step(step_id)
    assert(step['hostname'].startswith('airflow-worker-0'))

    # test explicit None
    try_number = None
    step = actions_helper.get_step(step_id, try_number)
    assert(step['hostname'].startswith('airflow-worker-0'))

    # test try_number associated with 0 worker
    try_number = 1
    step = actions_helper.get_step(step_id, try_number)
    assert(step['hostname'].startswith('airflow-worker-0'))

    # test try_number associated with 1 worker
    try_number = 2
    step = actions_helper.get_step(step_id, try_number)
    assert(step['hostname'].startswith('airflow-worker-1'))
