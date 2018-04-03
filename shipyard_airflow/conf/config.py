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
            cfg.IntOpt(
                'airflow_api_connect_timeout',
                default=5,
                help='Seconds to wait to connect to the airflow api'
            ),
            cfg.IntOpt(
                'airflow_api_read_timeout',
                default=60,
                help='Seconds to wait for a response from the airflow api'
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
            cfg.DictOpt(
                'named_log_levels',
                default={"keystoneauth": logging.INFO},
                help=('The logging levels for named loggers. '
                      'Use standard representations for logging levels: '
                      'ERROR. WARN, INFO, DEBUG. Configuration file format: '
                      'named_log_levels = keystoneauth:INFO,othlgr:WARN'
                      )
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
                    'the service lookup in the Keystone service catalog.'
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
                    'the service lookup in the Keystone service catalog.'
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
                    'the service lookup in the Keystone service catalog.'
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
                    'the service lookup in the Keystone service catalog.'
                )
            ),
        ]
    ),
    ConfigSection(
        name='requests_config',
        title='Requests Configuration',
        options=[
            cfg.IntOpt(
                'airflow_log_connect_timeout',
                default=5,
                help='Airflow logs retrieval connect timeout (in seconds)'
            ),
            cfg.IntOpt(
                'airflow_log_read_timeout',
                default=300,
                help='Airflow logs retrieval timeout (in seconds)'
            ),
            cfg.IntOpt(
                'deckhand_client_connect_timeout',
                default=5,
                help='Deckhand client connect timeout (in seconds)'
            ),
            cfg.IntOpt(
                'deckhand_client_read_timeout',
                default=300,
                help=(
                    'Deckhand client timeout (in seconds) for GET, '
                    'PUT, POST and DELETE request'
                )
            ),
            cfg.IntOpt(
                'validation_connect_timeout',
                default=5,
                help='UCP component validation connect timeout (in seconds)'
            ),
            cfg.IntOpt(
                'validation_read_timeout',
                default=300,
                help='UCP component validation timeout (in seconds)'
            ),
        ]
    ),
    ConfigSection(
        name='airflow',
        title='Airflow connection info',
        options=[
            cfg.StrOpt(
                'worker_endpoint_scheme',
                default='http',
                help='Airflow worker url scheme'
            ),
            cfg.IntOpt(
                'worker_port',
                default=8793,
                help='Airflow worker port'
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
