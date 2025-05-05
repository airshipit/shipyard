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

from airflow.exceptions import AirflowException
from airflow.plugins_manager import AirflowPlugin

try:
    from armada_base_operator import ArmadaBaseOperator
except ImportError:
    from shipyard_airflow.plugins.armada_base_operator import \
        ArmadaBaseOperator
from armada.exceptions import api_exceptions as errors

LOG = logging.getLogger(__name__)


class ArmadaPostApplyOperator(ArmadaBaseOperator):
    """Armada Post Apply Operator

    This operator will trigger armada to apply the manifest and
    start a site deployment/update/upgrade.

    """

    def do_execute(self, context):

        # Initialize Variables
        armada_manifest = None
        chart_set = []
        override_values = []
        upgrade_airflow_worker = False

        # Set up target manifest
        self.dc = self.xcom_puller.get_deployment_configuration()
        self.target_manifest = self.dc['armada.manifest']
        if self.action_info['name'] == 'update_software':
            self.target_manifest = self.dc['armada.update_manifest']

        # Update query dict with information of target_manifest
        self.query['target_manifest'] = self.target_manifest

        # Retrieve read timeout
        timeout = self.dc['armada.post_apply_timeout']

        # Execute Armada Apply to install the helm charts in sequence
        LOG.info("Armada Apply, target manifest: %s", self.target_manifest)

        try:
            armada_post_apply = self.armada_client.post_apply(
                manifest=armada_manifest,
                manifest_ref=self.design_ref,
                values=override_values,
                set=chart_set,
                query=self.query,
                timeout=timeout)

        except errors.ClientError as client_error:
            raise AirflowException(client_error)

        # if this is a retry, assume that the airflow worker needs to be
        # updated at the end of the workflow.
        # TODO(bryan-strassner) need to persist the decision to restart the
        #     airflow worker outside of the xcom structure. This is a work-
        #     around that will restart the worker more often than it
        #     needs to. Problem with xcom is that it is cleared for the task
        #     on retry, which means we can't use it as a flag reliably.
        if self.task_instance.try_number > 1:
            LOG.info(
                "Airflow Worker will be upgraded because retry may obfuscate "
                "an upgrade of shipyard/airflow.")
            upgrade_airflow_worker = True
        else:
            # Search for Shipyard deployment in the list of chart upgrades
            # NOTE: It is possible for the chart name to take on different
            # values, e.g. 'aic-ucp-shipyard', 'ucp-shipyard'. Hence we
            # will search for the word 'shipyard', which should exist as
            # part of the name of the Shipyard Helm Chart.
            for i in armada_post_apply['message']['upgrade']:
                if 'shipyard' in i:
                    LOG.info("Shipyard was upgraded. Airflow worker must be "
                             "restarted to reflect any workflow changes.")
                    upgrade_airflow_worker = True
                    break

        # Create xcom key 'upgrade_airflow_worker'
        # Value of key will depend on whether an upgrade has been
        # performed on the Shipyard/Airflow Chart
        if upgrade_airflow_worker:
            self.xcom_pusher.xcom_push(key='upgrade_airflow_worker',
                                       value='true')
        else:
            self.xcom_pusher.xcom_push(key='upgrade_airflow_worker',
                                       value='false')

        # We will expect Armada to return the releases that it is
        # deploying. Note that if we try and deploy the same release
        # twice, we will end up with empty response as nothing has
        # changed.
        if (armada_post_apply['message']['install'] or
                armada_post_apply['message']['upgrade']):
            LOG.info("Successfully Executed Armada Apply")
            LOG.info(armada_post_apply)
        else:
            LOG.warning("No new changes/updates were detected!")
            LOG.info(armada_post_apply)


class ArmadaPostApplyOperatorPlugin(AirflowPlugin):
    """Creates ArmadaPostApplyOperator in Airflow."""

    name = 'armada_post_apply_operator'
    operators = [ArmadaPostApplyOperator]
