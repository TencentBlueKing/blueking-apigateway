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
from collections.abc import Mapping

from django.utils.translation import gettext as _
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from apigateway.apis.backend_config import restore_masked_header_values, validate_ai_backend_config
from apigateway.apis.web.constants import BACKEND_CONFIG_SCHEME_MAP
from apigateway.apis.web.serializers import BaseBackendConfigSLZ
from apigateway.biz.validators import SchemeHostInputValidator
from apigateway.common.constants import CallSourceTypeEnum
from apigateway.common.fields import CurrentGatewayDefault
from apigateway.core.backend_config import BACKEND_CONFIG_TYPES
from apigateway.core.constants import DEFAULT_BACKEND_NAME, BackendKindEnum, BackendTypeEnum
from apigateway.core.models import Backend, BackendConfig, Stage

from .constants import BACKEND_NAME_PATTERN


class BackendConfigSLZ(BaseBackendConfigSLZ):
    stage_id = serializers.IntegerField()


class AIBackendConfigSLZ(serializers.Serializer):
    stage_id = serializers.IntegerField()

    def to_internal_value(self, data):
        if not isinstance(data, Mapping):
            return super().to_internal_value(data)

        stage = super().to_internal_value(data)
        raw_config = {key: value for key, value in data.items() if key != "stage_id"}
        return {"stage_id": stage["stage_id"], **validate_ai_backend_config(raw_config)}


class BackendInputSLZ(serializers.Serializer):
    gateway = serializers.HiddenField(default=CurrentGatewayDefault())
    name = serializers.RegexField(BACKEND_NAME_PATTERN, help_text="后端服务名称")
    description = serializers.CharField(
        allow_blank=True, allow_null=True, default="", max_length=512, required=False, help_text="描述"
    )
    type = serializers.ChoiceField(
        choices=BackendTypeEnum.get_choices(), default=BackendTypeEnum.HTTP.value, help_text="类型"
    )
    kind = serializers.ChoiceField(choices=BackendKindEnum.get_choices(), required=False)
    configs = serializers.ListField(child=serializers.DictField(), allow_empty=False, help_text="配置")

    class Meta:
        ref_name = "apigateway.apis.web.backend.serializers.BackendInputSLZ"
        validators = [
            UniqueTogetherValidator(
                queryset=Backend.objects.all(),
                fields=["gateway", "name"],
                message=_("网关下后端服务名称已经存在。"),
            ),
        ]

    def validate(self, attrs):
        kind = self._validate_kind(attrs)
        attrs["kind"] = kind
        attrs["configs"] = self._validate_configs(kind, attrs["configs"])
        stage_id_name = self._validate_stages(attrs["gateway"], attrs["configs"])
        self._validate_config_values(attrs, stage_id_name)
        return attrs

    def _validate_kind(self, attrs):
        kind = attrs.get(
            "kind",
            self.instance.kind if self.instance else BackendKindEnum.STANDARD.value,
        )
        if self.instance and kind != self.instance.kind:
            raise serializers.ValidationError({"kind": _("后端服务类型创建后不能修改。")})
        if kind == BackendKindEnum.AI.value:
            if not attrs["gateway"].is_ai_gateway:
                raise serializers.ValidationError({"kind": _("普通网关不支持模型服务。")})
            if attrs["type"] != BackendTypeEnum.HTTP.value:
                raise serializers.ValidationError({"type": _("模型服务仅支持 HTTP 类型。")})
        return kind

    def _validate_configs(self, kind, configs):
        validated_configs = []
        for config in configs:
            config_slz_class = AIBackendConfigSLZ if kind == BackendKindEnum.AI.value else BackendConfigSLZ
            config_slz = config_slz_class(data=config)
            config_slz.is_valid(raise_exception=True)
            validated_configs.append(config_slz.validated_data)
        return validated_configs

    def _validate_stages(self, gateway, configs):
        # 校验网关下所有的stage的配置都提交了
        stages = Stage.objects.filter(gateway=gateway).only("id", "name")
        stage_id_name = {stage.id: stage.name for stage in stages}

        for backend_config in configs:
            if backend_config["stage_id"] not in stage_id_name:
                raise serializers.ValidationError(
                    _("网关【{gateway}】下不存在id为【{stage_id}】的环境。").format(
                        gateway=gateway.name, stage_id=backend_config["stage_id"]
                    )
                )

        config_stage_id = {backend_config["stage_id"] for backend_config in configs}
        for stage in stages:
            if stage.id not in config_stage_id:
                raise serializers.ValidationError(
                    _("后端服务缺少网关【{gateway}】下【{stage_name}】环境配置。").format(
                        gateway=gateway.name, stage_name=stage.name
                    )
                )
        return stage_id_name

    def _validate_config_values(self, attrs, stage_id_name):
        existing_configs = {}
        if self.instance:
            existing_configs = {
                item.stage_id: item.config for item in BackendConfig.objects.filter(backend=self.instance)
            }

        for backend_config in attrs["configs"]:
            if attrs["kind"] == BackendKindEnum.AI.value:
                restore_masked_header_values(
                    backend_config,
                    existing_configs.get(backend_config["stage_id"]),
                )
            raw_config = {key: value for key, value in backend_config.items() if key != "stage_id"}
            try:
                BACKEND_CONFIG_TYPES[attrs["kind"]].model_validate(raw_config)
            except ValueError as err:
                raise serializers.ValidationError({"configs": str(err)}) from err

            if attrs["kind"] == BackendKindEnum.AI.value:
                continue
            for host in backend_config["hosts"]:
                # 校验 backend 下类型选择的关联性
                if host["scheme"] not in BACKEND_CONFIG_SCHEME_MAP[attrs["type"]]:
                    raise serializers.ValidationError(
                        _("环境【{stage_name}】的配置Scheme【{scheme}】不合法。").format(
                            stage_name=stage_id_name[backend_config["stage_id"]], scheme=host["scheme"]
                        )
                    )
                # 校验 backend 下的 host 下的类型的唯一性
                backend_instance = Backend(name=attrs["name"], type=attrs["type"])
                validator = SchemeHostInputValidator(hosts=backend_config["hosts"], backend=backend_instance)
                validator.validate_scheme(CallSourceTypeEnum.Web.value)


class BackendListOutputSLZ(serializers.ModelSerializer):
    resource_count = serializers.SerializerMethodField(help_text="资源数量")
    deletable = serializers.SerializerMethodField(help_text="是否可删除")

    class Meta:
        ref_name = "apigateway.apis.web.backend.serializers.BackendListOutputSLZ"
        model = Backend
        fields = ["id", "name", "description", "kind", "type", "resource_count", "deletable", "updated_time"]

    def get_resource_count(self, obj):
        return self.context["resource_count"].get(obj.id, 0)

    def get_deletable(self, obj):
        if obj.name == DEFAULT_BACKEND_NAME:
            return False

        return self.get_resource_count(obj) == 0


class BackendRetrieveOutputSLZ(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField(help_text="名称")
    description = serializers.CharField(help_text="描述")
    kind = serializers.ChoiceField(choices=BackendKindEnum.get_choices())
    type = serializers.ChoiceField(choices=BackendTypeEnum.get_choices())
    configs = serializers.SerializerMethodField(help_text="配置")

    class Meta:
        ref_name = "apigateway.apis.web.backend.serializers.BackendRetrieveOutputSLZ"

    def get_configs(self, obj):
        backend_configs = BackendConfig.objects.filter(backend=obj).prefetch_related("stage")

        data = []
        for backend_config in backend_configs:
            config = backend_config.get_config_for_display()
            config["stage"] = {
                "id": backend_config.stage.id,
                "name": backend_config.stage.name,
            }

            data.append(config)

        return data


class StageSLZ(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField(help_text="")

    class Meta:
        ref_name = "apigateway.apis.web.backend.serializers.StageSLZ"


class BackendUpdateOutputSLZ(serializers.Serializer):
    bound_stages = serializers.ListField(child=StageSLZ(), help_text="已绑定的环境列表")
    updated_stages = serializers.ListField(child=StageSLZ(), help_text="更改的环境列表")

    class Meta:
        ref_name = "apigateway.apis.web.backend.serializers.BackendUpdateOutputSLZ"
