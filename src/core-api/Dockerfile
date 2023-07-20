FROM golang:1.20.4 AS builder

COPY ./ /app
WORKDIR /app

ARG BINARY=bk-apigateway-core-api

RUN make build && chmod +x ${BINARY}

FROM debian:bullseye-slim

ARG BINARY=bk-apigateway-core-api

RUN mkdir -p /app/logs
COPY --from=builder /app/${BINARY} /app/${BINARY}

CMD ["/app/bk-apigateway-core-api", "-c", "/app/config.yaml"]
