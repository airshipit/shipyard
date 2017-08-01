# Shipyard API

Logically, the API has three parts to handle the three areas of functionality in Shipyard.

1. Document Staging
2. Action Handling 
3. Airflow Monitoring 

There are several standard error responses that should be handled appropriately by a client of this API:
* 401 Authentication Error  
If not authenticated
* 403 Forbidden  
If not authorized
* 404 Not found  
If a variable in the path doesn't reference a valid resource 
* 503 Service Unavailable  
Error if an upstream system cannot be reached (e.g. Deckhand for documents, Airflow for actions)

---
## Headers
### Required

* X-Auth-Token - The auth token to identify the invoking user.

### Optional

* X-Context-Marker - A context id that will be carried on all logs for this cleint-provided marker. This marker may only be a 36-character canonical representation of an UUID  (8-4-4-4-12)

---
## <a name="DocumentStagingAPI"></a> Document Staging API
Shipyard will serve as the entrypoint for documents and secrets into a site. At any point in time, there will be two represented versions of documents in a site that are accessible via this API. 

* The lastDeployed version, which represents the last version of documents that successfully completed deployment.
* The staged version, which represents the document set that has been ingested by this API since the lastDeployed version.

### /v1.0/configDocs  
Represents the site configuration documents.  

#### Payload Structure
The yaml documents separated by --- and concluded by ...


#### POST 
Ingests site configuration documents. Synchronous.
##### Responses
* 201 Created    
If the documents are successfully ingested, even with validation failures. Response message includes: 
  * a list of validation results  

The response headers will include a Location indicating the GET endpoint to retrieve the configDocs

#### GET 
Returns the source documents for the most recently staged version
##### Query Parameters
* lastDeployed=true|**false**  
Return the documents for the currently deployed version instead of the most recently staged
* compiled=true|**false**  
Return the documents in their compiled state instead of source documents

##### Responses
* 200 OK  
If documents can be retrieved.

#### DELETE  
Updates the configDocs to be the lastDeployed versions in deckhand, effectively discarding any staged documents. If there is no prior deployed version this effectively removes all secrets.

##### Responses
* 204 No Content


### /v1.0/secrets
Represents the secrets documents that will be used in combination with the config docs.  

#### Payload Structure
The yaml documents separated by --- and concluded by ...

#### POST 
Ingest new secrets documents.
##### Responses
* 201 Created  
If the documents are successfully ingested, even with validation failures. Response message includes:
  * a list of validation results

The response headers will include a Location indicating the GET endpoint to retrieve the configDocs

#### GET 
Return the secrets documents

##### Query Parameters
* lastDeployed=true|**false**  
Return the documents for the currently deployed version instead of the most recently staged
* compiled=true|**false**  
Return the documents in their compiled state instead of source documents

##### Responses
* 200 OK  
If documents can be retrieved.

#### DELETE
Updates the secrets to be the lastDeployed versions in deckhand, effectively discarding any staged documents. If there is no prior deployed version this effectively removes all secrets.
##### Responses
* 204 No Content


### /v1.0/validations
Represents the validation messages for the documents in deckhand  

#### Payload Structure
The list of validations
```
[
  { TBD }
]
```

#### GET 
Returns the validations

##### Query Parameters
* lastDeployed=true|**false**  
Return the documents for the currently deployed version instead of the most recently staged

##### Responses
* 200 OK  
If the validations can be retrieved.

---
## <a name="ActionAPI"></a> Action API
Signal to Shipyard to take an action (e.g. Invoke a named DAG)
See [Action Commands](API_action_commands.md) for supported actions


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
Returns the list of actions in the system that have been posted, and are accessible to the current user.

##### Responses
* 200 OK  
If the actions can be retrieved.

#### POST
Creates an action in the system. This will cause some action to start.
The input body to this post will represent an action object that has at least these fields:
* name  
The name of the action to invoke. This is likely to map to the actual DAG Names, but may be mapped for "nicer" values.
* parameters  
A dictionary of parameters to use for the trigger invocation. The supported parameters will vary for the action invoked.
```
{ 
  "name" : "action name",
  "parameters" : { varies by action }
}
```

The POST will synchrounously create the action (a shell object that represents a DAG invocation), perform any checks to validate the preconditions to run the DAG, and trigger the invocation of the DAG.
The DAG will run asynchronously in airflow.
##### Responses
* 201 Created  
If the action is created successfully, and all preconditions to run the DAG are successful. The response body is the action entity created.  
* 400 Bad Request  
If the action name doesn't exist, or the payload is otherwise malformed.  
* 409 Conflict  
For any failed validations. The response body is the action entity created, with the failed validations. The DAG will not begin execution in this case.  


### /v1.0/actions/{action_id} 
Each action will be assigned an unique id that can be used to get details for the action, including the execution status.

#### Payload Structure
All actions will include fields that indicate the following data:
* id (assigned during POST)
* name - the name of the action - likely to be the DAG Names, but may be mapped for "nicer" values.
* parameters - a dictionary of the parameters configuring the action.
* tracking info - (user, time, etc)
* action_lifecycle value:
  * Pending
  * Validation Failed
  * Processing 
  * Complete
  * Failed
* DAG_status - representing the status that airflow provides for an executing DAG
* validations - a list of validations that have been done, including any status information for those validations. During the lifecycle of the DAG, this list of validations may continue to grow.
* steps - the list of steps for this action, including the status for that step.

```
{ TBD }
```

#### GET
Returns the action entity for the specified id.
##### Responses
* 200 OK 


### /v1.0/actions/{action_id}/validationDetails/{validation_id} 
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


### /v1.0/actions/{action_id}/steps/{step_id}
Allow for drilldown to step information. The step information includes details of the steps excution, successful or not, and enough to facilitate troubleshooting in as easy a fashion as possible. 

#### Payload Structure
The detailed information representing a single step of execution as part of an action
```
{ TBD }
```

#### GET
Returns the details for a step by id for the given action by Id.
##### Responses
* 200 OK 


### /v1.0/actions/{action_id}/{control_verb}
Allows for issuing DAG controls against an action.

#### Payload Structure
None, there is no associated body for this resource

#### POST 
Trigger a control action against an activity.- this includes: pause, unpause
##### Responses
* 202 Accepted

---
## <a name="AirflowMonitoringAPI"></a> Airflow Monitoring API
Airflow has a primary function of scheduling DAGs, as opposed to Shipyard's primary case of triggering DAGs.  Shipyard will need to provide functionality to allow for an operator to monitor and review the scheduled tasks.  This API will allow for accessing Airflow DAGs of either type.

### /v1.0/completedDAGs
The resource that represents DAGs in airflow

#### Payload Structure
A list of objects representing the DAGs that have run in airflow.
```
[ 
  {TBD},
  ...
]
```

#### GET 
Queries airflow for recent completed DAGs (a summary).
##### Query parameters
* elapsedDays={n}  
optional, the number of days of history to retrieve. Default is 30 days.
##### Responses
* 200 OK


#### /v1.0/completedDAGs/{id}


#### Payload Structure
An object representing the information available from airflow regarding a DAG's execution

```
{ TBD }
```


#### GET
Further details of a particular scheduled DAG's output
##### Responses
* 200 OK
