VERSION = `git describe --tags --abbrev=0`
COMMIT=`git rev-parse HEAD`

.PHONY: init
init:
	# go get -u github.com/golangci/golangci-lint/cmd/golangci-lint
	curl -sSfL https://raw.githubusercontent.com/golangci/golangci-lint/master/install.sh | sh -s -- -b $(LOCALBIN) v2.1.6
	# for ginkgo
	GOBIN=$(LOCALBIN) go install github.com/onsi/ginkgo/v2/ginkgo@latest
	# for make mock
	GOBIN=$(LOCALBIN) go install github.com/golang/mock/mockgen@v1.6.0
	# for gofumpt
	GOBIN=$(LOCALBIN) go install mvdan.cc/gofumpt@latest
	# for golines
	GOBIN=$(LOCALBIN) go install github.com/segmentio/golines@latest
	# for goimports
	GOBIN=$(LOCALBIN) go install -v github.com/incu6us/goimports-reviser/v3@latest
	# for swag
	GOBIN=$(LOCALBIN) go install github.com/swaggo/swag/cmd/swag@latest

.PHONY: dep
dep:
	go mod tidy
	go mod vendor

doc:
	$(SWAG) init

.PHONY: mock
mock:
	go generate ./...

.PHONY: lint
lint:
	export GOFLAGS=-mod=vendor
	$(GOLINTER) run
	find . -name "*.go" -not -path "./vendor/*" | xargs -n 1 grep -L 'TencentBlueKing is pleased to ' | grep -v '/mock/' | wc -l | xargs -I {} bash -c '[[ {} -eq 0 ]] && exit 0 || exit 1'

.PHONY: check-license
check-license:
	find . -name "*.go" -not -path "./vendor/*" | xargs -n 1 grep -L 'TencentBlueKing is pleased to ' | grep -v '/mock/'



.PHONY: fmt
fmt:
	$(GOLINES) ./ -m 120 -w --base-formatter gofmt --no-reformat-tags
	$(GOFUMPT)  -l -w .
	$(GOIMPORTS) -rm-unused -set-alias -excludes '.git,vendor' -format ./...


.PHONY: test
test:
	$(GINKGO) -r -mod=vendor --cover --coverprofile=.coverage.cov ./...

.PHONY: cov
cov:
	go tool cover -html=.coverage.cov

.PHONY: build
build:
	go build -ldflags "-X core/pkg/version.Version=$(VERSION) -X core/pkg/version.Commit=$(COMMIT) -X core/pkg/version.BuildTime=`date +%Y-%m-%d_%I:%M:%S` -X 'core/pkg/version.GoVersion=`go version`'" -o bk-apigateway-mcp-proxy

.PHONY: serve
serve: build
	./bk-apigateway-mcp-proxy -c config.yaml

.PHONY: dev-image
dev-image:
	docker build --build-arg VERSION=`git describe --tags --abbrev=0` --build-arg COMMIT=`git rev-parse HEAD`  -f  Dockerfile . -t bk-apigateway-mcp-proxy:development



LOCALBIN ?= $(shell pwd)/bin
$(LOCALBIN):
	mkdir -p $(LOCALBIN)

## Tool Binaries
GOLINES ?= $(LOCALBIN)/golines
GOFUMPT ?= $(LOCALBIN)/gofumpt
SWAG ?= $(LOCALBIN)/swag
GOLINTER ?=$(LOCALBIN)/golangci-lint
GOIMPORTS ?=$(LOCALBIN)/goimports-reviser
GINKGO ?=$(LOCALBIN)/ginkgo