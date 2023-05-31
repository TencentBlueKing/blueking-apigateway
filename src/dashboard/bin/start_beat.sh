#!/usr/bin/env bash
set -e

envfile="${BK_HOME}/etc/bk_apigateway/bk_apigateway.env"
if [ -f "${envfile}" ]; then
    set -a
    source "${envfile}"
    set +a
fi

command="celery -A apigateway.apigateway beat --pidfile= -l INFO"
exec bash -c "$command"