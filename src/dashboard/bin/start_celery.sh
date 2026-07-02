#!/usr/bin/env bash
set -e

envfile="${BK_HOME}/etc/bk_apigateway/bk_apigateway.env"
if [ -f "${envfile}" ]; then
    set -a
    source "${envfile}"
    set +a
fi

celery_worker_concurrency="${BK_APIGW_CELERY_WORKER_CONCURRENCY:-12}"
command="celery -A apigateway.apigateway worker -l INFO -c ${celery_worker_concurrency}"
exec bash -c "$command"
