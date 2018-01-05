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
#
""" Module providing the oslo_config based configuration for Shipyard
"""
import logging

import keystoneauth1.loading as ks_loading
from oslo_config import cfg

from shipyard_airflow.conf.opts import ConfigSection

CONF = cfg.CONF
SECTIONS = [
    ConfigSection(
        name='base',
        title='Base Configuration',
        options=[
            cfg.StrOpt(
                'web_server',
                default='http://localhost:32080/',
                help='The web server for Airflow'
            ),
            cfg.StrOpt(
                'postgresql_db',
                default=(
                    'postgresql+psycopg2://shipyard:changeme'
                    '@postgresql.ucp:5432/shipyard'
                ),
                help='The database for shipyard'
            ),
            cfg.StrOpt(
                'postgresql_airflow_db',
                default=(
                    'postgresql+psycopg2://shipyard:changeme'
                    '@postgresql.ucp:5432/airflow'
                ),
                help='The database for airflow'
            ),
            cfg.StrOpt(
                'alembic_ini_path',
                default='/home/shipyard/shipyard',
                help='The direcotry containing the alembic.ini file'
            ),
            cfg.BoolOpt(
                'upgrade_db',
                default=True,
                help='Upgrade the database on startup'
            )
        ]
    ),
    ConfigSection(
        name='logging',
        title='Logging Options',
        options=[
            cfg.IntOpt(
                'log_level',
                default=logging.DEBUG,
                help=('The default logging level for the root logger. '
                      'ERROR=40, WARNING=30, INFO=20, DEBUG=10')
            ),
        ]
    ),
    ConfigSection(
        name='shipyard',
        title='Shipyard connection info',
        options=[
            cfg.StrOpt(
                'service_type',
                default='shipyard',
                help=(
                    'The service type for the service playing the role '
                    'of Shipyard. The specified type is used to perform '
                    'the service lookup in the Keystone service catalog. '
                )
            ),
        ]
    ),
    ConfigSection(
        name='deckhand',
        title='Deckhand connection info',
        options=[
            cfg.StrOpt(
                'service_type',
                default='deckhand',
                help=(
                    'The service type for the service playing the role '
                    'of Deckhand. The specified type is used to perform '
                    'the service lookup in the Keystone service catalog. '
                )
            ),
        ]
    ),
    ConfigSection(
        name='armada',
        title='Armada connection info',
        options=[
            cfg.StrOpt(
                'service_type',
                default='armada',
                help=(
                    'The service type for the service playing the role '
                    'of Armada. The specified type is used to perform '
                    'the service lookup in the Keystone service catalog. '
                )
            ),
        ]
    ),
    ConfigSection(
        name='drydock',
        title='Drydock connection info',
        options=[
            cfg.StrOpt(
                'service_type',
                default='physicalprovisioner',
                help=(
                    'The service type for the service playing the role '
                    'of Drydock. The specified type is used to perform '
                    'the service lookup in the Keystone service catalog. '
                )
            ),
            cfg.IntOpt(
                'verify_site_query_interval',
                default=10,
                help='Query interval (in seconds) for verify_site task'
            ),
            cfg.IntOpt(
                'verify_site_task_timeout',
                default=60,
                help='Time out (in seconds) for verify_site task'
            ),
            cfg.IntOpt(
                'prepare_site_query_interval',
                default=10,
                help='Query interval (in seconds) for prepare_site task'
            ),
            cfg.IntOpt(
                'prepare_site_task_timeout',
                default=300,
                help='Time out (in seconds) for prepare_site task'
            ),
            cfg.IntOpt(
                'prepare_node_query_interval',
                default=30,
                help='Query interval (in seconds) for prepare_node task'
            ),
            cfg.IntOpt(
                'prepare_node_task_timeout',
                default=1800,
                help='Time out (in seconds) for prepare_node task'
            ),
            cfg.IntOpt(
                'deploy_node_query_interval',
                default=30,
                help='Query interval (in seconds) for deploy_node task'
            ),
            cfg.IntOpt(
                'deploy_node_task_timeout',
                default=3600,
                help='Time out (in seconds) for deploy_node task'
            ),
            cfg.IntOpt(
                'cluster_join_check_backoff_time',
                default=120,
                help='Backoff time (in seconds) before checking cluster join'
            ),
        ]
    ),
]


def register_opts(conf):
    """ Registers all the sections in this module.
    """
    for section in SECTIONS:
        conf.register_group(
            cfg.OptGroup(name=section.name,
                         title=section.title,
                         help=section.help))
        conf.register_opts(section.options, group=section.name)

    conf.register_opts(
        ks_loading.get_auth_plugin_conf_options('password'),
        group='keystone_authtoken'
    )


def list_opts():
    """ List the options identified by this configuration
    """
    return {
        section.name: section.options for section in SECTIONS
    }


def parse_args(args=None, usage=None, default_config_files=None):
    """ Triggers the parsing of the arguments/configs
    """
    CONF(args=args,
         project='shipyard',
         usage=usage,
         default_config_files=default_config_files)


register_opts(CONF)
