FROM golang:1.24.4-bullseye AS builder

WORKDIR /app

# Cache dependencies first
COPY go.mod go.sum ./
RUN go mod download

# Copy source code (vendor excluded via .dockerignore)
COPY ./ ./

ARG BINARY=bk-apigateway-mcp-proxy
ARG VERSION=latest
ARG COMMIT=HEAD
RUN GOMAXPROCS=1 go build -buildvcs=false -p 1 -ldflags "-X core/pkg/version.Version=${VERSION} -X core/pkg/version.Commit=${COMMIT} -X core/pkg/version.BuildTime=$(date +%Y-%m-%d_%I:%M:%S) -X 'core/pkg/version.GoVersion=$(go version)'" -o ${BINARY} && chmod +x ${BINARY}

# install dlv
RUN go install github.com/go-delve/delve/cmd/dlv@v1.25.2

FROM tencentos/tencentos4-minimal:4.4-v20250922

# Install curl for healthcheck
RUN dnf install -y curl && dnf clean all

ARG BINARY=bk-apigateway-mcp-proxy

RUN mkdir -p /app/logs
COPY --from=builder /app/${BINARY} /app/${BINARY}
COPY --from=builder /go/bin/dlv /usr/local/bin/dlv

CMD ["/app/bk-apigateway-mcp-proxy", "-c", "/app/config.yaml"]
