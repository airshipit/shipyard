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
import yaml

import jsonschema
import pkg_resources
import pytest
import shutil

from jsonschema.exceptions import ValidationError

LOG = logging.getLogger(__name__)


class BaseSchemaValidationTest(object):
    def _test_validate(self, schema, expect_failure, input_files, input):
        """validates input yaml against schema.
        :param schema: schema yaml file
        :param expect_failure: should the validation pass or fail.
        :param input_files: pytest fixture used to access the test input files
        :param input: test input yaml doc filename"""
        schema_dir = pkg_resources.resource_filename('shipyard_airflow',
                                                     'schemas')
        schema_filename = os.path.join(schema_dir, schema)
        schema_file = open(schema_filename, 'r')
        schema = yaml.safe_load(schema_file)

        input_file = input_files.join(input)
        instance_file = open(str(input_file), 'r')
        instance = yaml.safe_load(instance_file)

        LOG.info('Input: %s, Schema: %s', input_file, schema_filename)

        if expect_failure:
            with pytest.raises(ValidationError):
                jsonschema.validate(instance['data'], schema['data'])
        else:
            jsonschema.validate(instance['data'], schema['data'])


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

    @pytest.fixture(scope='module')
    def input_files(self, tmpdir_factory, request):
        tmpdir = tmpdir_factory.mktemp('data')
        samples_dir = os.path.dirname(str(
            request.fspath)) + "/" + "../yaml_samples"
        samples = os.listdir(samples_dir)

        for f in samples:
            src_file = samples_dir + "/" + f
            dst_file = str(tmpdir) + "/" + f
            shutil.copyfile(src_file, dst_file)
        return tmpdir
