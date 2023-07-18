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
import logging
import uuid
from typing import List

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from jsonfield import JSONField
from tencent_apigateway_common.i18n.field import I18nProperty

from apigateway.common.mixins.models import ConfigModelMixin, OperatorModelMixin, TimestampedModelMixin
from apigateway.core import managers
from apigateway.core.constants import (
    DEFAULT_STAGE_NAME,
    PATH_TO_NAME_PATTERN,
    RESOURCE_METHOD_CHOICES,
    APIHostingTypeEnum,
    APIStatusEnum,
    BackendConfigTypeEnum,
    BackendUpstreamTypeEnum,
    ContextScopeTypeEnum,
    ContextTypeEnum,
    LoadBalanceTypeEnum,
    MicroGatewayStatusEnum,
    PassHostEnum,
    ProxyTypeEnum,
    PublishEventEnum,
    PublishEventStatusEnum,
    ReleaseStatusEnum,
    SchemeEnum,
    SSLCertificateBindingScopeTypeEnum,
    SSLCertificateTypeEnum,
    StageItemTypeEnum,
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
    API, a system
    the name is unique and will be part of the path in APIGateway
    /api/{api.name}/{stage.name}/{resource.path}/
    """

    name = models.CharField(max_length=64, unique=True)
    description_i18n = I18nProperty(models.CharField(max_length=512, blank=True, null=True, default=None))
    description = description_i18n.default_field(default="")
    description_en = description_i18n.field("en")

    _maintainers = models.CharField(db_column="maintainers", max_length=1024, default="")

    # status
    status = models.IntegerField(choices=APIStatusEnum.choices())

    is_public = models.BooleanField(default=False)
    # 不同的托管类型决定特性集
    hosting_type = models.IntegerField(
        choices=APIHostingTypeEnum.get_choices(),
        default=APIHostingTypeEnum.DEFAULT.value,
    )

    objects = managers.GatewayManager()

    def __str__(self):
        return f"<API: {self.pk}/{self.name}>"

    class Meta:
        verbose_name = "API"
        verbose_name_plural = "API"
        db_table = "core_api"

    @property
    def maintainers(self) -> List[str]:
        if not self._maintainers:
            return []
        return self._maintainers.split(";")

    @maintainers.setter
    def maintainers(self, data: List[str]):
        self._maintainers = ";".join(data)

    def has_permission(self, username):
        """
        用户是否有网关操作权限，只有网关维护者有权限，创建者仅作为标记，不具有权限
        """
        return username in self.maintainers

    @property
    def is_active(self):
        return self.status == APIStatusEnum.ACTIVE.value

    @property
    def is_active_and_public(self):
        return self.is_public and self.is_active

    @property
    def docs_url(self):
        return settings.API_DOCS_URL_TMPL.format(api_name=self.name)

    @property
    def domain(self):
        return settings.BK_API_URL_TMPL.format(api_name=self.name)

    @property
    def is_micro_gateway(self) -> bool:
        """是否为微网关实例"""
        return self.hosting_type == APIHostingTypeEnum.MICRO.value

    @property
    def max_stage_count(self) -> int:
        return settings.MAX_STAGE_COUNT_PER_GATEWAY

    @property
    def max_resource_count(self) -> int:
        return settings.API_GATEWAY_RESOURCE_LIMITS["max_resource_count_per_gateway_whitelist"].get(
            self.name, settings.API_GATEWAY_RESOURCE_LIMITS["max_resource_count_per_gateway"]
        )

    @property
    def max_api_label_count(self) -> int:
        return settings.MAX_API_LABEL_COUNT_PER_GATEWAY


class Stage(TimestampedModelMixin, OperatorModelMixin):
    """
    The running environment of an API
    each stage context contains the env vars for path render
    e.g. prod/stage
    """

    api = models.ForeignKey(Gateway, on_delete=models.PROTECT)
    name = models.CharField(max_length=64)
    description_i18n = I18nProperty(models.CharField(max_length=512, blank=True, null=True))
    description = description_i18n.default_field()
    description_en = description_i18n.field("en", default=None)

    # 环境对应的微网关实例，不同环境允许使用不同网关实例，提供隔离能力
    micro_gateway = models.ForeignKey("MicroGateway", on_delete=models.SET_NULL, null=True, default=None, blank=True)

    _vars = models.TextField(db_column="vars")

    status = models.IntegerField(choices=StageStatusEnum.choices(), default=StageStatusEnum.INACTIVE.value)

    is_public = models.BooleanField(default=True)

    objects = managers.StageManager()

    def __str__(self):
        return f"<Stage: {self.pk}/{self.name}>"

    class Meta:
        verbose_name = "Stage"
        verbose_name_plural = "Stage"
        unique_together = ("api", "name")
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

    api-method-path should be unique

    NOTE: do unique check for api/method/path
    """

    name = models.CharField(max_length=256, default="", blank=True, null=True)
    description_i18n = I18nProperty(models.CharField(max_length=512, default=None, blank=True, null=True))
    description = description_i18n.default_field(default="")
    description_en = description_i18n.field("en")

    api = models.ForeignKey(Gateway, on_delete=models.PROTECT)
    method = models.CharField(max_length=10, choices=RESOURCE_METHOD_CHOICES, blank=False, null=False)
    path = models.CharField(max_length=2048, blank=False, null=False)
    match_subpath = models.BooleanField(default=False)

    # only one proxy is activated
    proxy_id = models.IntegerField(blank=False, null=False)

    is_public = models.BooleanField(default=True)
    allow_apply_permission = models.BooleanField(default=True)

    objects = managers.ResourceManager()

    def __str__(self):
        return f"<Resource: {self.pk}/{self.name}>"

    class Meta:
        verbose_name = "Resource"
        verbose_name_plural = "Resource"
        # unique_together = (
        #     ('api', 'method', 'path'),
        # )
        db_table = "core_resource"

    @property
    def identity(self):
        """
        资源标识
        """
        return f"{self.method} {self.path_display}"

    @property
    def action_name(self):
        if self.name:
            return self.name
        return "_".join([self.method.lower(), *PATH_TO_NAME_PATTERN.findall(self.path.lower())])

    @property
    def path_display(self):
        return get_path_display(self.path, self.match_subpath)


class Proxy(ConfigModelMixin):
    """
    Proxy has the proxy settings of the resource.
    - type is http, then the schema can be  proxy_http-1 or proxy_http-2
    - type is mock, then the schema can be  proxy_mock-1 or proxy_mock-2

    # 从http 1.0升级到http2.0
    # 此时这里type=http, 只能存一条, 所以schema需要变更为proxy_http-2
    """

    resource = models.ForeignKey(Resource, on_delete=models.PROTECT)
    type = models.CharField(max_length=20, choices=ProxyTypeEnum.get_choices(), blank=False, null=False)

    backend_config_type = models.CharField(max_length=32, default=BackendConfigTypeEnum.DEFAULT.value)
    backend_service = models.ForeignKey("BackendService", on_delete=models.SET_NULL, null=True, default=None)

    schema = models.ForeignKey(Schema, on_delete=models.PROTECT)
    # config = from ConfigModelMixin

    objects = managers.ProxyManager()

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
            self.config
        except Exception as e:
            logger.exception("the config field is not a valid json")
            raise e

        super().save(*args, **kwargs)


class StageResourceDisabled(TimestampedModelMixin, OperatorModelMixin):
    """
    The status of a stage-resource
    Enabled by default for api-stage-resource, but you can disabled part of them.
    """

    # can be delete cascade
    stage = models.ForeignKey(Stage, on_delete=models.CASCADE)
    # can be delete cascade
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE)

    objects = managers.StageResourceDisabledManager()

    def __str__(self):
        return f"<StageResourceDisabled: {self.stage}-{self.resource}>"

    class Meta:
        verbose_name = "StageResourceDisabled"
        verbose_name_plural = "StageResourceDisabled"
        unique_together = ("stage", "resource")
        db_table = "core_stage_resource_disabled"


class StageItem(TimestampedModelMixin, OperatorModelMixin):
    """Stage 配置项"""

    api = models.ForeignKey(Gateway, on_delete=models.CASCADE)
    type = models.CharField(max_length=64, choices=StageItemTypeEnum.get_choices())
    name = models.CharField(max_length=128)
    description = models.TextField(blank=True, default="")

    objects = managers.StageItemManager()

    class Meta:
        db_table = "core_stage_item"


class StageItemConfig(TimestampedModelMixin, OperatorModelMixin):
    """Stage 配置项数据"""

    api = models.ForeignKey(Gateway, on_delete=models.CASCADE)
    stage = models.ForeignKey(Stage, on_delete=models.CASCADE)
    stage_item = models.ForeignKey(StageItem, on_delete=models.CASCADE)
    config = JSONField(default=dict, dump_kwargs={"indent": None}, blank=True)

    objects = managers.StageItemConfigManager()

    class Meta:
        unique_together = ("api", "stage", "stage_item")
        db_table = "core_stage_item_config"


# ============================================ context ============================================


class Context(ConfigModelMixin):
    """
    NOTE: only one schema+config store for the scope_type+scope_id
    - the Context type is api_auth, while the schema can be `bkauth` or `other auth, like basic auth`
    - the Context type is stage_proxy, while the schema can be `proxy_http` or `proxy_mock`
    """

    scope_type = models.CharField(
        max_length=32,
        choices=ContextScopeTypeEnum.choices(),
        blank=False,
        null=False,
        db_index=True,
    )
    scope_id = models.IntegerField(blank=False, null=False, db_index=True)
    type = models.CharField(max_length=32, choices=ContextTypeEnum.choices(), blank=False, null=False)

    schema = models.ForeignKey(Schema, on_delete=models.PROTECT)
    # config = from ConfigModelMixin

    objects = managers.ContextManager()

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
        if self.type not in dict(ContextTypeEnum.choices()):
            raise ValueError("type should be one of ContextTypeEnum")

        # check the config value
        try:
            self.config
        except Exception as e:
            logger.exception("the config field is not a valid json")
            raise e

        super().save(*args, **kwargs)

    def should_do_publish(self):
        """
        NOTE: for resource context, is static, will be online after release be published
        but the context of api/stage, is dynamic, will be online after the settings be saved
        """
        return self.scope_type in (ContextScopeTypeEnum.API.value, ContextScopeTypeEnum.STAGE.value)


# ============================================ version and release ============================================
class ResourceVersion(TimestampedModelMixin, OperatorModelMixin):
    """
    Resource version
    """

    api = models.ForeignKey(Gateway, on_delete=models.PROTECT)
    version = models.CharField(max_length=128, default="", db_index=True, help_text=_("符合 semver 规范"))
    name = models.CharField(_("[Deprecated] 版本名"), max_length=128, unique=True)
    title = models.CharField(max_length=128, blank=True, default="", null=True)
    comment = models.CharField(max_length=512, blank=True, null=True)
    _data = models.TextField(db_column="data")
    created_time = models.DateTimeField(null=True, blank=True)

    objects = managers.ResourceVersionManager()

    @property
    def data(self) -> list:
        return json.loads(self._data)

    @data.setter
    def data(self, data: list):
        self._data = json.dumps(data)

    @property
    def data_display(self) -> list:
        data = self.data
        for resource in data:
            resource["path"] = get_path_display(resource["path"], resource.get("match_subpath"))
            if resource["proxy"]["type"] == ProxyTypeEnum.HTTP.value:
                proxy_config = json.loads(resource["proxy"]["config"])
                proxy_config["path"] = get_path_display(proxy_config["path"], proxy_config.get("match_subpath"))
                resource["proxy"]["config"] = json.dumps(proxy_config)

        return data

    def get_resource_data(self, resource_id):
        """获取资源数据"""
        for resource_data in self.data:
            if resource_data["id"] == resource_id:
                return resource_data
        return None

    @property
    def object_display(self):
        if not self.version:
            return f"{self.name}({self.title})"

        return f"{self.version}({self.title})"

    def __str__(self):
        return f"<ResourceVersion: {self.api}/{self.version}>"

    class Meta:
        verbose_name = "ResourceVersion"
        verbose_name_plural = "ResourceVersion"
        db_table = "core_resource_version"


class Release(TimestampedModelMixin, OperatorModelMixin):
    """
    Release
    only one activate resource_version per stage
    """

    api = models.ForeignKey(Gateway, on_delete=models.PROTECT)

    # only one stage-resource_version
    stage = models.OneToOneField(Stage, on_delete=models.PROTECT)
    resource_version = models.ForeignKey(ResourceVersion, on_delete=models.PROTECT)

    comment = models.CharField(max_length=512, blank=True, null=True)

    objects = managers.ReleaseManager()

    def __str__(self):
        return f"<Release: {self.api}/{self.stage}/{self.resource_version}>"

    class Meta:
        verbose_name = "Release"
        verbose_name_plural = "Release"
        db_table = "core_release"


class ReleasedResource(TimestampedModelMixin):
    """当前已发布版本中的资源信息"""

    api = models.ForeignKey(Gateway, on_delete=models.CASCADE)
    resource_version_id = models.IntegerField(blank=False, null=False, db_index=True)
    resource_id = models.IntegerField(blank=False, null=False, db_index=True)
    resource_name = models.CharField(max_length=256, default="", blank=True, null=False)
    resource_method = models.CharField(max_length=10, blank=False, null=False)
    resource_path = models.CharField(max_length=2048, blank=False, null=False)
    data = JSONField(help_text="resource data in resource version")

    objects = managers.ReleasedResourceManager()

    def __str__(self):
        return f"<ReleasedResource: {self.pk}>"

    class Meta:
        verbose_name = "ReleasedResource"
        verbose_name_plural = "ReleasedResource"
        unique_together = ("api", "resource_version_id", "resource_id")
        db_table = "core_released_resource"


class ReleaseHistory(TimestampedModelMixin, OperatorModelMixin):
    """
    Release History
    Store the release history records
    """

    api = models.ForeignKey(Gateway, on_delete=models.CASCADE)

    # only one stage-resource_version
    stage = models.ForeignKey(Stage, related_name="+", on_delete=models.CASCADE)
    stages = models.ManyToManyField(Stage)
    resource_version = models.ForeignKey(ResourceVersion, on_delete=models.CASCADE)
    comment = models.CharField(max_length=512, blank=True, null=True)

    status = models.CharField(
        _("发布状态"),
        max_length=16,
        choices=ReleaseStatusEnum.choices(),
        default=ReleaseStatusEnum.PENDING.value,
    )
    message = models.TextField(blank=True, default="")

    objects = managers.ReleaseHistoryManager()

    def __str__(self):
        return f"<Release: {self.api}/{self.stage}/{self.resource_version}>"

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

    objects = managers.PublishEventManager()

    @property
    def detail(self):
        return json.loads(self._detail)

    @detail.setter
    def detail(self, detail: dict):
        self._detail = json.dumps(detail)

    def __str__(self):
        return f"<PublishEvent: {self.gateway_id}/{self.stage_id}/{self.publish_id}/{self.name}>/{self.status}"

    class Meta:
        verbose_name = "PublishEvent"
        verbose_name_plural = "PublishEvent"
        db_table = "core_publish_event"
        index_together = ("gateway_id", "publish_id")


# ============================================ auth ============================================


class JWT(TimestampedModelMixin, OperatorModelMixin):
    """
    jwt for each api
    """

    # api = models.ForeignKey(API, on_delete=models.PROTECT, unique=True)
    api = models.OneToOneField(
        Gateway,
        on_delete=models.CASCADE,
        primary_key=True,
    )

    private_key = models.TextField(blank=True, default="", null=False)
    public_key = models.TextField(blank=False, null=False)

    encrypted_private_key = models.TextField(blank=False, null=False, default="")

    objects = managers.JWTManager()

    def __str__(self):
        return f"<JWT: {self.api}>"

    class Meta:
        verbose_name = "JWT"
        verbose_name_plural = "JWT"
        db_table = "core_jwt"


class APIRelatedApp(TimestampedModelMixin):
    """网关关联的蓝鲸应用"""

    api = models.ForeignKey(Gateway, on_delete=models.CASCADE)
    bk_app_code = models.CharField(max_length=32, db_index=True)

    objects = managers.APIRelatedAppManager()

    def __str__(self):
        return f"<APIRelatedApp: {self.bk_app_code}/{self.api_id}>"

    class Meta:
        db_table = "core_api_related_app"


# ============================================ gateway instance ============================================


class MicroGateway(ConfigModelMixin):
    """微网关实例"""

    id = models.UUIDField(default=uuid.uuid4, primary_key=True)

    api = models.ForeignKey(Gateway, on_delete=models.PROTECT)

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

    objects = managers.MicroGatewayManager()

    class Meta:
        db_table = "core_micro_gateway"

    @property
    def instance_id(self):
        """微网关实例 ID"""
        return str(self.pk)

    def query_related_api_gateways(self):
        if not self.is_shared:
            return Gateway.objects.filter(id=self.api_id)

        return Gateway.objects.filter(
            hosting_type=APIHostingTypeEnum.MICRO.value,
        )


class MicroGatewayReleaseHistory(models.Model):
    """微网关资源发布历史，不同于 ReleaseHistory，这里关注的是单个实例"""

    api = models.ForeignKey(Gateway, on_delete=models.CASCADE)
    # 因为实例和环境的绑定关系可能会修改，所以这里不能是强关联
    stage = models.ForeignKey(Stage, null=True, on_delete=models.SET_NULL)
    micro_gateway = models.ForeignKey(MicroGateway, on_delete=models.CASCADE)
    release_history = models.ForeignKey(ReleaseHistory, on_delete=models.CASCADE)
    message = models.TextField(blank=True, null=True, default="")
    status = models.CharField(
        _("发布状态"),
        max_length=16,
        choices=ReleaseStatusEnum.choices(),
        default=ReleaseStatusEnum.PENDING.value,
    )
    details = JSONField(blank=True, null=True)

    class Meta:
        db_table = "core_micro_gateway_release_history"


class BackendService(TimestampedModelMixin, OperatorModelMixin):
    """网关后端服务"""

    api = models.ForeignKey(Gateway, on_delete=models.CASCADE)

    name = models.CharField(max_length=128, db_index=True)
    description_i18n = I18nProperty(models.TextField(blank=True, null=True, default=None))
    description = description_i18n.default_field(default="")
    description_en = description_i18n.field("en")

    loadbalance = models.CharField(max_length=32, default=LoadBalanceTypeEnum.RR.value)
    upstream_type = models.CharField(max_length=64, default=BackendUpstreamTypeEnum.NODE.value)
    stage_item = models.ForeignKey(StageItem, on_delete=models.PROTECT, blank=True, null=True, default=None)
    upstream_custom_config = JSONField(default=dict, dump_kwargs={"indent": None}, blank=True)
    upstream_config = JSONField(default=dict, dump_kwargs={"indent": None}, blank=True)
    upstream_extra_config = JSONField(default=dict, dump_kwargs={"indent": None}, blank=True)

    pass_host = models.CharField(max_length=32, default=PassHostEnum.PASS.value)
    upstream_host = models.CharField(max_length=512, default="")
    scheme = models.CharField(max_length=32, default=SchemeEnum.HTTP.value)
    timeout = JSONField(default=dict, dump_kwargs={"indent": None}, blank=True)
    ssl_enabled = models.BooleanField(default=False)

    objects = managers.BackendServiceManager()

    class Meta:
        db_table = "core_backend_service"


class SslCertificate(TimestampedModelMixin, OperatorModelMixin):
    """SSL 证书"""

    api = models.ForeignKey(Gateway, on_delete=models.CASCADE)
    type = models.CharField(
        max_length=32,
        choices=SSLCertificateTypeEnum.get_choices(),
        db_index=True,
    )
    name = models.CharField(max_length=128, db_index=True, help_text=_("引用类证书，名称表示引用名称"))
    snis = JSONField(default=list, blank=True)
    cert = models.TextField(blank=True, default="")
    key = models.TextField(blank=True, default="")
    ca_cert = models.TextField(blank=True, default="")
    expires = models.DateTimeField(_("过期时间"))

    objects = managers.SslCertificateManager()

    class Meta:
        db_table = "core_ssl_certificate"

    def __str__(self):
        return f"<SslCertificate: {self.pk}/{self.name}>"


class SslCertificateBinding(TimestampedModelMixin, OperatorModelMixin):
    """证书绑定"""

    api = models.ForeignKey(Gateway, on_delete=models.CASCADE)
    scope_type = models.CharField(
        max_length=32,
        choices=SSLCertificateBindingScopeTypeEnum.get_choices(),
        db_index=True,
    )
    scope_id = models.IntegerField(db_index=True)
    ssl_certificate = models.ForeignKey(SslCertificate, on_delete=models.PROTECT)

    objects = managers.SslCertificateBindingManager()

    def __str__(self):
        return f"<SslCertificateBinding: {self.scope_type}/{self.scope_id}>"

    class Meta:
        db_table = "core_ssl_certificate_binding"
        unique_together = ("api", "scope_type", "scope_id", "ssl_certificate")
