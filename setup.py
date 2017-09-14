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

from setuptools import setup

setup(
    name='shipyard_airflow',
    version='0.1a1',
    description='API for managing Airflow-based orchestration',
    url='http://github.com/att-comdev/shipyard',
    author='Anthony Lin - AT&T',
    author_email='al498u@att.com',
    license='Apache 2.0',
    packages=['shipyard_airflow', 'shipyard_airflow.control'],
    entry_points={
        "oslo.policy.policies":
        ["shipyard = shipyard.common.policies:list_rules"],
        "oslo.config.opts": ["shipyard = shipyard.conf.opts:list_opts"]
    },
    install_requires=[
        'falcon',
        'requests',
        'configparser',
        'uwsgi>1.4',
        'python-dateutil',
        'oslo.config',
    ])
