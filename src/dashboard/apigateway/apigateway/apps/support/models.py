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
import json
from typing import ClassVar

from django.db import models
from django.utils.translation import gettext_lazy as _
from jsonfield import JSONField

from apigateway.apps.support.constants import (
    SDK_GENERATION_LANGUAGE_VALUES,
    DocLanguageEnum,
    DocSourceEnum,
    DocTypeEnum,
    ProgrammingLanguageEnum,
    SDKArtifactTypeEnum,
    SDKDistributorEnum,
    SDKGenerationStatusEnum,
)
from apigateway.apps.support.managers import (
    GatewaySDKManager,
    ReleasedResourceDocManager,
    ResourceDocVersionManager,
)
from apigateway.common.mixins.models import ConfigModelMixin, OperatorModelMixin, TimestampedModelMixin
from apigateway.core.models import Gateway, ResourceVersion
from apigateway.schema.models import Schema
from apigateway.utils import time


class ResourceDoc(TimestampedModelMixin, OperatorModelMixin):
    gateway = models.ForeignKey(Gateway, db_column="api_id", on_delete=models.CASCADE, null=True)
    resource_id = models.IntegerField(blank=False, null=False, db_index=True)
    type = models.CharField(max_length=32, choices=DocTypeEnum.get_choices())
    language = models.CharField(
        max_length=32,
        choices=DocLanguageEnum.get_choices(),
        default=DocLanguageEnum.ZH.value,
        db_index=True,
    )
    source = models.CharField(
        max_length=32, choices=DocSourceEnum.get_choices(), default=DocSourceEnum.CUSTOM.value, db_index=True
    )
    content = models.TextField(blank=True, null=True, default="")

    def __self__(self):
        return f"<ResourceDoc: {self.resource}>"

    class Meta:
        verbose_name = _("资源文档")
        verbose_name_plural = _("资源文档")
        db_table = "support_resource_doc"
        unique_together = ("gateway", "resource_id", "language")

    def snapshot(self, as_dict=False):
        data = {
            "resource_id": self.resource_id,
            "type": self.type,
            "language": self.language,
            "content": self.content,
            "created_time": time.format(self.created_time),
            "updated_time": time.format(self.updated_time),
        }
        if as_dict:
            return data
        return json.dumps(data)


class ResourceDocVersion(TimestampedModelMixin, OperatorModelMixin):
    gateway = models.ForeignKey(Gateway, db_column="api_id", on_delete=models.CASCADE)
    resource_version = models.ForeignKey(ResourceVersion, on_delete=models.CASCADE)
    _data = models.TextField(db_column="data")

    objects: ClassVar[ResourceDocVersionManager] = ResourceDocVersionManager()

    def __str__(self):
        return f"<ResourceDocVersion: {self.gateway}/{self.resource_version}>"

    class Meta:
        verbose_name = "ResourceDocVersion"
        verbose_name_plural = "ResourceDocVersion"
        db_table = "support_resource_doc_version"
        unique_together = ("gateway", "resource_version")

    @property
    def data(self) -> list:
        return json.loads(self._data)

    @data.setter
    def data(self, data: list):
        self._data = json.dumps(data)


class ReleasedResourceDoc(TimestampedModelMixin):
    """资源已发布的资源文档"""

    gateway = models.ForeignKey(Gateway, db_column="api_id", on_delete=models.CASCADE)
    resource_version_id = models.IntegerField(blank=False, null=False, db_index=True)
    resource_id = models.IntegerField(blank=False, null=False, db_index=True)
    language = models.CharField(
        max_length=32,
        choices=DocLanguageEnum.get_choices(),
        default=DocLanguageEnum.ZH.value,
        db_index=True,
    )
    data = JSONField(help_text="resource doc data in resource doc version")

    objects: ClassVar[ReleasedResourceDocManager] = ReleasedResourceDocManager()

    def __str__(self):
        return f"<ReleasedResourceDoc: {self.id}"

    class Meta:
        verbose_name = "ReleasedResourceDoc"
        verbose_name_plural = "ReleasedResourceDoc"
        unique_together = ("gateway", "resource_version_id", "resource_id", "language")
        db_table = "support_released_resource_doc"


class GatewaySDK(ConfigModelMixin):
    gateway = models.ForeignKey(Gateway, db_column="api_id", on_delete=models.CASCADE)
    resource_version = models.ForeignKey(ResourceVersion, on_delete=models.CASCADE, blank=True, null=True)
    name = models.CharField(max_length=128, blank=True, default="", help_text=_("SDK 名称"))
    url = models.TextField(blank=True, default="", help_text=_("下载地址"))
    language = models.CharField(max_length=32, choices=ProgrammingLanguageEnum.get_choices())
    version_number = models.CharField(max_length=64)
    include_private_resources = models.BooleanField(default=False)
    # FIXME: remove those fields
    filename = models.CharField(max_length=128, help_text=_("SDK 文件名, 废弃"))
    is_public_latest = models.BooleanField(default=False, db_index=True, help_text=_("废弃"))

    # is_recommended 说明这个版本是被推荐的，隐含了2个前提
    # 1. 这个版本是公开的
    # 2. 这个版本是最新的
    is_recommended = models.BooleanField(default=False, db_index=True)

    # FIXME: is_public is always True, no private SDK in the future
    # is_public 说明这个版本是公开且发布过的
    is_public = models.BooleanField(default=False, db_index=True)

    schema = models.ForeignKey(Schema, on_delete=models.PROTECT, null=True)

    objects: ClassVar[GatewaySDKManager] = GatewaySDKManager()

    def __self__(self):
        return f"<APISDK: {self.gateway}>"

    class Meta:
        verbose_name = _("网关SDK")
        verbose_name_plural = _("网关SDK")
        db_table = "support_api_sdk"
        unique_together = ("gateway", "language", "version_number")


class SDKGenerationTask(TimestampedModelMixin, OperatorModelMixin):
    gateway = models.ForeignKey(Gateway, db_column="api_id", on_delete=models.CASCADE)
    resource_version = models.ForeignKey(ResourceVersion, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=32,
        choices=SDKGenerationStatusEnum.get_choices(),
        default=SDKGenerationStatusEnum.PENDING.value,
        db_index=True,
    )

    class Meta:
        db_table = "support_sdk_generation_task"
        constraints = [
            models.UniqueConstraint(
                fields=["resource_version"], name="support_sdk_generation_task_resource_version_uniq"
            ),
            models.CheckConstraint(
                condition=models.Q(status__in=SDKGenerationStatusEnum.get_values()),
                name="support_sdk_generation_task_status_valid",
            ),
        ]


class SDKGenerationItem(TimestampedModelMixin, OperatorModelMixin):
    task = models.ForeignKey(SDKGenerationTask, on_delete=models.CASCADE, related_name="items")
    language = models.CharField(max_length=32, choices=ProgrammingLanguageEnum.get_choices())
    status = models.CharField(
        max_length=32,
        choices=SDKGenerationStatusEnum.get_choices(),
        default=SDKGenerationStatusEnum.PENDING.value,
        db_index=True,
    )
    lease_token = models.CharField(max_length=128, blank=True, default="", db_index=True)
    lease_expires_at = models.DateTimeField(null=True, blank=True, db_index=True)
    attempt_count = models.PositiveIntegerField(default=0)
    input_fingerprint = models.CharField(max_length=64, blank=True, default="", db_index=True)
    config_snapshot = models.JSONField(default=dict, blank=True)
    error_code = models.CharField(max_length=64, blank=True, default="")
    error_message = models.CharField(max_length=1024, blank=True, default="")
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "support_sdk_generation_item"
        constraints = [
            models.UniqueConstraint(
                fields=["task", "language"], name="support_sdk_generation_item_task_language_uniq"
            ),
            models.CheckConstraint(
                condition=models.Q(language__in=SDK_GENERATION_LANGUAGE_VALUES),
                name="support_sdk_generation_item_language_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(status__in=SDKGenerationStatusEnum.get_values()),
                name="support_sdk_generation_item_status_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(attempt_count__gte=0),
                name="support_sdk_generation_item_attempt_count_valid",
            ),
        ]


class SDKArtifact(TimestampedModelMixin):
    item = models.ForeignKey(SDKGenerationItem, on_delete=models.CASCADE, related_name="artifacts")
    distributor = models.CharField(
        max_length=32,
        choices=SDKDistributorEnum.get_choices(),
        default=SDKDistributorEnum.BKREPO_GENERIC.value,
    )
    artifact_type = models.CharField(
        max_length=32,
        choices=SDKArtifactTypeEnum.get_choices(),
        default=SDKArtifactTypeEnum.ARCHIVE.value,
    )
    filename = models.CharField(max_length=512)
    remote_key = models.CharField(max_length=1024, blank=True, default="")
    coordinate = models.CharField(max_length=512, blank=True, default="")
    url = models.TextField(blank=True, default="")
    size = models.PositiveBigIntegerField(default=0)
    sha256 = models.CharField(max_length=64, blank=True, default="")
    original_version = models.CharField(max_length=64, blank=True, default="")
    package_version = models.CharField(max_length=64, blank=True, default="")
    status = models.CharField(
        max_length=32,
        choices=SDKGenerationStatusEnum.get_choices(),
        default=SDKGenerationStatusEnum.PENDING.value,
        db_index=True,
    )

    class Meta:
        db_table = "support_sdk_artifact"
        constraints = [
            models.UniqueConstraint(
                fields=["item", "distributor", "filename"], name="support_sdk_artifact_item_distributor_filename_uniq"
            ),
            models.CheckConstraint(
                condition=models.Q(distributor__in=SDKDistributorEnum.get_values()),
                name="support_sdk_artifact_distributor_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(artifact_type__in=SDKArtifactTypeEnum.get_values()),
                name="support_sdk_artifact_type_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(status__in=SDKGenerationStatusEnum.get_values()),
                name="support_sdk_artifact_status_valid",
            ),
            models.CheckConstraint(condition=models.Q(size__gte=0), name="support_sdk_artifact_size_valid"),
        ]
