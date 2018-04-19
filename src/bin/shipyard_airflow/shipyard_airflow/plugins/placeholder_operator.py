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
import logging

from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults
from airflow.plugins_manager import AirflowPlugin


class PlaceholderOperator(BaseOperator):
    """
    Operator that writes a log of its presence, as not implemented.
    This is intended to be a little noisy so it's easy to see what's
    missing.
    """

    template_fields = tuple()
    ui_color = '#e8f7e4'

    @apply_defaults
    def __init__(self, *args, **kwargs):
        super(PlaceholderOperator, self).__init__(*args, **kwargs)

    def execute(self, context):
        logging.info('%s : %s !!! not implemented', self.dag.dag_id,
                     self.task_id)


class PlaceholderOperatorPlugin(AirflowPlugin):
    name = "placeholder_operator_plugin"
    operators = [PlaceholderOperator]
