..
      Copyright 2017 AT&T Intellectual Property.
      All Rights Reserved.

      Licensed under the Apache License, Version 2.0 (the "License"); you may
      not use this file except in compliance with the License. You may obtain
      a copy of the License at

          http://www.apache.org/licenses/LICENSE-2.0

      Unless required by applicable law or agreed to in writing, software
      distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
      WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
      License for the specific language governing permissions and limitations
      under the License.

.. _shipyard_cli:

Shipyard CLI
============

Environment Variables
---------------------
All commands will utilize the following environment variables to
determine necessary information for execution, unless otherwise noted.

OpenStack Keystone Authorization environment variables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The Shipyard CLI/API Client will check for the presence of appropriate
environment setup to do authentication on behalf of the user. The openrc
variables that will be used are as follows:

-  OS_PROJECT_DOMAIN_NAME ("default" if not specified)
-  OS_USER_DOMAIN_NAME ("default" if not specified)
-  OS_DOMAIN_NAME
-  OS_AUTH_TOKEN
-  OS_PROJECT_NAME
-  OS_USERNAME
-  OS_PASSWORD
-  OS_AUTH_URL The fully qualified identity endpoint. E.g. http://keystone.ucp.fully.qualified.name:80/v3

OpenStack Keystone Authorization environment variables *not* used
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
These OpenStack identity variables are not supported by shipyard.

-  OS_IDENTITY_API_VERSION
     This value will be ignored as Shipyard only supports version 3 at this time

Shipyard command options
------------------------
The base shipyard command supports options that determine cross-CLI behaviors.
These options are positioned immediately following the shipyard command as
shown here:

::

    shipyard <--these options> subcommands...

    shipyard
      [--context-marker=<uuid>]
      [--debug/--no-debug]
      [--os-{various}=<value>]
      [--output-format=[format | raw | cli]]  (default = cli)
      [--verbosity=[0-5]  (default = 1)
      <subcommands, as noted in this document>


\--context-marker=<uuid>
  Specifies a UUID (8-4-4-4-12 format) that will be used to correlate logs,
  transactions, etc... in downstream activities triggered by this interaction.
  If not specified, Shipyard will supply a new UUID to serve as this marker.
  (optional)

\--debug | --no-debug
  Enable/disable debugging of this CLI and API client. Defaults to no debug

\--os-<various>=<value>
  See supported OpenStack Keystone Authorization Environment variables above
  for the list of supported names, converting to a downcase version of the
  environment variable. E.g.: --os-auth-url=http://keystone.ucp:80/v3
  If not specified, the environment variables matching these options will be
  used instead. The Keystone os-auth-url should reference the exposed
  keystone:port for the target Shipyard environment, as this Keystone will be
  used to discover the instance of Shipyard. For most invocations other than
  help, a valid combination of values must be resolved to authenticate and
  authorize the user's invocation.

\--output-format=<format | raw | cli>
  Specifies the desired output formatting such that:

  -  format
       Display the raw output from the invoked Shipyard API in a column
       restricted mode.
  -  raw
       Display the result from the invoked Shipyard API as-is, without
       modification.
  -  cli (default)
       Display results in a plain text interpretation of the response from the
       invoked Shipyard API.

\--verbosity=<0-5>
  Integer value specifying the level of verbosity for the response information
  gathered from the API server. Setting a verbosity of ``0`` will remove all
  additional information from the response, a verbosity setting of ``1`` will
  include summary level notes and information, and ``5`` will include all
  available information. This setting does not necessarily effect all of the
  CLI commands, but may be set on all invocations. A default value of ``1`` is
  used if not specified.


Commit Commands
---------------

commit configdocs
~~~~~~~~~~~~~~~~~
Attempts to commit the Shipyard Buffer documents, first invoking validation by
downstream components.

::

    shipyard commit configdocs
        [--force]
        [--dryrun]

    Example:
        shipyard commit configdocs

\--force
  Force the commit to occur, even if validations fail.

\--dryrun
  Retrieve validation status for the contents of the buffer without committing.

Sample
^^^^^^

::

    $ shipyard commit configdocs
    Configuration documents committed.
    Status: Validations succeeded
    Reason: Validation
    - Info: DD1001
            Message: Rational Boot Storage: Validation successful.
            Source: Drydock
    - Info: DD2002
            Message: IP Locality Check: Validation successful.
            Source: Drydock
    - Info: DD2003
            Message: MTU Rationality: Validation successful.
            Source: Drydock
    - Info: DD2004
            Message: Network Trunking Rationalty: Validation successful.
            Source: Drydock
    - Info: DD2005
            Message: Duplicated IP Check: Validation successful.
            Source: Drydock
    - Info: DD3001
            Message: Platform Selection: Validation successful.
            Source: Drydock
    - Info: DD1006
            Message: Network Bond Rationality: Validation successful.
            Source: Drydock
    - Info: DD2002
            Message: Storage Partitioning: Validation successful.
            Source: Drydock
    - Info: DD2003
            Message: Storage Sizing: Validation successful.
            Source: Drydock
    - Info: DD1007
            Message: Allowed Network Check: Validation successful.
            Source: Drydock

    ####  Errors: 0, Warnings: 0, Infos: 10, Other: 0  ####

Control commands
----------------

stop
~~~~~~~~~~~~~~~~~~~~

Three separate commands with a common format that allow for controlling
the processing of actions created in Shipyard.

stop
  stops an executing item e.g. an action

::

    shipyard stop
        <type>
        <id>

    shipyard
        stop
        <qualified name>

    Example:

        shipyard stop action 01BTG32JW87G0YKA1K29TKNAFX


<type>
  The type of entity to take action upon. Currently supports: action
<id>
  The id of the entity to take action upon.
<qualified name>
  The qualified name of the item to take the specified action upon

Sample
^^^^^^

::

    $ shipyard stop action/01BZZMEXAVYGG7BT0BMA3RHYY7
    stop successfully submitted for action 01BZZMEXAVYGG7BT0BMA3RHYY7

A failed command:

::

    $ shipyard stop action/01BZZK07NF04XPC5F4SCTHNPKN
    Error: Unable to stop action
    Reason: dag_run state must be running, but is failed
    - Error: dag_run state must be running, but is failed

Create Commands
---------------

create action
~~~~~~~~~~~~~

Invokes the specified workflow through Shipyard. Returns the
id of the action invoked so that it can be queried subsequently.

::

    shipyard create action
        <action_command>
        --param=<parameter>    (repeatable)
        [--allow-intermediate-commits]

    Example:
        shipyard create action redeploy_server --param="target_nodes=mcp"
        shipyard create action update_site --param="continue-on-fail=true"

<action_command>
  The action to invoke.

\--param=<parameter>
  A parameter to be provided to the action being invoked. (repeatable)
  Note that we can pass in different information to the create action
  workflow, i.e. name of server to be redeployed, whether to continue
  the workflow if there are failures in Drydock, e.g. failed health
  checks.

\--allow-intermediate-commits
  Allows continuation of a site action, e.g. update_site even when the
  current committed revision of documents has other prior commits that
  have not been used as part of a site action.

Sample
^^^^^^

::

    $ shipyard create action deploy_site
    Name               Action                                   Lifecycle
    deploy_site        action/01BZZK07NF04XPC5F4SCTHNPKN        None


create configdocs
~~~~~~~~~~~~~~~~~
Load documents into the Shipyard Buffer. The use of one or more filenames
or one or more directory options must be specified.

::

    shipyard create configdocs
        <collection>
        [--append | --replace] [--empty-collection]
        --filename=<filename>    (repeatable)
            |
        --directory=<directory>  (repeatable)

    Example:
        shipyard create configdocs design --append --filename=site_design.yaml

.. note::

  If neither append nor replace are specified, the Shipyard API default value
  of rejectoncontents will be used.

.. note::

  --filename and/or --directory must be specified unless --empty-collection
  is used.

<collection>
  The collection to load.

\--append
  Add the collection to the Shipyard Buffer. This will fail if the collection
  already exists.

\--replace
  Clear the shipyard buffer and replace it with the specified contents.

\--empty-collection
  Indicate to Shipyard that the named collection should be made empty (contain
  no documents). If --empty-collection is specified, the files named by
  --filename or --directory will be ignored.

\--filename=<filename>
  The file name to use as the contents of the collection. (repeatable) If
  any documents specified fail basic validation, all of the documents will
  be rejected. Use of ``filename`` parameters may not be used in conjunction
  with the directory parameter.

\--directory=<directory>
  A directory containing documents that will be joined and loaded as a
  collection. (Repeatable) Any documents that fail basic validation will
  reject the whole set. Use of the ``directory`` parameter may not be used
  with the ``filename`` parameter.

\--recurse
  Recursively search through all directories for sub-directories that
  contain yaml files.

Sample
^^^^^^

::

    $ shipyard create configdocs coll1 --filename=/home/ubuntu/yaml/coll1.yaml
    Configuration documents added.
    Status: Validations succeeded
    Reason: Validation

Attempting to load the same collection into the uncommitted buffer.

::

    $ shipyard create configdocs coll1 --filename=/home/ubuntu/yaml/coll1.yaml
    Error: Invalid collection specified for buffer
    Reason: Buffermode : rejectoncontents
    - Error: Buffer is either not empty or the collection already exists in buffer. Setting a different buffermode may provide the desired functionality

Replace the buffer with --replace

::

    $ shipyard create configdocs coll1 --replace --filename=/home/ubuntu/yaml/coll1.yaml
    Configuration documents added.
    Status: Validations succeeded
    Reason: Validation

Describe Commands
-----------------

describe
~~~~~~~~

Retrieves the detailed information about the supplied namespaced item

::

    shipyard describe
        <namespaced_item>

    Example:
        shipyard describe action/01BTG32JW87G0YKA1K29TKNAFX
          Equivalent to:
        shipyard describe action 01BTG32JW87G0YKA1K29TKNAFX

        shipyard describe notedetails/01BTG32JW87G0YKA1KA9TBNA32
          Equivalent to:
        shipyard describe notedetails 01BTG32JW87G0YKA1KA9TBNA32

        shipyard describe step/01BTG32JW87G0YKA1K29TKNAFX/preflight
          Equivalent to:
        shipyard describe step preflight --action=01BTG32JW87G0YKA1K29TKNAFX

        shipyard describe validation/01BTG32JW87G0YKA1K29TKNAFX/01BTG3PKBS15KCKFZ56XXXBGF2
          Equivalent to:
        shipyard describe validation 01BTG3PKBS15KCKFZ56XXXBGF2 \
            --action=01BTG32JW87G0YKA1K29TKNAFX

        shipyard describe workflow/deploy_site__2017-01-01T12:34:56.123456
          Equivalent to:
        shipyard describe workflow deploy_site__2017-01-01T12:34:56.123456


describe action
~~~~~~~~~~~~~~~

Retrieves the detailed information about the supplied action id.

::

    shipyard describe action
        <action_id>

    Example:
        shipyard describe action 01BTG32JW87G0YKA1K29TKNAFX

Sample
^^^^^^

::

    $ shipyard describe action/01BZZK07NF04XPC5F4SCTHNPKN
    Name:                  deploy_site
    Action:                action/01BZZK07NF04XPC5F4SCTHNPKN
    Lifecycle:             Failed
    Parameters:            {}
    Datetime:              2017-11-27 20:34:24.610604+00:00
    Dag Status:            failed
    Context Marker:        71d4112e-8b6d-44e8-9617-d9587231ffba
    User:                  shipyard

    Steps                                                              Index        State     Footnotes
    step/01BZZK07NF04XPC5F4SCTHNPKN/action_xcom                        1            success
    step/01BZZK07NF04XPC5F4SCTHNPKN/dag_concurrency_check              2            success
    step/01BZZK07NF04XPC5F4SCTHNPKN/deckhand_get_design_version        3            failed    (1)
    step/01BZZK07NF04XPC5F4SCTHNPKN/validate_site_design               4            None
    step/01BZZK07NF04XPC5F4SCTHNPKN/deckhand_get_design_version        5            failed
    step/01BZZK07NF04XPC5F4SCTHNPKN/deckhand_get_design_version        6            failed
    step/01BZZK07NF04XPC5F4SCTHNPKN/drydock_build                      7            None

    Step Footnotes        Note
    (1)                   > step metadata: deckhand_get_design_version(2017-11-27 20:34:34.443053): Unable to determine version
                            - Info available with 'describe notedetails/09876543210987654321098765'

    Commands        User            Datetime
    invoke          shipyard        2017-11-27 20:34:34.443053+00:00

    Validations: None

    Action Notes:
    > action metadata: 01BZZK07NF04XPC5F4SCTHNPKN(2017-11-27 20:34:24.610604): Invoked using revision 3

describe notedetails
~~~~~~~~~~~~~~~~~~~~
Retrieves extended information related to a note.

::

    shipyard describe notedetails <note_id>

    Example:
        shipyard describe notedetails/01BTG32JW87G0YKA1KA9TBNA32

<note_id>
  The id of the note referenced as having more details in a separate response

Sample
^^^^^^

::

    $ shipyard describe notedetails/01BTG32JW87G0YKA1KA9TBNA32
    <a potentially large amount of data as returned by the source of info>

describe step
~~~~~~~~~~~~~
Retrieves the step details associated with an action and step.

::

    shipyard describe step
        <step_id>
        --action=<action id>

    Example:
        shipyard describe step preflight --action=01BTG32JW87G0YKA1K29TKNAFX

<step id>
  The id of the step found in the describe action response.

\--action=<action id>
  The action id that provides the context for this step.

Sample
^^^^^^

::

    $ shipyard describe step/01BZZK07NF04XPC5F4SCTHNPKN/action_xcom
    Name:              action_xcom
    Task ID:           step/01BZZK07NF04XPC5F4SCTHNPKN/action_xcom
    Index:             1
    State:             success
    Start Date:        2017-11-27 20:34:45.604109
    End Date:          2017-11-27 20:34:45.818946
    Duration:          0.214837
    Try Number:        1
    Operator:          PythonOperator

    Step Notes:
    > step metadata: deckhand_get_design_version(2017-11-27 20:34:34.443053): Unable to determine version
      - Info available with 'describe notedetails/09876543210987654321098765'

describe validation
~~~~~~~~~~~~~~~~~~~

Retrieves the validation details associated with an action and
validation id

::

    shipyard describe validation
        <validation_id>
        --action=<action_id>

    Example:
        shipyard describe validation 01BTG3PKBS15KCKFZ56XXXBGF2 \
            --action=01BTG32JW87G0YKA1K29TKNAFX

<validation_id>
  The id of the validation found in the describe action response.

\--action=<action_id>
  The action id that provides the context for this validation.

Sample
^^^^^^

::

    TBD

describe workflow
~~~~~~~~~~~~~~~~~

Retrieves the details for a workflow that is running or has run in the
workflow engine.

::

    shipyard describe workflow
        <workflow_id>

    Example:
        shipyard describe workflow deploy_site__2017-01-01T12:34:56.123456

<workflow_id>
  The id of the workflow found in the get workflows response.

Sample
^^^^^^

::

    $ shipyard describe workflow deploy_site__2017-11-27T20:34:33.000000
    Workflow:                deploy_site__2017-11-27T20:34:33.000000
    State:                   failed
    Dag ID:                  deploy_site
    Execution Date:          2017-11-27 20:34:33
    Start Date:              2017-11-27 20:34:33.979594
    End Date:                None
    External Trigger:        True

    Steps                              State
    action_xcom                        success
    dag_concurrency_check              success
    deckhand_get_design_version        failed
    validate_site_design               None
    deckhand_get_design_version        failed
    deckhand_get_design_version        failed
    drydock_build                      None

    Subworkflows:
    Workflow:                deploy_site.deckhand_get_design_version__2017-11-27T20:34:33.000000
    State:                   failed
    Dag ID:                  deploy_site.deckhand_get_design_version
    Execution Date:          2017-11-27 20:34:33
    Start Date:              2017-11-27 20:35:06.281825
    End Date:                None
    External Trigger:        False

    Workflow:                deploy_site.deckhand_get_design_version.deckhand_get_design_version__2017-11-27T20:34:33.000000
    State:                   failed
    Dag ID:                  deploy_site.deckhand_get_design_version.deckhand_get_design_version
    Execution Date:          2017-11-27 20:34:33
    Start Date:              2017-11-27 20:35:20.725506
    End Date:                None
    External Trigger:        False

Get Commands
------------

get actions
~~~~~~~~~~~

Lists the actions that have been invoked.

::

    shipyard get actions


Sample
^^^^^^

::

    $ shipyard get actions
    Name               Action                                   Lifecycle        Execution Time             Step Succ/Fail/Oth        Footnotes
    deploy_site        action/01BTP9T2WCE1PAJR2DWYXG805V        Failed           2017-09-23T02:42:12        12/1/3                    (1)
    update_site        action/01BZZKMW60DV2CJZ858QZ93HRS        Processing       2017-09-23T04:12:21        6/0/10                    (2)

    Action Footnotes        Note
    (1)                     > action metadata:01BTP9T2WCE1PAJR2DWYXG805V(2017-09-23 02:42:23.346534): Invoked with revision 3
    (2)                     > action metadata:01BZZKMW60DV2CJZ858QZ93HRS(2017-09-23 04:12:31.465342): Invoked with revision 4


get configdocs
~~~~~~~~~~~~~~

Retrieve documents loaded into Shipyard. The possible options include last
committed, last site action, last successful site action and retrieval from
the Shipyard Buffer. Site actions include ``deploy_site``, ``update_site`` and
``update_software``. Note that only one option may be selected when retrieving
the documents for a particular collection.

The command will compare the differences between the revisions specified if
the collection option is not specified. Note that we can only compare between
2 revisions. The relevant Deckhand revision id will be shown in the output as
well.

If both collection and revisions are not specified, the output will show the
differences between the 'committed' and 'buffer' revision (default behavior).

::

    shipyard get configdocs
        [--collection=<collection>]
        [--committed | --last-site-action | --successful-site-action | --buffer]
        [--cleartext-secrets]

    Example:
        shipyard get configdocs --collection=design
        shipyard get configdocs --collection=design --last-site-action
        shipyard get configdocs
        shipyard get configdocs --committed --last-site-action

\--collection=<collection>
  The collection to retrieve for viewing. If no collection is entered, the
  status of the collections in the buffer and those that are committed will be
  displayed.

\--committed
  Retrieve the documents that have last been committed for this collection

\--last-site-action
  Retrieve the documents associated with the last successful or failed site
  action for this collection

\--successful-site-action
  Retrieve the documents associated with the last successful site action
  for this collection

\--buffer
  Retrive the documents that have been loaded into Shipyard since the
  prior commit. If no documents have been loaded into the buffer for this
  collection, this will return an empty response (default)

\--cleartext-secrets
  Returns secrets as cleartext for encrypted documents if the user has the
  appropriate permissions in the target environment.  If the user does not
  have the appropriate permissions and sets this flag to true an error is
  returned.  Only impacts returned documents, not lists of documents.

Sample
^^^^^^

::

    $ shipyard get configdocs
     Comparing Base: committed (Deckhand revision 2)
             to New: buffer (Deckhand revision 3)
    Collection                  Base                  New
    coll1                       present               unmodified
    coll2                       not present           created

::

    $ shipyard get configdocs --committed --last-site-action
     Comparing Base: last_site_action (Deckhand revision 2)
             to New: committed (Deckhand revision 2)
    Collection                    Base                    New
    secrets                       present                 unmodified
    design                        present                 unmodified

::

    $ shipyard get configdocs --collection=coll1
    data:
      chart_groups: [kubernetes-proxy, container-networking, dns, kubernetes, kubernetes-rbac]
      release_prefix: ucp
    id: 1
    metadata:
      layeringDefinition: {abstract: false, layer: site}
      name: cluster-bootstrap-1
      schema: metadata/Document/v1.0
      storagePolicy: cleartext
    schema: armada/Manifest/v1.0
    status: {bucket: coll1, revision: 1}

get renderedconfigdocs
~~~~~~~~~~~~~~~~~~~~~~
Retrieve the rendered version of documents loaded into Shipyard.
Rendered documents are the "final" version of the documents after
applying Deckhand layering and substitution.

::

    shipyard get renderedconfigdocs
        [--committed | --last-site-action | --successful-site-action | --buffer]
        [--cleartext-secrets]

    Example:
        shipyard get renderedconfigdocs

\--committed
  Retrieve the documents that have last been committed.

\--last-site-action
  Retrieve the documents associated with the last successful or failed site action.

\--successful-site-action
  Retrieve the documents associated with the last successful site action.

\--buffer
  Retrieve the documents that have been loaded into Shipyard since the
  prior commit. (default)

\--cleartext-secrets
  Returns secrets as cleartext for encrypted documents if the user has the
  appropriate permissions in the target environment.  If the user does not
  have the appropriate permissions and sets this flag to true an error is
  returned.

Sample
^^^^^^

::

    $ shipyard get renderedconfigdocs
    data:
      chart_groups: [kubernetes-proxy, container-networking, dns, kubernetes, kubernetes-rbac]
      release_prefix: ucp
    id: 1
    metadata:
      layeringDefinition: {abstract: false, layer: site}
      name: cluster-bootstrap-1
      schema: metadata/Document/v1.0
      storagePolicy: cleartext
    schema: armada/Manifest/v1.0
    status: {bucket: coll1, revision: 1}

get workflows
~~~~~~~~~~~~~
Retrieve workflows that are running or have run in the workflow engine.
This includes processes that may not have been started as an action
(e.g. scheduled tasks).

::

    shipyard get workflows
      [--since=<date>]

    Example:
        shipyard get workflows

        shipyard get workflows --since=2017-01-01T12:34:56.123456

\--since=<date>
  The historical cutoff date to limit the results of this response.

Sample
^^^^^^

::

    $ shipyard get workflows
    Workflows                                      State
    deploy_site__2017-11-27T20:34:33.000000        failed
    update_site__2017-11-27T20:45:47.000000        running

get site-statuses
~~~~~~~~~~~~~~~~~

Retrieve the provisioning status of nodes and/or power states of the baremetal
machines in the site. If no option provided, retrieve records for both status types.

::

    shipyard get site-statuses
        [--status-type=<status-type>] (repeatable)
                   |

    Example:
        shipyard get site-statuses
        shipyard get site-statuses --status-type=nodes-provision-status
        shipyard get site-statuses --status-type=machines-power-state
        shipyard get site-statuses --status-type=nodes-provision-status --status-type=machines-power-state

\--status-type=<status-type>
  Retrieve provisioning statuses of all nodes for status-type
  "nodes-provision-status" and retrieve power states of all baremetal
  machines in the site for status-type "machines-power-state".

Sample
^^^^^^

::

    $ shipyard get site-statuses

     Nodes Provision Status:
    Hostname           Status
    abc.xyz.com        Ready
    def.xyz.com        Deploying

     Machines Power State:
    Hostname           Power State
    abc.xyz.com        On
    def.xyz.com        On

::

    $ shipyard get site-statuses --status-type=nodes-provision-status

     Nodes Provision Status:
    Hostname           Status
    abc.xyz.com        Ready
    def.xyz.com        Deploying

::

    $ shipyard get site-statuses --status-type=nodes-power-state

     Machines Power State:
    Hostname           Power State
    abc.xyz.com        On
    def.xyz.com        On

::

    $ shipyard get site-statuses --status-type=nodes-provision-status --status-type=nodes-power-state

     Nodes Provision Status:
    Hostname           Status
    abc.xyz.com        Ready
    def.xyz.com        Deploying

     Machines Power State:
    Hostname           Power State
    abc.xyz.com        On
    def.xyz.com        On

Logs Commands
-------------

logs
~~~~

Retrieves the logs of the supplied namespaced item

::

    shipyard logs
        <namespaced_item>

    Example:
        shipyard logs step/01BTG32JW87G0YKA1K29TKNAFX/drydock_validate_site_design
          Equivalent to:
        shipyard logs step drydock_validate_site_design --action=01BTG32JW87G0YKA1K29TKNAFX

        shipyard logs step/01BTG32JW87G0YKA1K29TKNAFX/drydock_validate_site_design/2
          Equivalent to:
        shipyard logs step drydock_validate_site_design --action=01BTG32JW87G0YKA1K29TKNAFX --try=2


logs step
~~~~~~~~~

Retrieves the logs for a particular workflow step. Note that 'try'
is an optional parameter.

::

    shipyard logs step
        <step_id> --action=<action_name> [--try=<try>]

    Example:
        shipyard logs step drydock_validate_site_design --action=01BTG32JW87G0YKA1K29TKNAFX

        shipyard logs step drydock_validate_site_design --action=01BTG32JW87G0YKA1K29TKNAFX --try=2

Sample
^^^^^^

::

    $ shipyard logs step/01C9VVQSCFS7V9QB5GBS3WFVSE/action_xcom
    [2018-04-11 07:30:41,945] {{cli.py:374}} INFO - Running on host airflow-worker-0.airflow-worker-discovery.ucp.svc.cluster.local
    [2018-04-11 07:30:41,991] {{models.py:1197}} INFO - Dependencies all met for <TaskInstance: deploy_site.action_xcom 2018-04-11 07:30:37 [queued]>
    [2018-04-11 07:30:42,001] {{models.py:1197}} INFO - Dependencies all met for <TaskInstance: deploy_site.action_xcom 2018-04-11 07:30:37 [queued]>
    [2018-04-11 07:30:42,001] {{models.py:1407}} INFO -
    --------------------------------------------------------------------------------
    Starting attempt 1 of 1
    --------------------------------------------------------------------------------

    [2018-04-11 07:30:42,022] {{models.py:1428}} INFO - Executing <Task(PythonOperator): action_xcom> on 2018-04-11 07:30:37
    [2018-04-11 07:30:42,023] {{base_task_runner.py:115}} INFO - Running: ['bash', '-c', 'airflow run deploy_site action_xcom 2018-04-11T07:30:37 --job_id 2 --raw -sd DAGS_FOLDER/deploy_site.py']
    [2018-04-11 07:30:42,606] {{base_task_runner.py:98}} INFO - Subtask: [2018-04-11 07:30:42,606] {{driver.py:120}} INFO - Generating grammar tables from /usr/lib/python3.5/lib2to3/Grammar.txt
    [2018-04-11 07:30:42,635] {{base_task_runner.py:98}} INFO - Subtask: [2018-04-11 07:30:42,634] {{driver.py:120}} INFO - Generating grammar tables from /usr/lib/python3.5/lib2to3/PatternGrammar.txt
    [2018-04-11 07:30:43,515] {{base_task_runner.py:98}} INFO - Subtask: [2018-04-11 07:30:43,515] {{configuration.py:206}} WARNING - section/key [celery/celery_ssl_active] not found in config
    [2018-04-11 07:30:43,516] {{base_task_runner.py:98}} INFO - Subtask: [2018-04-11 07:30:43,515] {{default_celery.py:41}} WARNING - Celery Executor will run without SSL
    [2018-04-11 07:30:43,517] {{base_task_runner.py:98}} INFO - Subtask: [2018-04-11 07:30:43,516] {{__init__.py:45}} INFO - Using executor CeleryExecutor
    [2018-04-11 07:30:43,822] {{base_task_runner.py:98}} INFO - Subtask: [2018-04-11 07:30:43,821] {{models.py:189}} INFO - Filling up the DagBag from /usr/local/airflow/dags/deploy_site.py
    [2018-04-11 07:30:43,892] {{cli.py:374}} INFO - Running on host airflow-worker-0.airflow-worker-discovery.ucp.svc.cluster.local
    [2018-04-11 07:30:43,945] {{base_task_runner.py:98}} INFO - Subtask: [2018-04-11 07:30:43,944] {{python_operator.py:90}} INFO - Done. Returned value was: None
    [2018-04-11 07:30:43,992] {{base_task_runner.py:98}} INFO - Subtask:   """)


Help Commands
-------------

help
~~~~
Provides topical help for shipyard.

.. note::

  --help will provide more specific command help.

::

    shipyard help
        [<topic>]

    Example:
        shipyard help configdocs

<topic>
  The topic of the help to be displayed. If this parameter is not
  specified the list of available topics will be displayed.

Sample
^^^^^^

::

    $ shipyard help
    THE SHIPYARD COMMAND
    The base shipyard command supports options that determine cross-CLI behaviors.

    FORMAT
    shipyard [--context-marker=<uuid>] [--os_{various}=<value>]
        [--debug/--no-debug] [--output-format] <subcommands>

    Please Note: --os_auth_url is required for every command except shipyard help
         <topic>.

    TOPICS
    For information of the following topics, run shipyard help <topic>
        actions
        configdocs
