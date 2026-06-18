BUILD_PATH ?= $(shell pwd)/build
VERSION = `git describe --tags --abbrev=0`
COMMIT=`git rev-parse HEAD`
# Image URL to use all building/pushing image targets
IMG ?= bk-micro-gateway-operator:development

## Location to install dependencies to
LOCALBIN ?= $(shell pwd)/bin
GOBIN=$(LOCALBIN)
$(LOCALBIN):
	mkdir -p $(LOCALBIN)


## Tool Binaries
GOLANGCI_LINT = $(LOCALBIN)/golangci-lint
MOCKGEN = $(LOCALBIN)/mockgen
GINKGO = $(LOCALBIN)/ginkgo
GCI = $(LOCALBIN)/gci
SETUP_ENVTEST = $(LOCALBIN)/setup-envtest

## Docker Compose command detection (supports both 'docker compose' and 'docker-compose')
DOCKER_COMPOSE := $(shell if docker compose version >/dev/null 2>&1; then echo "docker compose"; elif command -v docker-compose >/dev/null 2>&1; then echo "docker-compose"; else echo ""; fi)

## Tool Versions
GOLANGCI_LINT_VERSION ?= v2.11.4
MOCKGEN_VERSION ?= v1.6.0
GINKGO_VERSION ?= v2.27.2
GCI_VERSION ?= v0.14.0
SETUP_ENVTEST_VERSION ?= v0.0.0-20260305142021-f9589b9f2b9d


# Setting SHELL to bash allows bash commands to be executed by recipes.
# This is a requirement for 'setup-envtest.sh' in the test target.
# Options are set to exit when a recipe line exits non-zero or a piped command fails.
SHELL = /usr/bin/env bash -o pipefail
.SHELLFLAGS = -ec


.PHONY: init
init: $(LOCALBIN)
	# for golangci-lint
	curl -sSfL https://raw.githubusercontent.com/golangci/golangci-lint/master/install.sh | sh -s -- -b $(LOCALBIN) $(GOLANGCI_LINT_VERSION)
	# for make mock
	GOBIN=$(LOCALBIN) go install github.com/golang/mock/mockgen@$(MOCKGEN_VERSION)
	# for ginkgo
	GOBIN=$(LOCALBIN) go install github.com/onsi/ginkgo/v2/ginkgo@$(GINKGO_VERSION)
	# for gci
	GOBIN=$(LOCALBIN) go install github.com/daixiang0/gci@$(GCI_VERSION)
	# for envtest
	GOBIN=$(LOCALBIN) go install sigs.k8s.io/controller-runtime/tools/setup-envtest@$(SETUP_ENVTEST_VERSION)


.PHONY: all
all: build

$(BUILD_PATH):
	mkdir -p $(BUILD_PATH)


.PHONY: fmt
fmt:
	$(GOLANGCI_LINT) fmt  ./...

.PHONY: lint
lint:
	# Use single core to avoid golangci-lint typecheck OOM in this environment.
	GOMAXPROCS=1 $(GOLANGCI_LINT) run --fix ./...

.PHONY: test
test: ## Run tests.
	$(GINKGO) --skip-package=vendor,tests/integration -ldflags="-s=false" -gcflags="-l" --cover --coverprofile cover.out ./...


.PHONY: build
build: ## Build manager binary.
	go build -ldflags "-X operator/pkg/version.Version=$(VERSION)  \
		-X operator/pkg/version.Commit=$(COMMIT) \
		-X operator/pkg/version.BuildTime=`date +%Y-%m-%d_%I:%M:%S` \
		-X 'operator/pkg/version.GoVersion=`go version`'" \
		-o $(BUILD_PATH)/micro-gateway-operator .

.PHONY: docker-build
docker-build: ## Build docker image with the manager.
	docker build --build-arg VERSION=$(VERSION) --build-arg COMMIT=$(COMMIT) -t ${IMG} .


.PHONY: integration
integration: docker-build
ifeq ($(DOCKER_COMPOSE),)
	$(error "Neither 'docker compose' nor 'docker-compose' found. Please install Docker Compose.")
endif
	cd tests/integration && $(DOCKER_COMPOSE) down && $(DOCKER_COMPOSE) up -d --wait && $(GINKGO) -ldflags="-s=false" -gcflags="-l"; $(DOCKER_COMPOSE) down
