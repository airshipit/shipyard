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
The workflow actions that may be invoked using Shipyard

deploy_site: Triggers the initial deployment of a site using the latest
             committed configuration documents.

update_site: Triggers the initial deployment of a site, using the latest
             committed configuration documents.

redeploy_server: Using parameters to indicate which server(s), triggers a
                 redeployment of servers to the last committed design and
                 secrets.
    '''


def configdocs():
    return '''CONFIGDOCS
The Shipyard Buffer Documents

Supported Commands:
    shipyard commit configdocs
    shipyard create configdocs
    shipyard get configdocs'''
