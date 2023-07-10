ARG IMAGE=python
ARG TAG=3.6.15-slim-buster
FROM ${IMAGE}:${TAG}

RUN apt-get update && apt-get install -y libssl-dev default-libmysqlclient-dev libffi-dev build-essential libc6-dev libjpeg-dev zlib1g-dev vim

ARG PYPI="https://pypi.org/simple/"
RUN pip config set global.index-url "${PYPI}"

WORKDIR /app
ADD build/requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt

ADD build /app


CMD ["bash", "/app/bin/start.sh"]
