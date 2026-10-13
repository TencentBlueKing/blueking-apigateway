# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
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

import pytest
from celery import Celery, current_app
from django.conf import settings
from django_celery_beat.models import PeriodicTask
from django_celery_beat.schedulers import DatabaseScheduler, ModelEntry


@pytest.mark.django_db
@pytest.mark.parametrize("existing_task", [False, True])
def test_publish_event_cleanup_is_disabled_on_scheduler_startup(existing_task):
    task_name = "delete_old_publish_events"
    task_config = settings.CELERY_BEAT_SCHEDULE[task_name]
    original_app = current_app._get_current_object()
    with Celery("test_publish_event_cleanup", set_as_current=False) as app:
        app.conf.update(
            beat_schedule={task_name: task_config},
            timezone=settings.CELERY_TIMEZONE,
            result_expires=None,
        )
        if existing_task:
            ModelEntry.from_entry(task_name, app=app, **{**task_config, "enabled": True})

        for _ in range(2):
            scheduler = DatabaseScheduler(app=app)
            try:
                assert not PeriodicTask.objects.get(name=task_name).enabled
                assert task_name not in scheduler.schedule
            finally:
                scheduler.close()

    assert current_app._get_current_object() is original_app
