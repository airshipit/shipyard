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

BUILD_CTX                  ?= src/bin
DOCKER_REGISTRY            ?= quay.io
IMAGE_PREFIX               ?= attcomdev
IMAGE_TAG                  ?= latest
HELM                       ?= helm
LABEL                      ?= commit-id
IMAGE_NAME                 := airflow shipyard

IMAGE:=${DOCKER_REGISTRY}/${IMAGE_PREFIX}/$(IMAGE_NAME):${IMAGE_TAG}
IMAGE_DIR:=images/$(IMAGE_NAME)

.PHONY: images
#Build all images in the list
images: $(IMAGE_NAME)
#Build and run all images in list
#sudo make images IMAGE_NAME=airflow will Build and Run airflow
#sudo make images will build and run airflow and shipyard
$(IMAGE_NAME):
	@echo
	@echo "===== Processing [$@] image ====="
	@make build_$@ IMAGE=${DOCKER_REGISTRY}/${IMAGE_PREFIX}/$@:${IMAGE_TAG} IMAGE_DIR=images/$@
	@make run IMAGE=${DOCKER_REGISTRY}/${IMAGE_PREFIX}/$@:${IMAGE_TAG} SCRIPT=./tools/$@_image_run.sh

# Build all docker images for this project

# Create tgz of the chart
.PHONY: charts
charts: clean
	tools/helm_tk.sh $(HELM)
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


.PHONY: tests
tests:
	cd $(BUILD_CTX)/shipyard_airflow; tox
	cd $(BUILD_CTX)/shipyard_client; tox

# Make targets intended for use by the primary targets above.

.PHONY: run
run:
	$(SCRIPT) $(IMAGE)

.PHONY: build_airflow
build_airflow:
	docker build -t $(IMAGE) --label $(LABEL) -f $(IMAGE_DIR)/Dockerfile $(IMAGE_DIR)

.PHONY: build_shipyard
build_shipyard:
	docker build -t $(IMAGE) --label $(LABEL) -f $(IMAGE_DIR)/Dockerfile --build-arg ctx_base=$(BUILD_CTX) .

.PHONY: clean
clean:
	cd $(BUILD_CTX)/shipyard_airflow; rm -rf build
	cd $(BUILD_CTX)/shipyard_client; rm -rf build

.PHONY: pep8
pep8:
	cd $(BUILD_CTX)/shipyard_airflow; tox -e pep8
	cd $(BUILD_CTX)/shipyard_client; tox -e pep8

.PHONY: helm_lint
helm_lint: clean
	tools/helm_tk.sh $(HELM)
	$(HELM) lint charts/shipyard

.PHONY: build_docs
build_docs:
	tox -e docs
