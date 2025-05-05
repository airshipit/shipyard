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
"""
Status helper is a layer for status API, which interacts with
multiple components to fetch required status as per the filter
values.
"""
import logging

from drydock_provisioner import error as dderrors
import falcon
from oslo_config import cfg

import shipyard_airflow.control.service_clients as sc
from shipyard_airflow.errors import ApiError, AppError

CONF = cfg.CONF
LOG = logging.getLogger(__name__)

NODE_PROVISION_STATUS = 'nodes-provision-status'
MACHINES_POWER_STATE = 'machines-power-state'

# This will be expanded with new status filters to support more status types.
valid_filters = [NODE_PROVISION_STATUS, MACHINES_POWER_STATE]


def get_machines_powerstate(drydock):
    # Calls Drydock client to fetch nodes power state
    try:
        machines = drydock.get_nodes()
        machines_ps = []
        for machine in machines:
            machines_ps.append({
                'hostname': machine.get('hostname'),
                'power_state': machine.get('power_state')
            })
    except dderrors.ClientError as ddex:
        raise AppError(
            title='Unable to retrieve nodes power-state',
            description=(
                'Drydock has responded unexpectedly: {}'.format(ddex)),
            status=falcon.HTTP_500,
            retry=False,
        )
    machines_powerstate = {'machines_powerstate': machines_ps}
    return machines_powerstate


def get_nodes_provision_status(drydock):
    # Calls Drydock client to fetch node provision status
    try:
        nodes = drydock.get_nodes()
        nodes_status = []
        for node in nodes:
            nodes_status.append({
                'hostname': node.get('hostname'),
                'status': node.get('status_name')
            })
    except dderrors.ClientError as ddex:
        raise AppError(
            title='Unable to retrieve nodes status',
            description=(
                'Drydock has responded unexpectedly: {}'.format(ddex)),
            status=falcon.HTTP_500,
            retry=False,
        )
    machine_status = {'nodes_provision_status': nodes_status}
    return machine_status


class StatusHelper(object):
    """
    StatusHelper provides a layer to fetch statuses from respective
    components based on filter values.
    A new status_helper is intended to be used for each invocation..
    """

    def __init__(self, context):
        """
        Sets up this status helper with the supplied
        request context
        """
        # Instantiate the client for a component api interaction
        self.drydock = None
        self.ctx = context

    def get_site_statuses(self, sts_filters=None):
        """
        :param sts_filters: A list of filters representing statuses
        that needs to be fetched

        Returns dictionary of statuses
        """
        # check for filters else set to all valid filters.
        if sts_filters:
            pass
        else:
            sts_filters = valid_filters

        LOG.debug("Filters for status search are %s", sts_filters)

        # check for valid status filters
        for sts_filter in sts_filters:
            if sts_filter not in valid_filters:
                raise ApiError(title='Not a valid status filter',
                               description='filter {} is not supported'.format(
                                   sts_filter),
                               status=falcon.HTTP_400,
                               retry=False)

        # get Drydock client
        if not self.drydock:
            self.drydock = sc.drydock_client(
                context_marker=self.ctx.request_id, end_user=self.ctx.user)

        statuses = {}
        # iterate through filters to invoke required fun
        for sts_filter in sts_filters:
            call_func = self._switcher(sts_filter)
            status = call_func(self.drydock)
            statuses.update(status)

        return statuses

    def _switcher(self, fltr):
        # Helper that returns mapped function name as per filter

        status_func_switcher = {
            NODE_PROVISION_STATUS: get_nodes_provision_status,
            MACHINES_POWER_STATE: get_machines_powerstate,
        }

        call_func = status_func_switcher.get(fltr, lambda: None)

        # return the function name from switcher dictionary
        return call_func
