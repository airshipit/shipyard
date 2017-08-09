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

FROM ubuntu:16.04

ENV DEBIAN_FRONTEND noninteractive
ENV container docker

RUN set -x && \
    apt-get -qq update && \
    apt-get -y install \
    git \
    curl \
    netcat \
    netbase \
    python3 \
    python3-setuptools \
    python3-pip \
    python3-dev \
    python3-dateutil \
    ca-certificates \
    gcc \
    g++ \
    make \
    libffi-dev \
    libssl-dev \
    --no-install-recommends \
    && python3 -m pip install -U pip \
    && pip3 install falcon \
    && pip3 install requests \
    && pip3 install uwsgi \
    && pip3 install configparser \
    && pip3 install python-openstackclient==3.11.0 \
    && apt-get clean \
    && rm -rf \
        /var/lib/apt/lists/* \
        /tmp/* \
        /var/tmp/* \
        /usr/share/man \
        /usr/share/doc \
        /usr/share/doc-base

# Create shipyard user
RUN useradd -ms /bin/bash shipyard

# Clone the shipyard repository
COPY ./ /home/shipyard/shipyard

# Copy entrypoint.sh to /home/shipyard
COPY entrypoint.sh /home/shipyard/entrypoint.sh

# Copy shipyard.conf to /home/shipyard
COPY ./shipyard_airflow/control/shipyard.conf /home/shipyard/shipyard.conf

# Change permissions
RUN chown -R shipyard: /home/shipyard \
    && chmod +x /home/shipyard/entrypoint.sh

# Expose port 9000 for application
EXPOSE 9000

# Set work directory
USER shipyard
WORKDIR /home/shipyard/shipyard

# Execute entrypoint
ENTRYPOINT ["/home/shipyard/entrypoint.sh"]

