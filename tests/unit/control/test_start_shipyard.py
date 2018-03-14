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
import os

from shipyard_airflow.control.start_shipyard import start_shipyard


class TestStartShipyard():
    def test_start_shipyard_logging_levels(self):
        cur_dir = os.path.dirname(__file__)
        filename = os.path.join(cur_dir, 'test.conf')

        api = start_shipyard(default_config_files=[filename])
        cheese_logger = logging.getLogger("cheese")
        ksauth_logger = logging.getLogger("keystoneauth")
        pumpkin_logger = logging.getLogger("pumpkins")
        assert ksauth_logger.level == logging.ERROR
        assert cheese_logger.level == logging.WARN
        assert pumpkin_logger.level == logging.INFO
