# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2017 THL A29 Limited, a Tencent company. All rights reserved.
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
from celery.schedules import crontab

# celery configuration
CELERY_TIMEZONE = "Asia/Shanghai"
CELERY_ENABLE_UTC = True
CELERY_TASK_IGNORE_RESULT = True
# celery 复用 django 日志配置
# - https://docs.celeryq.dev/en/v4.3.0/userguide/configuration.html#std:setting-worker_hijack_root_logger
CELERY_WORKER_HIJACK_ROOT_LOGGER = False

CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"

CELERY_IMPORTS = (
    "apigateway.apps.monitor.tasks",
    "apigateway.apps.metrics.tasks",
    "apigateway.apps.permission.tasks",
    "apigateway.legacy_esb.tasks",
    "apigateway.apps.esb.component.tasks",
    "apigateway.controller.tasks",
)

CELERY_BEAT_SCHEDULE = {
    # "add-every-minute": {
    #     "task": "apigateway.apps.monitor.tasks.add",
    #     "schedule": crontab(),
    # },
    "apigateway.controller.tasks.clean_task.delete_old_publish_events": {
        "task": "apigateway.controller.clean_task.delete_old_publish_events",
        "schedule": crontab(day_of_week="monday", hour=0, minute=0),
    },
}

CELERY_CHORD_UNLOCK_MAX_RETRIES = 60
CELERY_BROKER_HEARTBEAT = 0
