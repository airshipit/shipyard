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
from testfixtures import LogCapture
from types import SimpleNamespace
from shipyard_airflow.dags import failure_handlers

CONTEXT = {'task_instance': SimpleNamespace(task_id='cheese')}


def test_step_failure_handler():
    """
    Ensure that the failure handler is logging as intended.
    """
    with LogCapture() as log_capturer:
        failure_handlers.step_failure_handler(CONTEXT)
        log_capturer.check(('root', 'INFO', 'cheese step failed'))
