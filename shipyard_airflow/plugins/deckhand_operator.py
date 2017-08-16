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


class DeckhandOperator(BaseOperator):
    """
    Supports interaction with Deckhand.
    """

    #TODO () remove this special coloring when the operator is done.
    ui_color = '#e8f7e4'

    @apply_defaults
    def __init__(self, *args, **kwargs):
        super(DeckhandOperator, self).__init__(*args, **kwargs)

    # TODO () make this communicate with Deckhand.
    # Needs to expose functionality so general interaction
    # with deckhand can occur.
    def execute(self, context):
        logging.info('%s : %s !!! not implemented. '
                     'Need to get design revision from Deckhand',
                     self.dag.dag_id, self.task_id)


class DeckhandOperatorPlugin(AirflowPlugin):
    name = 'deckhand_operator_plugin'
    operators = [DeckhandOperator]
