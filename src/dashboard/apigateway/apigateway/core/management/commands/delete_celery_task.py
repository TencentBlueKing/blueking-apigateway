# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2025 Tencent. All rights reserved.
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
import logging

from django.core.management.base import BaseCommand
from django.db import connection

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Delete a Celery task from the database"

    def add_arguments(self, parser):
        parser.add_argument("--task-name", dest="task_name", required=True, help="Name of the Celery task to delete")

    def handle(self, task_name: str, *args, **kwargs):
        # 查询任务是否存在
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM django_celery_beat_periodictask WHERE name=%s", [task_name])
            task_exists = cursor.fetchone()[0]

        if not task_exists:
            logger.info("Task %s doesn't exist ", task_name)
            return

        # 构建 SQL 语句
        sql = "DELETE FROM django_celery_beat_periodictask WHERE name=%s"

        # 执行 SQL 语句
        with connection.cursor() as cursor:
            cursor.execute(sql, [task_name])

        logger.info("Task %s deleted successfully. ", task_name)
