# npm part
FROM node:16.20.2  AS builder

WORKDIR /app
COPY . /app

ARG EDITION=ee
ENV APP_VERSION=${EDITION}

RUN npm install --unsafe-perm --force --registry=https://mirrors.tencent.com/npm/
RUN npm run build:${EDITION:?}

# nginx part
FROM smebberson/alpine-nginx:3.0.0

RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.tencent.com/g' /etc/apk/repositories
RUN sed -i 's/dl-4.alpinelinux.org/mirrors.tencent.com/g' /etc/apk/repositories

RUN apk update && apk add gettext
RUN ln -sf /dev/stdout /var/log/nginx/access.log && \
    ln -sf /dev/stderr /var/log/nginx/error.log

# clean useless files
RUN cd /var/www && rm -r localhost
# cp nginx files
COPY custom-configs/default /etc/nginx/conf.d/default.conf
COPY custom-configs/30-render /etc/cont-init.d/30-render
COPY --from=0 /app/dist/ /var/www/
