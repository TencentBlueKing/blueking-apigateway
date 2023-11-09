ARG IMAGE="node"
ARG TAG="14.17.6"

FROM ${IMAGE}:${TAG} AS builder

COPY . /app

WORKDIR /app

# ARG NPM_REGISTRY="https://registry.npmjs.org/"

ARG NODE_ENV=production
ENV NODE_ENV=${NODE_ENV}

ARG EDITION=ee
ENV APP_VERSION=${EDITION}

# RUN ls . && cat index.html &&exit 1
# RUN npm install --no-optional --registry="${NPM_REGISTRY:?}"
# RUN npm install && npm run build:${EDITION}
RUN npm i && ls ./node_modules | wc -l && exit 1

# FROM ${IMAGE}:${TAG}

# RUN useradd blueking --home-dir /app --create-home

# COPY --from=builder --chown=blueking /app/.babelrc /app/.babelrc
# COPY --from=builder --chown=blueking /app/build /app/build
# COPY --from=builder --chown=blueking /app/dist /app/dist
# COPY --from=builder --chown=blueking /app/node_modules /app/node_modules
# COPY --from=builder --chown=blueking /app/package.json /app/package.json

# USER blueking
# WORKDIR /app

CMD [ "npm", "run", "server" ]
