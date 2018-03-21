# Copyright 2018 AT&T Intellectual Property.  All other rights reserved.
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
from functools import wraps

from airflow.exceptions import AirflowException
from kubernetes import client, config


def get_pod_port_ip(*pods, namespace):
    def get_k8s_pod_port_ip(func):
        @wraps(func)
        def k8s_pod_port_ip_get(self, pods_ip_port):
            """This function retrieves Kubernetes Pod Port and IP
               information. It can be used to retrieve information of
               single pod deployment and/or statefulsets. For instance,
               it can be used to retrieve the tiller pod IP and port
               information for usage in the Armada Operator.

            :param pods_ip_port: IP and port information of the pods

            Example::

                from get_k8s_pod_port_ip import get_pod_port_ip

                @get_pod_port_ip('tiller', namespace='kube-system')
                def get_pod_info(self, pods_ip_port={}):

                    tiller_ip = pods_ip_port['tiller']['ip']
                    tiller_port = pods_ip_port['tiller']['port']

            """
            # Initialize variable
            k8s_pods = {}

            # The function allows us to query information on multiple
            # pods
            for pod_name in pods:
                # Initialize variables
                pod_attr = {}
                pod_attr[pod_name] = {}

                # Initialize/Reset counter
                count = 0

                # Make use of kubernetes client to retrieve pod IP
                # and port information
                # Note that we should use 'in_cluster_config'
                # Note that we will only search for pods in the namespace
                # that was specified in the request
                config.load_incluster_config()
                v1 = client.CoreV1Api()
                ret = v1.list_namespaced_pod(namespace=namespace,
                                             watch=False)

                # Loop through items to extract port and IP information
                # of the pod
                for i in ret.items:
                    if pod_name in i.metadata.name:
                        # Get pod IP
                        logging.info("Retrieving %s IP", pod_name)
                        pod_attr[pod_name]['ip'] = i.status.pod_ip
                        logging.info("%s IP is %s", pod_name,
                                     pod_attr[pod_name]['ip'])

                        # Get pod port
                        logging.info("Retrieving %s Port", pod_name)

                        # It is possible for a pod to have an IP with no
                        # port. For instance maas-rack takes on genesis
                        # node IP and has no port associated with it. We
                        # will assign the value 'None' to the port value
                        # in such cases.
                        try:
                            specs_dict = i.spec.containers[0].__dict__
                            ports_dict = specs_dict['_ports'][0].__dict__
                            pod_attr[pod_name]['port'] = (
                                ports_dict['_container_port'])
                            logging.info("%s Port is %s", pod_name,
                                         pod_attr[pod_name]['port'])
                        except:
                            pod_attr[pod_name]['port'] = 'None'
                            logging.warning("%s Port is None", pod_name)

                        # Update k8s_pods with new entry
                        k8s_pods.update(pod_attr)

                        # It is possible for different pods to have the same
                        # partial names. This means that we can end up with
                        # inconsistent results depending on how the pods were
                        # ordered in the results for 'list_namespaced_pod'.
                        # Hence an exception should be raised when the function
                        # returns results for 2 or more pods.
                        if count > 0:
                            raise AirflowException(
                                "Pod search string is not unique!")

                        # Step counter
                        count += 1

                # Raise Execptions if the pod does not exits in the
                # Kubernetes cluster
                if not pod_attr[pod_name]:
                    raise AirflowException("Unable to locate", pod_name)

            return func(self, pods_ip_port=k8s_pods)

        return k8s_pod_port_ip_get
    return get_k8s_pod_port_ip
