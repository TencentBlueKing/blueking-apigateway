ARG IMAGE=python
ARG TAG=3.6.15-slim
FROM ${IMAGE}:${TAG}

ADD build /app
WORKDIR /app
RUN apt-get clean && \
    apt-get update && \
    apt-get install --no-install-recommends -y libssl-dev default-libmysqlclient-dev \
    libffi-dev libc6-dev build-essential vim procps && \
    apt-get autoremove -y && \
    apt-get clean -y && \
    rm -rf \
    /usr/share/doc \
    /usr/share/man \
    /usr/share/info \
    /usr/share/locale \
    /var/lib/apt/lists/* \
    /var/log/* \
    /var/cache/debconf/* \
    /etc/systemd \
    /lib/lsb \
    /lib/udev \
    /usr/lib/x86_64-linux-gnu/gconv/IBM* \
    /usr/lib/x86_64-linux-gnu/gconv/EBC* && \
    bash -c "mkdir -p /usr/share/man/man{1..8}"

ARG PYPI="https://pypi.org/simple/"
RUN pip config set global.index-url "${PYPI}" && \
    pip install --upgrade pip && \
    pip install "setuptools<58.0.0" && \
    pip install -r requirements.txt

CMD ["bash", "/app/bin/start.sh"]