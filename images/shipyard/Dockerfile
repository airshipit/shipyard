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

# Expose port 9000 for application
EXPOSE $PORT

# Execute entrypoint
ENTRYPOINT ["/home/shipyard/entrypoint.sh"]
CMD ["server"]

# Create shipyard user
RUN useradd -ms /bin/bash shipyard

# Copy entrypoint.sh to /home/shipyard
COPY entrypoint.sh /home/shipyard/entrypoint.sh
# Change permissions
RUN chown -R shipyard: /home/shipyard \
    && chmod +x /home/shipyard/entrypoint.sh

# Set work directory and install dependencies
WORKDIR /home/shipyard/shipyard
COPY requirements.txt /home/shipyard/shipyard
RUN pip3 install -r requirements.txt

COPY . /home/shipyard/shipyard
RUN python3 setup.py install

# Set user to shipyard
USER shipyard
