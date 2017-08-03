Please note that this API information is being superseded by a new client facing API (under development) This file will stay in place for now, but needs to be removed when the newer API is in place.  Please see API.md for the newer information.

## REST API ##

The default deployment will build an environment where the Falcon API server listens on port 31901

The Airflow Web UI can be accessed on the localhost via port 32080

At the present moment, Shipyard expects authentication token to be passed, i.e. *10* for the shipyard
user and *admin* for the admin user. An authentication error like the one below will be thrown if the
token is not passed in or if an invalid token is used (note that keystone will be used to perform 
authentication in the future).

```
$ http localhost:31901/api/experimental/dags/airflow_task_state/tasks/airflow_task_state
HTTP/1.1 401 Unauthorized
content-length: 97
content-type: application/json; charset=UTF-8
vary: Accept
x-shipyard-req: 1a35a1cf-29c4-4642-aba6-9c12e3fb7f04

{
    "description": "This resource requires an authorized role.",
    "title": "Authentication required"
}

```

Note: An optional X-Context-Marker can also be passed with the REST call


The same Airflow REST API [endpoints](https://airflow.incubator.apache.org/api.html) are used in
Shipyard to perform API calls to airflow


Note: The following examples make use of [HTTPie](https://httpie.org/) to perform RESTful API calls

### Example 1 ###

Retrieve information of a particular task 

```
$ http localhost:31901/api/experimental/dags/airflow_task_state/tasks/airflow_task_state X-Auth-Token:admin
HTTP/1.1 200 OK
content-length: 1153
content-type: application/json; charset=UTF-8
x-shipyard-req: e3afc941-a31a-42ab-a1b5-8717777fe155

{
    "adhoc": "False",
    "airflow_command": "airflow task_state airflow_task_state airflow_task_state 2016-06-26T16:35:45.068576",
    "airflow_dag_id": "airflow_task_state",
    "airflow_execution_date": "2016-06-26T16:35:45.068576",
    "airflow_task_id": "airflow_task_state",
    "depends_on_past": "False",
    "email": "['airflow@example.com']",
    "email_on_failure": "False",
    "email_on_retry": "False",
    "end_date": "None",
    "execution_timeout": "None",
    "max_retry_delay": "None",
    "on_failure_callback": "None",
    "on_retry_callback": "None",
    "on_success_callback": "None",
    "owner": "airflow",
    "params": "{}",
    "pool": "None",
    "priority_weight": "1",
    "queue": "default",
    "resources": "{'disk': {'_qty': 512, '_units_str': 'MB', '_name': 'Disk'}, 'gpus': {'_qty': 0, '_units_str': 'gpu(s)', '_name': 'GPU'}, 'ram': {'_qty': 512, '_units_str': 'MB', '_name': 'RAM'}, 'cpus': {'_qty': 1, '_units_str': 'core(s)', '_name': 'CPU'}}",
    "retries": "1",
    "retry_delay": "0:01:00",
    "retry_exponential_backoff": "False",
    "run_as_user": "None",
    "sla": "None",
    "start_date": "2017-06-25 00:00:00",
    "task_id": "airflow_task_state",
    "trigger_rule": "all_success",
    "wait_for_downstream": "False"
}

```


Note that we will get an error response if we try and retrieve an invalid task:

```
$ http localhost:31901/api/experimental/dags/airflow_task_state/tasks/test123 X-Auth-Token:10
HTTP/1.1 400 Bad Request
content-length: 61
content-type: application/json; charset=UTF-8
x-shipyard-req: ec150a0c-30bf-40ba-a40e-ad4627d8770b

{
    "error": "Task test123 not found in dag airflow_task_state"
}

```


Retrieval of invalid dag will end up with error as well:

```
$ http localhost:31901/api/experimental/dags/test123/tasks/airflow_task_state X-Auth-Token:10
HTTP/1.1 400 Bad Request
content-length: 34
content-type: application/json; charset=UTF-8
x-shipyard-req: d718820b-7f74-4893-affb-92e783ec4541

{
    "error": "Dag test123 not found"
}

```


### Example 2 ###

Execute a Dag

```
$ http POST localhost:31901/api/experimental/dags/airflow_task_state/dag_runs X-Auth-Token:10 X-Context-Marker:airflow_task_state_testing
HTTP/1.1 200 OK
content-length: 0
content-type: application/json; charset=UTF-8
x-shipyard-req: a2f2a49c-82c8-4131-9764-fc15495b520c

```

In this example, the *airflow_task_state* dag will get executed and the information of the task instances
can be retrieved from the Airflow Web UI which is usually located at this [link](http://localhost:32080/admin/taskinstance/)


Note that we will get an error response if we try and execute an invalid dag:

```
$ http POST localhost:31901/api/experimental/dags/test123/dag_runs X-Auth-Token:10
HTTP/1.1 400 Bad Request
content-length: 67
content-type: application/json
x-shipyard-req: ad978d6c-eb5b-4392-a8cb-461dd42a9b00

{
    "message": "Fail to Execute Dag",
    "retry": false,
    "type": "error"
}

```

