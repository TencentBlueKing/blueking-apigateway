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
import os

from celery import Celery
from celery.signals import worker_init

# set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "apigateway.settings")

app = Celery("apigateway")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


@worker_init.connect
def limit_chord_unlock_tasks(sender, **kwargs):
    # celery 使用这个内置任务来轮转编排任务的状态
    # 但是一些异常情况下，前置任务的状态丢失或没有更新，会导致这个任务一直重试，无法结束
    # 因此设置一个最大重试次数，强制让等待过长的任务结束
    task = sender.app.tasks["celery.chord_unlock"]
    if task.max_retries is None:
        retries = getattr(sender.app.conf, "CHORD_UNLOCK_MAX_RETRIES", None)
        task.max_retries = retries
