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

ARG FROM=opensuse/leap:15.0
FROM ${FROM}

LABEL org.opencontainers.image.authors='airship-discuss@lists.airshipit.org, irc://#airshipit@freenode'
LABEL org.opencontainers.image.url='https://airshipit.org'
LABEL org.opencontainers.image.documentation='https://airship-shipyard.readthedocs.org'
LABEL org.opencontainers.image.source='https://git.openstack.org/openstack/airship-shipyard'
LABEL org.opencontainers.image.vendor='The Airship Authors'
LABEL org.opencontainers.image.licenses='Apache-2.0'

ENV container docker
ENV PORT 9000
ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8
# Setting the version explicitly for PBR
ENV PBR_VERSION 0.1a1

ARG ctx_base=src/bin

# Expose port 9000 for application
EXPOSE $PORT

RUN set -ex && \
    zypper --gpg-auto-import-keys refresh && \
    zypper -q update -y && \
    zypper --non-interactive install --no-recommends \
        ca-certificates \
        curl \
        netcfg \
        python3-devel \
        python3-setuptools \
    && zypper clean -a \
    && rm -rf \
        /tmp/* \
        /var/tmp/* \
        /usr/share/man \
        /usr/share/doc \
        /usr/share/doc-base

# Create shipyard user
RUN useradd -ms /bin/bash shipyard \
    && mkdir -p /home/shipyard/shipyard \
    && mkdir -p /home/shipyard/shipyard_client

# Copy entrypoint.sh to /home/shipyard
COPY ${ctx_base}/shipyard_airflow/entrypoint.sh /home/shipyard/entrypoint.sh
# Change permissions and set up directories
RUN chown -R shipyard: /home/shipyard \
    && chmod +x /home/shipyard/entrypoint.sh

# Requirements and Shipyard source
COPY ${ctx_base}/shipyard_airflow/requirements.txt /home/shipyard/api_requirements.txt
COPY ${ctx_base}/shipyard_client/requirements.txt /home/shipyard/client_requirements.txt
COPY ${ctx_base}/shipyard_client /home/shipyard/shipyard_client/
COPY ${ctx_base}/shipyard_airflow /home/shipyard/shipyard/

# Build
 RUN set -ex \
    && buildDeps=' \
      gcc \
      git-core \
      libopenssl-devel \
      make \
      python3-pip \
    ' \
    && zypper -q update -y \
    && zypper --non-interactive install --no-recommends $buildDeps \
    && python3 -m pip install -U pip \
    && pip3 install -r /home/shipyard/client_requirements.txt --no-cache-dir \
    && cd /home/shipyard/shipyard_client \
    && python3 setup.py install \
    && pip3 install -r /home/shipyard/api_requirements.txt --no-cache-dir \
    && cd /home/shipyard/shipyard \
    && python3 setup.py install \
    && zypper remove -y --clean-deps $buildDeps \
    && zypper clean -a \
    && rm -rf \
        /tmp/* \
        /var/tmp/* \
        /var/log/* \
        /usr/share/man \
        /usr/share/doc \
        /usr/share/doc-base

# Entrypoint
ENTRYPOINT ["/home/shipyard/entrypoint.sh"]
CMD ["server"]
# Set user to shipyard
USER shipyard
