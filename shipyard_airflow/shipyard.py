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
import shipyard_airflow.control.api as api

def start_shipyard():

    # Setup root logger
    logger = logging.getLogger('shipyard')

    logger.setLevel('DEBUG')
    ch = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # Specalized format for API logging
    logger = logging.getLogger('shipyard.control')
    logger.propagate = False
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(user)s - %(req_id)s - %(external_ctx)s - %(message)s')

    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return api.start_api()

shipyard = start_shipyard()

