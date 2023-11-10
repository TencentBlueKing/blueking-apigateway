ARG IMAGE="node"
ARG TAG="14.17.6"

FROM ${IMAGE}:${TAG} AS builder

WORKDIR /app
COPY . /app


# ARG NPM_REGISTRY="https://registry.npmjs.org/"


ARG EDITION=ee
ENV APP_VERSION=${EDITION}

# RUN npm install --no-optional --registry="${NPM_REGISTRY:?}"
RUN npm config set registry http://mirrors.cloud.tencent.com/npm/
RUN npm install
RUN npm run build:${EDITION:?}

FROM ${IMAGE}:${TAG}

ARG NODE_ENV=production
ENV NODE_ENV=${NODE_ENV}

RUN useradd blueking --home-dir /app --create-home

COPY --from=builder --chown=blueking /app/.babelrc /app/.babelrc
COPY --from=builder --chown=blueking /app/build /app/build
COPY --from=builder --chown=blueking /app/dist /app/dist
COPY --from=builder --chown=blueking /app/node_modules /app/node_modules
COPY --from=builder --chown=blueking /app/package.json /app/package.json

USER blueking
WORKDIR /app

CMD [ "npm", "run", "server" ]