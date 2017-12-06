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
from shipyard_airflow.control.base import ShipyardRequestContext
from shipyard_airflow.control.api import VersionsResource
from tests.unit.control.common import create_req, create_resp

context = ShipyardRequestContext()


class TestVersionsResource():
    def test_on_get(self):
        version_resource = VersionsResource()
        req = create_req(context, None)
        resp = create_resp()
        version_resource.on_get(req, resp)
        assert sorted(resp.body) == sorted(
            '{"v1.0": {"status": "stable", "path": "/api/v1.0"}}')
        assert resp.status == '200 OK'
