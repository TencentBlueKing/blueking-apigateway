
.PHONY: init
VERSION = `git describe --tags --abbrev=0`
COMMIT=`git rev-parse HEAD`
init:
	pip install pre-commit
	pre-commit install
	# go get -u github.com/golangci/golangci-lint/cmd/golangci-lint
	curl -sSfL https://raw.githubusercontent.com/golangci/golangci-lint/master/install.sh | sh -s -- -b $(shell go env GOPATH)/bin v1.46.2
	# for ginkgo
	go install github.com/onsi/ginkgo/v2/ginkgo@latest
	# for make mock
	go install github.com/golang/mock/mockgen@v1.6.0
	# for gofumpt
	go install mvdan.cc/gofumpt@latest
	# for golines
	go install github.com/segmentio/golines@latest
	# for goimports
	go install -v github.com/incu6us/goimports-reviser/v3@latest

.PHONY: dep
dep:
	go mod tidy
	go mod vendor

.PHONY: mock
mock:
	go generate ./...

.PHONY: lint
lint:
	export GOFLAGS=-mod=vendor
	golangci-lint run
	find . -name "*.go" -not -path "./vendor/*" | xargs -n 1 grep -L 'TencentBlueKing is pleased to ' | grep -v '/mock/' | wc -l | xargs -I {} bash -c '[[ {} -eq 0 ]] && exit 0 || exit 1'

.PHONY: check-license
check-license:
	find . -name "*.go" -not -path "./vendor/*" | xargs -n 1 grep -L 'TencentBlueKing is pleased to ' | grep -v '/mock/'



.PHONY: fmt
fmt:
	golines ./ -m 120 -w --base-formatter gofmt --no-reformat-tags
	gofumpt  -l -w .
	goimports-reviser -rm-unused -set-alias -format ./...


.PHONY: test
test:
	go test -mod=vendor -gcflags=all=-l $(shell go list ./... | grep -v mock | grep -v docs) -covermode=count -coverprofile .coverage.cov

.PHONY: cov
cov:
	go tool cover -html=.coverage.cov

.PHONY: build
build:
	go build -ldflags "-X core/pkg/version.Version=$(VERSION) -X core/pkg/version.Commit=$(COMMIT) -X core/pkg/version.BuildTime=`date +%Y-%m-%d_%I:%M:%S` -X 'core/pkg/version.GoVersion=`go version`'" -o bk-apigateway-core-api

.PHONY: serve
serve: build
	./bk-apigateway-core-api -c config.yaml

.PHONY: dev-image
dev-image:
	docker build --build-arg VERSION=`git describe --tags --abbrev=0` --build-arg COMMIT=`git rev-parse HEAD`  -f  Dockerfile . -t bk-apigateway-core-api:development
