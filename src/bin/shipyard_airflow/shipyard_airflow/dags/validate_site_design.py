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

from airflow.models import DAG

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


def validate_site_design(parent_dag_name, child_dag_name, args, targets=None):
    """Subdag to delegate design verification to the UCP components

    There is no wiring of steps - they all execute in parallel
    """
    dag = DAG(
        '{}.{}'.format(parent_dag_name, child_dag_name),
        default_args=args)

    if targets is None:
        targets = [BAREMETAL, SOFTWARE]

    # Always add Deckhand validations
    DeckhandValidateSiteDesignOperator(
        task_id='deckhand_validate_site_design',
        shipyard_conf=config_path,
        main_dag_name=parent_dag_name,
        retries=1,
        dag=dag
    )

    if BAREMETAL in targets:
        # Add Drydock and Promenade validations
        DrydockValidateDesignOperator(
            task_id='drydock_validate_site_design',
            shipyard_conf=config_path,
            main_dag_name=parent_dag_name,
            retries=1,
            dag=dag
        )

        PromenadeValidateSiteDesignOperator(
            task_id='promenade_validate_site_design',
            shipyard_conf=config_path,
            main_dag_name=parent_dag_name,
            retries=1,
            dag=dag
        )

    if SOFTWARE in targets:
        # Add Armada validations
        ArmadaValidateDesignOperator(
            task_id='armada_validate_site_design',
            shipyard_conf=config_path,
            main_dag_name=parent_dag_name,
            retries=1,
            dag=dag
        )

    return dag
