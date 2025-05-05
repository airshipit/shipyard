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
import logging

from airflow.exceptions import AirflowException

LOG = logging.getLogger(__name__)


class XcomPusher(object):
    """XcomPusher pushes xcom value

    Create specific key with value and stores as xcom.
    """

    def __init__(self, task_instance):
        self.ti = task_instance

    def xcom_push(self, key=None, value=None):
        """Push a particular xcom value"""

        LOG.info("Pushing xcom from %s.%s with key %s and value %s",
                 self.ti.dag_id, self.ti.task_id, key, value)

        try:
            self.ti.xcom_push(key=key, value=value)
        except:
            raise AirflowException("Xcom push failed!")
