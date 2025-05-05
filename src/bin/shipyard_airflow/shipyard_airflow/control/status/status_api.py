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

from shipyard_airflow import policy
from shipyard_airflow.control.helpers.status_helper import (StatusHelper)
from shipyard_airflow.control.base import BaseResource

LOG = logging.getLogger(__name__)


# /api/v1.0/site_statuses
class StatusResource(BaseResource):
    """
    The status resource handles the retrieval of Drydock provisioning
    node status and power state
    """

    @policy.ApiEnforcer(policy.GET_SITE_STATUSES)
    def on_get(self, req, resp, **kwargs):
        """
        Return site based statuses that has been invoked through shipyard.
        :returns: a json array of site status entities
        """
        status_filters = req.get_param(name='filters') or None
        if status_filters:
            fltrs = status_filters.split(',')
        else:
            fltrs = None
        helper = StatusHelper(req.context)
        resp.text = self.to_json(helper.get_site_statuses(fltrs))
        resp.status = falcon.HTTP_200
