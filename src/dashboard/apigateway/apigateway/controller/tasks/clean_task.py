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
import logging
from datetime import datetime, timedelta

from celery import shared_task
from django.conf import settings

from apigateway.core.models import PublishEvent

logger = logging.getLogger(__name__)


@shared_task(ignore_result=True)
def delete_old_publish_events():
    """
    Deletes publish events that are more than a year old.
    """
    deleted_end_time = datetime.now() - timedelta(days=settings.CLEAN_PUBLISH_EVENT_INTERVAL_DAYS)
    logger.info(f"deleting publish events older than {deleted_end_time}")

    deleted_count, _ = PublishEvent.objects.filter(created_at__lt=deleted_end_time).delete()

    logger.info(f"deleted {deleted_count} publish events older than {deleted_end_time}")
