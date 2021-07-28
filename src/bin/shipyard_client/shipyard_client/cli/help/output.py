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


def default():
    return '''THE SHIPYARD COMMAND
The base shipyard command supports options that determine cross-CLI behaviors.

FORMAT
shipyard [--context-marker=<uuid>] [--os_{various}=<value>]
    [--debug/--no-debug] [--output-format] <subcommands>

Please Note: --os_auth_url is required for every command except shipyard help
     <topic>.

TOPICS
For information of the following topics, run shipyard help <topic>
    actions
    configdocs'''


def actions():
    return '''ACTIONS
Workflow actions that may be invoked using Shipyard.

deploy_site
    Triggers the initial deployment of a site using the latest committed
    configdocs.

update_site
    Triggers the update to a deployment of a site, using the latest committed
    configdocs.

update_software
    Starts an update that only exercises the software portion of the committed
    configdocs.

redeploy_server
    Using the --param="target_nodes=node1,node2" parameter to target server(s),
    triggers a redeployment of servers using the last committed configdocs.

relabel_nodes
    Using the --param="target_nodes=node1,node2" parameter to target server(s),
    updates the Kubernetes node labels for the nodes on those servers.

test_site
    Triggers the Helm tests for the site, using parameters to control the
    tests:
    --param="release=release-name" to target a specific Helm release instead of
        all releases (the default if this parameter is not specified).
    '''


def configdocs():
    return '''CONFIGDOCS
The Shipyard Buffer Documents

Supported Commands:
    shipyard commit configdocs
    shipyard create configdocs
    shipyard get configdocs'''


def logs():
    return '''LOGS
Allows users to query and view logs using Shipyard

Supported Commands:
    shipyard logs step'''
