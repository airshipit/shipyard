# Copyright 2017 The Openstack-Helm Authors.
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

# Actions requiring admin authority
#"admin_required": "role:admin"

# List workflow actions invoked by users
# GET  /api/v1.0/actions
#"workflow_orchestrator:list_actions": "rule:admin_required"

# Create a workflow action
# POST  /api/v1.0/actions
#"workflow_orchestrator:create_actions": "rule:admin_required"

# Retreive an action by its id
# GET  /api/v1.0/actions/{action_id}
#"workflow_orchestrator:get_action": "rule:admin_required"

# Retreive an action step by its id
# GET  /api/v1.0/actions/{action_id}/steps/{step_id}
#"workflow_orchestrator:get_action_step": "rule:admin_required"

# Retreive an action validation by its id
# GET  /api/v1.0/actions/{action_id}/validations/{validation_id}
#"workflow_orchestrator:get_action_validation": "rule:admin_required"

# Send a control to an action
# POST  /api/v1.0/actions/{action_id}/control/{control_verb}
#"workflow_orchestrator:invoke_action_control": "rule:admin_required"
