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
import datetime
from typing import List, Optional

from django.db import models

from apigateway.apps.permission.constants import (
    DEFAULT_PERMISSION_EXPIRE_DAYS,
    ApplyStatusEnum,
    GrantDimensionEnum,
    GrantTypeEnum,
)
from apigateway.apps.permission.utils import calculate_expires
from apigateway.utils.time import now_datetime, to_datetime_from_now


class AppAPIPermissionManager(models.Manager):
    def filter_public_permission_by_app(self, bk_app_code: str):
        return self.filter(bk_app_code=bk_app_code, api__is_public=True)

    def save_permissions(self, gateway, resource_ids=None, bk_app_code=None, grant_type=None, expire_days=None):
        self.update_or_create(
            api=gateway,
            bk_app_code=bk_app_code,
            defaults={
                "expires": calculate_expires(expire_days),
            },
        )

    def renew_by_ids(self, gateway, ids, expires=DEFAULT_PERMISSION_EXPIRE_DAYS):
        expires = to_datetime_from_now(days=expires)
        self.filter(api=gateway, id__in=ids, expires__lt=expires).update(
            expires=expires,
            updated_time=now_datetime(),
        )


class AppResourcePermissionManager(models.Manager):
    def filter_public_permission_by_app(self, bk_app_code: str):
        return self.filter(bk_app_code=bk_app_code, api__is_public=True)

    def renew_by_ids(self, gateway, ids, expires=DEFAULT_PERMISSION_EXPIRE_DAYS, grant_type=GrantTypeEnum.RENEW.value):
        expires = to_datetime_from_now(days=expires)
        self.filter(api=gateway, id__in=ids, expires__lt=expires).update(
            expires=expires,
            grant_type=grant_type,
        )

    def renew_by_resource_ids(
        self,
        gateway,
        bk_app_code,
        resource_ids,
        grant_type=GrantTypeEnum.RENEW.value,
        expire_days=DEFAULT_PERMISSION_EXPIRE_DAYS,
    ):
        queryset = self.filter(api=gateway, bk_app_code=bk_app_code, resource_id__in=resource_ids)
        # 仅续期权限期限小于待续期时间的权限
        expires = to_datetime_from_now(days=expire_days)
        queryset = queryset.filter(expires__lt=expires)
        queryset.update(
            expires=expires,
            grant_type=grant_type,
        )

    def renew_not_expired_permissions(
        self,
        gateway_id: int,
        bk_app_code: str,
        resource_ids: List[int],
        grant_type=GrantTypeEnum.RENEW.value,
        expire_days=DEFAULT_PERMISSION_EXPIRE_DAYS,
    ):
        """仅续期未过期且权限期限小于待续期时间的权限"""
        expires = to_datetime_from_now(days=expire_days)
        queryset = self.filter(
            api_id=gateway_id,
            bk_app_code=bk_app_code,
            resource_id__in=resource_ids,
            expires__range=(now_datetime(), expires),
        )
        queryset.update(
            expires=expires,
            grant_type=grant_type,
        )

    def save_permissions(self, gateway, resource_ids, bk_app_code, grant_type, expire_days=None):
        expires = calculate_expires(expire_days)

        # 此处不再重复校验 resource_id 属于网关
        # - 在接口 serializer 处校验 resource_id 是否有效
        # - 对于已删除，但线上版本中包含的资源，也无法通过 Resource 模型中数据判断 resource_id 是否有效
        for resource_id in resource_ids:
            self.update_or_create(
                api=gateway,
                resource_id=resource_id,
                bk_app_code=bk_app_code,
                defaults={
                    "expires": expires,
                    "grant_type": grant_type,
                    "created_time": now_datetime(),
                    "updated_time": now_datetime(),
                },
            )

    def sync_from_gateway_permission(self, gateway, bk_app_code, resource_ids):
        from apigateway.apps.permission.models import AppAPIPermission

        api_perm = AppAPIPermission.objects.filter(bk_app_code=bk_app_code, api_id=gateway.id).first()
        if not api_perm or api_perm.has_expired:
            return

        has_perm_resource_ids = list(
            self.filter(bk_app_code=bk_app_code, api_id=gateway.id, resource_id__in=resource_ids).values_list(
                "resource_id", flat=True
            )
        )

        for resource_id in set(resource_ids) - set(has_perm_resource_ids):
            # 此处使用 get_or_create, 其它功能同时添加权限时，可跳过此处的同步
            self.get_or_create(
                api=gateway,
                resource_id=resource_id,
                bk_app_code=bk_app_code,
                defaults={
                    "expires": api_perm.expires,
                    "grant_type": GrantTypeEnum.SYNC.value,
                },
            )

    def get_permission_or_none(self, gateway, resource_id, bk_app_code):
        try:
            return self.get(api=gateway, resource_id=resource_id, bk_app_code=bk_app_code)
        except self.model.DoesNotExist:
            return None


class AppPermissionRecordManager(models.Manager):
    def save_record(
        self,
        record_id,
        gateway,
        bk_app_code,
        applied_by,
        applied_time,
        handled_by,
        resource_ids,
        handled_resource_ids,
        status,
        comment,
        reason,
        expire_days,
        grant_dimension,
    ):
        if not record_id:
            return self.create(
                api=gateway,
                bk_app_code=bk_app_code,
                applied_by=applied_by,
                applied_time=applied_time,
                handled_by=handled_by,
                handled_time=now_datetime(),
                resource_ids=resource_ids,
                handled_resource_ids=handled_resource_ids,
                status=status,
                comment=comment,
                reason=reason,
                expire_days=expire_days,
                grant_dimension=grant_dimension,
            )

        record = self.get(id=record_id)
        record.handled_by = handled_by
        record.handled_time = now_datetime()
        record.handled_resource_ids = handled_resource_ids
        record.status = status
        record.comment = comment
        record.save()
        return record

    def filter_record(
        self,
        queryset,
        bk_app_code: str = "",
        applied_by: str = "",
        applied_time_start: Optional[datetime.datetime] = None,
        applied_time_end: Optional[datetime.datetime] = None,
        status: str = "",
        query: str = "",
        order_by: str = "",
    ):
        if bk_app_code:
            queryset = queryset.filter(bk_app_code=bk_app_code)

        if applied_by:
            queryset = queryset.filter(applied_by=applied_by)

        if applied_time_start and applied_time_end:
            queryset = queryset.filter(applied_time__range=(applied_time_start, applied_time_end))

        if status:
            queryset = queryset.filter(status=status)

        if query:
            queryset = queryset.filter(api__name__icontains=query)

        if order_by:
            queryset = queryset.order_by(order_by)

        return queryset


class AppPermissionApplyStatusManager(models.Manager):
    def is_permission_pending_by_gateway(self, gateway_id: int, bk_app_code: str) -> bool:
        return self.filter(
            bk_app_code=bk_app_code,
            api_id=gateway_id,
            grant_dimension=GrantDimensionEnum.API.value,
            status=ApplyStatusEnum.PENDING.value,
        ).exists()
