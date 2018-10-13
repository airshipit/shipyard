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
import functools
import logging

import falcon
from oslo_config import cfg
from oslo_policy import policy

from shipyard_airflow.errors import ApiError, AppError

CONF = cfg.CONF
LOG = logging.getLogger(__name__)
policy_engine = None

# Policy name constants
LIST_ACTIONS = 'workflow_orchestrator:list_actions'
CREATE_ACTION = 'workflow_orchestrator:create_action'
GET_ACTION = 'workflow_orchestrator:get_action'
GET_ACTION_STEP = 'workflow_orchestrator:get_action_step'
GET_ACTION_STEP_LOGS = 'workflow_orchestrator:get_action_step_logs'
GET_ACTION_VALIDATION = 'workflow_orchestrator:get_action_validation'
INVOKE_ACTION_CONTROL = 'workflow_orchestrator:invoke_action_control'
GET_CONFIGDOCS_STATUS = 'workflow_orchestrator:get_configdocs_status'
CREATE_CONFIGDOCS = 'workflow_orchestrator:create_configdocs'
GET_CONFIGDOCS = 'workflow_orchestrator:get_configdocs'
COMMIT_CONFIGDOCS = 'workflow_orchestrator:commit_configdocs'
GET_RENDEREDCONFIGDOCS = 'workflow_orchestrator:get_renderedconfigdocs'
LIST_WORKFLOWS = 'workflow_orchestrator:list_workflows'
GET_WORKFLOW = 'workflow_orchestrator:get_workflow'
GET_NOTEDETAILS = 'workflow_orchestrator:get_notedetails'
GET_SITE_STATUSES = 'workflow_orchestrator:get_site_statuses'
ACTION_DEPLOY_SITE = 'workflow_orchestrator:action_deploy_site'
ACTION_UPDATE_SITE = 'workflow_orchestrator:action_update_site'
ACTION_UPDATE_SOFTWARE = 'workflow_orchestrator:action_update_software'
ACTION_REDEPLOY_SERVER = 'workflow_orchestrator:action_redeploy_server'
ACTION_RELABEL_NODES = 'workflow_orchestrator:action_relabel_nodes'
ACTION_TEST_SITE = 'workflow_orchestrator:action_test_site'


class ShipyardPolicy(object):
    """
    Initialize policy defaults
    """

    RULE_ADMIN_REQUIRED = 'rule:admin_required'
    RULE_DENY_ALL = 'rule:deny_all'

    # Base Policy
    base_rules = [
        policy.RuleDefault(
            'admin_required',
            'role:admin',
            description='Actions requiring admin authority'
        ),
        policy.RuleDefault(
            'deny_all',
            '!',
            description='Rule to deny all access. Used for default denial'
        ),
    ]

    # Orchestrator Policy
    task_rules = [
        policy.DocumentedRuleDefault(
            LIST_ACTIONS,
            RULE_ADMIN_REQUIRED,
            'List workflow actions invoked by users',
            [{
                'path': '/api/v1.0/actions',
                'method': 'GET'
            }]
        ),
        # See below for finer grained action access. This controls access
        # to being able to create any actions.
        policy.DocumentedRuleDefault(
            CREATE_ACTION,
            RULE_ADMIN_REQUIRED,
            'Create a workflow action',
            [{
                'path': '/api/v1.0/actions',
                'method': 'POST'
            }]
        ),
        policy.DocumentedRuleDefault(
            GET_ACTION,
            RULE_ADMIN_REQUIRED,
            'Retrieve an action by its id',
            [{
                'path': '/api/v1.0/actions/{action_id}',
                'method': 'GET'
            }]
        ),
        policy.DocumentedRuleDefault(
            GET_ACTION_STEP,
            RULE_ADMIN_REQUIRED,
            'Retrieve an action step by its id',
            [{
                'path': '/api/v1.0/actions/{action_id}/steps/{step_id}',
                'method': 'GET'
            }]
        ),
        policy.DocumentedRuleDefault(
            GET_ACTION_STEP_LOGS,
            RULE_ADMIN_REQUIRED,
            'Retrieve logs of an action step by its id',
            [{
                'path': '/api/v1.0/actions/{action_id}/steps/{step_id}/logs',
                'method': 'GET'
            }]
        ),
        policy.DocumentedRuleDefault(
            GET_ACTION_VALIDATION,
            RULE_ADMIN_REQUIRED,
            'Retrieve an action validation by its id',
            [{
                'path':
                '/api/v1.0/actions/{action_id}/validations/{validation_id}',
                'method': 'GET'
            }]
        ),
        policy.DocumentedRuleDefault(
            INVOKE_ACTION_CONTROL,
            RULE_ADMIN_REQUIRED,
            'Send a control to an action',
            [{
                'path': '/api/v1.0/actions/{action_id}/control/{control_verb}',
                'method': 'POST'
            }]
        ),
        policy.DocumentedRuleDefault(
            GET_CONFIGDOCS_STATUS,
            RULE_ADMIN_REQUIRED,
            'Retrieve the status of the configdocs',
            [{
                'path': '/api/v1.0/configdocs',
                'method': 'GET'
            }]
        ),
        policy.DocumentedRuleDefault(
            CREATE_CONFIGDOCS,
            RULE_ADMIN_REQUIRED,
            'Ingest configuration documents for the site design',
            [{
                'path': '/api/v1.0/configdocs/{collection_id}',
                'method': 'POST'
            }]
        ),
        policy.DocumentedRuleDefault(
            GET_CONFIGDOCS,
            RULE_ADMIN_REQUIRED,
            'Retrieve a collection of configuration documents',
            [{
                'path': '/api/v1.0/configdocs/{collection_id}',
                'method': 'GET'
            }]
        ),
        policy.DocumentedRuleDefault(
            COMMIT_CONFIGDOCS,
            RULE_ADMIN_REQUIRED,
            ('Move documents from the Shipyard buffer to the committed '
             'documents'),
            [{
                'path': '/api/v1.0/commitconfigdocs',
                'method': 'POST'
            }]
        ),
        policy.DocumentedRuleDefault(
            GET_RENDEREDCONFIGDOCS,
            RULE_ADMIN_REQUIRED,
            ('Retrieve the configuration documents rendered by Deckhand into '
             'a complete design'),
            [{
                'path': '/api/v1.0/renderedconfigdocs',
                'method': 'GET'
            }]
        ),
        policy.DocumentedRuleDefault(
            LIST_WORKFLOWS,
            RULE_ADMIN_REQUIRED,
            ('Retrieve the list of workflows (DAGs) that have been invoked '
             'in Airflow, whether via Shipyard or scheduled'),
            [{
                'path': '/api/v1.0/workflows',
                'method': 'GET'
            }]
        ),
        policy.DocumentedRuleDefault(
            GET_WORKFLOW,
            RULE_ADMIN_REQUIRED,
            ('Retrieve the detailed information for a workflow (DAG) from '
             'Airflow'),
            [{
                'path': '/api/v1.0/workflows/{id}',
                'method': 'GET'
            }]
        ),
        policy.DocumentedRuleDefault(
            GET_NOTEDETAILS,
            RULE_ADMIN_REQUIRED,
            ('Retrieve the details for a note. Further authorization is '
             'required depending on the topic of the note'),
            [{
                'path': '/api/v1.0/notedetails/{note_id}',
                'method': 'GET'
            }]
        ),
        policy.DocumentedRuleDefault(
            GET_SITE_STATUSES,
            RULE_ADMIN_REQUIRED,
            'Retrieve the statuses for the site',
            [{
                'path': '/api/v1.0/site_statuses',
                'method': 'GET'
            }]
        ),
        # Specific actions - can be controlled independently. See above for
        # overall access to creating an action. This controls the ability to
        # create specific actions (invoke specific workflows)
        policy.DocumentedRuleDefault(
            ACTION_DEPLOY_SITE,
            RULE_ADMIN_REQUIRED,
            'Create a workflow action to deploy the site',
            [{
                'path': '/api/v1.0/actions',
                'method': 'POST'
            }]
        ),
        policy.DocumentedRuleDefault(
            ACTION_UPDATE_SITE,
            RULE_ADMIN_REQUIRED,
            'Create a workflow action to update the site',
            [{
                'path': '/api/v1.0/actions',
                'method': 'POST'
            }]
        ),
        policy.DocumentedRuleDefault(
            ACTION_UPDATE_SOFTWARE,
            RULE_ADMIN_REQUIRED,
            'Create a workflow action to update the site software',
            [{
                'path': '/api/v1.0/actions',
                'method': 'POST'
            }]
        ),
        policy.DocumentedRuleDefault(
            ACTION_REDEPLOY_SERVER,
            RULE_ADMIN_REQUIRED,
            'Create a workflow action to redeploy target servers',
            [{
                'path': '/api/v1.0/actions',
                'method': 'POST'
            }]
        ),
        policy.DocumentedRuleDefault(
            ACTION_RELABEL_NODES,
            RULE_ADMIN_REQUIRED,
            'Create a workflow action to relabel target nodes',
            [{
                'path': '/api/v1.0/actions',
                'method': 'POST'
            }]
        ),
        policy.DocumentedRuleDefault(
            ACTION_TEST_SITE,
            RULE_ADMIN_REQUIRED,
            'Create a workflow action to invoke Helm tests on all releases ' \
            'or a targeted release',
            [{
                'path': '/api/v1.0/actions',
                'method': 'POST'
            }]
        ),
    ]

    # Regions Policy

    def __init__(self):
        self.enforcer = policy.Enforcer(cfg.CONF)

    def register_policy(self):
        self.enforcer.register_defaults(ShipyardPolicy.base_rules)
        self.enforcer.register_defaults(ShipyardPolicy.task_rules)

    def authorize(self, action, ctx):
        target = {'project_id': ctx.project_id, 'user_id': ctx.user_id}
        return self.enforcer.authorize(action, target, ctx.to_policy_view())


class ApiEnforcer(object):
    """
    A decorator class for enforcing RBAC policies
    """

    def __init__(self, action):
        self.action = action
        self.logger = LOG

    def __call__(self, f):
        @functools.wraps(f)
        def secure_handler(slf, req, resp, *args, **kwargs):
            check_auth(ctx=req.context, rule=self.action)
            return f(slf, req, resp, *args, **kwargs)
        return secure_handler


def check_auth(ctx, rule):
    """Checks the authorization to the requested rule

    :param ctx: the request context for the action being performed
    :param rule: the name of the policy rule to validate the user in the
        context against

    Returns if authorized, otherwise raises an ApiError.
    """
    try:
        policy_eng = ctx.policy_engine
        LOG.info("Policy Engine: %s", policy_eng.__class__.__name__)
        # perform auth
        LOG.info("Enforcing policy %s on request %s", rule, ctx.request_id)
        # policy engine must be configured
        if policy_eng is None:
            LOG.error(
                "Error-Policy engine required-action: %s", rule)
            raise AppError(
                title="Auth is not being handled by any policy engine",
                status=falcon.HTTP_500,
                retry=False
            )
        if policy_eng.authorize(rule, ctx):
            # authorized - log and return
            LOG.info("Request to %s is authorized", rule)
            return
    except Exception as ex:
        # couldn't service the auth request
        LOG.exception("Error - Expectation Failed - action: %s", rule)
        raise ApiError(
            title="Expectation Failed",
            status=falcon.HTTP_417,
            retry=False
        )
    # raise the appropriate response exeception
    if ctx.authenticated:
        # authenticated but not authorized
        LOG.error("Error: Forbidden access - action: %s", rule)
        raise ApiError(
            title="Forbidden",
            status=falcon.HTTP_403,
            description="Credentials do not permit access",
            retry=False
        )
    else:
        LOG.error("Error - Unauthenticated access")
        raise ApiError(
            title="Unauthenticated",
            status=falcon.HTTP_401,
            description="Credentials are not established",
            retry=False
        )


def list_policies():
    default_policy = []
    default_policy.extend(ShipyardPolicy.base_rules)
    default_policy.extend(ShipyardPolicy.task_rules)

    return default_policy
