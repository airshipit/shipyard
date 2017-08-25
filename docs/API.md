# Shipyard API

Logically, the API has three parts to handle the three areas of functionality
in Shipyard.

1. Document Staging
2. Action Handling
3. Airflow Monitoring


## Standards used by the API
See [UCP API conventions](https://github.com/att-comdev/ucp-integration/blob/master/docs/api-conventions.md)

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

#### Payload Structure
The documents as noted above (commonly yaml), in a format understood by
Deckhand


#### POST
Ingests a collection of documents. Synchronous. POSTing an empty body
indicates that the specified collection should be deleted when the Shipyard
Buffer is committed. If a POST to the commitconfigdocs is in progress, this
POST should be rejected with a 409 error.

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

#### GET
Returns the source documents for a collection of documents
##### Query Parameters
* version=committed|**buffer**  
Return the documents for the version specified - buffer by default.

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

#### GET
Returns the full set of configdocs in their rendered form.
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
#### Payload Structure
The response will be the list of validations from all downstream systems that
perform validation during the commit process.  The structure will match the
error response object described in the [UCP API conventions](https://github.com/att-comdev/ucp-integration/blob/master/docs/api-conventions.md)
and will be an aggregation of each UCP component's responses.

#### POST
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

#### Payload Structure
A list of actions that have been executed through shipyard's action API.
```
[
  { Action objects summarized, TBD },
  ...
]
```

#### GET
Returns the list of actions in the system that have been posted, and are
accessible to the current user.

##### Responses
* 200 OK  
If the actions can be retrieved.

#### POST
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

The POST will synchrounously create the action (a shell object that represents
a DAG invocation), perform any checks to validate the preconditions to run the
DAG, and trigger the invocation of the DAG. The DAG will run asynchronously in
airflow.
##### Responses
* 201 Created  
If the action is created successfully, and all preconditions to run the DAG
are successful. The response body is the action entity created.  
* 400 Bad Request  
If the action name doesn't exist, or the payload is otherwise malformed.  
* 409 Conflict  
For any failed pre-run validations. The response body is the action entity
created, with the failed validations. The DAG will not begin execution in this
case.  

---
### /v1.0/actions/{action_id}
Each action will be assigned an unique id that can be used to get details for
the action, including the execution status.

#### Payload Structure
All actions will include fields that indicate the following data:
* id (assigned during POST)
* name - the name of the action - likely to be the DAG Names, but may be mapped
for "nicer" values.
* parameters - a dictionary of the parameters configuring the action.
* tracking info - (user, time, etc)
* action_lifecycle value:
  * Pending
  * Validation Failed
  * Processing
  * Complete
  * Failed
* DAG_status - representing the status that airflow provides for an executing
DAG
* validations - a list of validations that have been done, including any status
information for those validations. During the lifecycle of the DAG, this list
of validations may continue to grow.
* steps - the list of steps for this action, including the status for that
step.

```
{ TBD }
```

#### GET
Returns the action entity for the specified id.
##### Responses
* 200 OK

---
### /v1.0/actions/{action_id}/validationdetails/{validation_id}
Allows for drilldown to validation detailed info.

#### Payload Structure
The detailed information for a validation
```
{ TBD }
```

#### GET
Returns the validation detail by Id for the supplied action Id.
##### Responses
* 200 OK

---
### /v1.0/actions/{action_id}/steps/{step_id}
Allow for drilldown to step information. The step information includes details
of the steps excution, successful or not, and enough to facilitate
troubleshooting in as easy a fashion as possible.

#### Payload Structure
The detailed information representing a single step of execution as part of an
action.
```
{ TBD }
```

#### GET
Returns the details for a step by id for the given action by Id.
##### Responses
* 200 OK

---
### /v1.0/actions/{action_id}/control/{control_verb}
Allows for issuing DAG controls against an action.

#### Payload Structure
None, there is no associated body for this resource

#### POST
Trigger a control action against an activity.- this includes: pause, unpause
##### Responses
* 202 Accepted

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

#### Payload Structure
A list of objects representing the DAGs that have run in airflow.
```
[
  {TBD},
  ...
]
```

#### GET
Queries airflow for DAGs that are running or have run (successfully or
unsuccessfully) and provides a summary of those things.
##### Query parameters
* since={iso8601 date (past) or duration}  
optional, a boundary in the past within which to retrieve results. Default is
30 days in the past.
##### Responses
* 200 OK

---
### /v1.0/workflows/{id}

#### Payload Structure
An object representing the information available from airflow regarding a DAG's
execution

```
{ TBD }
```

#### GET
Further details of a particular scheduled DAG's output
##### Responses
* 200 OK
