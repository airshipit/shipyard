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
"""
Module for resources representing the renderedconfigdocs API
"""

import falcon
from oslo_config import cfg

from shipyard_airflow import policy
from shipyard_airflow.control.base import BaseResource
from shipyard_airflow.control.helpers.configdocs_helper import \
    ConfigdocsHelper
from shipyard_airflow.errors import ApiError

CONF = cfg.CONF
VERSION_VALUES = ['buffer',
                  'committed',
                  'last_site_action',
                  'successful_site_action']


class RenderedConfigDocsResource(BaseResource):
    """
    RenderedConfigDocsResource represents the retrieval of configdocs
    in a complete or rendered state.
    """

    @policy.ApiEnforcer(policy.GET_RENDEREDCONFIGDOCS)
    def on_get(self, req, resp):
        """
        Returns the whole set of rendered documents
        """
        version = (req.params.get('version') or 'buffer')
        self._validate_version_parameter(version)
        helper = ConfigdocsHelper(req.context)
        resp.body = self.get_rendered_configdocs(
            helper=helper,
            version=version
        )
        resp.append_header('Content-Type', 'application/x-yaml')
        resp.status = falcon.HTTP_200

    def _validate_version_parameter(self, version):
        # performs validation of version parameter
        if version.lower() not in VERSION_VALUES:
            raise ApiError(
                title='Invalid version query parameter specified',
                description=(
                    'version must be {}'.format(', '.join(VERSION_VALUES))
                ),
                status=falcon.HTTP_400,
                retry=False,
            )

    def get_rendered_configdocs(self, helper, version='buffer'):
        """
        Get and return the rendered configdocs from the helper/Deckhand
        """
        return helper.get_rendered_configdocs(version)
