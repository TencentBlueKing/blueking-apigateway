ARG IMAGE=python
ARG TAG=3.10.12-slim-bullseye
FROM ${IMAGE}:${TAG}

RUN apt-get update && apt-get install -y libssl-dev libffi-dev \
    build-essential libc6-dev libjpeg-dev zlib1g-dev vim procps curl zip unzip

ARG PYPI="https://pypi.org/simple/"
RUN pip config set global.index-url "${PYPI}"

WORKDIR /app
ADD build/requirements.txt /app/requirements.txt
# while the celery 4.4.7 can't be installed via pip >=24.x
# RUN pip install --upgrade pip
RUN pip install pip==23.0.1
RUN pip install -r requirements.txt

ADD build /app


CMD ["bash", "/app/bin/start.sh"]
