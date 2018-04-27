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

.. _shipyard_api:

Shipyard API
============
Logically, the API has three parts to handle the three areas of
functionality in Shipyard.

1. Document Staging
2. Action Handling
3. Airflow Monitoring
4. Logs Retrieval

Standards used by the API
-------------------------
See `UCP API
conventions <https://github.com/att-comdev/ucp-integration/blob/master/docs>`__

Notes on examples
-----------------
Examples assume the following environment variables are set before
issuing the curl commands shown:

::

    $TOKEN={a valid keystone token}
    $URL={the url and port of the shipyard api}

-  Examples will use json formatted by the jq command for sake of
   presentation.
-  Actual responses will not formatted.
-  The use of ellipsis indicate a repeated structure in the case of
   lists, or prior/subsequent structure unimportant to the example (or
   considered understood).
-  The content-length response headers have been removed so as to not
   cause confusion with the listed output.

Example response for an invalid token:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    HTTP/1.1 401 Unauthorized
    content-type: application/json
    x-shipyard-req: a8194b97-8973-4b04-a3b3-2bd319024c5d
    WWW-Authenticate: Keystone uri='http://keystone-api.ucp.svc.cluster.local:80/v3'

    {
      "apiVersion": "v1.0",
      "status": "Failure",
      "metadata": {},
      "message": "Unauthenticated",
      "code": "401 Unauthorized",
      "details": {
        "errorList": [
          {
            "message": "Credentials are not established"
          }
        ],
        "errorCount": 1,
        "errorType": "ApiError"
      },
      "kind": "status",
      "reason": "Credentials are not established"
    }

Document Staging API
--------------------
Shipyard will serve as the entrypoint for documents (designs, secrets,
configurations, etc...) into a site. Documents are posted to Shipyard in
collections, rather than individually. At any point in time, there will
be several versions of documents in a site that are accessible via this API:

- The "Committed Documents" version, which represents the last version of
  documents that were successfully commited with a commit_configdocs action.
- The "Shipyard Buffer" version, which represents the collection of documents
  that have been ingested by this API since the last commited version. Note
  that only one set of documents maybe posted to the buffer at a time by
  default. (This behavior can be overridden by query parameters issued by the
  user of Shipyard)
- The "Last Site Action" version represents the version of documents associated
  with the last successful or failed site action. Site actions include 'deploy_site'
  and 'update_site'.
- The "Successful Site Action" version represents the version of documents
  associated with the last successful site action. Site actions include 'deploy_site'
  and 'update_site'.

All versions of documents rely upon Deckhand for storage. Shipyard uses the
tagging features of Deckhand to find the appropriate Committed Documents,
Last Site Action, Successful Site Action and Shipyard Buffer version.

/v1.0/configdocs
~~~~~~~~~~~~~~~~
Represents the site configuration documents' current statuses

GET /v1.0/configdocs
^^^^^^^^^^^^^^^^^^^^
Returns a list of collections including their committed and buffer status.

.. note::

   The output type for this request is 'Content-Type: application/json'

Responses
'''''''''
200 OK
  If documents can be retrieved

/v1.0/configdocs/{collection_id}
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Represents the site configuration documents

Entity Structure
^^^^^^^^^^^^^^^^
The documents as noted above (commonly yaml), in a format understood by
Deckhand

POST /v1.0/configdocs/{collection_id}
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Ingests a collection of documents. Synchronous. POSTing an empty body
indicates that the specified collection should be deleted when the
Shipyard Buffer is committed. If a POST to the commitconfigdocs is in
progress, this POST should be rejected with a 409 error.

.. note::

   The expected input type for this request is ‘Content-Type: application/x-yaml’


Query Parameters
''''''''''''''''

-  buffermode=append|replace\|\ **rejectOnContents**
   Indicates how the existing Shipyard Buffer should be handled. By default,
   Shipyard will reject the POST if contents already exist in the Shipyard
   Buffer.

   -  append: Add the collection to the Shipyard Buffer, only if that
      collection doesn’t already exist in the Shipyard Buffer. If the
      collection is already present, the request will be rejected and a 409
      Conflict will be returned.
   -  replace: Clear the Shipyard Buffer before adding the specified
      collection.

Responses
'''''''''
201 Created
  If the documents are successfully ingested, even with validation failures.
  Response message includes:

  -  a list of validation results
  -  The response headers will include a Location indicating the GET
     endpoint to retrieve the configDocs

400 Bad Request
  When:

  - The request is missing a message body, attempting to create a collection
    with no contents.
  - The request has no new/changed contents for the collection.
  - The request is missing a Content-Length header.

409 Conflict
  A condition in the system is blocking this document ingestion

  -  If a commitconfigdocs POST is in progress.
  -  If any collections exist in the Shipyard Buffer unless buffermode=replace
     or buffermode=append.
  -  If buffermode=append, and the collection being posted is already in the
     Shipyard Buffer

GET /v1.0/configdocs/{collection_id}
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Returns the source documents for a collection of documents

.. note::

   The output type for this request is ‘Content-Type: application/x-yaml’

Query Parameters
''''''''''''''''
version=committed | last_site_action | successful_site_action | **buffer**
  Return the documents for the version specified - buffer by default.

Responses
'''''''''
200 OK
  If documents can be retrieved.

  -  If the response is 200 with an empty response body, this indicates
     that the buffer version is attempting to ‘delete’ the collection
     when it is committed. An empty response body will only be possible
     for version=buffer.

404 Not Found
  If the collection is not represented

  -  When version=buffer, this indicates that no representations of this
     collection have been POSTed since the last committed version.
  -  When version=committed, this indicates that either the collection has
     never existed or has been deleted by a prior commit.

/v1.0/renderedconfigdocs
~~~~~~~~~~~~~~~~~~~~~~~~
Represents the site configuration documents, as a whole set - does not
consider collections in any way.

GET /v1.0/renderedconfigdocs
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Returns the full set of configdocs in their rendered form.

.. note::

   The output type for this request is 'Content-Type: application/x-yaml'

Query Parameters
''''''''''''''''
version=committed | last_site_action | successful_site_action | **buffer**
  Return the documents for the version specified - buffer by default.

Responses
'''''''''
200 OK
  If documents can be retrieved.


/v1.0/commitconfigdocs
~~~~~~~~~~~~~~~~~~~~~~
An RPC style command to trigger a commit of the configuration documents from
the Shipyard Buffer to the Committed Documents. This resource will support POST
only.

Entity Structure
^^^^^^^^^^^^^^^^
The response will be the list of validations from all downstream systems that
perform validation during the commit process. The structure will match the
error response object described in the `UCP API
conventions <https://github.com/att-comdev/ucp-integration/blob/master/docs>`__
and will be an aggregation of each UCP component’s responses.

POST /v1.0/commitconfigdocs
^^^^^^^^^^^^^^^^^^^^^^^^^^^
Synchronous. Performs the commit of the Shipyard Buffer to the Committed
Documents. This invokes each of the UCP components to examine the Shipyard
Buffer version of the configuration documents and aggregate the responses.
While performing this commit, further POSTing of configdocs, or other commits
may not be invoked (Shipyard will block those requests with a 409 response). If
there are any failures to validate, the Shipyard Buffer and Committed Documents
will remain unchanged. If successful, the Shipyard Buffer will be cleared, and
the Committed documents will be updated.

.. note::

   If there are unhandled runtime errors during the commitconfigdocs POST, a
   deadlock situation may be possible. Future enhancements may improve this
   handling.

Query Parameters
''''''''''''''''
force=true | **false**
  By default, false, if there are validation failures the POST will
  fail with a 400 response. With force=true, allows for the commit to
  succeed (with a 200 response) even if there are validation failures
  from downstream components. The aggregate response of validation
  failures will be returned in this case, but the invalid documents
  will still be moved from the Shipyard Buffer to the Committed
  Documents.

dryrun=true | **false**
  By default, false.  With dryrun=true, the response will contain the
  validation status for the contents of the buffer.  The Shipyard Buffer will
  not be committed.

Responses
'''''''''
200 OK
  If the validations are successful. Returns an “empty” structure as as
  response indicating no errors. A 200 may also be returned if there
  are validation failures, but the force=true query parameter was
  specified. In this case, the response will contain the list of
  validations.
400 Bad Request
  If the validations fail. Returns a populated response structure
  containing the aggregation of the failed validations.
409 Conflict
  If the there is a POST to commitconfigdocs in progress.

Example
'''''''

::

    {
        "apiVersion": "v1",
        "code": "400 Bad Request",
        "details": {
            "errorCount": 2,
            "messageList": [
                {
                    "error": true,
                    "message": "Error loading effective site: 'NoneType' object is not iterable",
                    "name": "Drydock"
                },
                {
                    "error": true,
                    "message": "Armada unable to validate configdocs",
                    "name": "Armada"
                }
            ]
        },
        "kind": "Status",
        "message": "Validations failed",
        "metadata": {},
        "reason": "Validation",
        "status": "Failure"
    }

Action API
----------
The Shipyard Action API is a resource that allows for creation, control and
investigation of triggered workflows. These actions encapsulate a command
interface for the Undercloud Platform. See :ref:`shipyard_action_commands` for
supported actions

/v1.0/actions
~~~~~~~~~~~~~

Entity Structure
^^^^^^^^^^^^^^^^
A list of actions that have been executed through shipyard's action API.

::

    [
      { Action objects summarized, See below},
      ...
    ]


GET /v1.0/actions
^^^^^^^^^^^^^^^^^
Returns the list of actions in the system that have been posted, and are
accessible to the current user.

Responses
'''''''''
200 OK
  If the actions can be retrieved.

Example
'''''''

::

    $ curl -X GET $URL/api/v1.0/actions -H "X-Auth-Token:$TOKEN"

    HTTP/1.1 200 OK
    x-shipyard-req: 0804d13e-08fc-4e60-a819-3b7532cac4ec
    content-type: application/json; charset=UTF-8

    [
      {
        "dag_status": "failed",
        "parameters": {},
        "steps": [
          {
            "id": "action_xcom",
            "url": "/actions/01BTP9T2WCE1PAJR2DWYXG805V/steps/action_xcom",
            "index": 1,
            "state": "success"
          },
          {
            "id": "dag_concurrency_check",
            "url": "/actions/01BTP9T2WCE1PAJR2DWYXG805V/steps/dag_concurrency_check",
            "index": 2,
            "state": "success"
          },
          {
            "id": "preflight",
            "url": "/actions/01BTP9T2WCE1PAJR2DWYXG805V/steps/preflight",
            "index": 3,
            "state": "failed"
          },
          ...
        ],
        "action_lifecycle": "Failed",
        "dag_execution_date": "2017-09-23T02:42:12",
        "id": "01BTP9T2WCE1PAJR2DWYXG805V",
        "dag_id": "deploy_site",
        "datetime": "2017-09-23 02:42:06.860597+00:00",
        "user": "shipyard",
        "context_marker": "416dec4b-82f9-4339-8886-3a0c4982aec3",
        "name": "deploy_site"
      },
      ...
    ]

POST /v1.0/actions
^^^^^^^^^^^^^^^^^^
Creates an action in the system. This will cause some action to start. The
input body to this post will represent an action object that has at least these
fields:

name
  The name of the action to invoke, as noted in :ref:`shipyard_action_commands`

parameters
  A dictionary of parameters to use for the trigger invocation. The supported
  parameters will vary for the action invoked.

  ::

    {
      "name" : "action name",
      "parameters" : { varies by action }
    }

The POST will synchronously create the action (a shell object that represents
a DAG invocation), perform any checks to validate the preconditions to run the
DAG, and trigger the invocation of the DAG. The DAG will run asynchronously in
airflow.

Query Parameters
''''''''''''''''
allow-intermediate-commits=true | **false**
  By default, false. User will not be able to continue with a site action,
  e.g. update_site if the current committed revision of documents has other
  prior commits that have not been used as part of a site action. With
  allow-intermediate-commits=true, it allows user to override the default
  behavior and continue with the site action. This may be the case when the
  user is aware of the existence of such commits and/or when such commits are
  intended.

Responses
'''''''''
201 Created
  If the action is created successfully, and all preconditions to run the DAG
  are successful. The response body is the action entity created.
400 Bad Request
  If the action name doesn't exist, or the input entity is otherwise malformed.
409 Conflict
  For any failed pre-run validations. The response body is the action entity
  created, with the failed validations. The DAG will not begin execution in
  this case.

Example
'''''''

::

    $ curl -D - -d '{"name":"deploy_site"}' -X POST $URL/api/v1.0/actions \
      -H "X-Auth-Token:$TOKEN" -H "content-type:application/json"

    HTTP/1.1 201 Created
    location: {$URL}/api/v1.0/actions/01BTTMFVDKZFRJM80FGD7J1AKN
    x-shipyard-req: 629f2ea2-c59d-46b9-8641-7367a91a7016
    content-type: application/json; charset=UTF-8

    {
      "dag_status": "SCHEDULED",
      "parameters": {},
      "dag_execution_date": "2017-09-24T19:05:49",
      "id": "01BTTMFVDKZFRJM80FGD7J1AKN",
      "dag_id": "deploy_site",
      "name": "deploy_site",
      "user": "shipyard",
      "context_marker": "629f2ea2-c59d-46b9-8641-7367a91a7016",
      "timestamp": "2017-09-24 19:05:43.603591"
    }

/v1.0/actions/{action_id}
~~~~~~~~~~~~~~~~~~~~~~~~~
Each action will be assigned an unique id that can be used to get
details for the action, including the execution status.

Entity Structure
^^^^^^^^^^^^^^^^
All actions will include fields that indicate the following data:

action_lifecycle
  A summarized value indicating the status or lifecycle phase of the action.

  -  Pending - The action is scheduled or preparing for execution.
  -  Processing - The action is underway.
  -  Complete - The action has completed successfully.
  -  Failed - The action has encountered an error, and has failed.
  -  Paused - The action has been paused by a user.

command audit
  A list of commands that have been issued against the action. Initially,
  the action listed will be “invoke”, but may include “pause”, “unpause”,
  or “stop” if those commands are issued.

context_marker
  The user supplied or system assigned context marker associated with the
  action

dag_execution_date
  The execution date assigned by the workflow system during action
  creation.

dag_status
  Represents the status that airflow provides for an executing DAG.

datetime
  The time at which the action was invoked.

id
  The identifier for the action, a 26 character ULID assigned during the
  creation of the action.

name
  The name of the action, e.g.: deploy_site.

parameters
  The parameters configuring the action that were supplied by the user
  during action creation.

steps
  The list of steps for the action, including the status for that step.

user
  The user who has invoked this action, as acquired from the authorization
  token.

validations
  A list of validations that have been done, including any status
  information for those validations. During the lifecycle of the action,
  this list of validations may continue to grow.

GET /v1.0/actions/{action_id}
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Returns the action entity for the specified id.

Responses
'''''''''
200 OK

Example
'''''''

::

    $ curl -D - -X GET $URL/api/v1.0/actions/01BTTMFVDKZFRJM80FGD7J1AKN \
      -H "X-Auth-Token:$TOKEN"

    HTTP/1.1 200 OK
    x-shipyard-req: eb3eacb3-4206-40df-bd91-2a3a6d81cd02
    content-type: application/json; charset=UTF-8

    {
      "name": "deploy_site",
      "dag_execution_date": "2017-09-24T19:05:49",
      "validations": [],
      "id": "01BTTMFVDKZFRJM80FGD7J1AKN",
      "dag_id": "deploy_site",
      "command_audit": [
        {
          "id": "01BTTMG16R9H3Z4JVQNBMRV1MZ",
          "action_id": "01BTTMFVDKZFRJM80FGD7J1AKN",
          "datetime": "2017-09-24 19:05:49.530223+00:00",
          "user": "shipyard",
          "command": "invoke"
        }
      ],
      "user": "shipyard",
      "context_marker": "629f2ea2-c59d-46b9-8641-7367a91a7016",
      "datetime": "2017-09-24 19:05:43.603591+00:00",
      "dag_status": "failed",
      "parameters": {},
      "steps": [
        {
          "id": "action_xcom",
          "url": "/actions/01BTTMFVDKZFRJM80FGD7J1AKN/steps/action_xcom",
          "index": 1,
          "state": "success"
        },
        {
          "id": "dag_concurrency_check",
          "url": "/actions/01BTTMFVDKZFRJM80FGD7J1AKN/steps/dag_concurrency_check",
          "index": 2,
          "state": "success"
        },
        {
          "id": "preflight",
          "url": "/actions/01BTTMFVDKZFRJM80FGD7J1AKN/steps/preflight",
          "index": 3,
          "state": "failed"
        },
        {
          "id": "deckhand_get_design_version",
          "url": "/actions/01BTTMFVDKZFRJM80FGD7J1AKN/steps/deckhand_get_design_version",
          "index": 4,
          "state": null
        },
        ...
      ],
      "action_lifecycle": "Failed"
    }

/v1.0/actions/{action_id}/validationdetails/{validation_id}
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Allows for drilldown to validation detailed info.

Entity Structure
^^^^^^^^^^^^^^^^
The detailed information for a validation

::

    { TBD }

GET /v1.0/actions/{action_id}/validationdetails/{validation_id}
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Returns the validation detail by Id for the supplied action Id.

Responses
'''''''''
200 OK

/v1.0/actions/{action_id}/steps/{step_id}
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Allow for drilldown to step information. The step information includes
details of the steps execution, successful or not, and enough to
facilitate troubleshooting in as easy a fashion as possible.

Entity Structure
^^^^^^^^^^^^^^^^
A step entity represents detailed information representing a single step
of execution as part of an action. Not all fields are necessarily
represented in every returned entity.

dag_id
  The name/id of the workflow DAG that contains this step.

duration
  The duration (seconds) for the step.

end_date
  The timestamp of the completion of the step.

execution_date
  The execution date of the workflow that contains this step.

index
  The numeric value representing the position of this step in the sequence
  of steps associated with this step.

operator
  The name of the processing facility used by the workflow system.

queued_dttm
  The timestamp when the step was enqueued by the workflow system.

start_date
  The timestamp for the beginning of execution for this step.

state
  The execution state of the step.

task_id
  The name of the task used by the workflow system (and also representing
  this step name queried in the request.

try_number
  A number of retries taken in the case of failure. Some workflow steps
  may be configured to retry before considering the step truly failed.


GET /v1.0/actions/{action_id}/steps/{step_id}
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Returns the details for a step by id for the given action by Id. #####

Responses
'''''''''
200 OK

Example
'''''''

::

    $ curl -D - \
      -X GET $URL/api/v1.0/actions/01BTTMFVDKZFRJM80FGD7J1AKN/steps/action_xcom \
      -H "X-Auth-Token:$TOKEN"

    HTTP/1.1 200 OK
    x-shipyard-req: 72daca4d-1f79-4e08-825f-2ad181912a47
    content-type: application/json; charset=UTF-8

    {
      "end_date": "2017-09-24 19:05:59.446213",
      "duration": 0.165181,
      "queued_dttm": "2017-09-24 19:05:52.993983",
      "operator": "PythonOperator",
      "try_number": 1,
      "task_id": "action_xcom",
      "state": "success",
      "execution_date": "2017-09-24 19:05:49",
      "dag_id": "deploy_site",
      "index": 1,
      "start_date": "2017-09-24 19:05:59.281032"
    }

/v1.0/actions/{action_id}/control/{control_verb}
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Allows for issuing DAG controls against an action.

Entity Structure
^^^^^^^^^^^^^^^^
None, there is no associated response entity for this resource

POST /v1.0/actions/{action_id}/{control_verb}
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Trigger a control action against an activity.- this includes: pause, unpause

Responses
'''''''''
202 Accepted

Example
'''''''
Failure case - command is invalid for the execution state of the action.

::

    $ curl -D - \
      -X POST $URL/api/v1.0/actions/01BTTMFVDKZFRJM80FGD7J1AKN/control/pause \
      -H "X-Auth-Token:$TOKEN"

    HTTP/1.1 409 Conflict
    content-type: application/json
    x-shipyard-req: 9c9551e0-335c-4297-af93-8440cc6b324f

    {
      "apiVersion": "v1.0",
      "status": "Failure",
      "metadata": {},
      "message": "Unable to pause action",
      "code": "409 Conflict",
      "details": {
        "errorList": [
          {
            "message": "dag_run state must be running, but is failed"
          }
        ],
        "errorCount": 1,
        "errorType": "ApiError"
      },
      "kind": "status",
      "reason": "dag_run state must be running, but is failed"
    }

Success case

::

    $ curl -D - \
      -X POST $URL/api/v1.0/actions/01BTTMFVDKZFRJM80FGD7J1AKN/control/pause \
      -H "X-Auth-Token:$TOKEN"

    HTTP/1.1 202 Accepted
    content-length: 0
    x-shipyard-req: 019fae1c-03b0-4af1-b57d-451ae6ddac77
    content-type: application/json; charset=UTF-8


Airflow Monitoring API
----------------------
Airflow has a primary function of scheduling DAGs, as opposed to Shipyard’s
primary case of triggering DAGs. Shipyard provides functionality to allow for
an operator to monitor and review these scheduled workflows (DAGs) in addition
to the ones triggered by Shipyard. This API will allow for accessing Airflow
DAGs of any type – providing a peek into the totality of what is happening in
Airflow.

/v1.0/workflows
~~~~~~~~~~~~~~~
The resource that represents DAGs (workflows) in airflow

Entity Structure
^^^^^^^^^^^^^^^^
A list of objects representing the DAGs that have run in airflow.

GET /v1.0/workflows
^^^^^^^^^^^^^^^^^^^
Queries airflow for DAGs that are running or have run (successfully or
unsuccessfully) and provides a summary of those things.

Query parameters
''''''''''''''''
since={iso8601 date (past) or duration}
  optional, a boundary in the past within which to retrieve results. Default is
  30 days in the past.

Responses
'''''''''
200 OK

Example
'''''''
Notice the workflow_id values, these can be used for drilldown.

::

    curl -D - -X GET $URL/api/v1.0/workflows -H "X-Auth-Token:$TOKEN"

    HTTP/1.1 200 OK
    content-type: application/json; charset=UTF-8
    x-shipyard-req: 3ab4ccc6-b956-4c7a-9ae6-183c562d8297

    [
      {
        "execution_date": "2017-10-09 21:18:56",
        "end_date": null,
        "workflow_id": "deploy_site__2017-10-09T21:18:56.000000",
        "start_date": "2017-10-09 21:18:56.685999",
        "external_trigger": true,
        "dag_id": "deploy_site",
        "state": "failed",
        "run_id": "manual__2017-10-09T21:18:56"
      },
      {
        "execution_date": "2017-10-09 21:19:03",
        "end_date": null,
        "workflow_id": "deploy_site__2017-10-09T21:19:03.000000",
        "start_date": "2017-10-09 21:19:03.361522",
        "external_trigger": true,
        "dag_id": "deploy_site",
        "state": "failed",
        "run_id": "manual__2017-10-09T21:19:03"
      }
      ...
    ]

/v1.0/workflows/{workflow_id}
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Entity Structure
^^^^^^^^^^^^^^^^
An object representing the information available from airflow regarding
a DAG’s execution

GET /v1.0/workflows/{id}
^^^^^^^^^^^^^^^^^^^^^^^^
Further details of a particular workflow’s steps. All steps of all
sub-dags will be included in the list of steps, as well as section
indicating the sub-dags for this parent workflow.

Responses
'''''''''
200 OK

Example
'''''''
.. note::

   Sub_dags can be queried to restrict to only that sub-dag’s steps. e.g. using
   this as {workflow_id}:
   deploy_site.preflight.armada_preflight_check__2017-10-09T21:19:03.000000

::

    curl -D - \
        -X GET $URL/api/v1.0/workflows/deploy_site__2017-10-09T21:19:03.000000 \
        -H "X-Auth-Token:$TOKEN"

    HTTP/1.1 200 OK
    content-type: application/json; charset=UTF-8
    x-shipyard-req: 98d71530-816a-4692-9df2-68f22c057467

    {
      "execution_date": "2017-10-09 21:19:03",
      "end_date": null,
      "workflow_id": "deploy_site__2017-10-09T21:19:03.000000",
      "start_date": "2017-10-09 21:19:03.361522",
      "external_trigger": true,
      "steps": [
        {
          "end_date": "2017-10-09 21:19:14.916220",
          "task_id": "action_xcom",
          "start_date": "2017-10-09 21:19:14.798053",
          "duration": 0.118167,
          "queued_dttm": "2017-10-09 21:19:08.432582",
          "try_number": 1,
          "state": "success",
          "operator": "PythonOperator",
          "dag_id": "deploy_site",
          "execution_date": "2017-10-09 21:19:03"
        },
        {
          "end_date": "2017-10-09 21:19:25.283785",
          "task_id": "dag_concurrency_check",
          "start_date": "2017-10-09 21:19:25.181492",
          "duration": 0.102293,
          "queued_dttm": "2017-10-09 21:19:19.283132",
          "try_number": 1,
          "state": "success",
          "operator": "ConcurrencyCheckOperator",
          "dag_id": "deploy_site",
          "execution_date": "2017-10-09 21:19:03"
        },
        {
          "end_date": "2017-10-09 21:20:05.394677",
          "task_id": "preflight",
          "start_date": "2017-10-09 21:19:34.994775",
          "duration": 30.399902,
          "queued_dttm": "2017-10-09 21:19:28.449848",
          "try_number": 1,
          "state": "failed",
          "operator": "SubDagOperator",
          "dag_id": "deploy_site",
          "execution_date": "2017-10-09 21:19:03"
        },
        ...
      ],
      "dag_id": "deploy_site",
      "state": "failed",
      "run_id": "manual__2017-10-09T21:19:03",
      "sub_dags": [
        {
          "execution_date": "2017-10-09 21:19:03",
          "end_date": null,
          "workflow_id": "deploy_site.preflight__2017-10-09T21:19:03.000000",
          "start_date": "2017-10-09 21:19:35.082479",
          "external_trigger": false,
          "dag_id": "deploy_site.preflight",
          "state": "failed",
          "run_id": "backfill_2017-10-09T21:19:03"
        },
        ...,
        {
          "execution_date": "2017-10-09 21:19:03",
          "end_date": null,
          "workflow_id": "deploy_site.preflight.armada_preflight_check__2017-10-09T21:19:03.000000",
          "start_date": "2017-10-09 21:19:48.265023",
          "external_trigger": false,
          "dag_id": "deploy_site.preflight.armada_preflight_check",
          "state": "failed",
          "run_id": "backfill_2017-10-09T21:19:03"
        }
      ]
    }


Logs Retrieval API
------------------
This API allows users to query and view logs. Its usuage is currently limited
to Airflow logs retrieval but it can be extended in the future to retrieve other
logs. For instance, a possible use case might be to retrieve or ``tail`` the
Kubernetes logs.

/v1.0/actions/{action_id}/steps/{step_id}/logs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
This API allows users to query and view the logs for a particular workflow
step in Airflow. By default, it will retrieve the logs from the last attempt.
Note that a workflow step can retry multiple times with the names of the logs
as 1.log, 2.log, 3.log, etc. A user can specify the try number to view the logs
for a particular failed attempt, which will be useful during a troubleshooting
session.

Entity Structure
^^^^^^^^^^^^^^^^
Raw text of the logs retrieved from Airflow for that particular workflow step.

GET /v1.0/actions/{action_id}/steps/{step_id}/logs
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Queries Airflow and retrieves logs for a particular workflow step.

Query parameters
''''''''''''''''
try={int try_number}
  optional, represents a particular attempt of the workflow step. Default value
  is set to None.

Responses
'''''''''
200 OK

Example
'''''''

::

    curl -D - \
        -X GET $URL/api/v1.0/actions/01CASSSZT7CP1F0NKHCAJBCJGR/steps/action_xcom/logs?try=2 \
        -H "X-Auth-Token:$TOKEN"

    HTTP/1.1 200 OK
    content-type: application/json; charset=UTF-8
    x-shipyard-req: 49f74418-22b3-4629-8ddb-259bdfccf2fd

    [2018-04-11 07:30:41,945] {{cli.py:374}} INFO - Running on host airflow-worker-0.airflow-worker-discovery.ucp.svc.cluster.local
    [2018-04-11 07:30:41,991] {{models.py:1197}} INFO - Dependencies all met for <TaskInstance: deploy_site.action_xcom 2018-04-11 07:30:37 [queued]>
    [2018-04-11 07:30:42,001] {{models.py:1197}} INFO - Dependencies all met for <TaskInstance: deploy_site.action_xcom 2018-04-11 07:30:37 [queued]>
    [2018-04-11 07:30:42,001] {{models.py:1407}} INFO -
    --------------------------------------------------------------------------------
    Starting attempt 2 of 2
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
