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
            cfg.StrOpt('web_server',
                       default='http://localhost:8080/',
                       help='The web server for Airflow'),
            cfg.IntOpt('airflow_api_connect_timeout',
                       default=5,
                       help='Seconds to wait to connect to the airflow api'),
            cfg.IntOpt(
                'airflow_api_read_timeout',
                default=60,
                help='Seconds to wait for a response from the airflow api'),
            cfg.StrOpt('postgresql_db',
                       default=('postgresql+psycopg2://shipyard:changeme'
                                '@postgresql.ucp:5432/shipyard'),
                       help='The database for shipyard'),
            cfg.StrOpt('postgresql_airflow_db',
                       default=('postgresql+psycopg2://shipyard:changeme'
                                '@postgresql.ucp:5432/airflow'),
                       help='The database for airflow'),
            cfg.IntOpt('pool_size',
                       default=15,
                       help='The SQLalchemy database connection pool size.'),
            cfg.BoolOpt(
                'pool_pre_ping',
                default=True,
                help='Should DB connections be validated prior to use.'),
            cfg.IntOpt(
                'pool_timeout',
                default=30,
                help=('How long a request for a connection should wait before '
                      'one becomes available.')),
            cfg.IntOpt(
                'pool_overflow',
                default=10,
                help=('How many connections above pool_size are allowed to be '
                      'open during high usage.')),
            cfg.IntOpt(
                'connection_recycle',
                default=-1,
                help=('Time, in seconds, when a connection should be closed '
                      'and re-established. -1 for no recycling.')),
            cfg.StrOpt('alembic_ini_path',
                       default='/home/shipyard/shipyard',
                       help='The directory containing the alembic.ini file'),
            cfg.BoolOpt('profiler',
                        default=False,
                        help=('Enable profiling of API requests. Do NOT '
                              'use in production.')),
        ]),
    ConfigSection(
        name='logging',
        title='Logging Options',
        options=[
            cfg.IntOpt('log_level',
                       default=logging.DEBUG,
                       help=('The default logging level for the root logger. '
                             'ERROR=40, WARNING=30, INFO=20, DEBUG=10')),
            cfg.DictOpt(
                'named_log_levels',
                default={
                    "keystoneauth": logging.INFO,
                    "keystonemiddleware": logging.INFO
                },
                help=('The logging levels for named loggers. '
                      'Use standard representations for logging levels: '
                      'ERROR. WARN, INFO, DEBUG. Configuration file format: '
                      'named_log_levels = keystoneauth:INFO,othlgr:WARN')),
        ]),
    ConfigSection(
        name='shipyard',
        title='Shipyard Connection Info',
        options=[
            cfg.StrOpt(
                'service_type',
                default='shipyard',
                help=('The service type for the service playing the role '
                      'of Shipyard. The specified type is used to perform '
                      'the service lookup in the Keystone service catalog.')),
        ]),
    ConfigSection(
        name='deckhand',
        title='Deckhand Connection Info',
        options=[
            cfg.StrOpt(
                'service_type',
                default='deckhand',
                help=('The service type for the service playing the role '
                      'of Deckhand. The specified type is used to perform '
                      'the service lookup in the Keystone service catalog.')),
        ]),
    ConfigSection(
        name='armada',
        title='Armada Connection Info',
        options=[
            cfg.StrOpt(
                'service_type',
                default='armada',
                help=('The service type for the service playing the role '
                      'of Armada. The specified type is used to perform '
                      'the service lookup in the Keystone service catalog.')),
        ]),
    ConfigSection(
        name='drydock',
        title='Drydock Connection Info',
        options=[
            cfg.StrOpt(
                'service_type',
                default='physicalprovisioner',
                help=('The service type for the service playing the role '
                      'of Drydock. The specified type is used to perform '
                      'the service lookup in the Keystone service catalog.')),
        ]),
    ConfigSection(
        name='promenade',
        title='Promenade Connection Info',
        options=[
            cfg.StrOpt(
                'service_type',
                default='kubernetesprovisioner',
                help=('The service type for the service playing the role '
                      'of Promenade. The specified type is used to perform '
                      'the service lookup in the Keystone service catalog.')),
        ]),
    ConfigSection(
        name='requests_config',
        title='Requests Configuration',
        options=[
            cfg.IntOpt(
                'airflow_log_connect_timeout',
                default=5,
                help='Airflow logs retrieval connect timeout (in seconds)'),
            cfg.IntOpt('airflow_log_read_timeout',
                       default=300,
                       help='Airflow logs retrieval timeout (in seconds)'),
            cfg.IntOpt('validation_connect_timeout',
                       default=5,
                       help=('Airship component validation connect timeout '
                             '(in seconds)')),
            cfg.IntOpt(
                'validation_read_timeout',
                default=300,
                help='Airship component validation timeout (in seconds)'),
            cfg.IntOpt(
                'notes_connect_timeout',
                default=5,
                help=('Maximum time to wait to connect to a note source URL '
                      '(in seconds)')),
            cfg.IntOpt('notes_read_timeout',
                       default=10,
                       help='Read timeout for a note source URL (in seconds)'),
            cfg.IntOpt('deckhand_client_connect_timeout',
                       default=5,
                       help='Deckhand client connect timeout (in seconds)'),
            cfg.IntOpt('deckhand_client_read_timeout',
                       default=300,
                       help=('Deckhand client timeout (in seconds) for GET, '
                             'PUT, POST and DELETE request')),
            cfg.IntOpt(
                'drydock_client_connect_timeout',
                default=20,
                help=('Connect timeout used for connecting to Drydock using '
                      'the Drydock client (in seconds)')),
            cfg.IntOpt(
                'drydock_client_read_timeout',
                default=300,
                help=('Read timeout used for responses from Drydock using '
                      'the Drydock client (in seconds)')),
        ]),
    ConfigSection(name='airflow',
                  title='Airflow connection info',
                  options=[
                      cfg.StrOpt('worker_endpoint_scheme',
                                 default='http',
                                 help='Airflow worker url scheme'),
                      cfg.IntOpt('worker_port',
                                 default=8793,
                                 help='Airflow worker port'),
                      cfg.StrOpt('worker_log_jwt_secret',
                                 default='changeme',
                                 help='Secret key for signing JWT tokens '
                                 'for Airflow worker logs'),
                  ]),
    ConfigSection(name='k8s_logs',
                  title='Parameters for K8s Pods Logs',
                  options=[
                      cfg.StrOpt('ucp_namespace',
                                 default='ucp',
                                 help='Namespace of Airship Pods'),
                  ]),
    ConfigSection(
        name='deployment_status_configmap',
        title='Parameters for Deployment Status ConfigMap',
        options=[
            cfg.StrOpt('name',
                       default='deployment-status',
                       help='Name of the Deployment Status ConfigMap'),
            cfg.StrOpt('namespace',
                       default='ucp',
                       help='Namespace of the Deployment Status ConfigMap'),
        ]),
    ConfigSection(
        name='document_info',
        title=('Information about some of the documents Shipyard needs to '
               'handle'),
        options=[
            cfg.StrOpt(
                'deployment_version_name',
                default='deployment-version',
                help=('The name of the deployment version document that '
                      'Shipyard validates')),
            cfg.StrOpt(
                'deployment_version_schema',
                default='pegleg/DeploymentData/v1',
                help=('The schema of the deployment version document that '
                      'Shipyard validates')),
            cfg.StrOpt(
                'deployment_configuration_name',
                default='deployment-configuration',
                help=('The name of the deployment-configuration document that '
                      'Shipyard expects and validates')),
            cfg.StrOpt(
                'deployment_configuration_schema',
                default='shipyard/DeploymentConfiguration/v1',
                help=('The schema of the deployment-configuration document '
                      'that Shipyard expects and validates')),
            cfg.StrOpt(
                'deployment_strategy_schema',
                default='shipyard/DeploymentStrategy/v1',
                help=('The schema of the deployment strategy document that '
                      'Shipyard expects and validates. Note that the name of '
                      'this document is not configurable, because it is '
                      'controlled by a field in the deployment configuration '
                      'document.')),
        ]),
    ConfigSection(
        name='validations',
        title='Validation Configurations',
        options=[
            cfg.StrOpt('deployment_version_create',
                       default='Skip',
                       help=('Control the severity of the deployment-version '
                             'validation during create configdocs.'),
                       ignore_case=True,
                       choices=[('Skip', 'Skip the validation altogether'),
                                ('Info', 'Print an Info level message if the '
                                 'validation fails'),
                                ('Warning',
                                 'Print a Warning level message if the '
                                 'validation fails'),
                                ('Error',
                                 'Return an error when the validation fails '
                                 'and prevent the configdocs create from '
                                 'proceeding')]),
            cfg.StrOpt(
                'deployment_version_commit',
                default='Skip',
                help=('Control the severity of the deployment-version '
                      'validation validation during commit configdocs.'),
                ignore_case=True,
                choices=[('Skip', 'Skip the validation altogether'),
                         ('Info', 'Print an Info level message if the '
                          'validation fails'),
                         ('Warning', 'Print a Warning level message if the '
                          'validation fails'),
                         ('Error', 'Return an error when the validation fails '
                          'and prevent the commit from proceeding')]),
        ]),
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

    ks_loading.register_auth_conf_options(conf, group='keystone_authtoken')


def list_opts():
    """ List the options identified by this configuration
    """
    all_opts = {section.name: section.options for section in SECTIONS}
    all_opts['keystone_authtoken'] = ks_loading.get_session_conf_options()
    return all_opts


def parse_args(args=None, usage=None, default_config_files=None):
    """ Triggers the parsing of the arguments/configs
    """
    CONF(args=args,
         project='shipyard',
         usage=usage,
         default_config_files=default_config_files)


register_opts(CONF)
