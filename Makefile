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

AIRFLOW_SRC                ?=
AIRFLOW_HOME               ?=
DISTRO_BASE_IMAGE          ?=
DISTRO            ?= ubuntu_jammy
DISTRO_ALIAS	   ?= ubuntu_jammy

IMAGE:=${DOCKER_REGISTRY}/${IMAGE_PREFIX}/$(IMAGE_NAME):${IMAGE_TAG}-${DISTRO}
IMAGE_ALIAS              := ${DOCKER_REGISTRY}/${IMAGE_PREFIX}/${IMAGE_NAME}:${IMAGE_TAG}-${DISTRO_ALIAS}
IMAGE_DIR:=images/$(IMAGE_NAME)

.PHONY: images

# Build all docker images for this project
images: build_images

build_images: build_airflow build_shipyard

run_images: build_airflow run_airflow  build_shipyard run_shipyard

#Build all images in list
build_airflow:
	@echo
	@echo "===== Processing [airflow] image ====="
	@make build IMAGE=${DOCKER_REGISTRY}/${IMAGE_PREFIX}/airflow:${IMAGE_TAG}-${DISTRO} IMAGE_DIR=images/airflow IMAGE_NAME=airflow

build_shipyard:
	@echo
	@echo "===== Processing [shipyard] image ====="
	@make build IMAGE=${DOCKER_REGISTRY}/${IMAGE_PREFIX}/shipyard:${IMAGE_TAG}-${DISTRO} IMAGE_DIR=images/shipyard IMAGE_NAME=shipyard


#Run all images in list

run_airflow:
	@echo
	@echo "===== Processing [airflow] image ====="
	@make run IMAGE=${DOCKER_REGISTRY}/${IMAGE_PREFIX}/airflow:${IMAGE_TAG}-${DISTRO} SCRIPT=./tools/airflow_image_run.sh
run_shipyard:
	@echo
	@echo "===== Processing [shipyard] image ====="
	@make run IMAGE=${DOCKER_REGISTRY}/${IMAGE_PREFIX}/shipyard:${IMAGE_TAG}-${DISTRO} SCRIPT=./tools/shipyard_image_run.sh

# Create tgz of the chart
.PHONY: charts
charts: clean helm-toolkit
	$(HELM) dep up charts/shipyard
	$(HELM) package charts/shipyard

# Perform Linting
.PHONY: lint
lint: pep8 helm-lint build_docs

# Dry run templating of chart
.PHONY: dry-run
dry-run: clean helm-toolkit
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
	USE_PROXY=$(USE_PROXY) PROXY=$(PROXY) NO_PROXY=$(NO_PROXY) $(SCRIPT) $(IMAGE)

_BASE_IMAGE_ARG := $(if $(DISTRO_BASE_IMAGE),--build-arg FROM="${DISTRO_BASE_IMAGE}" ,)
ifeq ($(IMAGE_NAME), airflow)
	_AIRFLOW_SRC_ARG := $(if $(AIRFLOW_SRC),--build-arg AIRFLOW_SRC="${AIRFLOW_SRC}" ,)
	_AIRFLOW_HOME_ARG := $(if $(AIRFLOW_HOME),--build-arg AIRFLOW_HOME="${AIRFLOW_HOME}" ,)
endif

.PHONY: build
build:
ifeq ($(USE_PROXY), true)
	docker build --force-rm --network host -t $(IMAGE) --label $(LABEL) \
		--label "org.opencontainers.image.revision=$(COMMIT)" \
		--label "org.opencontainers.image.created=$(shell date --rfc-3339=seconds --utc)" \
		--label "org.opencontainers.image.title=$(IMAGE_NAME)" \
		-f $(IMAGE_DIR)/Dockerfile.$(DISTRO) \
		$(_BASE_IMAGE_ARG) \
		$(_AIRFLOW_SRC_ARG) \
		$(_AIRFLOW_HOME_ARG) \
		--build-arg http_proxy=$(PROXY) \
		--build-arg https_proxy=$(PROXY) \
		--build-arg HTTP_PROXY=$(PROXY) \
		--build-arg HTTPS_PROXY=$(PROXY) \
		--build-arg no_proxy=$(NO_PROXY) \
		--build-arg NO_PROXY=$(NO_PROXY) \
		--build-arg ctx_base=$(BUILD_CTX) .
else
	docker build --force-rm --network host -t $(IMAGE) --label $(LABEL) \
		--label "org.opencontainers.image.revision=$(COMMIT)" \
		--label "org.opencontainers.image.created=$(shell date --rfc-3339=seconds --utc)" \
		--label "org.opencontainers.image.title=$(IMAGE_NAME)" \
		-f $(IMAGE_DIR)/Dockerfile.$(DISTRO) \
		$(_BASE_IMAGE_ARG) \
		$(_AIRFLOW_SRC_ARG) \
		$(_AIRFLOW_HOME_ARG) \
		--build-arg ctx_base=$(BUILD_CTX) .
endif
ifneq ($(DISTRO), $(DISTRO_ALIAS))
	docker tag $(IMAGE) $(IMAGE_ALIAS)
ifeq ($(DOCKER_REGISTRY), localhost:5000)
	docker push $(IMAGE_ALIAS)
endif
endif
ifeq ($(DOCKER_REGISTRY), localhost:5000)
	docker push $(IMAGE)
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
	rm -rf doc/build
	rm -f charts/*.tgz
	rm -f charts/*/requirements.lock
	rm -rf charts/*/charts
	rm -rf .tox

.PHONY: pep8
pep8:
	cd $(BUILD_CTX)/shipyard_client; tox -e pep8
	cd $(BUILD_CTX)/shipyard_airflow; tox -e pep8

.PHONY: helm-lint
helm-lint: clean helm-toolkit
	$(HELM) dep up charts/shipyard
	$(HELM) lint charts/shipyard

# Initialize local helm config
.PHONY: helm-toolkit
helm-toolkit: helm-install
	./tools/helm_tk.sh $(HELM)

# Install helm binary
.PHONY: helm-install
helm-install:
	tools/helm_install.sh $(HELM)

.PHONY: docs
docs: clean build_docs

.PHONY: build_docs
build_docs:
	tox -e docs
