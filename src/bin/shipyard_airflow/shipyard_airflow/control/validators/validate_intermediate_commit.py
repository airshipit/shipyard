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


class ValidateIntermediateCommit:
    """Validtor to ensure that intermediate commits are not present

    If allow_intermediate_commits is set on the action, this validator will
    not check.
    """
    def __init__(self, action, configdocs_helper):
        self.action = action
        self.configdocs_helper = configdocs_helper

    def validate(self):
        if self.action.get('allow_intermediate_commits'):
            LOG.debug("Intermediate commit check skipped due to user input")
        else:
            intermediate_commits = (
                self.configdocs_helper.check_intermediate_commit())
            if intermediate_commits:
                raise ApiError(
                    title='Intermediate commit detected',
                    description=(
                        'The current committed revision of documents has '
                        'other prior commits that have not been used as '
                        'part of a site action, e.g. update_site. If you '
                        'are aware and these other commits are intended, '
                        'please rerun this action with the option '
                        '`allow-intermediate-commits=True`'),
                    status=falcon.HTTP_409,
                    retry=False
                )
