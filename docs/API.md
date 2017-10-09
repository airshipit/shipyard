# Shipyard API

Logically, the API has three parts to handle the three areas of functionality
in Shipyard.

1. Document Staging
2. Action Handling
3. Airflow Monitoring


## Standards used by the API
See [UCP API conventions](https://github.com/att-comdev/ucp-integration/blob/master/docs/api-conventions.md)


## Notes on examples
Examples assume the following environment variables are set before issuing
the curl commands shown:
```
$TOKEN={a valid keystone token}
$URL={the url and port of the shipyard api}
```
* Examples will use json formatted by the jq command for sake of presentation.
* Actual responses will not formatted.
* The use of ellipsis indicate a repeated structure in the case of lists, or
prior/subsequent structure unimportant to the example (or considered
understood).
* The content-length response headers have been removed so as to not cause
confusion with the listed output.

### Example response for an invalid token:

```
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
```


---
## <a name="DocumentStagingAPI"></a> Document Staging API
>Shipyard will serve as the entrypoint for documents (designs, secrets,
configurations, etc...) into a site. Documents are posted to Shipyard in
collections, rather than individually. At any point in time, there will be two
represented versions of documents in a site that are accessible via this API:
>
>* The "Committed Documents" version, which represents the last version of
documents that were successfully commited with a commit_configdocs action.
>* The "Shipyard Buffer" version, which represents the collection of documents
that have been ingested by this API since the last commited version. Note that
only one set of documents maybe posted to the buffer at a time by default.
(This behavior can be overridden by query parameters issued by the user of
Shipyard)
>
> All versions of documents rely upon Deckhand for storage. Shipyard uses the
tagging features of Deckhand of to find the appropriate Committed Documents
and Shipyard Buffer version.

---
### /v1.0/configdocs/{collection_id}
Represents the site configuration documents

#### Entity Structure
The documents as noted above (commonly yaml), in a format understood by
Deckhand


#### POST /v1.0/configdocs/{collection_id}
Ingests a collection of documents. Synchronous. POSTing an empty body
indicates that the specified collection should be deleted when the Shipyard
Buffer is committed. If a POST to the commitconfigdocs is in progress, this
POST should be rejected with a 409 error.

Important:  
The expected input type for this request is 'Content-Type: application/x-yaml'

##### Query Parameters
* bufferMode=append|replace|**rejectOnContents**  
Indicates how the existing Shipyard Buffer should be handled. By default,
Shipyard will reject the POST if contents already exist in the Shipyard
Buffer.
  * append: Add the collection to the Shipyard Buffer, only if that
  collection doesn't already exist in the Shipyard Buffer. If the collection
  is already present, the request will be rejected and a 409 Conflict will be
  returned.
  * replace: Clear the Shipyard Buffer before adding the specified collection.
##### Responses
* 201 Created  
If the documents are successfully ingested, even with validation failures.
Response message includes:
  * a list of validation results
  * The response headers will include a Location indicating the GET endpoint
  to retrieve the configDocs

* 409 Conflict  
  * If a commitconfigdocs POST is in progress.
  * If any collections exist in the Shipyard Buffer unless bufferMode=replace
  or bufferMode=append.
  * If bufferMode=append, and the collection being posted is already in the
  Shipyard Buffer

#### GET /v1.0/configdocs/{collection_id}
Returns the source documents for a collection of documents
##### Query Parameters
* version=committed|**buffer**  
Return the documents for the version specified - buffer by default.

Important:  
The output type for this request is 'Content-Type: application/x-yaml'

##### Responses
* 200 OK  
If documents can be retrieved.
  * If the response is 200 with an empty response body, this indicates that
the buffer version is attempting to 'delete' the collection when it is
committed. An empty response body will only be possible for version=buffer.
* 404 Not Found  
If the collection is not represented
  * When version=buffer, this indicates that no representations of this
collection have been POSTed since the last committed version.
  * When version=committed, this indicates that either the collection has
never existed or has been deleted by a prior commit

---
### /v1.0/renderedconfigdocs
Represents the site configuration documents, as a whole set - does not
consider collections in any way.

#### GET /v1.0/renderedconfigdocs
Returns the full set of configdocs in their rendered form.

Important:  
The output type for this request is 'Content-Type: application/x-yaml'

##### Query Parameters
* version=committed|**buffer**  
Return the documents for the version specified - buffer by default.
##### Responses
* 200 OK  
If documents can be retrieved.

---
### /v1.0/commitconfigdocs
A RPC style command to trigger a commit of the configuration documents from the
Shipyard Buffer to the Committed Documents. This resource will support POST
only.
#### Entity Structure
The response will be the list of validations from all downstream systems that
perform validation during the commit process.  The structure will match the
error response object described in the [UCP API conventions](https://github.com/att-comdev/ucp-integration/blob/master/docs/api-conventions.md)
and will be an aggregation of each UCP component's responses.

#### POST /v1.0/commitconfigdocs
Performs the commit of the Shipyard Buffer to the Committed Documents.
Synchronous. This invokes each of the UCP components to examine the Shipyard
Buffer version of the configuration documents and aggregate the responses.
While performing this commit, further POSTing of configdocs, or other commits
may not be invoked (Shipyard will block those requests with a 409 response).
If there are any failures to validate, the Shipyard Buffer and Commited
Documents will remain unchanged. If successful, the Shipyard Buffer will be
cleared, and the Committed documents will be updated.

**Note**: if there are unhandled runtime errors during the commitconfigdocs POST,
a deadlock situation may be possible. Future enhancements may improve this
handling.

##### Query Parameters
* force=true|**false**  
By default, false, if there are validation failures the POST will fail with
a 400 response. With force=true, allows for the commit to succeed (with a 200
response) even if there are validation failures from downstream components. The
aggregate response of validation failures will be returned in this case, but
the invalid documents will still be moved from the Shipyard Buffer to the
Committed Documents.

##### Responses
* 200 OK  
If the validations are successful. Returns an "empty" structure as as response
indicating no errors. A 200 may also be returned if there are validation
failures, but the force=true query parameter was specified. In this case, the
response will contain the list of validations.
* 400 Bad Request  
If the validations fail.  Returns a populated response structure containing
the aggregation of the failed validations.
* 409 Conflict  
If the there is a POST to commitconfigdocs in progress.
---
## <a name="ActionAPI"></a> Action API
>The Shipyard Action API is a resource that allows for creation, control and
investigation of triggered workflows. These actions encapsulate a command
interface for the Undercloud Platform.
See [Action Commands](API_action_commands.md) for supported actions

---
### /v1.0/actions

#### Entity Structure
A list of actions that have been executed through shipyard's action API.
```
[
  { Action objects summarized, See below},
  ...
]
```

#### GET /v1.0/actions
Returns the list of actions in the system that have been posted, and are
accessible to the current user.

##### Responses
* 200 OK  
If the actions can be retrieved.

##### Example
```
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
```

#### POST /v1.0/actions
Creates an action in the system. This will cause some action to start.
The input body to this post will represent an action object that has at least
these fields:
* name  
The name of the action to invoke, as noted in
[Action Commands](API_action_commands.md)
* parameters  
A dictionary of parameters to use for the trigger invocation. The supported
parameters will vary for the action invoked.
```
{
  "name" : "action name",
  "parameters" : { varies by action }
}
```

The POST will synchronously create the action (a shell object that represents
a DAG invocation), perform any checks to validate the preconditions to run the
DAG, and trigger the invocation of the DAG. The DAG will run asynchronously in
airflow.
##### Responses
* 201 Created  
If the action is created successfully, and all preconditions to run the DAG
are successful. The response body is the action entity created.
* 400 Bad Request  
If the action name doesn't exist, or the input entity is otherwise malformed.
* 409 Conflict  
For any failed pre-run validations. The response body is the action entity
created, with the failed validations. The DAG will not begin execution in this
case.

##### Example
```
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
```
---
### /v1.0/actions/{action_id}
Each action will be assigned an unique id that can be used to get details for
the action, including the execution status.

#### Entity Structure
All actions will include fields that indicate the following data:
<dl>
  <dt>action_lifecycle</dt>
  <dd>A summarized value indicating the status or lifecycle phase of the
  action.</dd>
    <ul>
      <li>Pending - The action is scheduled or preparing for execution.</li>
      <li>Processing - The action is underway.</li>
      <li>Complete - The action has completed successfully.</li>
      <li>Failed - The action has encountered an error, and has failed.</li>
      <li>Paused - The action has been paused by a user.</li>
    </ul>
  </dd>
  <dt>command audit</dt>
  <dd>A list of commands that have been issued against the action. Initially,
      the action listed will be "invoke", but may include "pause", "unpause",
      or "stop" if those commands are issued.</dd>
  <dt>context_marker</dt>
  <dd>The user supplied or system assigned context marker associated with the
      action</dd>
  <dt>dag_execution_date</dt>
  <dd>The execution date assigned by the workflow system during action
  creation.</dd>
  <dt>dag_status</dt>
  <dd>Represents the status that airflow provides for an executing DAG.</dd>
  <dt>datetime</dt>
  <dd>The time at which the action was invoked.</dd>
  <dt>id</dt>
  <dd>The identifier for the action, a 26 character ULID assigned during the
creation of the action.</dd>
  <dt>name</dt>
  <dd>The name of the action, e.g.: deploy_site.</dd>
  <dt>parameters</dt>
  <dd>The parameters configuring the action that were supplied by the
user during action creation.</dd>
  <dt>steps</dt>
  <dd>The list of steps for the action, including the status for that
      step.</dd>
  <dt>user</dt>
  <dd>The user who has invoked this action, as acquired from the authorization
      token.</dd>
  <dt>validations</dt>
  <dd>A list of validations that have been done, including any status
      information for those validations. During the lifecycle of the action,
      this list of validations may continue to grow.</dd>


#### GET /v1.0/actions/{action_id}
Returns the action entity for the specified id.
##### Responses
* 200 OK

##### Example
```
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

```

---
### /v1.0/actions/{action_id}/validationdetails/{validation_id}
Allows for drilldown to validation detailed info.

#### Entity Structure
The detailed information for a validation
```
{ TBD }
```

#### GET /v1.0/actions/{action_id}/validationdetails/{validation_id}
Returns the validation detail by Id for the supplied action Id.
##### Responses
* 200 OK

---
### /v1.0/actions/{action_id}/steps/{step_id}
Allow for drilldown to step information. The step information includes details
of the steps excution, successful or not, and enough to facilitate
troubleshooting in as easy a fashion as possible.

#### Entity Structure
A step entity represents detailed information representing a single step of
execution as part of an action. Not all fields are necessarily represented in
every returned entity.

<dl>
  <dt>dag_id</dt>
  <dd>The name/id of the workflow DAG that contains this step.</dd>
  <dt>duration</dt>
  <dd>The duration (seconds) for the step.</dd>
  <dt>end_date</dt>
  <dd>The timestamp of the completion of the step.</dd>
  <dt>execution_date</dt>
  <dd>The execution date of the workflow that contains this step.</dd>
  <dt>index</dt>
  <dd>The ordinal value representing the position of this step in the sequence
      of steps associated with this step.</dd>
  <dt>operator</dt>
  <dd>The name of the processing facility used by the workflow system.</dd>
  <dt>queued_dttm</dt>
  <dd>The timestamp when the step was enqueued by the workflow system.</dd>
  <dt>start_date</dt>
  <dd>The timestamp for the beginning of execution for this step.</dd>
  <dt>state</dt>
  <dd>The execution state of the step.</dd>
  <dt>task_id</dt>
  <dd>The name of the task used by the workflow system (and also representing
      this step name queried in the reqeust.</dd>
  <dt>try_number</dt>
  <dd>A number of retries taken in the case of failure. Some workflow steps may
      be configured to retry before considering the step truly failed.</dd>
</dl>

#### GET /v1.0/actions/{action_id}/steps/{step_id}
Returns the details for a step by id for the given action by Id.
##### Responses
* 200 OK

##### Example
```
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

```
---
### /v1.0/actions/{action_id}/control/{control_verb}
Allows for issuing DAG controls against an action.

#### Entity Structure
None, there is no associated response entity for this resource

#### POST /v1.0/actions/{action_id}/{control_verb}
Trigger a control action against an activity.- this includes: pause, unpause
##### Responses
* 202 Accepted
##### Example
Failure case - command is invalid for the execution state of the action.
```
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
```

Success case
```
$ curl -D - \
  -X POST $URL/api/v1.0/actions/01BTTMFVDKZFRJM80FGD7J1AKN/control/pause \
  -H "X-Auth-Token:$TOKEN"

HTTP/1.1 202 Accepted
content-length: 0
x-shipyard-req: 019fae1c-03b0-4af1-b57d-451ae6ddac77
content-type: application/json; charset=UTF-8
```



---
## <a name="AirflowMonitoringAPI"></a> Airflow Monitoring API
>Airflow has a primary function of scheduling DAGs, as opposed to Shipyard's
primary case of triggering DAGs.  
Shipyard provides functionality to allow for an operator to monitor and review
these scheduled workflows (DAGs) in addition to the ones triggered by Shipyard.
This API will allow for accessing Airflow DAGs of any type -- providing a peek
into the totality of what is happening in Airflow.

---
### /v1.0/workflows
The resource that represents DAGs (workflows) in airflow

#### Entity Structure
A list of objects representing the DAGs that have run in airflow.

#### GET /v1.0/workflows
Queries airflow for DAGs that are running or have run (successfully or
unsuccessfully) and provides a summary of those things.
##### Query parameters
* since={iso8601 date (past) or duration}  
optional, a boundary in the past within which to retrieve results. Default is
30 days in the past.
##### Responses
* 200 OK

##### Example

Note the workflow_id values, these can be used for drilldown.

```
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
```

---
### /v1.0/workflows/{workflow_id}

#### Entity Structure
An object representing the information available from airflow regarding a DAG's
execution

#### GET /v1.0/workflows/{id}
Further details of a particular workflow's steps. All steps of all sub-dags
will be included in the list of steps, as well as  section indicating the
sub-dags for this parent workflow.
##### Responses
* 200 OK
##### Example

Note that sub_dags can be queried to restrict to only that sub-dag's steps.
e.g. using this as {workflow_id}:
deploy_site.preflight.armada_preflight_check__2017-10-09T21:19:03.000000


```
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
```
