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
from airflow import DAG

from shipyard_airflow.dags import deploy_site
from shipyard_airflow.dags import update_site
from shipyard_airflow.dags import update_software
from shipyard_airflow.dags import redeploy_server


def test_dags_load():
    """assert that each dag is a DAG object after importing the modules

    As these are the top level dags, the subdags and many operators
    will be loaded as a result. This ensures that basic construction
    is working for most of the workflow logic, however it tests nearly
    none of the decision making.
    """
    for d in [deploy_site.dag, update_site.dag,
              update_software.dag, redeploy_server.dag]:
        assert isinstance(d, DAG)
        assert d.task_count > 0
