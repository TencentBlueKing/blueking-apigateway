#!/usr/bin/env bash
set -euo pipefail

envfile="${BK_HOME}/etc/bk_apigateway/bk_apigateway.env"
if [ -f "${envfile}" ]; then
    set -a
    source "${envfile}"
    set +a
fi

worker_concurrency="${BK_APIGW_SDK_WORKER_CONCURRENCY:-2}"
queue="${BK_APIGW_SDK_CELERY_QUEUE:-sdk.generate}"
command=(celery -A apigateway.apigateway worker -l INFO -c "${worker_concurrency}" -Q "${queue}")
exec "${command[@]}"
