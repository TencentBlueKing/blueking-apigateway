# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关 (BlueKing - APIGateway) available.
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
import logging
import uuid
from datetime import datetime
from typing import ClassVar, Dict, List

from django.db import models
from django.utils.translation import gettext_lazy as _
from jsonfield import JSONField

from apigateway.common.i18n.field import I18nProperty
from apigateway.common.mixins.models import ConfigModelMixin, OperatorModelMixin, TimestampedModelMixin
from apigateway.core import managers
from apigateway.core.constants import (
    DEFAULT_STAGE_NAME,
    EVENT_FAIL_INTERVAL_TIME,
    RESOURCE_METHOD_CHOICES,
    BackendTypeEnum,
    ContextScopeTypeEnum,
    ContextTypeEnum,
    GatewayKindEnum,
    GatewayStatusEnum,
    MicroGatewayStatusEnum,
    ProgrammableGatewayLanguageEnum,
    ProxyTypeEnum,
    PublishEventEnum,
    PublishEventNameTypeEnum,
    PublishEventStatusEnum,
    PublishSourceEnum,
    ReleaseHistoryStatusEnum,
    ResourceVersionSchemaEnum,
    StageStatusEnum,
)
from apigateway.core.utils import get_path_display
from apigateway.schema.models import Schema

logger = logging.getLogger(__name__)

"""
NOTE:
    - all foreign key reference to core/schema here should be on_delete=models.PROTECT
    - if use on_delete != models.PROTECT, comment why
"""


class Gateway(TimestampedModelMixin, OperatorModelMixin):
    """
    Gateway, a system
    the name is unique and will be part of the path in APIGateway
    /api/{gateway.name}/{stage.name}/{resource.path}/
    """

    name = models.CharField(max_length=64, unique=True)
    description_i18n = I18nProperty(models.CharField(max_length=512, blank=True, null=True, default=None))
    description = description_i18n.default_field(default="")
    description_en = description_i18n.field("en")

    _maintainers = models.CharField(db_column="maintainers", max_length=1024, default="")
    _developers = models.CharField(db_column="developers", max_length=1024, blank=True, null=True, default="")
    _doc_maintainers = JSONField(
        db_column="doc_maintainers", default=dict, dump_kwargs={"indent": None}, blank=True, null=True
    )

    # status
    status = models.IntegerField(choices=GatewayStatusEnum.get_choices())

    # kind is normal or programmable, while the gateway_type is already been occupied on the context of gateway_auth
    # 这个 kind 仅对 web 产品页面感知，openapi 自动化注册等，不需要感知
    # 注意，可编程网关其  gateway_name = bk_app_code
    kind = models.IntegerField(
        choices=GatewayKindEnum.get_choices(), default=GatewayKindEnum.NORMAL.value, null=True, blank=True
    )
    # NOTE: 后续所有的 JSONField，必须使用 models.JSONField
    _extra_info = models.JSONField(db_column="extra_info", default=dict, blank=True, null=True)

    is_public = models.BooleanField(default=False)

    def __str__(self):
        return f"<Gateway: {self.pk}/{self.name}>"

    class Meta:
        verbose_name = "Gateway"
        verbose_name_plural = "Gateway"
        db_table = "core_api"

    @property
    def maintainers(self) -> List[str]:
        if not self._maintainers:
            return []
        return self._maintainers.split(";")

    @maintainers.setter
    def maintainers(self, data: List[str]):
        self._maintainers = ";".join(data)

    @property
    def doc_maintainers(self) -> Dict:
        if not self._doc_maintainers or self._doc_maintainers.get("type") == "":
            return {
                "type": "user",
                "contacts": self.maintainers,
                "service_account": {
                    "name": "",
                    "link": "",
                },
            }
        return self._doc_maintainers

    @doc_maintainers.setter
    def doc_maintainers(self, data: Dict):
        self._doc_maintainers = data

    @property
    def developers(self) -> List[str]:
        if not self._developers:
            return []
        return self._developers.split(";")

    @developers.setter
    def developers(self, data: List[str]):
        self._developers = ";".join(data)

    @property
    def extra_info(self) -> Dict:
        return self._extra_info

    @extra_info.setter
    def extra_info(self, data: Dict):
        if self.is_programmable:
            if data.get("language") not in ProgrammableGatewayLanguageEnum.get_values():
                raise ValueError("language should be one of [python, go]")

            if not data.get("repository"):
                raise ValueError("repository is required")

            # now only support language and repository
            self._extra_info = {
                "language": data.get("language", ""),
                "repository": data.get("repository", ""),
            }
        else:
            # 非编程网关，额外信息为空
            self._extra_info = {}

    def has_permission(self, username):
        """
        用户是否有网关操作权限，只有网关维护者有权限，创建者仅作为标记，不具有权限
        """
        return username in self.maintainers

    @property
    def is_programmable(self):
        return self.kind == GatewayKindEnum.PROGRAMMABLE.value

    @property
    def is_active(self):
        return self.status == GatewayStatusEnum.ACTIVE.value

    @property
    def is_active_and_public(self):
        return self.is_public and self.is_active


class Stage(TimestampedModelMixin, OperatorModelMixin):
    """
    The running environment of an API
    each stage context contains the env vars for path render
    e.g. prod/stage
    """

    gateway = models.ForeignKey(Gateway, on_delete=models.PROTECT, db_column="api_id")
    name = models.CharField(max_length=64)
    description_i18n = I18nProperty(models.CharField(max_length=512, blank=True, null=True))
    description = description_i18n.default_field()
    description_en = description_i18n.field("en", default=None)

    # 环境对应的微网关实例，不同环境允许使用不同网关实例，提供隔离能力
    micro_gateway = models.ForeignKey("MicroGateway", on_delete=models.SET_NULL, null=True, default=None, blank=True)

    _vars = models.TextField(db_column="vars", default="{}")

    status = models.IntegerField(choices=StageStatusEnum.get_choices(), default=StageStatusEnum.INACTIVE.value)

    is_public = models.BooleanField(default=True)

    objects: ClassVar[managers.StageManager] = managers.StageManager()

    def __str__(self):
        return f"<Stage: {self.pk}/{self.name}>"

    class Meta:
        verbose_name = "Stage"
        verbose_name_plural = "Stage"
        unique_together = ("gateway", "name")
        db_table = "core_stage"

    @property
    def vars(self) -> dict:
        return json.loads(self._vars)

    @vars.setter
    def vars(self, data: dict):
        self._vars = json.dumps(data)

    @property
    def is_active(self):
        return self.status == StageStatusEnum.ACTIVE.value

    @property
    def deletable(self):
        """
        环境可否被删除
        """
        return not self.is_active and self.name != DEFAULT_STAGE_NAME


class Resource(TimestampedModelMixin, OperatorModelMixin):
    """
    The specific endpoint registered to APIGateway.

    gateway-method-path should be unique

    NOTE: do unique check for gateway/method/path
    """

    name = models.CharField(max_length=256, default="", blank=True, null=True)
    description_i18n = I18nProperty(models.CharField(max_length=512, default=None, blank=True, null=True))
    description = description_i18n.default_field(default="")
    description_en = description_i18n.field("en")

    gateway = models.ForeignKey(Gateway, db_column="api_id", on_delete=models.PROTECT)
    method = models.CharField(max_length=10, choices=RESOURCE_METHOD_CHOICES, blank=False, null=False)
    path = models.CharField(max_length=2048, blank=False, null=False)
    match_subpath = models.BooleanField(default=False)
    enable_websocket = models.BooleanField(default=False)

    # only one proxy is activated
    proxy_id = models.IntegerField(blank=False, null=False)

    is_public = models.BooleanField(default=True)
    allow_apply_permission = models.BooleanField(default=True)

    def __str__(self):
        return f"<Resource: {self.pk}/{self.name}>"

    class Meta:
        verbose_name = "Resource"
        verbose_name_plural = "Resource"
        db_table = "core_resource"

    @property
    def identity(self):
        """
        资源标识
        """
        return f"{self.method} {self.path_display}"

    @property
    def path_display(self):
        return get_path_display(self.path, self.match_subpath)


class Proxy(ConfigModelMixin):
    """
    Proxy has the proxy settings of the resource.
    - type is http, then the schema can be  proxy_http-1 or proxy_http-2
    - type is mock, then the schema can be  proxy_mock-1 or proxy_mock-2

    # 从 http 1.0 升级到 http2.0
    # 此时这里 type=http, 只能存一条，所以 schema 需要变更为 proxy_http-2
    """

    resource = models.ForeignKey(Resource, on_delete=models.PROTECT)
    type = models.CharField(max_length=20, choices=ProxyTypeEnum.get_choices(), blank=False, null=False)

    backend = models.ForeignKey("Backend", null=True, default=None, on_delete=models.PROTECT)

    # TODO: 1.14 待删除
    schema = models.ForeignKey(Schema, on_delete=models.PROTECT)

    # config = from ConfigModelMixin

    def __str__(self):
        return f"<Proxy: {self.pk}/{self.type}>"

    class Meta:
        verbose_name = "Proxy"
        verbose_name_plural = "Proxies"
        unique_together = ("resource", "type")
        db_table = "core_proxy"

    def snapshot(self, as_dict=False, schemas=None):
        """
        - can add field
        - should not delete field!!!!!!!!!
        """
        data = {
            "id": self.pk,
            "type": self.type,
            "backend_id": self.backend_id,
            # save the string
            # "config": self._config,
            "config": json.dumps(self.config, separators=(",", ":")),
            # "created_time": time.format(self.created_time),
            # "updated_time": time.format(self.updated_time),
        }

        if schemas is None:
            data["schema"] = self.schema.snapshot(as_dict=True)
        else:
            data["schema"] = schemas[self.schema_id]

        if as_dict:
            return data
        return json.dumps(data)

    def save(self, *args, **kwargs):
        if self.type not in dict(ProxyTypeEnum.get_choices()):
            raise ValueError("type should be one of ProxyTypeEnum")

        # check the config value
        try:
            _ = self.config
        except Exception:  # pylint: disable=broad-except
            logger.exception("the config field is not a valid json")
            raise

        super().save(*args, **kwargs)


class StageResourceDisabled(TimestampedModelMixin, OperatorModelMixin):
    """
    The status of a stage-resource
    Enabled by default for gateway-stage-resource, but you can disabled part of them.
    """

    # can be delete cascade
    stage = models.ForeignKey(Stage, on_delete=models.CASCADE)
    # can be delete cascade
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE)

    def __str__(self):
        return f"<StageResourceDisabled: {self.stage}-{self.resource}>"

    class Meta:
        verbose_name = "StageResourceDisabled"
        verbose_name_plural = "StageResourceDisabled"
        unique_together = ("stage", "resource")
        db_table = "core_stage_resource_disabled"


# ============================================ backend ============================================


class Backend(TimestampedModelMixin, OperatorModelMixin):
    gateway = models.ForeignKey(Gateway, on_delete=models.PROTECT)
    type = models.CharField(
        max_length=20,
        choices=BackendTypeEnum.get_choices(),
        default=BackendTypeEnum.HTTP.value,
        blank=False,
        null=False,
    )
    name = models.CharField(max_length=64)
    description = models.CharField(max_length=512, default="")

    class Meta:
        unique_together = ("gateway", "name")
        db_table = "core_backend"

    def __str__(self):
        return f"<Backend: {self.id}/{self.name}>"


class BackendConfig(TimestampedModelMixin, OperatorModelMixin):
    gateway = models.ForeignKey(Gateway, on_delete=models.PROTECT)
    backend = models.ForeignKey(Backend, on_delete=models.PROTECT)
    stage = models.ForeignKey(Stage, on_delete=models.PROTECT)
    config = JSONField(default=dict, dump_kwargs={"indent": None}, blank=True)

    class Meta:
        unique_together = ("gateway", "backend", "stage")
        db_table = "core_backend_config"


# ============================================ context ============================================


class Context(ConfigModelMixin):
    """
    NOTE: only one schema+config store for the scope_type+scope_id
    - the Context type is api_auth, while the schema can be `bkauth` or `other auth, like basic auth`
    - the Context type is stage_proxy, while the schema can be `proxy_http` or `proxy_mock`
    """

    scope_type = models.CharField(
        max_length=32,
        choices=ContextScopeTypeEnum.get_choices(),
        blank=False,
        null=False,
        db_index=True,
    )
    scope_id = models.IntegerField(blank=False, null=False, db_index=True)
    type = models.CharField(max_length=32, choices=ContextTypeEnum.get_choices(), blank=False, null=False)

    schema = models.ForeignKey(Schema, on_delete=models.PROTECT)
    # config = from ConfigModelMixin

    objects: ClassVar[managers.ContextManager] = managers.ContextManager()

    def __str__(self):
        return f"<Context: {self.scope_type}/{self.scope_id}/{self.type}>"

    class Meta:
        verbose_name = "Context"
        verbose_name_plural = "Context"
        unique_together = ("scope_type", "scope_id", "type")
        db_table = "core_context"

    def snapshot(self, as_dict=False, schemas=None):
        """
        - can add field
        - should not delete field!!!!!!!!!
        """
        data = {
            "id": self.pk,
            "scope_type": self.scope_type,
            "scope_id": self.scope_id,
            "type": self.type,
            # save the string
            # "config": self._config,
            "config": json.dumps(self.config, separators=(",", ":")),
            # "created_time": time.format(self.created_time),
            # "updated_time": time.format(self.updated_time),
        }

        if schemas is None:
            data["schema"] = self.schema.snapshot(as_dict=True)
        else:
            data["schema"] = schemas[self.schema_id]

        if as_dict:
            return data

        return json.dumps(data)

    def save(self, *args, **kwargs):
        if self.type not in dict(ContextTypeEnum.get_choices()):
            raise ValueError("type should be one of ContextTypeEnum")

        # check the config value
        try:
            _ = self.config
        except Exception:  # pylint: disable=broad-except
            logger.exception("the config field is not a valid json")
            raise

        super().save(*args, **kwargs)


# ============================================ version and release ============================================
class ResourceVersion(TimestampedModelMixin, OperatorModelMixin):
    """
    Resource version
    """

    gateway = models.ForeignKey(Gateway, db_column="api_id", on_delete=models.PROTECT)
    version = models.CharField(max_length=128, default="", db_index=True, help_text=_("符合 semver 规范"))
    comment = models.CharField(max_length=512, blank=True, null=True)
    _data = models.TextField(db_column="data")
    # 用于不同数据格式解析版本数据兼容历史数据
    schema_version = models.CharField(
        max_length=32,
        choices=ResourceVersionSchemaEnum.get_choices(),
        default=ResourceVersionSchemaEnum.V1.value,
    )

    created_time = models.DateTimeField(null=True, blank=True)

    objects: ClassVar[managers.ResourceVersionManager] = managers.ResourceVersionManager()

    @property
    def data(self) -> list:
        return json.loads(self._data)

    @data.setter
    def data(self, data: list):
        self._data = json.dumps(data)

    @property
    def object_display(self):
        if not self.version:
            return f"{self.gateway}({self.created_time})"

        return self.version

    @property
    def is_schema_v2(self):
        return self.schema_version == ResourceVersionSchemaEnum.V2.value

    def __str__(self):
        return f"<ResourceVersion: {self.gateway}/{self.version}>"

    class Meta:
        verbose_name = "ResourceVersion"
        verbose_name_plural = "ResourceVersion"
        db_table = "core_resource_version"


class Release(TimestampedModelMixin, OperatorModelMixin):
    """
    Release
    only one activate resource_version per stage
    """

    gateway = models.ForeignKey(Gateway, db_column="api_id", on_delete=models.PROTECT)

    # only one stage-resource_version
    stage = models.OneToOneField(Stage, on_delete=models.PROTECT)
    resource_version = models.ForeignKey(ResourceVersion, on_delete=models.PROTECT)

    comment = models.CharField(max_length=512, blank=True, null=True)

    objects: ClassVar[managers.ReleaseManager] = managers.ReleaseManager()

    def __str__(self):
        return f"<Release: {self.gateway}/{self.stage}/{self.resource_version}>"

    class Meta:
        verbose_name = "Release"
        verbose_name_plural = "Release"
        db_table = "core_release"


class ReleasedResource(TimestampedModelMixin):
    """当前已发布版本中的资源信息"""

    gateway = models.ForeignKey(Gateway, db_column="api_id", on_delete=models.CASCADE)
    resource_version_id = models.IntegerField(blank=False, null=False, db_index=True)
    resource_id = models.IntegerField(blank=False, null=False, db_index=True)
    resource_name = models.CharField(max_length=256, default="", blank=True, null=False)
    resource_method = models.CharField(max_length=10, blank=False, null=False)
    resource_path = models.CharField(max_length=2048, blank=False, null=False)
    data = JSONField(help_text="resource data in resource version")

    objects: ClassVar[managers.ReleasedResourceManager] = managers.ReleasedResourceManager()

    def __str__(self):
        return f"<ReleasedResource: {self.pk}>"

    class Meta:
        verbose_name = "ReleasedResource"
        verbose_name_plural = "ReleasedResource"
        unique_together = ("gateway", "resource_version_id", "resource_id")
        db_table = "core_released_resource"

    @property
    def is_public(self) -> bool:
        return self.data.get("is_public", False)


class ReleaseHistory(TimestampedModelMixin, OperatorModelMixin):
    """
    Release History
    Store the release history records
    """

    gateway = models.ForeignKey(Gateway, db_column="api_id", on_delete=models.CASCADE)

    # only one stage-resource_version
    stage = models.ForeignKey(Stage, related_name="+", on_delete=models.CASCADE)

    resource_version = models.ForeignKey(ResourceVersion, on_delete=models.CASCADE)
    comment = models.CharField(max_length=512, blank=True, null=True)

    # 发布来源
    source = models.CharField(
        max_length=64,
        choices=PublishSourceEnum.get_choices(),
        default=PublishSourceEnum.VERSION_PUBLISH.value,
    )

    objects: ClassVar[managers.ReleaseHistoryManager] = managers.ReleaseHistoryManager()

    def __str__(self):
        return f"<Release: {self.gateway}/{self.stage}/{self.resource_version}>"

    class Meta:
        verbose_name = "ReleaseHistory"
        verbose_name_plural = "ReleaseHistory"
        db_table = "core_release_history"


class PublishEvent(TimestampedModelMixin, OperatorModelMixin):
    """
    publish event
    Store the publish events records
    """

    id = models.AutoField(primary_key=True)
    gateway = models.ForeignKey(Gateway, related_name="+", on_delete=models.CASCADE)
    stage = models.ForeignKey(Stage, related_name="+", on_delete=models.CASCADE)
    publish = models.ForeignKey(ReleaseHistory, related_name="+", on_delete=models.CASCADE, db_column="publish_id")
    name = models.CharField(
        max_length=64,
        blank=True,
        null=False,
        choices=PublishEventEnum.get_choices(),
    )
    step = models.IntegerField(blank=False, null=False)
    status = models.CharField(
        max_length=32,
        choices=PublishEventStatusEnum.get_choices(),
    )
    _detail = models.TextField(help_text="detail", null=True, default="{}", db_column="detail")

    objects: ClassVar[managers.PublishEventManager] = managers.PublishEventManager()

    @property
    def detail(self):
        if self._detail:
            return json.loads(self._detail)
        return {}

    @detail.setter
    def detail(self, detail: dict):
        self._detail = json.dumps(detail)

    @property
    def is_last(self):
        return self.name == PublishEventNameTypeEnum.LOAD_CONFIGURATION.value

    @property
    def is_running(self):
        """通过最新的一个 event 判断当前发布是否还在继续执行"""

        # 如果不是最后一个事件，如果是 success 的话说明也是 running
        return self.status == PublishEventStatusEnum.DOING.value or (
            self.status == PublishEventStatusEnum.SUCCESS.value and not self.is_last
        )

    def get_release_history_status(self):
        """通过 end event 来返回 release_history 状态"""
        # 如果状态是 Doing 并且该状态已经过去了 10min，这种也认失败
        now = datetime.now().timestamp()
        if self.status == PublishEventStatusEnum.DOING.value and now - self.created_time.timestamp() > 600:
            return ReleaseHistoryStatusEnum.FAILURE.value

        # 如果是成功但不是最后一个节点并且该状态已经过去了 10min，这种也认失败
        if (
            self.status == PublishEventStatusEnum.SUCCESS.value and not self.is_last
        ) and now - self.created_time.timestamp() > EVENT_FAIL_INTERVAL_TIME:
            return ReleaseHistoryStatusEnum.FAILURE.value

        # 如果还在执行中
        if self.is_running:
            return ReleaseHistoryStatusEnum.DOING.value

        # 如已经结束
        if self.status == PublishEventStatusEnum.SUCCESS.value:
            return ReleaseHistoryStatusEnum.SUCCESS.value

        if self.status == PublishEventStatusEnum.FAILURE.value:
            return ReleaseHistoryStatusEnum.FAILURE.value

        return ReleaseHistoryStatusEnum.DOING.value

    def __str__(self):
        return f"<PublishEvent: {self.gateway_id}/{self.stage_id}/{self.publish_id}/{self.name}>/{self.status}"

    class Meta:
        verbose_name = "PublishEvent"
        verbose_name_plural = "PublishEvent"
        db_table = "core_publish_event"
        index_together = ("gateway_id", "publish_id")
        unique_together = ("gateway_id", "publish_id", "stage_id", "step", "status")


# ============================================ auth ============================================


class JWT(TimestampedModelMixin, OperatorModelMixin):
    """
    jwt for each gateway
    """

    gateway = models.OneToOneField(
        Gateway,
        db_column="api_id",
        on_delete=models.CASCADE,
        primary_key=True,
    )

    private_key = models.TextField(blank=True, default="", null=False)
    public_key = models.TextField(blank=False, null=False)

    encrypted_private_key = models.TextField(blank=False, null=False, default="")

    def __str__(self):
        return f"<JWT: {self.gateway}>"

    class Meta:
        verbose_name = "JWT"
        verbose_name_plural = "JWT"
        db_table = "core_jwt"


class GatewayRelatedApp(TimestampedModelMixin):
    """
    网关关联的蓝鲸应用
    - 应用可以通过 openapi 操作网关数据
    """

    gateway = models.ForeignKey(Gateway, db_column="api_id", on_delete=models.CASCADE)
    bk_app_code = models.CharField(max_length=32, db_index=True)

    def __str__(self):
        return f"<GatewayRelatedApp: {self.bk_app_code}/{self.gateway_id}>"

    class Meta:
        db_table = "core_api_related_app"


# ============================================ gateway instance ============================================


class MicroGateway(ConfigModelMixin):
    """微网关实例"""

    id = models.UUIDField(default=uuid.uuid4, primary_key=True)

    gateway = models.ForeignKey(Gateway, db_column="api_id", on_delete=models.PROTECT)

    name = models.CharField(max_length=256, blank=False, null=False, db_index=True)
    description_i18n = I18nProperty(models.TextField(blank=True, null=True, default=None))
    description = description_i18n.default_field(default="")
    description_en = description_i18n.field("en")
    is_shared = models.BooleanField(default=False, help_text=_("是否共享实例"))
    # 非管理实例表示外部部署接入的，不需要通过 bcs + helm 来管理更新
    is_managed = models.BooleanField(default=True, help_text=_("是否托管实例"))

    status = models.CharField(
        max_length=64,
        choices=MicroGatewayStatusEnum.get_choices(),
        default=MicroGatewayStatusEnum.PENDING.value,
    )
    status_updated_time = models.DateTimeField(null=True, blank=True)
    comment = models.CharField(max_length=512, blank=True, default="")

    schema = models.ForeignKey(Schema, on_delete=models.PROTECT)

    objects: ClassVar[managers.MicroGatewayManager] = managers.MicroGatewayManager()

    class Meta:
        db_table = "core_micro_gateway"

    @property
    def instance_id(self):
        """微网关实例 ID"""
        return str(self.pk)
