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

from shipyard_airflow.control.action import action_helper


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
