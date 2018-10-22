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

import setuptools

setuptools.setup(
    name='shipyard_api',
    version='0.1a1',
    description=('Directed acyclic graph controller for Kubernetes and '
                 'OpenStack control plane life cycle management'),
    url='https://github.com/openstack/airship-shipyard',
    author='The Airship Authors',
    license='Apache 2.0',
    packages=setuptools.find_packages(),
    entry_points={
        'oslo.config.opts':
            'shipyard_api = shipyard_airflow.conf.opts:list_opts',
        'oslo.policy.policies':
            'shipyard_api = shipyard_airflow.policy:list_policies',
        'console_scripts':
            'upgrade_db = shipyard_airflow.shipyard_upgrade_db:upgrade_db',
    },
    classifiers=[
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
)
