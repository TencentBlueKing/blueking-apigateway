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
from datetime import timedelta

from celery import shared_task
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.db.models import Count
from django.utils import timezone

from apigateway.apps.api_debug.models import APIDebugHistory
from apigateway.apps.monitor.models import AlarmRecord
from apigateway.apps.support.models import ReleasedResourceDoc, ResourceDocVersion
from apigateway.core.constants import ResourceVersionSchemaEnum
from apigateway.core.models import PublishEvent, Release, ReleasedResource, ResourceVersion

logger = logging.getLogger(__name__)


@shared_task(ignore_result=True)
def delete_old_publish_events():
    """
    Deletes publish events that are more than a year old.
    """
    deleted_end_time = timezone.now() - timedelta(days=settings.CLEAN_TABLE_INTERVAL_DAYS)
    logger.info("deleting publish events older than %s", deleted_end_time)

    deleted_count, _ = PublishEvent.objects.filter(created_time__lt=deleted_end_time).delete()

    logger.info("deleted %s publish events older than %s", deleted_count, deleted_end_time)


@shared_task(ignore_result=True)
def delete_old_resource_doc_version_records():
    """
    Deletes resource_doc_version that are more than CLEAN_TABLE_INTERVAL_DAYS.
    """
    logger.info("begin clean resource_doc_version old records")

    delete_end_time = timezone.now() - timedelta(days=settings.CLEAN_TABLE_INTERVAL_DAYS)

    # 找到所有 CLEAN_TABLE_INTERVAL_DAYS 以前的 ResourceVersion
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


@shared_task(ignore_result=True)
def delete_old_debug_history():
    """
    清理在线调试 6 个月前的调用历史
    """
    logger.info("begin clean debug old history")

    # 获取 6 个月的前一天日期
    delete_end_time = timezone.now() - relativedelta(months=6) - relativedelta(days=1)

    # 每次删除 1000 条记录
    debug_history_to_delete = APIDebugHistory.objects.filter(created_time__lte=delete_end_time)[:1000]

    # 要删除的 ID 列表
    ids_to_delete = list(debug_history_to_delete.values_list("id", flat=True))

    count, _ = APIDebugHistory.objects.filter(id__in=ids_to_delete).delete()

    logger.info("deleted %s debug history older than %s", count, delete_end_time)


@shared_task(ignore_result=True)
def delete_old_alarm_records():
    """清理 6 个月前的告警记录"""
    logger.info("begin clean alarm old records")
    delete_end_time = timezone.now() - relativedelta(months=6) - relativedelta(days=1)

    alarm_records_to_delete = AlarmRecord.objects.filter(created_time__lte=delete_end_time)[:1000]
    ids_to_delete = list(alarm_records_to_delete.values_list("id", flat=True))

    count, _ = AlarmRecord.objects.filter(id__in=ids_to_delete).delete()

    logger.info("deleted %s alarm records older than %s", count, delete_end_time)


@shared_task(ignore_result=True)
def delete_legacy_resource_version():
    """清理旧的 (v1) 资源版本
    1. gateway has more than 30 resource versions
    2. resource version created time < 3 years ago
    3. resource version's schema version is v1
    4. resource version is not used in Release

    当前风险较小，因为只处理大于 30 个版本的对应 v1 版本的 resource version
    - 如果想要彻底删掉所有的 v1 版本 resource version，需要重新评估改动这个清理任务的逻辑
    - 如果要清理 v2 版本的 resource version，需要重新评估风险，制定清理策略，另外写一个清理任务
    """

    logger.info("begin clean legacy resource version")

    delete_end_time = timezone.now() - relativedelta(years=3) - relativedelta(days=1)

    # having count > 30
    gateway_ids = (
        ResourceVersion.objects.values("gateway_id")
        .annotate(count=Count("id"))
        .filter(count__gt=30)
        .values_list("gateway_id", flat=True)
    )

    legacy_resource_version_ids = list(
        ResourceVersion.objects.filter(
            gateway_id__in=gateway_ids,
            schema_version=ResourceVersionSchemaEnum.V1.value,
            created_time__lt=delete_end_time,
        ).values_list("id", flat=True)
    )

    # check not used in Release
    used_legacy_resource_version_ids = list(
        Release.objects.filter(resource_version_id__in=legacy_resource_version_ids).values_list(
            "resource_version_id", flat=True
        )
    )

    # only get the top 30 for each time
    to_delete_legacy_resource_version_ids = list(
        set(legacy_resource_version_ids) - set(used_legacy_resource_version_ids)
    )
    to_delete_legacy_resource_version_ids = sorted(to_delete_legacy_resource_version_ids)[:30]

    if not to_delete_legacy_resource_version_ids:
        logger.info("no legacy resource version to delete, done")
        return

    logger.info("to delete legacy resource version ids: %s", to_delete_legacy_resource_version_ids)

    # delete the related records
    ReleasedResourceDoc.objects.filter(resource_version_id__in=to_delete_legacy_resource_version_ids).delete()
    ReleasedResource.objects.filter(resource_version_id__in=to_delete_legacy_resource_version_ids).delete()

    # delete the resource version
    ResourceVersion.objects.filter(id__in=to_delete_legacy_resource_version_ids).delete()
