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
""" Common methods for use by action api classes as necessary """

DAG_STATE_MAPPING = {
    'QUEUED': 'Pending',
    'RUNNING': 'Processing',
    'SUCCESS': 'Complete',
    'SHUTDOWN': 'Failed',
    'FAILED': 'Failed',
    'UP_FOR_RETRY': 'Processing',
    'UPSTREAM_FAILED': 'Failed',
    'SKIPPED': 'Failed',
    'REMOVED': 'Failed',
    'SCHEDULED': 'Pending',
    'NONE': 'Pending',
    'PAUSED': 'Paused'
}


def determine_lifecycle(dag_status=None):
    """ Convert a dag_status to an action_lifecycle value """
    if dag_status is None:
        dag_status = 'NONE'
    lifecycle = DAG_STATE_MAPPING.get(dag_status.upper())
    if lifecycle is None:
        lifecycle = 'Unknown ({})'.format(dag_status)
    return lifecycle


def format_action_steps(action_id, steps):
    """ Converts a list of action step db records to desired format """
    if not steps:
        return []
    steps_response = []
    for idx, step in enumerate(steps):
        steps_response.append(format_step(action_id=action_id,
                                          step=step,
                                          index=idx + 1))
    return steps_response


def format_step(action_id, step, index):
    """ reformat a step (dictionary) into a common response format """
    return {
        'url': '/actions/{}/steps/{}'.format(action_id, step.get('task_id')),
        'state': step.get('state'),
        'id': step.get('task_id'),
        'index': index
    }
