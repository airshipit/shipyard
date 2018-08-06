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
from shipyard_airflow.db import common_db


M_QUERY = """
SELECT
  junk_id,
  junk_name
FROM
  junk_table
WHERE
  junk_name = "Junk"
"""

M_RES = 'SELECT junk_id, junk_name FROM junk_table WHERE junk_name = "Junk"'

M2_QUERY = """




SELECT
  things


FROM

  tables

"""

M2_RES = 'SELECT things FROM tables'

S_QUERY = "SELECT 1 FROM dual"


class TestCommonDb():
    def test_single_line_query(self):
        assert M_RES == common_db._query_single_line(M_QUERY)
        assert M2_RES == common_db._query_single_line(M2_QUERY)
        assert S_QUERY == common_db._query_single_line(S_QUERY)
