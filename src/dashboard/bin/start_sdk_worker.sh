#!/usr/bin/env bash
#
# TencentBlueKing is pleased to support the open source community by making
# BlueKing - APIGateway available.
# Copyright (C) Tencent. All rights reserved.
# Licensed under the MIT License (the "License"); you may not use this file except
# in compliance with the License. You may obtain a copy of the License at
#
#     http://opensource.org/licenses/MIT
#
# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the License for the specific language governing permissions and
# limitations under the License.
#
# We undertake not to change the open source license (MIT license) applicable
# to the current version of the project delivered to anyone in the future.
#
set -euo pipefail

envfile="${BK_HOME}/etc/bk_apigateway/bk_apigateway.env"
if [ -f "${envfile}" ]; then
    set -a
    source "${envfile}"
    set +a
fi

python manage.py validate_sdk_worker

worker_concurrency="${BK_APIGW_SDK_WORKER_CONCURRENCY:-2}"
queue="${BK_APIGW_SDK_CELERY_QUEUE:-sdk.generate}"
command=(celery -A apigateway.apigateway worker -l INFO -c "${worker_concurrency}" -Q "${queue}")
exec "${command[@]}"
