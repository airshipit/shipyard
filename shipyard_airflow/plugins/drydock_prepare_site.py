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
from airflow.plugins_manager import AirflowPlugin

from drydock_base_operator import DrydockBaseOperator


class DrydockPrepareSiteOperator(DrydockBaseOperator):

    """Drydock Prepare Site Operator

    This operator will trigger drydock to prepare site for
    site deployment

    """

    def do_execute(self):

        # Trigger DryDock to execute task
        self.create_task('prepare_site')

        # Retrieve query interval and timeout
        q_interval = self.dc['physical_provisioner.prepare_site_interval']
        task_timeout = self.dc['physical_provisioner.prepare_site_timeout']

        # Query Task
        self.query_task(q_interval, task_timeout)


class DrydockPrepareSiteOperatorPlugin(AirflowPlugin):

    """Creates DrydockPrepareSiteOperator in Airflow."""

    name = 'drydock_prepare_site_operator'
    operators = [DrydockPrepareSiteOperator]
