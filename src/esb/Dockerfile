ARG IMAGE=hub.bktencent.com/blueking/python
ARG TAG=3.6.8-ts4
FROM ${IMAGE}:${TAG}

# already installed:  openssl-devel / libffi-devel / glibc-devel

RUN dnf -y install vim procps-ng

ADD build /app
WORKDIR /app

ARG PYPI="https://pypi.org/simple/"
RUN pip config set global.index-url "${PYPI}"
RUN pip install -r requirements.txt

CMD ["bash", "/app/bin/start.sh"]
