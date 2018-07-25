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
from unittest.mock import patch

import pytest

from shipyard_airflow.control.base import ShipyardRequestContext
from shipyard_airflow.control.configdocs.rendered_configdocs_api import \
    RenderedConfigDocsResource
from shipyard_airflow.control.helpers.configdocs_helper import \
    ConfigdocsHelper
from shipyard_airflow.errors import ApiError

CTX = ShipyardRequestContext()


def test_validate_version_parameter():
    """
    test of the version parameter validation
    """
    rcdr = RenderedConfigDocsResource()
    with pytest.raises(ApiError):
        rcdr._validate_version_parameter('asdfjkl')

    try:
        rcdr._validate_version_parameter('buffer')
        rcdr._validate_version_parameter('committed')
    except:
        assert False


def test_get_rendered_configdocs():
    """
    Tests the RenderedConfigDocsResource method get_rendered_configdocs
    """
    rcdr = RenderedConfigDocsResource()

    with patch.object(
        ConfigdocsHelper, 'get_rendered_configdocs'
    ) as mock_method:
        helper = ConfigdocsHelper(CTX)
        rcdr.get_rendered_configdocs(helper, version='buffer')

    mock_method.assert_called_once_with('buffer')


def test_get_rendered_last_site_action_configdocs():
    """
    Tests the RenderedConfigDocsResource method get_rendered_configdocs
    for last_site_action tag
    """
    rcdr = RenderedConfigDocsResource()

    with patch.object(
        ConfigdocsHelper, 'get_rendered_configdocs'
    ) as mock_method:
        helper = ConfigdocsHelper(CTX)
        rcdr.get_rendered_configdocs(helper, version='last_site_action')

    mock_method.assert_called_once_with('last_site_action')


def test_get_rendered_successful_site_action_configdocs():
    """
    Tests the RenderedConfigDocsResource method get_rendered_configdocs
    for successful_site_action tag
    """
    rcdr = RenderedConfigDocsResource()

    with patch.object(
        ConfigdocsHelper, 'get_rendered_configdocs'
    ) as mock_method:
        helper = ConfigdocsHelper(CTX)
        rcdr.get_rendered_configdocs(helper, version='successful_site_action')

    mock_method.assert_called_once_with('successful_site_action')
