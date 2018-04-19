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

FROM python:3.5

ENV container docker
ENV PORT 9000
ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8

ARG DEBIAN_FRONTEND=noninteractive
ARG ctx_base=src/bin

# Expose port 9000 for application
EXPOSE $PORT

# Execute entrypoint
ENTRYPOINT ["/home/shipyard/entrypoint.sh"]
CMD ["server"]

# Create shipyard user
RUN useradd -ms /bin/bash shipyard \
    && mkdir -p /home/shipyard/shipyard \
    && mkdir -p /home/shipyard/shipyard_client

# Copy entrypoint.sh to /home/shipyard
COPY ${ctx_base}/shipyard_airflow/entrypoint.sh /home/shipyard/entrypoint.sh
# Change permissions and set up directories
RUN chown -R shipyard: /home/shipyard \
    && chmod +x /home/shipyard/entrypoint.sh

# Requirements
COPY ${ctx_base}/shipyard_airflow/requirements.txt /home/shipyard/api_requirements.txt
RUN pip3 install -r /home/shipyard/api_requirements.txt

COPY ${ctx_base}/shipyard_client/requirements.txt /home/shipyard/client_requirements.txt
RUN pip3 install -r /home/shipyard/client_requirements.txt

# Shipyard source and installation
COPY ${ctx_base}/shipyard_client /home/shipyard/shipyard_client/
RUN cd /home/shipyard/shipyard_client \
    && python3 setup.py install
COPY ${ctx_base}/shipyard_airflow /home/shipyard/shipyard/
RUN cd /home/shipyard/shipyard \
    && python3 setup.py install

# Set user to shipyard
USER shipyard
