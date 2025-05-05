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

import logging
import time

from airflow.exceptions import AirflowException
from kubernetes import client, config


def check_pods_status(required_pods):
    """This function retrieves the current state of pods in the
       Kubernetes cluster. We can use it to check that all the pods
       that are of interest to us are up in the cluster. Function
       returns boolean True/False and queries every 30 seconds.

       :param required_pods: List of pods that are of interest to us

        Example::

        from check_k8s_pod_status import check_pods_status

        pods_ready = False
        required_pods = ['ceph-', 'calico-', 'coredns-', 'kubernetes-']

        # Time out can be set as required
        while not pods_ready:
            pods_ready = check_pods_status(required_pods)
    """
    # Note that we are using 'in_cluster_config'
    config.load_incluster_config()
    v1 = client.CoreV1Api()
    ret = v1.list_pod_for_all_namespaces(watch=False)

    # Loop through items to get the status of the pod
    for i in ret.items:
        for pod_name in required_pods:
            if pod_name in i.metadata.name:

                # Return Boolean 'False' if required pods are not in
                # 'Succeeded' or 'Running' state
                if i.status.phase not in ['Succeeded', 'Running']:
                    logging.info("Pods are not in ready state...")
                    logging.info("%s is in %s state", i.metadata.name,
                                 i.status.phase)
                    logging.info("Wait for 30 seconds...")

                    # Back off for 30 seconds
                    time.sleep(30)

                    return False

            # Raise Execptions if the pod does not exits in the
            # Kubernetes cluster
            else:
                raise AirflowException("Unable to locate pod(s) ", pod_name)

    # Return True when all required pods are in 'Succeeded' or
    # 'Running' state
    return True
