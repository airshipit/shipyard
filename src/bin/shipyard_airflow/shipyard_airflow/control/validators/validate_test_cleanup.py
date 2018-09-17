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
import falcon

from shipyard_airflow.errors import ApiError


class ValidateTestCleanup:
    """Validate that a valid cleanup value is specified for release testing"""
    def __init__(self, action):
        self.action = action

    def validate(self):
        """Retrieve cleanup parameter and verify it is a boolean value"""
        # Retrieve optional parameters
        parameters = self.action.get('parameters')
        if not parameters:
            return

        # Verify cleanup param (optional) is a boolean value
        cleanup = parameters.get('cleanup')
        if not cleanup:
            return
        elif str.lower(cleanup) in ['true', 'false']:
            return

        raise ApiError(
            title='Invalid cleanup value',
            description=(
                'Cleanup must be a boolean value.'
            ),
            status=falcon.HTTP_400,
            retry=False
        )
