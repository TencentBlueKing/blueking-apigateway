# npm part
FROM node:20.19.4-bookworm AS builder

WORKDIR /app
COPY . /app

ENV NODE_OPTIONS=--max_old_space_size=8192

RUN npm install -g npm@10.8.2
RUN npm install --force
RUN npm run build-only

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
COPY --from=builder /app/dist/ /var/www/
