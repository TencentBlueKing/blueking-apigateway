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
from typing import Optional

from django.conf import settings
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from tencent_apigateway_common.i18n.field import SerializerTranslatedField

from apigateway.apps.stage.validators import StageVarsValidator
from apigateway.biz.stage import StageHandler
from apigateway.common.contexts import StageProxyHTTPContext, StageRateLimitContext
from apigateway.common.fields import CurrentGatewayDefault
from apigateway.common.mixins.serializers import ExtensibleFieldMixin
from apigateway.core.constants import (
    DEFAULT_LB_HOST_WEIGHT,
    DOMAIN_PATTERN,
    HEADER_KEY_PATTERN,
    MAX_BACKEND_TIMEOUT_IN_SECOND,
    STAGE_NAME_PATTERN,
    LoadBalanceTypeEnum,
)
from apigateway.core.models import MicroGateway, Stage
from apigateway.core.signals import reversion_update_signal
from apigateway.core.validators import MaxCountPerGatewayValidator


class HostSLZ(serializers.Serializer):
    host = serializers.RegexField(DOMAIN_PATTERN)
    weight = serializers.IntegerField(min_value=1, required=False)


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
    # add = serializers.DictField(child=serializers.CharField(), required=False, allow_empty=True)
    # append = serializers.DictField(child=serializers.CharField(), required=False, allow_empty=True)
    # replace = serializers.DictField(child=serializers.CharField(), required=False, allow_empty=True)
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


class RateSLZ(serializers.Serializer):
    tokens = serializers.IntegerField(min_value=0)
    period = serializers.IntegerField(min_value=1)


class RateLimitSLZ(serializers.Serializer):
    enabled = serializers.BooleanField()
    rate = RateSLZ(required=False)

    def to_internal_value(self, data):
        return super().to_internal_value({k: v for k, v in data.items() if v not in ({},)})


class StageSLZ(ExtensibleFieldMixin, serializers.ModelSerializer):
    api = serializers.HiddenField(default=CurrentGatewayDefault())
    name = serializers.RegexField(STAGE_NAME_PATTERN)
    vars = serializers.DictField(
        label="环境变量",
        child=serializers.CharField(allow_blank=True, required=True),
        default=dict,
    )
    proxy_http = StageProxyHTTPConfigSLZ()
    rate_limit = RateLimitSLZ(required=False)
    micro_gateway_id = serializers.UUIDField(allow_null=True, required=False)
    description = SerializerTranslatedField(
        default_field="description_i18n", allow_blank=True, allow_null=True, max_length=512, required=False
    )

    class Meta:
        model = Stage
        fields = (
            "api",
            "id",
            "name",
            "description",
            "description_en",
            "vars",
            "status",
            "proxy_http",
            "rate_limit",
            "micro_gateway_id",
        )
        extra_kwargs = {
            "description_en": {
                "required": False,
            }
        }
        read_only_fields = ("id", "status")
        non_model_fields = ["proxy_http", "rate_limit"]
        lookup_field = "id"

        validators = [
            UniqueTogetherValidator(
                queryset=Stage.objects.all(),
                fields=["api", "name"],
                message=gettext_lazy("网关下环境名称已经存在。"),
            ),
            MaxCountPerGatewayValidator(
                Stage,
                max_count_callback=lambda gateway: gateway.max_stage_count,
                message=gettext_lazy("每个网关最多创建 {max_count} 个环境。"),
            ),
            StageVarsValidator(),
        ]

    def validate(self, data):
        self._validate_micro_gateway_stage_unique(data.get("micro_gateway_id"))
        return data

    def to_representation(self, instance):
        instance.proxy_http = StageProxyHTTPContext().get_config(instance.id)
        instance.rate_limit = StageRateLimitContext().get_config(instance.id)

        return super().to_representation(instance)

    def create(self, validated_data):
        # 1. save stage
        instance = super().create(validated_data)

        # 2. save related data
        StageHandler().save_related_data(
            instance,
            validated_data["proxy_http"],
            validated_data.get("rate_limit") or settings.DEFAULT_STAGE_RATE_LIMIT_CONFIG,
        )

        # 3. record audit log
        StageHandler().add_create_audit_log(validated_data["api"], instance, validated_data.get("created_by", ""))

        return instance

    def update(self, instance, validated_data):
        validated_data.pop("name", None)
        # 仅能通过发布更新 status，不允许直接更新 status
        validated_data.pop("status", None)
        validated_data.pop("created_by", None)

        # 1. 更新数据
        instance = super().update(instance, validated_data)

        # 2. save related data
        StageHandler().save_related_data(
            instance,
            validated_data["proxy_http"],
            validated_data.get("rate_limit"),
        )

        # 3. send signal
        reversion_update_signal.send(sender=Stage, instance_id=instance.id, action="update")

        # 4. 记录更新日志
        StageHandler().add_update_audit_log(validated_data["api"], instance, validated_data.get("updated_by", ""))

        return instance

    def validate_micro_gateway_id(self, value) -> Optional[uuid.UUID]:
        if value is None:
            return None

        gateway = self.context["request"].gateway
        if not MicroGateway.objects.filter(api=gateway, id=value).exists():
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


class QueryStageSLZ(serializers.Serializer):
    name = serializers.CharField(allow_blank=True, required=False)
    order_by = serializers.ChoiceField(
        choices=["name", "-name", "updated_time", "-updated_time"],
        allow_blank=True,
        required=False,
    )


class ListStageSLZ(serializers.ModelSerializer):
    deletable = serializers.BooleanField()
    release_status = serializers.SerializerMethodField()
    release_time = serializers.SerializerMethodField()
    resource_version_name = serializers.SerializerMethodField()
    resource_version_title = serializers.SerializerMethodField()
    resource_version_display = serializers.SerializerMethodField()
    access_strategies = serializers.SerializerMethodField()
    plugins = serializers.SerializerMethodField()
    micro_gateway_id = serializers.SerializerMethodField()
    micro_gateway_name = serializers.SerializerMethodField()
    description = SerializerTranslatedField(
        default_field="description_i18n", allow_blank=True, allow_null=True, max_length=512, required=False
    )

    class Meta:
        model = Stage
        fields = (
            "id",
            "name",
            "description",
            "description_en",
            "status",
            "deletable",
            "release_status",
            "release_time",
            "resource_version_name",
            "resource_version_title",
            "resource_version_display",
            "access_strategies",
            "plugins",
            "micro_gateway_id",
            "micro_gateway_name",
        )

    def get_release_status(self, obj):
        return self.context["stage_release"].get(obj.id, {}).get("release_status", False)

    def get_release_time(self, obj):
        release_time = self.context["stage_release"].get(obj.id, {}).get("release_time", "")
        return serializers.DateTimeField(allow_null=True, required=False).to_representation(release_time)

    def get_resource_version_name(self, obj):
        return self.context["stage_release"].get(obj.id, {}).get("resource_version_name", "")

    def get_resource_version_title(self, obj):
        return self.context["stage_release"].get(obj.id, {}).get("resource_version_title", "")

    def get_resource_version_display(self, obj):
        return self.context["stage_release"].get(obj.id, {}).get("resource_version_display", "")

    def get_access_strategies(self, obj):
        return self.context["scope_bindings"].get(obj.id, [])

    def get_plugins(self, obj):
        return []

    def get_micro_gateway_id(self, obj) -> Optional[uuid.UUID]:
        fields = self.context["stage_id_to_micro_gateway_fields"].get(obj.id) or {}
        return fields.get("id")

    def get_micro_gateway_name(self, obj) -> str:
        fields = self.context["stage_id_to_micro_gateway_fields"].get(obj.id) or {}
        return fields.get("name", "")


class QueryStageReleaseSLZ(serializers.Serializer):
    ids = serializers.ListField(child=serializers.IntegerField(), allow_empty=False)


class ListStageReleaseSLZ(serializers.ModelSerializer):
    release_status = serializers.SerializerMethodField()
    release_time = serializers.SerializerMethodField()
    resource_version_id = serializers.SerializerMethodField()
    resource_version_name = serializers.SerializerMethodField()
    resource_version_title = serializers.SerializerMethodField()
    resource_version_display = serializers.SerializerMethodField()

    class Meta:
        model = Stage
        fields = [
            "id",
            "name",
            "release_status",
            "release_time",
            "resource_version_id",
            "resource_version_name",
            "resource_version_title",
            "resource_version_display",
        ]

    def get_release_status(self, obj):
        return self.context["stage_release"].get(obj.id, {}).get("release_status", False)

    def get_release_time(self, obj):
        release_time = self.context["stage_release"].get(obj.id, {}).get("release_time", "")
        return serializers.DateTimeField(allow_null=True, required=False).to_representation(release_time)

    def get_resource_version_id(self, obj):
        return self.context["stage_release"].get(obj.id, {}).get("resource_version_id", None)

    def get_resource_version_name(self, obj):
        return self.context["stage_release"].get(obj.id, {}).get("resource_version_name", "")

    def get_resource_version_title(self, obj):
        return self.context["stage_release"].get(obj.id, {}).get("resource_version_title", "")

    def get_resource_version_display(self, obj):
        return self.context["stage_release"].get(obj.id, {}).get("resource_version_display", "")


class ListStageBasicSLZ(serializers.ModelSerializer):
    proxy_http = serializers.SerializerMethodField()
    description = SerializerTranslatedField(default_field="description_i18n", allow_blank=True)

    class Meta:
        model = Stage
        fields = [
            "id",
            "name",
            "description",
            "description_en",
            "status",
            "vars",
            "proxy_http",
        ]

    def get_proxy_http(self, obj):
        return self.context["proxy_http_id_config_map"][obj.id]


class UpdateStageStatusSLZ(serializers.ModelSerializer):
    class Meta:
        model = Stage
        fields = ("status",)
        lookup_field = "id"
