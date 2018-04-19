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
from testfixtures import LogCapture

from shipyard_airflow.control.middleware.logging_mw import LoggingMiddleware


class TestLoggingMw(object):

    def test_log_headers(self):
        lm = LoggingMiddleware()
        logger = 'shipyard_airflow.control.middleware.logging_mw'
        with LogCapture() as lc:
            lm._log_headers({"header": "val1",
                             "X-HEADER": "val2",
                             "x-hdr": "val3",
                             "hdrX-hdr": "val4",
                             "hdr-Xhdr": "val5"})
        # because the order is hash, can't simply log_capturer.check
        logs = ''
        for rec in lc.records:
            logs = logs + rec.msg % rec.args
        assert 'Header header: val1' in logs
        assert 'Header hdrX-hdr: val4' in logs
        assert 'Header hdr-Xhdr: val5' in logs
        assert 'val2' not in logs
        assert 'val3' not in logs
