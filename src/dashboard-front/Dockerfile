# npm part
FROM node:20.19.4-bookworm AS builder

WORKDIR /app
COPY package.json package-lock.json yarn.lock /app/

ENV NODE_OPTIONS=--max_old_space_size=8192

RUN npm install -g npm@11.5.2
RUN npm install --force

COPY . /app
RUN npm run build-only

# nginx part
FROM tencentos/tencentos4-minimal:4.4-v20250922

RUN dnf -y install nginx && \
    dnf clean all && \
    ln -sf /dev/stdout /var/log/nginx/access.log && \
    ln -sf /dev/stderr /var/log/nginx/error.log

# cp nginx files
COPY bin/default.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist/ /var/www/

COPY bin/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
