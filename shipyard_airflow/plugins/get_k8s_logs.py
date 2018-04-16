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

from kubernetes import client, config
from kubernetes.client.rest import ApiException

LOG = logging.getLogger(__name__)
_NOT_FOUND_MSG_FMT = ("No matching pods found for namespace: {}"
                      " pod: {} container: {}")


class K8sLoggingException(Exception):
    """ We do not really want the workflow to terminate due to logs
        retrieval issues and hence we will have another Exception
        handling class to handle this."""
    pass


def get_pod_logs(pod_name_pattern, namespace, container, since_seconds):
    """This function retrieves the logs of the kubernetes pod

       :param pod_name_pattern: Pattern of Pods name, e.g. 'drydock-api' if
                                we want to check the logs of the Drydock API
                                pods. Note that we are parsing pattern as
                                there are usually multiple pods present (for
                                redundancy purposes) and we will want to show
                                the logs of all the relevant pods.
       :param namespace: Namespace where Pods reside
       :param container: The container for which to stream logs. Defaults
                         to only container if there is one container in
                         the pod.
       :param since_seconds: A relative time in seconds before the current
                             time from which to show logs. If this value
                             precedes the time a pod was started, only logs
                             since the pod start will be returned. If this
                             value is in the future, no logs will be returned.

        Example::

            from get_k8s_logs import get_pod_logs

            # Calls function to retrieve logs
            get_pod_logs('airflow-worker', 'ucp', 'airflow-worker', 3600)
    """
    # Note that we are using 'in_cluster_config'
    config.load_incluster_config()
    v1 = client.CoreV1Api()

    # Initialize variable
    pods_list = []

    # Retrieve names of pods
    try:
        ret = v1.list_namespaced_pod(namespace=namespace,
                                     watch=False)

    except ApiException as e:
        LOG.error(e)
        msg = ("Caught %s while trying to retrieve namespaced pods from K8s"
               " API. Details: %s" % (e.__class__.__name__, e))
        raise K8sLoggingException(msg)

    if ret:
        for i in ret.items:
            if pod_name_pattern in i.metadata.name:
                pods_list.append(i.metadata.name)
    else:
        raise K8sLoggingException(_NOT_FOUND_MSG_FMT.format(namespace,
                                                            pod_name_pattern,
                                                            container))

    if pods_list:
        LOG.info("The following Pods matched the requested pattern %s: %s",
                 pod_name_pattern, ", ".join(pods_list))
    else:
        raise K8sLoggingException(_NOT_FOUND_MSG_FMT.format(namespace,
                                                            pod_name_pattern,
                                                            container))

    # Retrieve logs from pod
    for pod in pods_list:
        try:
            # Note that the kwarg 'pretty' takes on string value and will
            # ensure that the output is pretty printed if set 'true'.
            pod_logs = v1.read_namespaced_pod_log(name=pod,
                                                  namespace=namespace,
                                                  container=container,
                                                  pretty='true',
                                                  since_seconds=since_seconds)

        except ApiException as e:
            LOG.error(e)
            msg = ("Caught %s while trying to read logs from namespaced pod=%s"
                   ", namespace=%s, container=%s using the k8s API. Details: "
                   "%s" % (e.__class__.__name__, pod, namespace, container, e))
            raise K8sLoggingException(msg)

        LOG.info("\n\n================= Logs for container %s of pods %s in"
                 " namespace %s =================\n\n",
                 container, pod, namespace)

        LOG.info(pod_logs)

        LOG.info("\n\n================= End Logs for %s =================\n\n",
                 pod)
