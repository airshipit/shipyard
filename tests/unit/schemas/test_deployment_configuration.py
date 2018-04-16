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
from .base_schema_validation import BaseSchemaValidationTest


class TestValidation(BaseSchemaValidationTest):
    def test_validate_deploy_config_full_valid(self, input_files):
        self._test_validate('deploymentConfiguration.yaml', False, input_files,
                            'deploymentConfiguration_full_valid.yaml')

    def test_validate_deploy_config_bad_manifest(self, input_files):
        self._test_validate('deploymentConfiguration.yaml', True, input_files,
                            'deploymentConfiguration_bad_manifest.yaml')

    def test_validate_deploy_config_minimal_valid(self, input_files):
        self._test_validate('deploymentConfiguration.yaml', False, input_files,
                            'deploymentConfiguration_minimal_valid.yaml')
