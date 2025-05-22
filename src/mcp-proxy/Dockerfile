FROM golang:1.23.2-bullseye AS builder

COPY ./ /app
WORKDIR /app

ARG BINARY=bk-apigateway-mcp-proxy
ARG VERSION=latest
ARG COMMIT=HEAD
RUN make build -e VERSION=${VERSION} -e COMMIT=${COMMIT} && chmod +x ${BINARY}

# install dlv
RUN go install github.com/go-delve/delve/cmd/dlv@v1.23.1

FROM debian:bullseye-slim

ARG BINARY=bk-apigateway-mcp-proxy

RUN mkdir -p /app/logs
COPY --from=builder /app/${BINARY} /app/${BINARY}
COPY --from=builder /go/bin/dlv /usr/local/bin/dlv

CMD ["/app/bk-apigateway-mcp-proxy", "-c", "/app/config.yaml"]
