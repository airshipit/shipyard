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

import json
import yaml
from mock import patch, ANY
from requests.models import Response

from shipyard_client.cli.output_formatting import output_formatting

json_response = Response()
json_response._content = b'{ "key" : "a" }'
json_response.status_code = 200
json_response.headers['content-type'] = 'application/json'

yaml_response = Response()
yaml_response._content = b'''Projects:
  C/C++ Libraries:
  - libyaml       # "C" Fast YAML 1.1
  - Syck          # (dated) "C" YAML 1.0
  - yaml-cpp      # C++ YAML 1.2 implementation
  Ruby:
  - psych         # libyaml wrapper (in Ruby core for 1.9.2)
  - RbYaml        # YAML 1.1 (PyYAML Port)
  - yaml4r        # YAML 1.0, standard library syck binding
  Python:
  - PyYAML        # YAML 1.1, pure python and libyaml binding
  - ruamel.yaml   # YAML 1.2, update of PyYAML with round-tripping of comments
  - PySyck        # YAML 1.0, syck binding'''

yaml_response.headers['content-type'] = 'application/yaml'


def test_output_formatting():
    """call output formatting and check correct one was given"""

    with patch.object(json, 'dumps') as mock_method:
        output_formatting('format', json_response)
    mock_method.assert_called_once_with(
        json_response.json(), sort_keys=True, indent=4)

    with patch.object(yaml, 'dump_all') as mock_method:
        output_formatting('format', yaml_response)
    mock_method.assert_called_once_with(
        ANY, width=79, indent=4, default_flow_style=False)
