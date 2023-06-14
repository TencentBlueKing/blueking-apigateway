FROM golang:1.20 AS builder

COPY ./ /app
WORKDIR /app

# clean the sensitive data
RUN rm -rf .git README.md || echo "no found .git or README.md to be removed"


ARG BINARY=bk-apigateway-core-api

RUN make build && chmod +x ${BINARY}

FROM debian:bullseye-slim

ARG BINARY=bk-apigateway-core-api

RUN mkdir -p /app/logs
COPY --from=builder /app/${BINARY} /app/${BINARY}

CMD ["/app/bk-apigateway-core-api", "-c", "/app/config.yaml"]
