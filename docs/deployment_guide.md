## Deployment Guide ##

*Note that Shipyard is still under active development and this guide will evolve along the way*

The current deployment makes use of OpenStack-Helm to set up the underlaying Kubernetes
infrastructure and helm charts to deploy the containerized applications.


1) Follow the steps in the OpenStack-Helm All-In-One [guide](http://openstack-helm.readthedocs.io/en/latest/install/all-in-one.html)
   to set up the environment on an Ubuntu 16.04 Virtual Machine.  Follow the steps from the start of the
   wiki till the 'Deploy' section to get the base system up.

   *Note that we do not need to install the OpenStack Helm Charts for Shipyard to function*

   The environment should resemble the following after the executing the required steps in the guide:

   ```
   # kubectl get pods --all-namespaces
   NAMESPACE     NAME                                        READY     STATUS    RESTARTS   AGE
   default       nfs-provisioner-3807301966-b7sh4            1/1       Running   0          22h
   kube-system   calico-etcd-p4fct                           1/1       Running   0          22h
   kube-system   calico-node-35pbq                           2/2       Running   0          22h
   kube-system   calico-policy-controller-1777954159-wvp9h   1/1       Running   0          22h
   kube-system   etcd-labinstance                            1/1       Running   0          22h
   kube-system   kube-apiserver-labinstance                  1/1       Running   0          22h
   kube-system   kube-controller-manager-labinstance         1/1       Running   0          22h
   kube-system   kube-dns-692378583-h9cq2                    3/3       Running   0          22h
   kube-system   kube-proxy-259th                            1/1       Running   0          22h
   kube-system   kube-scheduler-labinstance                  1/1       Running   0          22h
   kube-system   tiller-deploy-1332173772-fplsk              1/1       Running   0          22h
   ```

2) Deploy Airflow Helm Chart

   Note: The airflow chart requires a postgresql instance and rabbitmq to be running


   Create shipyard namespace:

   ```
   kubectl create namespace shipyard
   ```


   Postgresql Helm Chart Installation:

   Clone the [OpenStack-Helm-Addons](https://github.com/att-comdev/openstack-helm-addons.git) repository to
   get the postgresql helm chart.  Bring up the postgresql container using the postgresql helm chart:

   ```
   helm install --name=shipyard-postgresql postgresql/ --namespace=shipyard
   ```

   Note: Postgresql may take a short time to reach the 'Running' state. Verify that postgresql is running:

   ```
   # kubectl get pods -n shipyard
   NAME                         READY     STATUS        RESTARTS   AGE
   postgresql-0                 1/1       Running       0          1m
   ```


   Rabbitmq Helm Chart Installation:

   Go to the openstack-helm directory that was created in Step 1

   Update the values.yaml of the rabbitmq charts to reflect the appropriate username and password for the
   environment, e.g. *airflow / airflow*

   Execute the following commands:

   ```
   helm install --name=shipyard-etcd-rabbitmq etcd/ --namespace=shipyard
   helm install --name=shipyard-rabbitmq rabbitmq/ --namespace=shipyard
   ```

   Note: We need to make sure that the etcd chart is executed before the rabbitmq chart due to dependencies

   ```
   # kubectl get pods -n shipyard
   NAME                       READY     STATUS    RESTARTS   AGE
   etcd-2810752095-054xb      1/1       Running   0          2m
   postgresql-0               1/1       Running   0          3m
   rabbitmq-646028817-0bwgp   1/1       Running   0          1m
   rabbitmq-646028817-3hb1z   1/1       Running   0          1m
   rabbitmq-646028817-sq6cw   1/1       Running   0          1m
   ```


   Airflow Helm Chart Installation:

   Create the following directories on the target host machine:
   ```
   $ mkdir -p /home/ubuntu/workbench/dags
   $ mkdir -p /home/ubuntu/workbench/plugins
   $ mkdir -p /home/ubuntu/workbench/logs
   ```

   Copy the [rest_api_plugin](https://github.com/att-comdev/shipyard/blob/master/shipyard_airflow/plugins/rest_api_plugin.py)
   into the newly created plugins directory, i.e. `/home/ubuntu/workbench/plugins` so that it can be loaded by Airflow during
   startup.  Note that other custom operators can also be added to the directory as required.

   Note: Custom dags should be added into the newly created dags directory, i.e. `/home/ubuntu/workbench/dags`

   Next, proceed to clone the [AIC-Helm](https://github.com/att-comdev/aic-helm.git) repository to get the Airflow Helm Charts.
   The charts can be found under the airflow directory.

   ```
   helm install --name=airflow airflow/ --namespace=shipyard
   ```

   Verify that the airflow helm charts were successful deployed:

   ```
   # kubectl get pods -n shipyard
   NAME                         READY     STATUS    RESTARTS   AGE
   etcd-2810752095-054xb        1/1       Running   0          1h
   flower-57424757-xqzls        1/1       Running   0          1m
   postgresql-0                 1/1       Running   0          1h
   rabbitmq-646028817-0bwgp     1/1       Running   0          1h
   rabbitmq-646028817-3hb1z     1/1       Running   0          1h
   rabbitmq-646028817-sq6cw     1/1       Running   0          1h
   scheduler-1793121224-z57t9   1/1       Running   0          1m
   web-1556478053-t06t9         1/1       Running   0          1m
   worker-3775326852-0747g      1/1       Running   0          1m

   ```


   To check that all resources are working as intended:

   ```
   $ kubectl get all --namespace=shipyard
   NAME                            READY     STATUS    RESTARTS   AGE
   po/etcd-2810752095-054xb        1/1       Running   0          1h
   po/flower-57424757-xqzls        1/1       Running   0          1m
   po/postgresql-0                 1/1       Running   0          1h
   po/rabbitmq-646028817-0bwgp     1/1       Running   0          1h
   po/rabbitmq-646028817-3hb1z     1/1       Running   0          1h
   po/rabbitmq-646028817-sq6cw     1/1       Running   0          1h
   po/scheduler-1793121224-z57t9   1/1       Running   0          1m
   po/web-1556478053-t06t9         1/1       Running   0          1m
   po/worker-3775326852-0747g      1/1       Running   0          1m

   NAME             CLUSTER-IP       EXTERNAL-IP   PORT(S)          AGE
   svc/etcd         10.102.166.90    <none>        2379/TCP         1h
   svc/flower       10.105.87.167    <nodes>       5555:32081/TCP   1m
   svc/postgresql   10.96.110.4      <none>        5432/TCP         1h
   svc/rabbitmq     10.100.94.226    <none>        5672/TCP         1h
   svc/web          10.103.245.128   <nodes>       8080:32080/TCP   1m

   NAME                      DESIRED   CURRENT   AGE
   statefulsets/postgresql   1         1         1h

   NAME                              DESIRED   SUCCESSFUL   AGE
   jobs/airflow-db-init-postgresql   1         1            1m
   jobs/airflow-db-sync              1         1            1m

   NAME               DESIRED   CURRENT   UP-TO-DATE   AVAILABLE   AGE
   deploy/etcd        1         1         1            1           1h
   deploy/flower      1         1         1            1           1m
   deploy/rabbitmq    3         3         3            3           1h
   deploy/scheduler   1         1         1            1           1m
   deploy/web         1         1         1            1           1m
   deploy/worker      1         1         1            1           1m

   NAME                      DESIRED   CURRENT   READY     AGE
   rs/etcd-2810752095        1         1         1         1h
   rs/flower-57424757        1         1         1         1m
   rs/rabbitmq-646028817     3         3         3         1h
   rs/scheduler-1793121224   1         1         1         1m
   rs/web-1556478053         1         1         1         1m
   rs/worker-3775326852      1         1         1         1m

   ```


3) Deploy Shipyard Helm Chart

   The Shipyard helm chart can be retrieved by performing the the following step:

   ```
   $ git clone http://review.gerrithub.io/att-comdev/aic-helm
   ```

   Shipyard Helm Chart Installation:

   ```
   $ helm install --name=shipyard shipyard/ --namespace=shipyard
   ```

   Check that all the helm charts have been properly deployed and that all services are up and running:

   ```
   # kubectl get pods -n shipyard
   NAME                         READY     STATUS    RESTARTS   AGE
   etcd-2810752095-7xbj2        1/1       Running   0          14m
   flower-3408049844-ntpt3      1/1       Running   0          6m
   postgresql-0                 1/1       Running   0          17m
   rabbitmq-4130740871-716vm    1/1       Running   0          13m
   rabbitmq-4130740871-dlxjk    1/1       Running   0          13m
   rabbitmq-4130740871-rj0pd    1/1       Running   0          13m
   scheduler-2853377807-jghld   1/1       Running   0          6m
   shipyard-1823745968-t794w    1/1       Running   0          2m
   web-3069981571-9tjt9         1/1       Running   0          6m
   worker-2534280303-fcb49      1/1       Running   0          6m


   # kubectl get service -n shipyard
   NAME           CLUSTER-IP       EXTERNAL-IP   PORT(S)          AGE
   etcd           10.97.149.59     <none>        2379/TCP         13m
   flower         10.108.197.84    <nodes>       5555:32081/TCP   5m
   postgresql     10.108.17.95     <none>        5432/TCP         17m
   rabbitmq       10.98.1.115      <none>        5672/TCP         12m
   shipyard-api   10.108.189.157   <nodes>       9000:31901/TCP   1m
   web            10.97.88.69      <nodes>       8080:32080/TCP   5m

   ```

