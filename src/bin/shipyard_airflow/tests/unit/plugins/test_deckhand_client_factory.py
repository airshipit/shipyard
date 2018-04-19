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
import os

from deckhand.client import client as deckhand_client

from shipyard_airflow.plugins.deckhand_client_factory import (
    DeckhandClientFactory
)


def test_get_client():
    """Test the get_client functionality"""
    cur_dir = os.path.dirname(__file__)
    filename = os.path.join(cur_dir, 'test.conf')
    client_factory = DeckhandClientFactory(filename)
    client = client_factory.get_client()
    assert isinstance(client, deckhand_client.Client)
