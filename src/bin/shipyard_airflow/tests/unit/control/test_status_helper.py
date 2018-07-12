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
from unittest import mock

from shipyard_airflow.control.base import ShipyardRequestContext
from shipyard_airflow.control.helpers.status_helper import (
    StatusHelper)
import shipyard_airflow.control.helpers.status_helper as sh


CTX = ShipyardRequestContext()

MACH_STATUS_DICT = {
    'nodes_provision_status': [
        {
            'hostname': 'abc.xyz.com',
            'status': 'READY'
        },
        {
            'hostname': 'def.xyz.com',
            'status': 'DEPLOYING'
        }
    ]
}

MACH_POWERSTATE_DICT = {
    'machines_powerstate': [
        {
            'hostname': 'abc.xyz.com',
            'power_state': 'ON'
        },
        {
            'hostname': 'def.xyz.com',
            'power_state': 'ON'
        }
    ]
}

STATUS_LIST = [
    {
        'hostname': 'abc.xyz.com',
        'status': 'READY'
    },
    {
        'hostname': 'def.xyz.com',
        'status': 'DEPLOYING'
    }
]

MACH_PS_LIST = [
    {
        'hostname': 'abc.xyz.com',
        'power_state': 'ON'
    },
    {
        'hostname': 'def.xyz.com',
        'power_state': 'ON'
    }
]


ALL_STATUSES_DICT = {
    'nodes_provision_status': [
        {
            'hostname': 'abc.xyz.com',
            'status': 'READY'
        },
        {
            'hostname': 'def.xyz.com',
            'status': 'DEPLOYING'
        }
    ],
    'machines_powerstate': [
        {
            'hostname': 'abc.xyz.com',
            'power_state': 'ON'
        },
        {
            'hostname': 'def.xyz.com',
            'power_state': 'ON'
        }
    ]
}

NODE_LIST = [
    {
        'hostname': 'abc.xyz.com',
        'memory': 12800,
        'cpu_count': 32,
        'status_name': 'READY',
        'boot_mac': '08:00:27:76:c1:2c',
        'power_state': 'ON',
        'power_address': 'dummy',
        'boot_ip': '1.2.3.4'
    },
    {
        'hostname': 'def.xyz.com',
        'memory': 12800,
        'cpu_count': 32,
        'status_name': 'DEPLOYING',
        'boot_mac': '08:00:27:76:c1:2e',
        'power_state': 'ON',
        'power_address': 'dummy',
        'boot_ip': '1.2.3.5'
    }
]

NODE_PROVISION_STATUS = 'nodes-provision-status'
MACHINES_POWER_STATE = 'machines-power-state'


def test_construct_status_helper():
    """
    Creates a status helper, tests that the context
    is passed to the sub-helper
    """
    helper = StatusHelper(CTX)
    assert helper.ctx == CTX


@mock.patch(
    'shipyard_airflow.control.helpers.status_helper.get_machines_powerstate',
    return_value=MACH_POWERSTATE_DICT)
@mock.patch(
    'shipyard_airflow.control.helpers.status_helper'
    '.get_nodes_provision_status',
    return_value=MACH_STATUS_DICT)
def test_get_site_statuses(patch1, patch2):
    """
    Testing status according to filter values
    """
    helper = StatusHelper(CTX)

    helper.drydock = 'Dummy'
    # test with filter for machine provision status
    ret_mach_status = helper.get_site_statuses([NODE_PROVISION_STATUS])
    prov_status_list = ret_mach_status.get('nodes_provision_status')

    assert STATUS_LIST == sorted(prov_status_list, key=lambda x: x['hostname'])

    # test with filter for machine power state
    ret_mach_powerstate = helper.get_site_statuses([MACHINES_POWER_STATE])
    mach_ps_list = ret_mach_powerstate.get('machines_powerstate')

    assert MACH_PS_LIST == sorted(mach_ps_list, key=lambda x: x['hostname'])

    # test without filters
    ret_wo_filters = helper.get_site_statuses()
    psl_wo = ret_wo_filters.get('nodes_provision_status')

    assert STATUS_LIST == sorted(psl_wo, key=lambda x: x['hostname'])

    mpl_wo = ret_wo_filters.get('machines_powerstate')

    assert MACH_PS_LIST == sorted(mpl_wo, key=lambda x: x['hostname'])

    # test with both filters
    all_filters = [NODE_PROVISION_STATUS, MACHINES_POWER_STATE]
    ret_all_statuses = helper.get_site_statuses(all_filters)
    psl_with = ret_all_statuses.get('nodes_provision_status')

    assert STATUS_LIST == sorted(psl_with, key=lambda x: x['hostname'])

    mpl_with = ret_all_statuses.get('machines_powerstate')

    assert MACH_PS_LIST == sorted(mpl_with, key=lambda x: x['hostname'])


@mock.patch("drydock_provisioner.drydock_client.client.DrydockClient")
def test_get_machines_powerstate(drydock):
    """
    Tests the functionality of the get_machines_powerstate method
    """
    drydock.get_nodes.return_value = NODE_LIST
    mach_ps_dict = sh.get_machines_powerstate(drydock)
    actual = mach_ps_dict.get('machines_powerstate')
    expected = MACH_POWERSTATE_DICT.get('machines_powerstate')

    assert actual == sorted(expected, key=lambda x: x['hostname'])


@mock.patch("drydock_provisioner.drydock_client.client.DrydockClient")
def test_get_nodes_provision_status(drydock):
    """
    Tests the functionality of the get_nodes_provision_status method
    """
    drydock.get_nodes.return_value = NODE_LIST
    nodes_provision_status = sh.get_nodes_provision_status(drydock)
    actual = nodes_provision_status.get('nodes_provision_status')
    expected = MACH_STATUS_DICT.get('nodes_provision_status')

    assert actual == sorted(expected, key=lambda x: x['hostname'])


def test__switcher():
    """
    Tests the functionality of the _switcher() method
    """
    helper = StatusHelper(CTX)
    pns = "get_nodes_provision_status"
    mps = "get_machines_powerstate"
    actual_pns = helper._switcher(NODE_PROVISION_STATUS)
    actual_mps = helper._switcher(MACHINES_POWER_STATE)

    assert pns in str(actual_pns)
    assert mps in str(actual_mps)
