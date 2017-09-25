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
                default='http://localhost:32080',
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
                'host',
                default='shipyard-int.ucp',
                help='FQDN for the shipyard service'
            ),
            cfg.IntOpt(
                'port',
                default=9000,
                help='Port for the shipyard service'
            ),
        ]
    ),
    ConfigSection(
        name='deckhand',
        title='Deckhand connection info',
        options=[
            cfg.StrOpt(
                'host',
                default='deckhand-int.ucp',
                help='FQDN for the deckhand service'
            ),
            cfg.IntOpt(
                'port',
                default=80,
                help='Port for the deckhand service'
            ),
        ]
    ),
    ConfigSection(
        name='armada',
        title='Armada connection info',
        options=[
            cfg.StrOpt(
                'host',
                default='armada-int.ucp',
                help='FQDN for the armada service'
            ),
            cfg.IntOpt(
                'port',
                default=8000,
                help='Port for the armada service'
            ),
        ]
    ),
    ConfigSection(
        name='drydock',
        title='Drydock connection info',
        options=[
            cfg.StrOpt(
                'host',
                default='drydock-int.ucp',
                help='FQDN for the drydock service'
            ),
            cfg.IntOpt(
                'port',
                default=9000,
                help='Port for the drydock service'
            ),
            # TODO(Bryan Strassner) Remove this when integrated
            cfg.StrOpt(
                'token',
                default='bigboss',
                help='TEMPORARY: password for drydock'
            ),
            # TODO(Bryan Strassner) Remove this when integrated
            cfg.StrOpt(
                'site_yaml',
                default='/usr/local/airflow/plugins/drydock.yaml',
                help='TEMPORARY: location of drydock yaml file'
            ),
            # TODO(Bryan Strassner) Remove this when integrated
            cfg.StrOpt(
                'prom_yaml',
                default='/usr/local/airflow/plugins/promenade.yaml',
                help='TEMPORARY: location of promenade yaml file'
            ),
        ]
    ),
    ConfigSection(
        name='healthcheck',
        title='Healthcheck connection info',
        options=[
            cfg.StrOpt(
                'schema',
                default='http',
                help='Schema to perform health check with'
            ),
            cfg.StrOpt(
                'endpoint',
                default='/api/v1.0/health',
                help='Health check standard endpoint'
            ),
        ]
    ),
    # TODO (Bryan Strassner) This section is in use by the operators we send
    #                        to the airflow pod(s). Needs to be refactored out
    #                        when those operators are updated.
    ConfigSection(
        name='keystone',
        title='Keystone connection and credential information',
        options=[
            cfg.StrOpt(
                'OS_AUTH_URL',
                default='http://keystone-api.ucp:80/v3',
                help='The url for OpenStack Authentication'
            ),
            cfg.StrOpt(
                'OS_PROJECT_NAME',
                default='service',
                help='OpenStack project name'
            ),
            cfg.StrOpt(
                'OS_USER_DOMAIN_NAME',
                default='Default',
                help='The OpenStack user domain name'
            ),
            cfg.StrOpt(
                'OS_USERNAME',
                default='shipyard',
                help='The OpenStack username'
            ),
            cfg.StrOpt(
                'OS_PASSWORD',
                default='password',
                help='THe OpenStack password for the shipyard svc acct'
            ),
            cfg.StrOpt(
                'OS_REGION_NAME',
                default='Regionone',
                help='The OpenStack user domain name'
            ),
            cfg.IntOpt(
                'OS_IDENTITY_API_VERSION',
                default=3,
                help='The OpenStack identity api version'
            ),
        ]
    ),
]

def register_opts(conf):
    """
    Registers all the sections in this module.
    """
    for section in SECTIONS:
        conf.register_group(
            cfg.OptGroup(name=section.name,
                         title=section.title,
                         help=section.help))
        conf.register_opts(section.options, group=section.name)

    # TODO (Bryan Strassner) is there a better, more general way to do this,
    #                        or is password enough? Probably need some guidance
    #                        from someone with more experience in this space.
    conf.register_opts(
        ks_loading.get_auth_plugin_conf_options('password'),
        group='keystone_authtoken'
    )


def list_opts():
    return {
        section.name: section.options for section in SECTIONS
    }


def parse_args(args=None, usage=None, default_config_files=None):
    CONF(args=args,
         project='shipyard',
         usage=usage,
         default_config_files=default_config_files)


register_opts(CONF)
