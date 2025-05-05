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


class ValidateCommittedRevision:
    """Validate that the committed revision was found in Deckhand

    Does not perform the actual lookup - only validates that the action has
    the value populated with a valid value other than `None`
    """

    def __init__(self, action):
        self.action = action

    def validate(self):
        if self.action.get('committed_rev_id') is None:
            raise ApiError(
                title='No committed configdocs',
                description=(
                    'Unable to locate a committed revision in Deckhand'),
                status=falcon.HTTP_400,
                retry=False)
