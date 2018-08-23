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

import falcon

from shipyard_airflow.errors import ApiError

LOG = logging.getLogger(__name__)


class ValidateTargetNodes:
    """Validate that the target_nodes parameter has values in it

    For actions that target nodes, this parameter must have at least one value
    in it, and each value should be a string
    """
    def __init__(self, action):
        self.action = action

    def validate(self):
        parameters = self.action.get('parameters')
        valid = parameters is not None
        if valid:
            # target_nodes parameter should exist
            nodes = parameters.get('target_nodes')
            valid = nodes is not None
        if valid:
            # should be able to listify the nodes
            try:
                node_list = list(nodes)
                valid = len(node_list) > 0
            except TypeError:
                valid = False
        if valid:
            # each entry should be a string
            for s in node_list:
                if not isinstance(s, str):
                    valid = False
                    break
        if valid:
            # all valid
            return

        # something was invalid
        raise ApiError(
            title='Invalid target_nodes parameter',
            description=(
                'The target_nodes parameter for this action '
                'should be a list with one or more string values '
                'representing node names'
            ),
            status=falcon.HTTP_400,
            retry=False
        )
