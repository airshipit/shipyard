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

# Docker image to run Airflow on Kubernetes
FROM ubuntu:16.04

# Do not prompt user for choices on installation/configuration of packages
# Set port 8080 for Airflow Web
# Set port 5555 for Airflow Flower
# Set port 8793 for Airflow Worker
ENV DEBIAN_FRONTEND noninteractive
ENV container docker
ENV WEB_PORT 8080
ENV FLOWER_PORT 5555
ENV WORKER_PORT 8793

# Expose port for applications
EXPOSE $WEB_PORT
EXPOSE $FLOWER_PORT
EXPOSE $WORKER_PORT

# Airflow Home Directory
ARG AIRFLOW_HOME=/usr/local/airflow

# Kubectl version
ARG KUBECTL_VERSION=1.8.6

RUN set -ex && \
    apt-get -qq update && \
    apt-get -y install \
    ca-certificates \
    curl \
    gcc \
    git \
    g++ \
    libffi-dev \
    libssl-dev \
    libpq-dev \
    locales \
    netcat \
    netbase \
    python3 \
    python3-setuptools \
    python3-pip \
    python3-dev \
    python3-dateutil \
    make \
    --no-install-recommends \
    && python3 -m pip install -U pip \
    && apt-get clean \
    && rm -rf \
        /var/lib/apt/lists/* \
        /tmp/* \
        /var/tmp/* \
        /usr/share/man \
        /usr/share/doc \
        /usr/share/doc-base

# Copy dependency requirements
COPY ./requirements.txt /tmp/
RUN pip3 install -r /tmp/requirements.txt

# Note - removing snakebite (python 2 vs. 3). See:
#    https://github.com/puckel/docker-airflow/issues/77
RUN pip3 uninstall -y snakebite || true

# Install Armada, DeckHand and DryDock Client Libraries
RUN pip3 install -e git://github.com/att-comdev/armada.git@7a2ba22ab12a3f1f180b6af4085972ba44853377#egg=armada
RUN pip3 install -e git://github.com/att-comdev/deckhand.git@3cdf3d2d896d43c6e3bc26170522c3eee0d7158f#egg=deckhand
RUN pip3 install -e git://github.com/att-comdev/drydock.git@42aa3c486ee4c495c2377d31481df5ab681f84f2#egg=drydock_provisioner

# Create airflow user
RUN useradd -ms /bin/bash -d ${AIRFLOW_HOME} airflow

# Download and install kubectl
RUN curl -L -o /usr/local/bin/kubectl \
    https://storage.googleapis.com/kubernetes-release/release/v${KUBECTL_VERSION}/bin/linux/amd64/kubectl \
    && chmod +x /usr/local/bin/kubectl

# Copy entrypoint.sh, airflow_start_service.sh and
# airflow_logrotate.sh
COPY script/entrypoint.sh ${AIRFLOW_HOME}/entrypoint.sh
COPY script/airflow_start_service.sh ${AIRFLOW_HOME}/airflow_start_service.sh
COPY script/airflow_logrotate.sh ${AIRFLOW_HOME}/airflow_logrotate.sh
COPY script/upgrade_airflow_worker.sh ${AIRFLOW_HOME}/upgrade_airflow_worker.sh

# Change permissions
RUN chown -R airflow: ${AIRFLOW_HOME}

# Set work directory
USER airflow
WORKDIR ${AIRFLOW_HOME}

# Execute entrypoint
ENTRYPOINT ["./entrypoint.sh"]
