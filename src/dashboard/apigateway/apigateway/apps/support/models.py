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
import json

from django.db import models
from django.db.transaction import atomic
from django.utils.translation import gettext_lazy as _
from jsonfield import JSONField

from apigateway.apps.support.constants import DocLanguageEnum, DocSourceEnum, DocTypeEnum, ProgrammingLanguageEnum
from apigateway.apps.support.managers import (
    APISDKManager,
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


# TODO: 1.14 删除此表
class ResourceDocSwagger(TimestampedModelMixin):
    """资源文档扩展数据，若资源文档通过 Swagger 导入，可存储资源的 Swagger 描述"""

    gateway = models.ForeignKey(Gateway, db_column="api_id", on_delete=models.CASCADE)
    resource_doc = models.OneToOneField(ResourceDoc, on_delete=models.CASCADE)
    swagger = models.TextField(blank=True, default="")

    def __str__(self):
        return f"<ResourceDocSwagger: {self.resource_doc}>"

    class Meta:
        verbose_name = _("资源文档 Swagger 扩展")
        verbose_name_plural = _("资源文档 Swagger 扩展")
        db_table = "support_resource_doc_swagger"


class ResourceDocVersion(TimestampedModelMixin, OperatorModelMixin):
    gateway = models.ForeignKey(Gateway, db_column="api_id", on_delete=models.CASCADE)
    resource_version = models.ForeignKey(ResourceVersion, on_delete=models.CASCADE)
    _data = models.TextField(db_column="data")

    objects = ResourceDocVersionManager()

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

    objects = ReleasedResourceDocManager()

    def __str__(self):
        return f"<ReleasedResourceDoc: {self.id}"

    class Meta:
        verbose_name = "ReleasedResourceDoc"
        verbose_name_plural = "ReleasedResourceDoc"
        unique_together = ("gateway", "resource_version_id", "resource_id", "language")
        db_table = "support_released_resource_doc"


class APISDK(ConfigModelMixin):
    gateway = models.ForeignKey(Gateway, db_column="api_id", on_delete=models.CASCADE)
    resource_version = models.ForeignKey(ResourceVersion, on_delete=models.CASCADE, blank=True, null=True)
    name = models.CharField(max_length=128, blank=True, default="", help_text=_("SDK 名称"))
    url = models.TextField(blank=True, default="", help_text=_("下载地址"))
    filename = models.CharField(max_length=128, help_text=_("SDK 文件名, 废弃"))
    language = models.CharField(max_length=32, choices=ProgrammingLanguageEnum.get_choices())
    version_number = models.CharField(max_length=64)
    include_private_resources = models.BooleanField(default=False)
    is_public_latest = models.BooleanField(default=False, db_index=True, help_text=_("废弃"))
    # is_recommended 说明这个版本是被推荐的，隐含了2个前提
    # 1. 这个版本是公开的
    # 2. 这个版本是最新的
    is_recommended = models.BooleanField(default=False, db_index=True)
    # is_public 说明这个版本是公开且发布过的
    is_public = models.BooleanField(default=False, db_index=True)

    schema = models.ForeignKey(Schema, on_delete=models.PROTECT, null=True)

    objects = APISDKManager()

    def __self__(self):
        return f"<APISDK: {self.gateway}>"

    class Meta:
        verbose_name = _("网关SDK")
        verbose_name_plural = _("网关SDK")
        db_table = "support_api_sdk"
        unique_together = ("gateway", "language", "version_number")

    @atomic
    def mark_is_recommended(self):
        # 清理之前的标记
        APISDK.objects.filter(
            is_recommended=True,
            gateway=self.gateway,
        ).update(is_public_latest=False, is_recommended=False)

        self.is_public_latest = True
        self.is_recommended = True
        self.save(update_fields=["is_public_latest", "is_recommended"])
