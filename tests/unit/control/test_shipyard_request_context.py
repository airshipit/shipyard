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

from shipyard_airflow.control.base import ShipyardRequestContext


def test_set_user():
    '''test set_user '''
    ctx = ShipyardRequestContext()
    ctx.set_user('test_user')
    assert ctx.user == 'test_user'


def test_set_project():
    '''test set_project'''
    ctx = ShipyardRequestContext()
    ctx.set_project('test_project')
    assert ctx.project == 'test_project'


def test_add_role():
    '''test add_role'''
    ctx = ShipyardRequestContext()
    ctx.add_role('test_role')
    assert 'test_role' in ctx.roles


def test_add_roles():
    '''test add_roles'''
    ctx = ShipyardRequestContext()
    print(ctx.roles)
    test_roles = ['Waiter', 'Host', 'Chef']
    ctx.add_roles(test_roles)
    assert ['Chef', 'Host', 'Waiter', 'anyone'] == sorted(ctx.roles)


def test_remove_roles():
    '''test remove_roles'''
    ctx = ShipyardRequestContext()
    ctx.remove_role('anyone')
    assert ctx.roles == []


def test_set_external_marker():
    '''test set_external_marker'''
    ctx = ShipyardRequestContext()
    ctx.set_external_marker('test_ext_marker')
    assert ctx.external_marker == 'test_ext_marker'


def test_set_policy_engine():
    '''test set_policy_engine'''
    ctx = ShipyardRequestContext()
    ctx.set_policy_engine('test_policy_engine')
    assert ctx.policy_engine == 'test_policy_engine'


def test_to_policy_view():
    '''test to_policy_view'''
    ctx = ShipyardRequestContext()
    policy_dict = ctx.to_policy_view()
    assert policy_dict['user_id'] == ctx.user_id
    assert policy_dict['user_domain_id'] == ctx.user_domain_id
    assert policy_dict['project_domain_id'] == ctx.project_domain_id
    assert policy_dict['roles'] == ctx.roles
    assert policy_dict['is_admin_project'] == ctx.is_admin_project
