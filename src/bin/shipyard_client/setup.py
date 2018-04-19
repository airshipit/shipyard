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
    name='shipyard_client',
    version='0.1a1',
    description='CLI for Shipyard',
    url='https://github.com/att-comdev/shipyard',
    author='AT&T - AIC UCP Developers',
    license='Apache 2.0',
    packages=setuptools.find_packages(),
    entry_points={
        'console_scripts':
        'shipyard = shipyard_client.cli.commands:shipyard'
    },
    classifiers=[
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
    ],
)
