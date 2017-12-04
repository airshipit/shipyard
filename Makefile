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

AIRFLOW_IMAGE_NAME         ?= airflow
IMAGE_PREFIX               ?= attcomdev
IMAGE_TAG                  ?= latest
SHIPYARD_IMAGE_NAME        ?= shipyard
HELM                       ?= helm

# Build all docker images for this project
.PHONY: images
images: build_airflow build_shipyard

# Create tgz of the chart
.PHONY: charts
charts: clean
	$(HELM) dep up charts/shipyard
	$(HELM) package charts/shipyard

# Perform Linting
.PHONY: lint
lint: pep8 helm_lint build_docs

# Dry run templating of chart
.PHONY: dry-run
dry-run: clean
	tools/helm_tk.sh $(HELM)
	$(HELM) template charts/shipyard

.PHONY: docs
docs: clean build_docs

# Make targets intended for use by the primary targets above.

.PHONY: build_airflow
build_airflow:
	docker build -t $(IMAGE_PREFIX)/$(AIRFLOW_IMAGE_NAME):$(IMAGE_TAG) images/airflow/

.PHONY: build_shipyard
build_shipyard:
	docker build -t $(IMAGE_PREFIX)/$(SHIPYARD_IMAGE_NAME):$(IMAGE_TAG) -f images/shipyard/Dockerfile .

.PHONY: clean
clean:
	rm -rf build

.PHONY: pep8
pep8:
	tox -e pep8

.PHONY: helm_lint
helm_lint: clean
	tools/helm_tk.sh $(HELM)
	$(HELM) lint charts/shipyard

.PHONY: build_docs
build_docs:
	tox -e docs
