FROM golang:1.25.5-bookworm AS builder

COPY ./ /app
WORKDIR /app

ARG BINARY=bk-apigateway-core-api
ARG VERSION=latest
ARG COMMIT=HEAD
RUN make build -e VERSION=${VERSION} -e COMMIT=${COMMIT} && chmod +x ${BINARY}

# install dlv
RUN go install github.com/go-delve/delve/cmd/dlv@v1.26.3

FROM debian:bookworm-slim

ARG BINARY=bk-apigateway-core-api

RUN mkdir -p /app/logs
COPY --from=builder /app/${BINARY} /app/${BINARY}
COPY --from=builder /go/bin/dlv /usr/local/bin/dlv

CMD ["/app/bk-apigateway-core-api", "-c", "/app/config.yaml"]
