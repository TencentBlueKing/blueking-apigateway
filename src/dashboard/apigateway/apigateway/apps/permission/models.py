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
import json
from typing import Dict, List, Optional

from django.db import models
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from apigateway.apps.permission import managers
from apigateway.apps.permission.constants import (
    DEFAULT_PERMISSION_EXPIRE_DAYS,
    RENEWABLE_EXPIRE_DAYS,
    ApplyStatusEnum,
    GrantDimensionEnum,
    GrantTypeEnum,
    PermissionApplyExpireDaysEnum,
)
from apigateway.common.mixins.models import TimestampedModelMixin
from apigateway.core.models import Gateway, Resource
from apigateway.utils.time import NeverExpiresTime, to_datetime_from_now, to_seconds


def generate_expire_time() -> datetime.datetime:
    return to_datetime_from_now(days=DEFAULT_PERMISSION_EXPIRE_DAYS)


class AppAPIPermission(TimestampedModelMixin):
    """
    蓝鲸应用访问网关权限
    网关对应用授权网关所有资源的访问权限
    """

    bk_app_code = models.CharField(max_length=32, db_index=True)
    gateway = models.ForeignKey(Gateway, db_column="api_id", on_delete=models.CASCADE)
    expires = models.DateTimeField(default=generate_expire_time, blank=True, null=True, help_text=_("默认过期时间为180天"))

    objects = managers.AppAPIPermissionManager()

    def __str__(self):
        return f"<AppAPIPermission: {self.id}>"

    class Meta:
        verbose_name = _("蓝鲸应用访问网关权限")
        verbose_name_plural = _("蓝鲸应用访问网关权限")
        unique_together = ("bk_app_code", "gateway")
        db_table = "permission_app_api"

    @property
    def expires_in(self) -> Optional[int]:
        """返回过期时间"""
        if self.expires and not NeverExpiresTime.is_never_expired(self.expires):
            return int((self.expires - timezone.now()).total_seconds())

        return None

    @property
    def has_expired(self) -> bool:
        if self.expires_in is None:
            return False

        return self.expires_in <= 0

    @property
    def expires_display(self) -> Optional[datetime.datetime]:
        if NeverExpiresTime.is_never_expired(self.expires):
            return None

        return self.expires

    @property
    def allow_apply_permission(self):
        if self.expires_in is not None and self.expires_in < to_seconds(days=RENEWABLE_EXPIRE_DAYS):
            return True

        return False


class AppResourcePermission(TimestampedModelMixin):
    """
    蓝鲸应用访问网关资源权限
    """

    bk_app_code = models.CharField(max_length=32, db_index=True)
    gateway = models.ForeignKey(Gateway, db_column="api_id", on_delete=models.CASCADE)
    # NOTE: resource 若为 ForeignKey，若资源删除，则权限被级联删除，但是发布版本中的资源配置存在，会导致应用无权限访问对应资源
    resource_id = models.IntegerField(blank=False, null=False, db_index=True)
    expires = models.DateTimeField(default=generate_expire_time, blank=True, null=True, help_text=_("默认过期时间为180天"))
    grant_type = models.CharField(max_length=16, choices=GrantTypeEnum.choices(), db_index=True)

    objects = managers.AppResourcePermissionManager()

    def __str__(self):
        return f"<AppResourcePermission: {self.id}>"

    class Meta:
        verbose_name = _("蓝鲸应用访问资源权限")
        verbose_name_plural = _("蓝鲸应用访问资源权限")
        unique_together = ("bk_app_code", "gateway", "resource_id")
        db_table = "permission_app_resource"

    @property
    def expires_in(self) -> Optional[int]:
        """返回过期时间"""
        if self.expires and not NeverExpiresTime.is_never_expired(self.expires):
            return int((self.expires - timezone.now()).total_seconds())

        return None

    @property
    def has_expired(self) -> bool:
        expires_in = self.expires_in
        if expires_in is None:
            return False

        return expires_in <= 0

    def will_expired_in(self, seconds: int) -> bool:
        expires_in = self.expires_in
        if expires_in is None:
            return False

        return expires_in <= seconds

    @cached_property
    def resource(self) -> Optional[Resource]:
        return Resource.objects.filter(gateway_id=self.gateway_id, id=self.resource_id).first()


class AppPermissionApply(TimestampedModelMixin):
    """
    应用访问资源权限申请单，申请中的申请单
    """

    bk_app_code = models.CharField(max_length=32, db_index=True)
    applied_by = models.CharField(max_length=32)
    gateway = models.ForeignKey(Gateway, db_column="api_id", on_delete=models.CASCADE)
    _resource_ids = models.TextField(db_column="resource_ids")
    reason = models.CharField(max_length=512, blank=True, default="")
    expire_days = models.IntegerField(default=PermissionApplyExpireDaysEnum.SIX_MONTH.value)
    grant_dimension = models.CharField(
        max_length=32,
        choices=GrantDimensionEnum.get_choices(),
        default=GrantDimensionEnum.RESOURCE.value,
        db_index=True,
    )
    status = models.CharField(max_length=16, choices=ApplyStatusEnum.get_choices(), db_index=True)
    apply_record_id = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"<AppPermissionApply: {self.id}>"

    class Meta:
        verbose_name = _("蓝鲸应用访问资源权限待审批申请单")
        verbose_name_plural = _("蓝鲸应用访问资源权限待审批申请单")
        db_table = "permission_app_apply"

    @property
    def resource_ids(self) -> List[int]:
        if not self._resource_ids:
            return []
        return [int(i) for i in self._resource_ids.split(";")]

    @resource_ids.setter
    def resource_ids(self, data: List[int]):
        self._resource_ids = ";".join([str(i) for i in data])


class AppPermissionRecord(models.Model):
    """
    应用访问资源权限申请单
    """

    bk_app_code = models.CharField(max_length=32, db_index=True)
    applied_by = models.CharField(max_length=32)
    applied_time = models.DateTimeField()
    reason = models.CharField(max_length=512, blank=True, default="")
    expire_days = models.IntegerField(default=PermissionApplyExpireDaysEnum.SIX_MONTH.value)
    handled_by = models.CharField(max_length=32, blank=True, default="")
    handled_time = models.DateTimeField(blank=True, null=True)
    gateway = models.ForeignKey(Gateway, db_column="api_id", on_delete=models.CASCADE)
    _resource_ids = models.TextField(db_column="resource_ids", blank=True, default="")
    _handled_resource_ids = models.TextField(db_column="handled_resource_ids", blank=True, default="{}")
    grant_dimension = models.CharField(
        max_length=32,
        choices=GrantDimensionEnum.get_choices(),
        default=GrantDimensionEnum.RESOURCE.value,
        db_index=True,
    )
    status = models.CharField(max_length=16, choices=ApplyStatusEnum.get_choices(), db_index=True)
    comment = models.CharField(max_length=512, blank=True, default="")

    objects = managers.AppPermissionRecordManager()

    def __str__(self):
        return f"<AppPermissionRecord: {self.id}>"

    class Meta:
        verbose_name = _("蓝鲸应用访问资源权限申请单")
        verbose_name_plural = _("蓝鲸应用访问资源权限申请单")
        db_table = "permission_app_record"

    @property
    def resource_ids(self) -> List[int]:
        if not self._resource_ids:
            return []
        return [int(i) for i in self._resource_ids.split(";")]

    @resource_ids.setter
    def resource_ids(self, data: List[int]):
        self._resource_ids = ";".join([str(i) for i in data])

    @property
    def handled_resource_ids(self):
        try:
            return json.loads(self._handled_resource_ids or "{}")
        except Exception:
            return {}

    @handled_resource_ids.setter
    def handled_resource_ids(self, data: Dict):
        self._handled_resource_ids = json.dumps(data)


class AppPermissionApplyStatus(TimestampedModelMixin):
    """
    应用访问资源权限申请状态：申请中
    """

    apply = models.ForeignKey(AppPermissionApply, on_delete=models.CASCADE, blank=True, null=True)
    bk_app_code = models.CharField(max_length=32, db_index=True)
    gateway = models.ForeignKey(Gateway, db_column="api_id", on_delete=models.CASCADE, blank=True, null=True)
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, blank=True, null=True)
    grant_dimension = models.CharField(
        max_length=32,
        choices=GrantDimensionEnum.get_choices(),
        default=GrantDimensionEnum.RESOURCE.value,
        db_index=True,
    )
    status = models.CharField(max_length=16, choices=ApplyStatusEnum.get_choices())

    objects = managers.AppPermissionApplyStatusManager()

    def __str__(self):
        return f"<AppPermissionApplyStatus: {self.id}>"

    class Meta:
        verbose_name = _("蓝鲸应用访问资源权限申请状态")
        verbose_name_plural = _("蓝鲸应用访问资源权限申请状态")
        unique_together = ("bk_app_code", "gateway", "resource")
        db_table = "permission_app_apply_status"
