# Copyright 2017 AT&T Intellectual Property.  All other rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-1.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import yaml


def output_formatting(output_format, response):
    """formats response from api_client"""
    if output_format == 'raw':
        return response.text
    else:  # assume formatted
        return formatted(response)


def formatted(response):
    """Formats either json or yaml depending on call"""
    call = response.headers['Content-Type']
    if 'json' in call:
        try:
            input = response.json()
            return (json.dumps(input, sort_keys=True, indent=4))
        except ValueError:
            return ("This is not json and could not be printed as such. \n " +
                    response.text)

    else:  # all others should be yaml
        try:
            return (yaml.dump_all(
                yaml.safe_load_all(response.content),
                width=79,
                indent=4,
                default_flow_style=False))
        except ValueError:
            return ("This is not yaml and could not be printed as such.\n " +
                    response.text)
