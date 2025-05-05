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

from kubernetes import client
from kubernetes import config


def check_node_status(time_out, interval, expected_nodes):
    """This function retrieves the current state of the nodes in the
       Kubernetes cluster. We can use it to check the state of the
       cluster join process (drydock/promenade) and determine if all
       the bare metal nodes have successfully joined the Kubernetes
       cluster.

       :param time_out: Node should be in Ready state before Time Out
       :param interval: Time interval in which we query node state
       :param expected_nodes: The list of nodes that are expected to be
           present in the check for status

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

        # The expected nodes are the nodes to be compared against,
        # as there could be nodes that never show up as ready, and those
        # need to be represented in the response
        check_node_status(900, 60, expected_nodes=['a','b','c'])
    """
    # Initialize Variables - the nodes we are watching for
    if not expected_nodes:
        # if you're not looking for any, don't expect me to look either
        return []

    not_ready_node_list = list(expected_nodes)

    # Calculate number of times to execute the 'for' loop
    # Ensure that 'time_out' and 'interval' is passed in as integer
    # The result from the division will be a floating number which
    # We will round off to nearest whole number

    # no div/0 or negative intervals
    if interval < 1:
        interval = 1
    if time_out < 1:
        time_out = 1

    end_range = round(int(time_out) / int(interval))
    # end_range + 1 since the first check doesn't have a sleep ahead of it
    for i in range(0, end_range + 1):
        logging.info("Remaining expected nodes to join cluster: [%s]",
                     ", ".join(not_ready_node_list))
        # Get updated snapshot view of Cluster for each iteration
        ret = _get_all_k8s_node_status()

        # cautiously prevent crashing out of this code to ensure continued
        # processing.
        if ret is not None and hasattr(ret, 'items'):
            # Check the state of nodes against the remaining expceted nodes
            for j in ret.items:
                # resolve response item fields without letting them break
                # the processing loop.
                try:
                    node_name = j.metadata.name
                    summary_status = j.status.conditions[-1].status
                    summary_message = j.status.conditions[-1].message
                except (AttributeError, IndexError):
                    # any issue with the response object, move on to next item
                    logging.warning(
                        "Malformed node status response object. "
                        "Processing continues with the next item",
                        exc_info=True)
                    continue

                # only check nodes that we're currently waiting for
                if node_name in not_ready_node_list:
                    if summary_status != 'True':
                        # Node not ready, print current state of node
                        logging.info("Node %s is not ready. Status is: %s",
                                     node_name, summary_message)
                    else:
                        # Remove this node from list, it is ready
                        not_ready_node_list.remove(node_name)
                        logging.info("Node %s is in ready state", node_name)

        # determine what to do based on the not_ready_node_list
        if not_ready_node_list and i == end_range:
            # There are remining items, and the timeout is elapsed
            logging.info("Timed Out! Nodes [%s] did not reach ready state",
                         ", ".join(not_ready_node_list))
            break
        elif not not_ready_node_list:
            # Exit loop where there are no more nodes to wait for (all ready)
            logging.info("All expected nodes are in ready state")
            break
        else:
            # There are nodes remaining, and time remining
            # Back off and check again in next iteration
            logging.info("Waiting %d seconds for next check of cluster status",
                         int(interval))
            time.sleep(int(interval))

    # Return the nodes that are not ready.
    return not_ready_node_list


def _get_all_k8s_node_status():
    """Invoke Kubernetes and return the status response object"""
    # Note that we are using 'in_cluster_config'
    try:
        config.load_incluster_config()
        v1 = client.CoreV1Api()
        return v1.list_node(watch=False)
    except Exception:
        # Log some diagnostics and return None.
        logging.warning("There was an error retrieving the cluster status",
                        exc_info=True)
