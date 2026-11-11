# pnpm part
FROM node:24.22.1-bookworm-slim AS builder

WORKDIR /app
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml /app/

ENV NODE_OPTIONS=--max_old_space_size=8192

# pnpm 版本取自 package.json 的 packageManager，与本地、CI 保持一致
RUN npm install -g "$(node -p "require('./package.json').packageManager")"
RUN pnpm install --frozen-lockfile

COPY . /app
RUN pnpm run build

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
