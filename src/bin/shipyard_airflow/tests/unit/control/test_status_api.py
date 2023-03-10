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
""" Tests for the status_api"""
import json
from unittest.mock import patch

from shipyard_airflow.control.helpers.status_helper import \
    StatusHelper
from shipyard_airflow.control.base import ShipyardRequestContext
from tests.unit.control import common

CTX = ShipyardRequestContext()


class TestStatusResource():
    @patch.object(StatusHelper, 'get_site_statuses',
                  common.str_responder)
    def test_on_get(self, api_client):
        """Validate the on_get method returns 200 on success"""
        result = api_client.simulate_get(
            "/api/v1.0/site_statuses", headers=common.AUTH_HEADERS)
        assert result.status_code == 200
        assert result.text == json.dumps(common.str_responder(), default=str)
        assert result.headers[
            'content-type'] == 'application/json'
