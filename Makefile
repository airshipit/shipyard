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

BUILD_DIR                  := $(shell mktemp -d)
BUILD_CTX                  ?= src/bin

IMAGE_PREFIX               ?= airshipit
IMAGE_TAG                  ?= latest
IMAGE_NAME                 := airflow shipyard
# use this variable for image labels added in internal build process
LABEL                      ?= org.airshipit.build=community
COMMIT                     ?= $(shell git rev-parse HEAD)

DOCKER_REGISTRY            ?= quay.io
PUSH_IMAGE                 ?= false

HELM                       := $(BUILD_DIR)/helm

PROXY                      ?= http://proxy.foo.com:8000
NO_PROXY                   ?= localhost,127.0.0.1,.svc.cluster.local
USE_PROXY                  ?= false

UBUNTU_BASE_IMAGE          ?=

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
	@make build IMAGE=${DOCKER_REGISTRY}/${IMAGE_PREFIX}/$@:${IMAGE_TAG} IMAGE_DIR=images/$@ IMAGE_NAME=$@
	@make run IMAGE=${DOCKER_REGISTRY}/${IMAGE_PREFIX}/$@:${IMAGE_TAG} SCRIPT=./tools/$@_image_run.sh

# Build all docker images for this project

# Create tgz of the chart
.PHONY: charts
charts: clean helm-init
	$(HELM) dep up charts/shipyard
	$(HELM) package charts/shipyard

# Perform Linting
.PHONY: lint
lint: pep8 helm_lint build_docs

# Dry run templating of chart
.PHONY: dry-run
dry-run: clean helm-init
	$(HELM) template charts/shipyard

.PHONY: security
security:
	cd $(BUILD_CTX)/shipyard_client; tox -e bandit
	cd $(BUILD_CTX)/shipyard_airflow; tox -e bandit

.PHONY: tests
tests:
	cd $(BUILD_CTX)/shipyard_client; tox
	cd $(BUILD_CTX)/shipyard_airflow; tox

# Make targets intended for use by the primary targets above.

.PHONY: run
run:
	USE_PROXY=$(USE_PROXY) PROXY=$(PROXY) $(SCRIPT) $(IMAGE)

_BASE_IMAGE_ARG := $(if $(UBUNTU_BASE_IMAGE),--build-arg FROM="${UBUNTU_BASE_IMAGE}" ,)

.PHONY: build
build:
ifeq ($(USE_PROXY), true)
	docker build --network host -t $(IMAGE) --label $(LABEL) \
		--label "org.opencontainers.image.revision=$(COMMIT)" \
		--label "org.opencontainers.image.created=$(shell date --rfc-3339=seconds --utc)" \
		--label "org.opencontainers.image.title=$(IMAGE_NAME)" \
		-f $(IMAGE_DIR)/Dockerfile \
		$(_BASE_IMAGE_ARG) \
		--build-arg http_proxy=$(PROXY) \
		--build-arg https_proxy=$(PROXY) \
		--build-arg HTTP_PROXY=$(PROXY) \
		--build-arg HTTPS_PROXY=$(PROXY) \
		--build-arg no_proxy=$(NO_PROXY) \
		--build-arg NO_PROXY=$(NO_PROXY) \
		--build-arg ctx_base=$(BUILD_CTX) .
else
	docker build --network host -t $(IMAGE) --label $(LABEL) \
		--label "org.opencontainers.image.revision=$(COMMIT)" \
		--label "org.opencontainers.image.created=$(shell date --rfc-3339=seconds --utc)" \
		--label "org.opencontainers.image.title=$(IMAGE_NAME)" \
		-f $(IMAGE_DIR)/Dockerfile \
		$(_BASE_IMAGE_ARG) \
		--build-arg ctx_base=$(BUILD_CTX) .
endif
ifeq ($(PUSH_IMAGE), true)
	docker push $(IMAGE)
endif

.PHONY: clean
clean:
	rm -rf build
	rm -rf doc/build
	cd $(BUILD_CTX)/shipyard_client; rm -rf build
	cd $(BUILD_CTX)/shipyard_airflow; rm -rf build

.PHONY: pep8
pep8:
	cd $(BUILD_CTX)/shipyard_client; tox -e pep8
	cd $(BUILD_CTX)/shipyard_airflow; tox -e pep8

.PHONY: helm_lint
helm_lint: clean helm-init
	$(HELM) lint charts/shipyard

# Initialize local helm config
.PHONY: helm-init
helm-init: helm-install
	tools/helm_tk.sh $(HELM)

# Install helm binary
.PHONY: helm-install
helm-install:
	tools/helm_install.sh $(HELM)

.PHONY: docs
docs: clean build_docs

.PHONY: build_docs
build_docs:
	tox -e docs
