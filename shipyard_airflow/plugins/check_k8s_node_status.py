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


def check_node_status(time_out, interval):
    """This function retrieves the current state of the nodes in the
       Kubernetes cluster. We can use it to check the state of the
       cluster join process (drydock/promenade) and determine if all
       the bare metal nodes have successfully joined the Kubernetes
       cluster.

       :param time_out: Node should be in Ready state before Time Out
       :param interval: Time interval in which we query node state

        Example::

        import time
        from check_k8s_node_status import check_node_status

        # Wait for a while before checking the cluster-join process as
        # it takes time for process to be triggered across all nodes
        # We will wait for 120 seconds in this example
        time.sleep(120)

        # Calls function to check that all nodes are in Ready State
        # Time out in this case is set to 15 mins, the time interval
        # has been set to 60 seconds
        check_node_status(900, 60)
    """
    # Initialize Variable
    not_ready_node_list = []

    # Note that we are using 'in_cluster_config'
    config.load_incluster_config()
    v1 = client.CoreV1Api()

    # Logs initial state of all nodes in the cluster
    ret_init = v1.list_node(watch=False)

    logging.info("Current state of nodes in Cluster is")

    for i in ret_init.items:
        logging.info("%s\t%s\t%s", i.metadata.name,
                     i.status.conditions[-1].status,
                     i.status.conditions[-1].type)

        # Populates the list of nodes in the Cluster
        not_ready_node_list.append(i.metadata.name)

    # Calculate number of times to execute the 'for' loop
    # Ensure that 'time_out' and 'interval' is passed in as integer
    # The result from the division will be a floating number which
    # We will round off to nearest whole number
    end_range = round(int(time_out) / int(interval))

    for i in range(0, end_range + 1):
        # Reset node_ready to True for each iteration
        cluster_ready = True

        # Get updated snapshot view of Cluster for each iteration
        ret = v1.list_node(watch=False)

        # Check the current state of nodes that are not in Ready state
        # from the previous iteration
        for j in ret.items:
            if j.metadata.name in not_ready_node_list:
                if j.status.conditions[-1].status != 'True':
                    # Set cluster_ready to False
                    cluster_ready = False

                    # Print current state of node
                    logging.info("Node %s is not Ready", j.metadata.name)
                    logging.debug("Current status of %s is %s",
                                  j.metadata.name,
                                  j.status.conditions[-1].message)
                else:
                    # Remove 'Ready' node from list
                    not_ready_node_list.remove(j.metadata.name)

                    logging.info("Node %s is in Ready state", j.metadata.name)

        # Raise Time Out Exception
        if not cluster_ready and i == end_range:
            raise AirflowException("Timed Out! One or more Nodes fail to "
                                   "get into Ready State!")

        # Exit loop if Cluster is in Ready state
        if cluster_ready:
            logging.info("All nodes are in Ready state")
            break
        else:
            # Back off and check again in next iteration
            logging.info("Wait for %d seconds...", int(interval))
            time.sleep(int(interval))
