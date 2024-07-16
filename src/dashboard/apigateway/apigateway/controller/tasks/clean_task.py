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

from apigateway.apps.support.models import ResourceDocVersion
from apigateway.core.models import PublishEvent, Release

logger = logging.getLogger(__name__)


@shared_task(ignore_result=True)
def delete_old_publish_events():
    """
    Deletes publish events that are more than a year old.
    """
    deleted_end_time = datetime.now() - timedelta(days=settings.CLEAN_TABLE_INTERVAL_DAYS)
    logger.info("deleting publish events older than %s", deleted_end_time)

    deleted_count, _ = PublishEvent.objects.filter(created_time__lt=deleted_end_time).delete()

    logger.info("deleted %s publish events older than %s", deleted_count, deleted_end_time)


@shared_task(ignore_result=True)
def delete_old_resource_doc_version_records():
    """
    Deletes resource_doc_version that are more than CLEAN_TABLE_INTERVAL_DAYS.
    """
    logger.info("begin clean resource_doc_version old records")

    delete_end_time = datetime.now() - timedelta(days=settings.CLEAN_TABLE_INTERVAL_DAYS)

    # 找到所有 CLEAN_TABLE_INTERVAL_DAYS以前的 ResourceVersion
    old_resource_doc_versions = ResourceDocVersion.objects.filter(created_time__lt=delete_end_time)

    # 找到所有在 Release 中引用的 ResourceVersion
    referenced_resource_versions = Release.objects.values_list("resource_version_id", flat=True)

    # 过滤掉在 Release 中使用的 ResourceVersion
    resource_doc_versions_to_delete = old_resource_doc_versions.exclude(
        resource_version_id__in=referenced_resource_versions
    )

    # 每次最多删除 1000 条记录
    resource_doc_versions_to_delete = resource_doc_versions_to_delete[:1000]

    # 获取要删除的对象的 ID 列表
    ids_to_delete = list(resource_doc_versions_to_delete.values_list("id", flat=True))

    count, _ = ResourceDocVersion.objects.filter(id__in=ids_to_delete).delete()

    logger.info("deleted %s resource_doc_version older than %s", count, delete_end_time)
