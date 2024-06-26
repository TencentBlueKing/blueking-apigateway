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
import uuid
from typing import Any, Dict, List, Optional

from django.conf import settings
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from pydantic import parse_obj_as
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from apigateway.apis.web.stage.validators import StageVarsValidator
from apigateway.apps.plugin.constants import PluginBindingScopeEnum
from apigateway.apps.plugin.models import PluginType
from apigateway.biz.constants import MAX_BACKEND_TIMEOUT_IN_SECOND
from apigateway.biz.plugin.plugin_synchronizers import PluginConfigData, PluginSynchronizer
from apigateway.biz.validators import MaxCountPerGatewayValidator
from apigateway.common.django.validators import NameValidator
from apigateway.common.fields import CurrentGatewayDefault
from apigateway.common.i18n.field import SerializerTranslatedField
from apigateway.common.mixins.serializers import ExtensibleFieldMixin
from apigateway.common.plugin.header_rewrite import HeaderRewriteConvertor
from apigateway.common.plugin.plugin_validators import PluginConfigYamlValidator
from apigateway.core.constants import (
    DEFAULT_BACKEND_NAME,
    DEFAULT_LB_HOST_WEIGHT,
    STAGE_NAME_PATTERN,
    BackendTypeEnum,
    LoadBalanceTypeEnum,
)
from apigateway.core.models import Backend, BackendConfig, MicroGateway, Stage

from .constants import DOMAIN_PATTERN, HEADER_KEY_PATTERN


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
    host = serializers.RegexField(DOMAIN_PATTERN)
    weight = serializers.IntegerField(min_value=1, required=False)

    class Meta:
        ref_name = "apis.open.stage.HostSLZ"


class UpstreamsSLZ(serializers.Serializer):
    loadbalance = serializers.ChoiceField(choices=LoadBalanceTypeEnum.get_choices())
    hosts = serializers.ListField(child=HostSLZ(), allow_empty=False)

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


class BackendConfigSLZ(UpstreamsSLZ):
    timeout = serializers.IntegerField(max_value=MAX_BACKEND_TIMEOUT_IN_SECOND, min_value=1)

    class Meta:
        ref_name = "apis.open.stage.BackendConfigSLZ"


class BackendSLZ(serializers.Serializer):
    name = serializers.CharField(help_text="后端服务名称", required=True)
    config = BackendConfigSLZ(allow_empty=False)

    class Meta:
        ref_name = "apis.open.stage.BackendSLZ"


class PluginConfigSLZ(serializers.Serializer):
    type = serializers.CharField(help_text="插件类型名称")
    yaml = serializers.CharField(help_text="插件yaml配置")


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

    backends = serializers.ListSerializer(help_text="后端配置", child=BackendSLZ(), allow_null=True, required=False)

    plugin_configs = serializers.ListSerializer(
        help_text="插件配置", child=PluginConfigSLZ(), allow_null=True, required=False
    )

    micro_gateway_id = serializers.UUIDField(allow_null=True, required=False)
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
            "plugin_configs",
            "micro_gateway_id",
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
        self._validate_micro_gateway_stage_unique(data.get("micro_gateway_id"))
        self._validate_plugin_configs(data.get("plugin_configs"))
        self._validate_backend_hosts(data.get("backends"))
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

    def validate_micro_gateway_id(self, value) -> Optional[uuid.UUID]:
        if value is None:
            return None

        gateway = self.context["request"].gateway
        if not MicroGateway.objects.filter(gateway=gateway, id=value).exists():
            raise serializers.ValidationError(_("微网关实例不存在，id={value}。").format(value=value))

        return value

    def _validate_micro_gateway_stage_unique(self, micro_gateway_id: Optional[uuid.UUID]):
        """校验 micro_gateway 仅绑定到一个环境"""
        if not micro_gateway_id:
            return

        queryset = Stage.objects.filter(micro_gateway_id=micro_gateway_id)
        if self.instance is not None:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError(_("微网关实例已绑定到其它环境。"))

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
            except Exception as err:
                raise serializers.ValidationError(
                    _("插件配置校验失败，插件类型：{plugin_type_code}，错误信息：{err}。").format(
                        plugin_type_code=plugin_type.code,
                        err=err,
                    )
                )

    def _validate_backend_hosts(self, backends):
        for backend in backends:
            hosts = backend["config"]["hosts"]
            schemes = {host.get("scheme") for host in hosts}
            if len(schemes) > 1 and backend.type == BackendTypeEnum.HTTP.value:
                raise serializers.ValidationError(
                    _("后端服务【{backend_name}】的配置 scheme 同时存在 http 和 https， 需要保持一致。").format(
                        backend_name=backend.name
                    )
                )
            if len(schemes) > 1 and backend.type == BackendTypeEnum.GRPC.value:
                raise serializers.ValidationError(
                    _("后端服务【{backend_name}】的配置 scheme 同时存在 grpc 和 grpcs， 需要保持一致.").format(
                        backend_name=backend.name
                    )
                )

    def _sync_plugins(self, gateway_id: int, stage_id: int, plugin_configs: Optional[Dict[str, Any]] = None):
        # plugin_configs为None则，plugin_config_datas 设置[]则清空对应配置
        plugin_config_datas = parse_obj_as(Optional[List[PluginConfigData]], plugin_configs) if plugin_configs else []
        scope_id_to_plugin_configs = {stage_id: plugin_config_datas}
        synchronizer = PluginSynchronizer()
        synchronizer.sync(
            gateway_id=gateway_id,
            scope_type=PluginBindingScopeEnum.STAGE,
            scope_id_to_plugin_configs=scope_id_to_plugin_configs,
        )
