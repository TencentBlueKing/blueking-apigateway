# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关 (BlueKing - APIGateway) available.
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
from django.conf import settings
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from apigateway.apps.plugin.constants import PluginBindingScopeEnum
from apigateway.biz.constants import MAX_BACKEND_TIMEOUT_IN_SECOND
from apigateway.biz.stage import StageSyncHandler
from apigateway.biz.validators import (
    MaxCountPerGatewayValidator,
    ProgrammableGatewayStageNameValidator,
    SchemeHostInputValidator,
    StageVarsValidator,
    UpstreamValidator,
)
from apigateway.common.constants import DOMAIN_PATTERN, HEADER_KEY_PATTERN, CallSourceTypeEnum
from apigateway.common.django.validators import NameValidator
from apigateway.common.fields import CurrentGatewayDefault
from apigateway.common.i18n.field import SerializerTranslatedField
from apigateway.common.mixins.serializers import ExtensibleFieldMixin
from apigateway.core.constants import (
    DEFAULT_BACKEND_NAME,
    DEFAULT_LB_HOST_WEIGHT,
    STAGE_NAME_PATTERN,
    BackendKindEnum,
    HashOnTypeEnum,
    LoadBalanceTypeEnum,
)
from apigateway.core.models import Backend, BackendConfig, Stage
from apigateway.service.plugin import HeaderRewriteConvertor


class StageV1SLZ(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    description = SerializerTranslatedField(default_field="description_i18n", allow_blank=True)
    description_en = serializers.CharField(required=False, write_only=True)


class ResourceVersionInStageSLZ(serializers.Serializer):
    version = serializers.CharField()


class StageWithResourceVersionV1SLZ(serializers.Serializer):
    name = serializers.CharField()
    resource_version = ResourceVersionInStageSLZ(allow_null=True)
    released = serializers.SerializerMethodField()

    def to_representation(self, instance):
        instance.resource_version = self.context["stage_release"].get(instance.id, {}).get("resource_version")
        return super().to_representation(instance)

    def get_released(self, obj):
        return bool(obj.resource_version)


class HostSLZ(serializers.Serializer):
    host = serializers.RegexField(
        DOMAIN_PATTERN,
        error_messages={
            "invalid": _("host 格式不正确，需以 http:// 或 https:// 开头，且为合法的域名，service 地址或 ip:port"),
        },
    )
    weight = serializers.IntegerField(min_value=1, required=False)

    class Meta:
        ref_name = "apis.open.stage.HostSLZ"


# Health Check Serializers for Open API
class BaseHealthySLZ(serializers.Serializer):
    """Base serializer for healthy configurations"""

    http_statuses = serializers.ListField(
        child=serializers.IntegerField(min_value=100, max_value=599),
        required=False,
        allow_null=True,
        help_text="HTTP状态码列表",
    )
    successes = serializers.IntegerField(
        min_value=1, max_value=254, required=False, allow_null=True, help_text="成功次数"
    )


class PassiveHealthySLZ(BaseHealthySLZ):
    """Passive health check healthy configuration"""

    class Meta:
        ref_name = "apis.open.stage.PassiveHealthySLZ"


class ActiveHealthySLZ(BaseHealthySLZ):
    """Active health check healthy configuration"""

    interval = serializers.IntegerField(min_value=1, required=False, allow_null=True, help_text="检查间隔(秒)")

    class Meta:
        ref_name = "apis.open.stage.ActiveHealthySLZ"


class BaseUnhealthySLZ(serializers.Serializer):
    """Base serializer for unhealthy configurations"""

    http_statuses = serializers.ListField(
        child=serializers.IntegerField(min_value=100, max_value=599),
        required=False,
        allow_null=True,
        help_text="HTTP状态码列表",
    )
    http_failures = serializers.IntegerField(
        min_value=1, max_value=254, required=False, allow_null=True, help_text="HTTP失败次数"
    )
    tcp_failures = serializers.IntegerField(
        min_value=1, max_value=254, required=False, allow_null=True, help_text="TCP失败次数"
    )
    timeouts = serializers.IntegerField(min_value=1, required=False, allow_null=True, help_text="超时次数")


class PassiveUnhealthySLZ(BaseUnhealthySLZ):
    """Passive health check unhealthy configuration"""

    class Meta:
        ref_name = "apis.open.stage.PassiveUnhealthySLZ"


class ActiveUnhealthySLZ(BaseUnhealthySLZ):
    """Active health check unhealthy configuration"""

    interval = serializers.IntegerField(min_value=1, required=False, allow_null=True, help_text="检查间隔(秒)")

    class Meta:
        ref_name = "apis.open.stage.ActiveUnhealthySLZ"


class ActiveCheckSLZ(serializers.Serializer):
    """Active health check configuration"""

    type = serializers.ChoiceField(
        choices=[("http", "HTTP"), ("https", "HTTPS"), ("tcp", "TCP")], default="http", help_text="检查类型"
    )
    timeout = serializers.IntegerField(min_value=1, required=False, allow_null=True, help_text="超时时间(秒)")
    concurrency = serializers.IntegerField(
        min_value=1, max_value=100, required=False, allow_null=True, help_text="并发数"
    )
    http_path = serializers.CharField(required=False, allow_null=True, help_text="HTTP检查路径")
    https_verify_certificate = serializers.BooleanField(required=False, allow_null=True, help_text="HTTPS证书验证")
    # NOTE: 暂时不支持，后续再支持
    # host = serializers.CharField(required=False, allow_null=True, help_text="主机名")
    # port = serializers.IntegerField(min_value=1, max_value=65535, required=False, allow_null=True, help_text="端口")
    # req_headers = serializers.ListField(
    #     child=serializers.CharField(), required=False, allow_null=True, help_text="请求头"
    # )
    healthy = ActiveHealthySLZ(required=False, allow_null=True, help_text="健康配置")
    unhealthy = ActiveUnhealthySLZ(required=False, allow_null=True, help_text="不健康配置")

    class Meta:
        ref_name = "apis.open.stage.ActiveCheckSLZ"


class PassiveCheckSLZ(serializers.Serializer):
    """Passive health check configuration"""

    type = serializers.ChoiceField(
        choices=[("http", "HTTP"), ("https", "HTTPS"), ("tcp", "TCP")], default="http", help_text="检查类型"
    )
    healthy = PassiveHealthySLZ(required=False, allow_null=True, help_text="健康配置")
    unhealthy = PassiveUnhealthySLZ(required=False, allow_null=True, help_text="不健康配置")

    class Meta:
        ref_name = "apis.open.stage.PassiveCheckSLZ"


class CheckSLZ(serializers.Serializer):
    """Health check configuration (active required, passive optional)"""

    active = ActiveCheckSLZ(help_text="主动健康检查")
    passive = PassiveCheckSLZ(required=False, allow_null=True, help_text="被动健康检查")

    class Meta:
        ref_name = "apis.open.stage.CheckSLZ"


class UpstreamsSLZ(serializers.Serializer):
    loadbalance = serializers.ChoiceField(choices=LoadBalanceTypeEnum.get_choices())
    hash_on = serializers.ChoiceField(choices=HashOnTypeEnum.get_choices(), required=False)
    key = serializers.CharField(required=False)

    hosts = serializers.ListField(child=HostSLZ(), allow_empty=False)

    def __init__(self, *args, **kwargs):
        self.allow_empty = kwargs.pop("allow_empty", False)
        super().__init__(*args, **kwargs)

    def _update_hosts(self, data):
        """
        如果负载均衡类型为 RoundRobin 时，将权重设置为默认值
        """
        if data.get("loadbalance") == LoadBalanceTypeEnum.RR.value:
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


class TransformHeadersSLZ(serializers.Serializer):
    set = serializers.DictField(label="设置", child=serializers.CharField(), required=False, allow_empty=True)
    delete = serializers.ListField(label="删除", child=serializers.CharField(), required=False, allow_empty=True)

    def _validate_headers_key(self, value):
        for key in value:
            if not HEADER_KEY_PATTERN.match(key):
                raise serializers.ValidationError(_("Header 键由字母、数字、连接符（-）组成，长度小于 100 个字符。"))
        return value

    def validate_set(self, value):
        return self._validate_headers_key(value)

    def validate_delete(self, value):
        return self._validate_headers_key(value)


class StageProxyHTTPConfigSLZ(serializers.Serializer):
    timeout = serializers.IntegerField(max_value=MAX_BACKEND_TIMEOUT_IN_SECOND, min_value=1)
    upstreams = UpstreamsSLZ(allow_empty=False)
    transform_headers = TransformHeadersSLZ(required=False, default=dict)


class BackendConfigSLZ(UpstreamsSLZ):
    timeout = serializers.IntegerField(max_value=MAX_BACKEND_TIMEOUT_IN_SECOND, min_value=1)
    checks = CheckSLZ(required=False, allow_null=True, help_text="健康检查配置")

    class Meta:
        ref_name = "apis.open.stage.BackendConfigSLZ"


class BackendSLZ(serializers.Serializer):
    name = serializers.CharField(help_text="后端服务名称", required=True)
    config = BackendConfigSLZ(validators=[UpstreamValidator()], required=True, allow_empty=False)

    class Meta:
        ref_name = "apis.open.stage.BackendSLZ"


class RejectUnknownFieldsMixin:
    def to_internal_value(self, data):
        unknown = set(data) - set(self.fields)
        if unknown:
            raise serializers.ValidationError({key: _("不支持的字段。") for key in sorted(unknown)})
        return super().to_internal_value(data)


class AIBackendAuthSLZ(RejectUnknownFieldsMixin, serializers.Serializer):
    header = serializers.DictField(child=serializers.CharField(), required=False)


class AIBackendOptionsSLZ(serializers.Serializer):
    model = serializers.CharField(allow_blank=False)

    def to_internal_value(self, data):
        validated_data = super().to_internal_value(data)
        return {**data, **validated_data}


class AIBackendOverrideSLZ(RejectUnknownFieldsMixin, serializers.Serializer):
    endpoint = serializers.CharField(allow_blank=False)


class AIBackendInstanceSLZ(RejectUnknownFieldsMixin, serializers.Serializer):
    name = serializers.CharField(allow_blank=False)
    provider = serializers.ChoiceField(choices=["openai", "deepseek", "openai-compatible"])
    weight = serializers.IntegerField(min_value=1, max_value=1)
    auth = AIBackendAuthSLZ(required=False)
    options = AIBackendOptionsSLZ()
    override = AIBackendOverrideSLZ(required=False)


class AIBackendConfigSLZ(RejectUnknownFieldsMixin, serializers.Serializer):
    timeout = serializers.IntegerField(min_value=1, default=30000)
    instances = serializers.ListField(child=AIBackendInstanceSLZ(), min_length=1, max_length=1)


class AIBackendSLZ(RejectUnknownFieldsMixin, serializers.Serializer):
    name = serializers.CharField(help_text="模型服务名称")
    config = AIBackendConfigSLZ()


class PluginConfigSLZ(serializers.Serializer):
    type = serializers.CharField(help_text="插件类型名称")
    yaml = serializers.CharField(help_text="插件 yaml 配置")


class StageSLZ(ExtensibleFieldMixin, serializers.ModelSerializer):
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

    backends = serializers.ListSerializer(
        help_text="后端配置", child=BackendSLZ(), allow_null=True, allow_empty=False, required=False
    )
    modelBackends = serializers.ListField(  # noqa: N815 - external API field name
        help_text="模型服务配置", child=AIBackendSLZ(), allow_null=False, allow_empty=False, required=False
    )

    plugin_configs = serializers.ListSerializer(
        help_text="插件配置", child=PluginConfigSLZ(), allow_null=True, required=False
    )

    description = SerializerTranslatedField(
        default_field="description_i18n", allow_blank=True, allow_null=True, max_length=512, required=False
    )

    class Meta:
        ref_name = "apps.stage.StageSLZ"
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
            "modelBackends",
            "plugin_configs",
        )
        extra_kwargs = {
            "description_en": {
                "required": False,
            }
        }
        read_only_fields = ("id", "status")
        non_model_fields = ["proxy_http", "backends", "modelBackends", "plugin_configs", "rate_limit"]
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
            ProgrammableGatewayStageNameValidator(),
        ]

    def validate(self, data):
        StageSyncHandler.validate_plugin_configs(data.get("plugin_configs"))
        if data.get("backends"):
            self._validate_scheme_host(data.get("backends"))

        gateway = data["gateway"]
        if data.get("modelBackends") is not None and not gateway.is_ai_gateway:
            raise serializers.ValidationError({"modelBackends": _("普通网关不支持模型服务。")})
        if not gateway.is_ai_gateway and data.get("proxy_http") is None and data.get("backends") is None:
            raise serializers.ValidationError(_("proxy_http or backends 必须要选择一种方式配置后端服务"))
        if (
            gateway.is_ai_gateway
            and self.instance is None
            and data.get("proxy_http") is None
            and data.get("backends") is None
            and data.get("modelBackends") is None
        ):
            raise serializers.ValidationError(_("proxy_http、backends 和 modelBackends 必须至少配置一项"))
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
            config = StageSyncHandler.build_legacy_backend_config(proxy_http_config)
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

        # 3. create backend configs
        username = self.context["request"].user.username or settings.GATEWAY_DEFAULT_CREATOR
        StageSyncHandler.upsert_backend_configs(
            stage=instance,
            backend_items=validated_data.get("backends", []),
            kind=BackendKindEnum.STANDARD.value,
            username=username,
        )
        StageSyncHandler.upsert_backend_configs(
            stage=instance,
            backend_items=validated_data.get("modelBackends", []),
            kind=BackendKindEnum.AI.value,
            username=username,
        )

        # 4. sync stage plugin
        StageSyncHandler.sync_plugin_configs(
            gateway_id=instance.gateway_id,
            stage_id=instance.id,
            plugin_configs=validated_data.get("plugin_configs", None),
        )

        return instance

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

            backend_config.config = StageSyncHandler.build_legacy_backend_config(proxy_http_config)
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

        # 3. update backend configs
        username = self.context["request"].user.username or settings.GATEWAY_DEFAULT_CREATOR
        StageSyncHandler.upsert_backend_configs(
            stage=instance,
            backend_items=validated_data.get("backends", []),
            kind=BackendKindEnum.STANDARD.value,
            username=username,
        )
        StageSyncHandler.upsert_backend_configs(
            stage=instance,
            backend_items=validated_data.get("modelBackends", []),
            kind=BackendKindEnum.AI.value,
            username=username,
        )

        # 4. sync stage plugin
        StageSyncHandler.sync_plugin_configs(
            gateway_id=instance.gateway_id,
            stage_id=instance.id,
            plugin_configs=validated_data.get("plugin_configs", None),
        )

        return instance

    def _validate_scheme_host(self, backends):
        if backends is None:
            return
        for backend in backends:
            validator = SchemeHostInputValidator(hosts=backend["config"]["hosts"], backend=backend)
            validator.validate_scheme(CallSourceTypeEnum.OpenAPI.value)
