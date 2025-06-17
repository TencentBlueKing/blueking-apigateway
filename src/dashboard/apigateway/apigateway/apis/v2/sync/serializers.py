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
from typing import Any, Dict, List, Optional

from django.conf import settings
from django.utils.translation import gettext as _
from django.utils.translation.trans_null import gettext_lazy
from pydantic import TypeAdapter
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from apigateway.apps.permission.constants import FormattedGrantDimensionEnum, GrantDimensionEnum
from apigateway.apps.plugin.constants import PluginBindingScopeEnum
from apigateway.apps.plugin.models import PluginType
from apigateway.apps.support.constants import DocLanguageEnum, ProgrammingLanguageEnum
from apigateway.biz.constants import MAX_BACKEND_TIMEOUT_IN_SECOND, SEMVER_PATTERN
from apigateway.biz.plugin import PluginConfigData, PluginSynchronizer
from apigateway.biz.stage import StageHandler
from apigateway.biz.validators import (
    BKAppCodeListValidator,
    GatewayAPIDocMaintainerValidator,
    MaxCountPerGatewayValidator,
    ResourceVersionValidator,
    SchemeInputValidator,
    StageVarsValidator,
)
from apigateway.common.constants import (
    DOMAIN_PATTERN,
    GATEWAY_NAME_PATTERN,
    HEADER_KEY_PATTERN,
    GatewayAPIDocMaintainerTypeEnum,
)
from apigateway.common.django.validators import NameValidator
from apigateway.common.fields import CurrentGatewayDefault
from apigateway.common.i18n.field import SerializerTranslatedField
from apigateway.common.mixins.serializers import ExtensibleFieldMixin
from apigateway.core.constants import (
    DEFAULT_BACKEND_NAME,
    DEFAULT_LB_HOST_WEIGHT,
    STAGE_NAME_PATTERN,
    GatewayStatusEnum,
    GatewayTypeEnum,
    LoadBalanceTypeEnum,
)
from apigateway.core.models import Backend, BackendConfig, Gateway, ResourceVersion, Stage
from apigateway.service.plugin.header_rewrite import HeaderRewriteConvertor
from apigateway.service.plugin.validator import PluginConfigYamlValidator
from apigateway.utils.time import NeverExpiresTime


class UserConfigSLZ(serializers.Serializer):
    """
    目前仅支持开源版的用户配置字段，如果需要支持其他版本，可直接添加对应字段
    """

    from_bk_token = serializers.BooleanField(required=False)
    from_username = serializers.BooleanField(required=False)

    class Meta:
        ref_name = "apigateway.apis.v2.sync.serializers.UserConfigSLZ"


class ServiceAccountSLZ(serializers.Serializer):
    name = serializers.CharField(allow_blank=True, required=False, help_text="服务号名称")
    link = serializers.CharField(allow_blank=True, required=False, help_text="服务号链接")

    class Meta:
        ref_name = "apigateway.apis.v2.sync.serializers.ServiceAccountSLZ"


class GatewayAPIDocMaintainerSLZ(serializers.Serializer):
    type = serializers.ChoiceField(
        choices=GatewayAPIDocMaintainerTypeEnum.get_choices(), allow_blank=True, required=False, help_text="联系人类型"
    )
    contacts = serializers.ListField(
        child=serializers.CharField(), allow_empty=True, required=False, help_text="联系人"
    )
    service_account = ServiceAccountSLZ(required=False, help_text="服务号")

    class Meta:
        ref_name = "apigateway.apis.v2.sync.serializers.GatewayAPIDocMaintainerSLZ"
        validators = [GatewayAPIDocMaintainerValidator()]


class GatewaySyncInputSLZ(serializers.ModelSerializer):
    name = serializers.RegexField(
        GATEWAY_NAME_PATTERN,
        label="网关名称",
        max_length=64,
        validators=[NameValidator()],
    )
    maintainers = serializers.ListField(child=serializers.CharField(), allow_empty=True, required=False)
    doc_maintainers = GatewayAPIDocMaintainerSLZ(required=False)
    status = serializers.ChoiceField(choices=GatewayStatusEnum.get_choices(), default=GatewayStatusEnum.ACTIVE.value)
    # 只允许指定为普通网关或官方网关，不能指定为超级官方网关，超级官方网关会传递敏感参数到后端接口
    api_type = serializers.ChoiceField(
        choices=[GatewayTypeEnum.OFFICIAL_API.value, GatewayTypeEnum.CLOUDS_API.value], required=False
    )
    user_config = UserConfigSLZ(required=False)
    allow_delete_sensitive_params = serializers.BooleanField(default=True)

    class Meta:
        ref_name = "apigateway.apis.v2.sync.serializers.GatewaySyncInputSLZ"
        model = Gateway
        fields = [
            "name",
            "description",
            "description_en",
            "maintainers",
            "doc_maintainers",
            "status",
            "is_public",
            "api_type",
            "user_config",
            "allow_delete_sensitive_params",
        ]
        extra_kwargs = {
            "description_en": {
                "required": False,
            }
        }

    def validate(self, data):
        self._validate_name(data["name"], data.get("api_type"))

        data["gateway_type"] = data.pop("api_type", None)

        return data

    def _validate_name(self, name: str, api_type: Optional[int]):
        if api_type is None or api_type == GatewayTypeEnum.CLOUDS_API.value:
            return

        for prefix in settings.OFFICIAL_GATEWAY_NAME_PREFIXES:
            if name.startswith(prefix):
                return

        raise serializers.ValidationError(
            {
                "name": _("api_type 为 {api_type} 时，网关名 name 需以 {prefix} 开头。").format(
                    api_type=api_type, prefix=", ".join(settings.OFFICIAL_GATEWAY_NAME_PREFIXES)
                )
            }
        )


class GatewaySyncOutputSLZ(serializers.Serializer):
    id = serializers.IntegerField(read_only=True, help_text="网关ID")
    name = serializers.CharField(read_only=True, help_text="网关名称")

    class Meta:
        ref_name = "apigateway.apis.v2.sync.serializers.GatewaySyncOutputSLZ"


class HostSLZ(serializers.Serializer):
    host = serializers.RegexField(DOMAIN_PATTERN)
    weight = serializers.IntegerField(min_value=1, required=False)

    class Meta:
        ref_name = "apigateway.apis.v2.sync.serializers.HostSLZ"


class UpstreamsSLZ(serializers.Serializer):
    loadbalance = serializers.ChoiceField(choices=LoadBalanceTypeEnum.get_choices())
    hosts = serializers.ListField(child=HostSLZ(), allow_empty=False)

    class Meta:
        ref_name = "apigateway.apis.v2.sync.serializers.UpstreamsSLZ"

    def __init__(self, *args, **kwargs):
        self.allow_empty = kwargs.pop("allow_empty", False)
        super().__init__(*args, **kwargs)

    def _update_hosts(self, data):
        """
        如果负载均衡类型为 RoundRobin 时，将权重设置为默认值
        """
        if data.get("loadbalance") != LoadBalanceTypeEnum.RR.value:
            return data

        for host in data["hosts"]:
            host["weight"] = DEFAULT_LB_HOST_WEIGHT
        return data

    def to_internal_value(self, data):
        if self.allow_empty and not data:
            return {}
        data = super().to_internal_value(data)
        return self._update_hosts(data)

    def to_representation(self, instance):
        if self.allow_empty and not instance:
            return {}
        return super().to_representation(instance)

    def validate(self, data):
        if data.get("loadbalance") == LoadBalanceTypeEnum.WRR.value:
            host_without_weight = [host for host in data["hosts"] if host.get("weight") is None]
            if host_without_weight:
                raise serializers.ValidationError(_("负载均衡类型为 Weighted-RR 时，Host 权重必填。"))
        return data


class TransformHeadersSLZ(serializers.Serializer):
    set = serializers.DictField(label="设置", child=serializers.CharField(), required=False, allow_empty=True)
    delete = serializers.ListField(label="删除", child=serializers.CharField(), required=False, allow_empty=True)

    class Meta:
        ref_name = "apigateway.apis.v2.sync.serializers.TransformHeadersSLZ"

    def _validate_headers_key(self, value):
        for key in value:
            if not HEADER_KEY_PATTERN.match(key):
                raise serializers.ValidationError(_("Header 键由字母、数字、连接符（-）组成，长度小于100个字符。"))
        return value

    def validate_set(self, value):
        return self._validate_headers_key(value)

    def validate_delete(self, value):
        return self._validate_headers_key(value)


class StageProxyHTTPConfigSLZ(serializers.Serializer):
    timeout = serializers.IntegerField(max_value=MAX_BACKEND_TIMEOUT_IN_SECOND, min_value=1)
    upstreams = UpstreamsSLZ(allow_empty=False)
    transform_headers = TransformHeadersSLZ(required=False, default=dict)

    class Meta:
        ref_name = "apigateway.apis.v2.sync.serializers.StageProxyHTTPConfigSLZ"


class BackendConfigSLZ(UpstreamsSLZ):
    timeout = serializers.IntegerField(max_value=MAX_BACKEND_TIMEOUT_IN_SECOND, min_value=1)

    class Meta:
        ref_name = "apigateway.apis.v2.sync.serializers.BackendConfigSLZ"


class BackendSLZ(serializers.Serializer):
    name = serializers.CharField(help_text="后端服务名称", required=True)
    config = BackendConfigSLZ(allow_empty=False)

    class Meta:
        ref_name = "apigateway.apis.v2.sync.serializers.BackendSLZ"


class PluginConfigSLZ(serializers.Serializer):
    type = serializers.CharField(help_text="插件类型名称")
    yaml = serializers.CharField(help_text="插件yaml配置")

    class Meta:
        ref_name = "apigateway.apis.v2.sync.serializers.PluginConfigSLZ"


class StageSyncInputSLZ(ExtensibleFieldMixin, serializers.ModelSerializer):
    gateway = serializers.HiddenField(default=CurrentGatewayDefault())
    name = serializers.RegexField(
        STAGE_NAME_PATTERN,
        validators=[NameValidator()],
    )
    vars = serializers.DictField(
        label="环境变量",
        child=serializers.CharField(allow_blank=True, required=True),
        default=dict,
    )
    proxy_http = StageProxyHTTPConfigSLZ(required=False)

    backends = serializers.ListSerializer(help_text="后端配置", child=BackendSLZ(), allow_null=True, required=False)

    plugin_configs = serializers.ListSerializer(
        help_text="插件配置", child=PluginConfigSLZ(), allow_null=True, required=False
    )

    description = SerializerTranslatedField(
        default_field="description_i18n", allow_blank=True, allow_null=True, max_length=512, required=False
    )

    class Meta:
        ref_name = "apigateway.apis.v2.sync.serializers.StageSyncInputSLZ"
        model = Stage
        fields = (
            "gateway",
            "id",
            "name",
            "description",
            "description_en",
            "vars",
            "status",
            "proxy_http",
            "backends",
            "plugin_configs",
        )
        extra_kwargs = {
            "description_en": {
                "required": False,
            }
        }
        read_only_fields = ("id", "status")
        non_model_fields = ["proxy_http", "backends", "plugin_configs", "rate_limit"]
        lookup_field = "id"

        validators = [
            UniqueTogetherValidator(
                queryset=Stage.objects.all(),
                fields=["gateway", "name"],
                message=gettext_lazy("网关下环境名称已经存在。"),
            ),
            MaxCountPerGatewayValidator(
                Stage,
                max_count_callback=lambda gateway: settings.MAX_STAGE_COUNT_PER_GATEWAY,
                message=gettext_lazy("每个网关最多创建 {max_count} 个环境。"),
            ),
            StageVarsValidator(),
        ]

    def validate(self, data):
        self._validate_plugin_configs(data.get("plugin_configs"))
        self._validate_scheme(data.get("backends"))
        # validate stage backend
        if data.get("proxy_http") is None and data.get("backends") is None:
            raise serializers.ValidationError(_("proxy_http or backends 必须要选择一种方式配置后端服务"))
        return data

    def create(self, validated_data):
        # 1. save stage
        instance = super().create(validated_data)

        # 2. create default backend
        backend, _ = Backend.objects.get_or_create(
            gateway=instance.gateway,
            name=DEFAULT_BACKEND_NAME,
        )

        proxy_http_config = validated_data.get("proxy_http")
        # 兼容老的配置
        if proxy_http_config is not None and len(proxy_http_config) != 0:
            config = self._get_stage_backend_config(proxy_http_config)
            backend_config = BackendConfig(
                gateway=instance.gateway,
                backend=backend,
                stage=instance,
                config=config,
            )
            backend_config.save()

            # create or update header rewrite plugin config
            stage_transform_headers = proxy_http_config.get("transform_headers") or {}
            stage_config = HeaderRewriteConvertor.transform_headers_to_plugin_config(stage_transform_headers)
            HeaderRewriteConvertor.sync_plugins(
                instance.gateway_id,
                PluginBindingScopeEnum.STAGE.value,
                {instance.id: stage_config},
                self.context["request"].user.username,
            )

        # 3.create config backend
        backend_configs = []
        names = [DEFAULT_BACKEND_NAME]
        for backend_info in validated_data.get("backends", []):
            names.append(backend_info["name"])
            backend, _ = Backend.objects.get_or_create(
                gateway=instance.gateway,
                name=backend_info["name"],
            )
            config = self._get_stage_backend_config_v2(backend_info)
            backend_config = BackendConfig(
                gateway=instance.gateway,
                backend=backend,
                stage=instance,
                config=config,
            )
            backend_configs.append(backend_config)

        # 4. create other backend config with empty host
        backends = Backend.objects.filter(gateway=instance.gateway).exclude(name__in=names)
        config = {
            "type": "node",
            "timeout": 30,
            "loadbalance": "roundrobin",
            "hosts": [{"scheme": "http", "host": "", "weight": 100}],
        }

        for backend in backends:
            backend_config = BackendConfig(
                gateway=instance.gateway,
                backend=backend,
                stage=instance,
                config=config,
            )
            backend_configs.append(backend_config)

        if backend_configs:
            BackendConfig.objects.bulk_create(backend_configs)

        # 5. sync stage plugin
        self._sync_plugins(instance.gateway_id, instance.id, validated_data.get("plugin_configs", None))

        return instance

    def _get_stage_backend_config(self, proxy_http_config):
        hosts = []
        for host in proxy_http_config["upstreams"]["hosts"]:
            scheme, _host = host["host"].rstrip("/").split("://")
            hosts.append({"scheme": scheme, "host": _host, "weight": host["weight"]})

        return {
            "type": "node",
            "timeout": proxy_http_config["timeout"],
            "loadbalance": proxy_http_config["upstreams"]["loadbalance"],
            "hosts": hosts,
        }

    def _get_stage_backend_config_v2(self, backend: dict):
        hosts = []
        for host in backend["config"]["hosts"]:
            scheme, _host = host["host"].rstrip("/").split("://")
            hosts.append({"scheme": scheme, "host": _host, "weight": host["weight"]})

        return {
            "type": "node",
            "timeout": backend["config"]["timeout"],
            "loadbalance": backend["config"]["loadbalance"],
            "hosts": hosts,
        }

    def update(self, instance, validated_data):
        validated_data.pop("name", None)
        # 仅能通过发布更新 status，不允许直接更新 status
        validated_data.pop("status", None)
        validated_data.pop("created_by", None)

        # 1. 更新数据
        instance = super().update(instance, validated_data)

        # 2. create default backend
        proxy_http_config = validated_data.get("proxy_http")
        if proxy_http_config is not None and len(proxy_http_config) != 0:
            backend, _ = Backend.objects.get_or_create(
                gateway=instance.gateway,
                name=DEFAULT_BACKEND_NAME,
            )
            backend_config = BackendConfig.objects.filter(
                gateway=instance.gateway,
                backend=backend,
                stage=instance,
            ).first()
            if not backend_config:
                backend_config = BackendConfig(
                    gateway=instance.gateway,
                    backend=backend,
                    stage=instance,
                )

            backend_config.config = self._get_stage_backend_config(proxy_http_config)
            backend_config.save()

            # create or update header rewrite plugin config
            stage_transform_headers = proxy_http_config.get("transform_headers") or {}
            stage_config = HeaderRewriteConvertor.transform_headers_to_plugin_config(stage_transform_headers)
            HeaderRewriteConvertor.sync_plugins(
                instance.gateway_id,
                PluginBindingScopeEnum.STAGE.value,
                {instance.id: stage_config},
                self.context["request"].user.username,
            )

        # 3. update backend
        for backend_info in validated_data.get("backends", []):
            backend, _ = Backend.objects.get_or_create(
                gateway=instance.gateway,
                name=backend_info["name"],
            )
            backend_config = BackendConfig.objects.filter(
                gateway=instance.gateway,
                backend=backend,
                stage=instance,
            ).first()

            if not backend_config:
                backend_config = BackendConfig(
                    gateway=instance.gateway,
                    backend=backend,
                    stage=instance,
                )
            backend_config.config = self._get_stage_backend_config_v2(backend_info)
            backend_config.save()

        # 4. sync stage plugin
        self._sync_plugins(instance.gateway_id, instance.id, validated_data.get("plugin_configs", None))

        return instance

    def _validate_plugin_configs(self, plugin_configs):
        """
        校验插件配置
        - 1. 插件类型不能重复
        - 2. 插件类型必须已存在
        - 3. 插件配置，必须符合插件类型的 schema 约束
        """
        if not plugin_configs:
            return

        types = set()
        for plugin_config in plugin_configs:
            plugin_type = plugin_config["type"]
            if plugin_type in types:
                raise serializers.ValidationError(_("插件类型重复：{plugin_type}。").format(plugin_type=plugin_type))
            types.add(plugin_type)

        all_plugin_type = PluginType.objects.all()

        exist_plugin_types = set(all_plugin_type.values_list("code", flat=True))
        not_exist_types = types - exist_plugin_types
        if not_exist_types:
            raise serializers.ValidationError(
                _("插件类型 {not_exist_types} 不存在。").format(not_exist_types=", ".join(not_exist_types))
            )

        plugin_types = {plugin_type.code: plugin_type for plugin_type in all_plugin_type}
        yaml_validator = PluginConfigYamlValidator()

        for plugin_config in plugin_configs:
            plugin_type = plugin_types[plugin_config["type"]]
            try:
                yaml_validator.validate(
                    plugin_type.code,
                    plugin_config["yaml"],
                    plugin_type.schema and plugin_type.schema.schema,
                )
            except Exception as err:  # pylint: disable=broad-except
                raise serializers.ValidationError(
                    _("插件配置校验失败，插件类型：{plugin_type_code}，错误信息：{err}。").format(
                        plugin_type_code=plugin_type.code,
                        err=err,
                    )
                )

    def _validate_scheme(self, backends):
        if backends is None:
            return
        for backend in backends:
            validator = SchemeInputValidator(hosts=backend["config"]["hosts"], backend=backend)
            validator.validate_scheme()

    def _sync_plugins(self, gateway_id: int, stage_id: int, plugin_configs: Optional[Dict[str, Any]] = None):
        # plugin_configs 为 None 则，plugin_config_datas 设置 [] 则清空对应配置
        plugin_config_datas = (
            TypeAdapter(Optional[List[PluginConfigData]]).validate_python(plugin_configs) if plugin_configs else []
        )

        scope_id_to_plugin_configs = {stage_id: plugin_config_datas}
        synchronizer = PluginSynchronizer()
        synchronizer.sync(
            gateway_id=gateway_id,
            scope_type=PluginBindingScopeEnum.STAGE,
            scope_id_to_plugin_configs=scope_id_to_plugin_configs,
        )


class StageSyncOutputSLZ(serializers.Serializer):
    id = serializers.IntegerField(read_only=True, help_text="stage id")
    name = serializers.CharField(read_only=True, help_text="stage name")

    class Meta:
        ref_name = "apigateway.apis.v2.sync.serializers.StageSyncOutputSLZ"


class ResourceSyncOutputSLZ(serializers.Serializer):
    added = serializers.ListField(child=serializers.DictField())
    updated = serializers.ListField(child=serializers.DictField())
    deleted = serializers.ListField(child=serializers.DictField())

    class Meta:
        ref_name = "apigateway.apis.v2.sync.serializers.ResourceSyncOutputSLZ"


class ResourceImportInputSLZ(serializers.Serializer):
    gateway = serializers.HiddenField(default=CurrentGatewayDefault())
    content = serializers.CharField(allow_blank=False, required=True, help_text="导入内容，yaml/json 格式字符串")
    delete = serializers.BooleanField(required=False, default=False)
    doc_language = serializers.ChoiceField(
        choices=DocLanguageEnum.get_choices(),
        allow_blank=True,
        allow_null=True,
        required=False,
        help_text="文档语言，en: 英文，zh: 中文",
    )

    class Meta:
        ref_name = "apigateway.apis.v2.sync.serializers.ResourceImportInputSLZ"


class SDKGenerateInputSLZ(serializers.Serializer):
    resource_version = serializers.CharField(max_length=128, help_text="资源版本")
    languages = serializers.ListField(
        child=serializers.ChoiceField(choices=ProgrammingLanguageEnum.get_choices()),
        help_text="需要生成SDK的语言列表",
        default=[ProgrammingLanguageEnum.PYTHON.value],
    )
    version = serializers.CharField(default="", max_length=128, help_text="版本号")

    class Meta:
        ref_name = "apigateway.apis.v2.sync.serializers.SDKGenerateInputSLZ"


class SDKGenerateOutputSLZ(serializers.Serializer):
    name = serializers.CharField(help_text="SDK名称")
    version = serializers.CharField(help_text="版本号")
    url = serializers.CharField(help_text="下载链接")

    class Meta:
        ref_name = "apigateway.apis.v2.sync.serializers.SDKGenerateOutputSLZ"


class DocImportByArchiveInputSLZ(serializers.Serializer):
    file = serializers.FileField(required=True, help_text="导入的归档文档文件")

    class Meta:
        ref_name = "apigateway.apis.v2.sync.serializers.DocImportByArchiveInputSLZ"


class GatewayRelatedAppsAddInputSLZ(serializers.Serializer):
    related_app_codes = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=False,
        required=True,
        max_length=10,
        validators=[BKAppCodeListValidator()],
    )

    class Meta:
        ref_name = "apigateway.apis.v2.sync.serializers.GatewayRelatedAppsAddInputSLZ"


class GatewayPermissionListInputSLZ(serializers.Serializer):
    bk_app_code = serializers.CharField(required=False)
    grant_dimension = serializers.ChoiceField(choices=FormattedGrantDimensionEnum.get_choices(), required=True)

    class Meta:
        ref_name = "apigateway.apis.v2.sync.serializers.GatewayPermissionListInputSLZ"


class GatewayPermissionListOutputSLZ(serializers.Serializer):
    # common fields
    bk_app_code = serializers.CharField()
    expires = serializers.SerializerMethodField()
    grant_dimension = serializers.ChoiceField(choices=FormattedGrantDimensionEnum.get_choices())

    # only for resource permission
    # grant_type = serializers.ChoiceField(choices=GrantTypeEnum.get_choices())
    resource_id = serializers.IntegerField(required=False)
    resource_name = serializers.CharField(required=False)

    class Meta:
        ref_name = "apigateway.apis.v2.sync.serializers.GatewayPermissionListOutputSLZ"

    def get_expires(self, obj):
        expires = (
            None
            if (not obj.get("expires") or NeverExpiresTime.is_never_expired(obj.get("expires")))
            else obj.get("expires")
        )
        return serializers.DateTimeField(allow_null=True, required=False).to_representation(expires)


class GatewayAppPermissionGrantInputSLZ(serializers.Serializer):
    """
    网关关联应用，主动为应用授权访问网关API的权限
    """

    # 主动授权时，应用可能尚未创建，因此不校验 app_code 是否存在
    target_app_code = serializers.CharField(label="", max_length=32, required=True)
    expire_days = serializers.IntegerField(required=False)
    grant_dimension = serializers.ChoiceField(choices=GrantDimensionEnum.get_choices())
    resource_names = serializers.ListField(
        child=serializers.CharField(required=True), allow_empty=True, required=False
    )

    class Meta:
        ref_name = "apigateway.apis.v2.sync.serializers.GatewayAppPermissionGrantInputSLZ"


class ResourceVersionCreateInputSLZ(serializers.Serializer):
    gateway = serializers.HiddenField(default=CurrentGatewayDefault())
    version = serializers.RegexField(SEMVER_PATTERN, max_length=64, required=True)
    comment = serializers.CharField(allow_blank=True, allow_null=True, max_length=512, required=False)

    class Meta:
        ref_name = "apigateway.apis.v2.sync.serializers.ResourceVersionCreateInputSLZ"
        validators = [ResourceVersionValidator()]


class ResourceVersionListInputSLZ(serializers.Serializer):
    version = serializers.CharField(required=False)

    class Meta:
        ref_name = "apigateway.apis.v2.sync.serializers.ResourceVersionListInputSLZ"


class ResourceVersionListOutputSLZ(serializers.Serializer):
    version = serializers.CharField(read_only=True)
    comment = serializers.CharField(read_only=True)

    class Meta:
        ref_name = "apigateway.apis.v2.sync.serializers.ResourceVersionListOutputSLZ"


class GatewayResourceVersionLatestRetrieveOutputSLZ(serializers.Serializer):
    version = serializers.CharField(help_text="资源版本号")

    class Meta:
        ref_name = "apigateway.apis.v2.sync.serializers.GatewayResourceVersionLatestRetrieveOutputSLZ"


class ReleaseInputSLZ(serializers.Serializer):
    gateway = serializers.HiddenField(default=CurrentGatewayDefault())
    version = serializers.RegexField(SEMVER_PATTERN, max_length=64, required=False)
    stage_names = serializers.ListField(child=serializers.CharField(max_length=64), allow_empty=True, default=list)
    comment = serializers.CharField(max_length=512, allow_blank=True, default="")

    class Meta:
        ref_name = "apigateway.apis.v2.sync.serializers.ReleaseInputSLZ"

    def to_internal_value(self, data):
        data = super().to_internal_value(data)
        data["resource_version_id"] = self._get_resource_version_id(
            data["gateway"],
            data.get("version"),
        )
        data["stage_ids"] = StageHandler.get_stage_ids(data["gateway"], data["stage_names"])
        return data

    def _get_resource_version_id(self, gateway, version: Optional[str]) -> int:
        if version:
            resource_version_id = ResourceVersion.objects.get_id_by_version(gateway.id, version)
            if not resource_version_id:
                raise serializers.ValidationError({"version": _("版本【{version}】不存在。").format(version=version)})
            return resource_version_id

        raise serializers.ValidationError({"version": "请指定待发布的版本"})


class ReleaseOutputSLZ(serializers.Serializer):
    version = serializers.CharField(help_text="资源版本号")
    stage_names = serializers.ListField(
        child=serializers.CharField(max_length=64), allow_empty=True, default=list, help_text="发布到的环境名称列表"
    )

    class Meta:
        ref_name = "apigateway.apis.v2.sync.serializers.ReleaseOutputSLZ"
