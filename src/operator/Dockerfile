FROM golang:1.27.3 AS builder

COPY ./ /app
WORKDIR /app

ARG BINARY=micro-gateway-operator
ARG VERSION=latest
ARG COMMIT=HEAD

RUN make build -e VERSION=${VERSION} -e COMMIT=${COMMIT} && chmod +x ./build/${BINARY}

# install dlv
RUN go install github.com/go-delve/delve/cmd/dlv@v1.27.0

FROM tencentos/tencentos4-minimal:4.4-v20250922

ARG BINARY=micro-gateway-operator

RUN mkdir -p /app/logs
COPY --from=builder /go/bin/dlv /usr/local/bin/dlv
COPY --from=builder /app/build/${BINARY} /app/${BINARY}
RUN chmod 755 /app/${BINARY}

CMD ["/app/micro-gateway-operator", "--config=/app/config.yaml"]
