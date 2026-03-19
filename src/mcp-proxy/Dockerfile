FROM golang:1.24.4-bullseye AS builder

COPY ./ /app
WORKDIR /app

ARG BINARY=bk-apigateway-mcp-proxy
ARG VERSION=latest
ARG COMMIT=HEAD
RUN go mod vendor && go build -buildvcs=false -ldflags "-X core/pkg/version.Version=${VERSION} -X core/pkg/version.Commit=${COMMIT} -X core/pkg/version.BuildTime=$(date +%Y-%m-%d_%I:%M:%S) -X 'core/pkg/version.GoVersion=$(go version)'" -o ${BINARY} && chmod +x ${BINARY}

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
