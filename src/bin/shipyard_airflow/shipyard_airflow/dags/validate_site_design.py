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

from airflow.utils.task_group import TaskGroup

try:
    from airflow.operators import ArmadaValidateDesignOperator
    from airflow.operators import DeckhandValidateSiteDesignOperator
    from airflow.operators import DrydockValidateDesignOperator
    from airflow.operators import PromenadeValidateSiteDesignOperator
    from config_path import config_path
except ImportError:
    from shipyard_airflow.plugins.armada_validate_design import \
        ArmadaValidateDesignOperator
    from shipyard_airflow.plugins.deckhand_validate_site import \
        DeckhandValidateSiteDesignOperator
    from shipyard_airflow.plugins.drydock_validate_design import \
        DrydockValidateDesignOperator
    from shipyard_airflow.plugins.promenade_validate_site_design import \
        PromenadeValidateSiteDesignOperator
    from shipyard_airflow.dags.config_path import config_path

BAREMETAL = 'baremetal'
SOFTWARE = 'software'


def validate_site_design(dag, targets=None):
    """TaskGroup to delegate design verification to the Airship components

    There is no wiring of steps - they all execute in parallel
    """
    with TaskGroup(group_id="validate_site_design",
                   dag=dag) as validate_site_design:

        if targets is None:
            targets = [BAREMETAL, SOFTWARE]

        # Always add Deckhand validations
        deckhand_validate_site_design = DeckhandValidateSiteDesignOperator(
            task_id='deckhand_validate_site_design',
            shipyard_conf=config_path,
            retries=1,
            dag=dag
        )

        if BAREMETAL in targets:
            # Add Drydock and Promenade validations
            drydock_validate_site_design = DrydockValidateDesignOperator(
                task_id='drydock_validate_site_design',
                shipyard_conf=config_path,
                retries=1,
                dag=dag
            )

            promenade_validate_site_design = \
                PromenadeValidateSiteDesignOperator(
                    task_id='promenade_validate_site_design',
                    shipyard_conf=config_path,
                    retries=1,
                    dag=dag
                )

        if SOFTWARE in targets:
            # Add Armada validations
            armada_validate_site_design = ArmadaValidateDesignOperator(
                task_id='armada_validate_site_design',
                shipyard_conf=config_path,
                retries=1,
                dag=dag
            )

        return validate_site_design
