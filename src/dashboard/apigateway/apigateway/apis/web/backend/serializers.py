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
from django.utils.translation import gettext as _
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from apigateway.common.fields import CurrentGatewayDefault
from apigateway.core.constants import HOST_WITHOUT_SCHEME_PATTERN, MAX_BACKEND_TIMEOUT_IN_SECOND, BackendTypeEnum
from apigateway.core.models import Backend, BackendConfig, Stage

from .constants import (
    BACKEND_CONFIG_SCHEME_MAP,
    BACKEND_NAME_PATTERN,
    BackendConfigSchemeEnum,
    BackendConfigTypeEnum,
    LoadBalanceTypeEnum,
)


class HostSLZ(serializers.Serializer):
    scheme = serializers.ChoiceField(choices=BackendConfigSchemeEnum.get_choices())
    host = serializers.RegexField(HOST_WITHOUT_SCHEME_PATTERN)
    weight = serializers.IntegerField(min_value=1, required=False)


class BaseBackendConfigSLZ(serializers.Serializer):
    type = serializers.ChoiceField(
        choices=BackendConfigTypeEnum.get_choices(), default=BackendConfigTypeEnum.NODE.value
    )
    timeout = serializers.IntegerField(max_value=MAX_BACKEND_TIMEOUT_IN_SECOND, min_value=1)
    loadbalance = serializers.ChoiceField(choices=LoadBalanceTypeEnum.get_choices())
    hosts = serializers.ListField(child=HostSLZ(), allow_empty=False)


class BackendConfigSLZ(BaseBackendConfigSLZ):
    stage_id = serializers.IntegerField()


class BackendInputSLZ(serializers.Serializer):
    gateway = serializers.HiddenField(default=CurrentGatewayDefault())
    name = serializers.RegexField(BACKEND_NAME_PATTERN)
    description = serializers.CharField(allow_blank=True, allow_null=True, max_length=512, required=False)
    type = serializers.ChoiceField(choices=BackendTypeEnum.get_choices(), default=BackendTypeEnum.HTTP.value)
    configs = serializers.ListField(child=BackendConfigSLZ(), allow_empty=False)

    class Meta:
        validators = [
            UniqueTogetherValidator(
                queryset=Backend.objects.all(),
                fields=["gateway", "name"],
                message=_("网关下后端服务名称已经存在。"),
            ),
        ]

    def validate(self, attrs):
        # 校验网关下所有的stage的配置都提交了
        stages = Stage.objects.filter(gateway=attrs["gateway"]).only("id", "name")
        stage_id_name = {stage.id: stage.name for stage in stages}

        for backend_config in attrs["configs"]:
            if backend_config["stage_id"] not in stage_id_name:
                raise serializers.ValidationError(
                    _("网关【{gateway}】下不存在id为【{stage_id}】的环境。").format(
                        gateway=attrs["gateway"].name, stage_id=backend_config["stage_id"]
                    )
                )

        config_stage_id = set([backend_config["stage_id"] for backend_config in attrs["configs"]])
        for stage in stages:
            if stage.id not in config_stage_id:
                raise serializers.ValidationError(
                    _("后端服务缺少网关【{gateway}】下【{stage_name}】环境配置。").format(
                        gateway=attrs["gateway"].name, stage_name=stage.name
                    )
                )

        # 校验backend下类型选择的关联性
        for backend_config in attrs["configs"]:
            for host in backend_config["hosts"]:
                if host["scheme"] not in BACKEND_CONFIG_SCHEME_MAP[attrs["type"]]:
                    raise serializers.ValidationError(
                        _("环境【{stage_name}】的配置Scheme【{scheme}】不合法。").format(
                            stage_name=stage_id_name[backend_config["stage_id"]], scheme=host["scheme"]
                        )
                    )
        return attrs


class BackendListOutputSLZ(serializers.ModelSerializer):
    resource_count = serializers.SerializerMethodField()
    deletable = serializers.SerializerMethodField()

    class Meta:
        model = Backend
        fields = ["id", "name", "description", "resource_count", "deletable", "updated_time"]

    def get_resource_count(self, obj):
        # TODO 从resource关联的backend来算数量
        return 0

    def get_deletable(self, obj):
        # 提一个方法判断Backend是否可删除
        # TODO 查询Resource关联是否存在
        # TODO 查询Stage关联是否存在
        return True


class BackendRetrieveOutputSLZ(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    description = serializers.CharField()
    configs = serializers.SerializerMethodField()

    def get_configs(self, obj):
        backend_configs = BackendConfig.objects.filter(backend=obj).prefetch_related("stage")

        data = []
        for backend_config in backend_configs:
            config = backend_config.config
            config["stage"] = {
                "id": backend_config.stage.id,
                "name": backend_config.stage.name,
            }

            data.append(config)

        return data
