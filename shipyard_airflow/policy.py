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
#
import logging
import functools
import falcon

from oslo_config import cfg
from oslo_policy import policy

policy_engine = None


class ShipyardPolicy(object):
    """
    Initialize policy defaults
    """
    # Base Policy
    base_rules = [
        policy.RuleDefault(
            'admin_required',
            'role:admin',
            description='Actions requiring admin authority'),
    ]

    # Orchestrator Policy
    task_rules = [
        policy.DocumentedRuleDefault('workflow_orchestrator:get_regions',
                                     'role:admin', 'Get region information', [{
                                         'path':
                                         '/api/v1.0/regions',
                                         'method':
                                         'GET'
                                     }, {
                                         'path':
                                         '/api/v1.0/regions/{region_id}',
                                         'method':
                                         'GET'
                                     }])
    ]

    # Regions Policy

    def __init__(self):
        self.enforcer = policy.Enforcer(cfg.CONF)

    def register_policy(self):
        self.enforcer.register_defaults(ShipyardPolicy.base_rules)
        self.enforcer.register_defaults(ShipyardPolicy.task_rules)

    def authorize(self, action, ctx):
        target = {'project_id': ctx.project_id, 'user_id': ctx.user_id}
        self.enforcer.authorize(action, target, ctx.to_policy_view())
        return self.enforcer.authorize(action, target, ctx.to_policy_view())


class ApiEnforcer(object):
    """
    A decorator class for enforcing RBAC policies
    """

    def __init__(self, action):
        self.action = action
        self.logger = logging.getLogger('shipyard.policy')

    def __call__(self, f):
        @functools.wraps(f)
        def secure_handler(slf, req, resp, *args, **kwargs):
            ctx = req.context
            policy_engine = ctx.policy_engine
            self.logger.debug("Enforcing policy %s on request %s" %
                              (self.action, ctx.request_id))
            try:
                if policy_engine is not None and policy_engine.authorize(
                        self.action, ctx):
                    return f(slf, req, resp, *args, **kwargs)
                else:
                    if ctx.authenticated:
                        slf.info(ctx, "Error - Forbidden access - action: %s" %
                                 self.action)
                        slf.return_error(
                            resp,
                            falcon.HTTP_403,
                            message="Forbidden",
                            retry=False)
                    else:
                        slf.info(ctx, "Error - Unauthenticated access")
                        slf.return_error(
                            resp,
                            falcon.HTTP_401,
                            message="Unauthenticated",
                            retry=False)
            except:
                slf.info(
                    ctx,
                    "Error - Expectation Failed - action: %s" % self.action)
                slf.return_error(
                    resp,
                    falcon.HTTP_417,
                    message="Expectation Failed",
                    retry=False)

        return secure_handler


def list_policies():
    default_policy = []
    default_policy.extend(ShipyardPolicy.base_rules)
    default_policy.extend(ShipyardPolicy.task_rules)

    return default_policy
