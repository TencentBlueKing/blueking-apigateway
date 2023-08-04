ARG IMAGE=python
ARG TAG=3.6.15-slim-buster
FROM ${IMAGE}:${TAG}

RUN apt-get update && apt-get install -y libssl-dev default-libmysqlclient-dev libffi-dev libc6-dev build-essential vim procps

ADD build /app
WORKDIR /app

ARG PYPI="https://pypi.org/simple/"
RUN pip config set global.index-url "${PYPI}"
RUN pip install -r requirements.txt

CMD ["bash", "/app/bin/start.sh"]