ARG IMAGE=hub.bktencent.com/blueking/python
ARG TAG=3.14-tencentos4
FROM ${IMAGE}:${TAG}

RUN dnf install -y vim mysql curl zip unzip git \
    && dnf clean all \
    && rm -rf /var/cache/dnf /var/cache/yum

COPY --from=ghcr.io/astral-sh/uv:0.11.26 /uv /uvx /bin/

WORKDIR /app
COPY build/pyproject.toml build/uv.lock /app/
RUN export UV_PROJECT_ENVIRONMENT=/usr/local/ && uv sync --locked --no-dev && uv clean

ADD build /app


CMD ["bash", "/app/bin/start.sh"]
