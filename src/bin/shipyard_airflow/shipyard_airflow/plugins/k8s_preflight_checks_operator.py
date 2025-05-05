# Copyright 2018 AT&T Intellectual Property.  All other rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging

from airflow.exceptions import AirflowException
from airflow.sdk import BaseOperator
from airflow.plugins_manager import AirflowPlugin
from kubernetes import client, config


class K8sHealthCheckOperator(BaseOperator):
    """
    Performs basic Kubernetes Health Check
    """

    def __init__(self, *args, **kwargs):

        super(K8sHealthCheckOperator, self).__init__(*args, **kwargs)

    def execute(self, context):
        logging.info("Running Basic Kubernetes Cluster Health Check:")

        # Note that we are using 'in_cluster_config'
        config.load_incluster_config()
        v1 = client.CoreV1Api()
        ret = v1.list_pod_for_all_namespaces(watch=False)

        # Loop through items to get the status of all pods
        # Note that the current health check only checks to
        # ensure that all pods are either in 'Succeeded' or
        # in 'Running' state. The k8s health checks can be
        # expanded in future if need be.
        for i in ret.items:
            logging.info("%s is in %s state", i.metadata.name, i.status.phase)

            if i.status.phase not in ['Succeeded', 'Running']:
                # NOTE: Kubelet receives information about the pods
                # and node from etcd after a restart. It seems that
                # it is possible for kubelet to set the pod status to
                # 'MatchNodeSelector' after a hard reboot of the node.
                # This might happen if the labels in the initial node
                # info is different from the node info in etcd, which
                # will in turn cause the pod admission to fail.
                #
                # As the system does recover after a hard reboot with
                # new pods created for various services, there is a need
                # to ignore the failed pods with 'MatchNodeSelector' status
                # to avoid false alarms. Hence the approach that we will
                # be taking in such situation will be to log warning messages
                # printing the current state of these pods as opposed to
                # failing the health checks.
                if (i.status.phase == 'Failed' and
                        i.status.container_statuses is None and
                        i.status.reason == 'MatchNodeSelector'):
                    logging.warning("%s is in %s state with status",
                                    i.metadata.name, i.status.phase)
                    logging.warning(i.status)
                else:
                    raise AirflowException("Kubernetes Health Checks Failed!")


class K8sHealthCheckPlugin(AirflowPlugin):
    name = "k8s_healthcheck_plugin"
    operators = [K8sHealthCheckOperator]
