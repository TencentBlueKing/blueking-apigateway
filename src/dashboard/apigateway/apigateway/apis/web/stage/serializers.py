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
from django.utils.translation import gettext_lazy
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from tencent_apigateway_common.i18n.field import SerializerTranslatedField

from apigateway.apis.web.backend.constants import BACKEND_CONFIG_SCHEME_MAP
from apigateway.apis.web.backend.serializers import BaseBackendConfigSLZ
from apigateway.common.fields import CurrentGatewayDefault
from apigateway.core.constants import STAGE_NAME_PATTERN
from apigateway.core.models import Backend, Stage
from apigateway.core.validators import MaxCountPerGatewayValidator

from .validators import StageVarsValidator


class StageOutputSLZ(serializers.ModelSerializer):
    release_status = serializers.SerializerMethodField()
    release_time = serializers.SerializerMethodField()
    release_by = serializers.SerializerMethodField()
    resource_version = serializers.SerializerMethodField()
    publish_id = serializers.SerializerMethodField()
    new_resource_version = serializers.SerializerMethodField()
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
            "created_time",
            # by method
            "release_status",
            "release_time",
            "release_by",
            "resource_version",
            "publish_id",
            "new_resource_version",
        )

    def get_release_status(self, obj):
        # TODO 从发布的biz中获取到所有stage的发布状态
        return ""

    def get_release_time(self, obj):
        release_time = self.context["stage_release"].get(obj.id, {}).get("release_time", "")
        return serializers.DateTimeField(allow_null=True, required=False).to_representation(release_time)

    def get_release_by(self, obj):
        return self.context["stage_release"].get(obj.id, {}).get("release_by", "")

    def get_resource_version(self, obj):
        return self.context["stage_release"].get(obj.id, {}).get("resource_version", {}).get("version", "")

    def get_publish_id(self, obj):
        # TODO 从发布的biz中获取到所有stage的发布状态, 用户显示发布日志
        return 0

    def get_new_resource_version(self, obj):
        new_resource_version = self.context["new_resource_version"]
        stage_resource_version = self.get_resource_version(obj)

        if not stage_resource_version or new_resource_version > stage_resource_version:
            return new_resource_version

        return ""


class BackendSLZ(serializers.Serializer):
    id = serializers.IntegerField()
    config = BaseBackendConfigSLZ()


class StageInputSLZ(serializers.Serializer):
    api = serializers.HiddenField(default=CurrentGatewayDefault())
    name = serializers.RegexField(STAGE_NAME_PATTERN)
    description = serializers.CharField(allow_blank=True, allow_null=True, max_length=512, required=False)
    backends = serializers.ListField(child=BackendSLZ(), allow_empty=False)

    class Meta:
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
        ]

    def validate(self, attrs):
        # 查询网关下所有的backend
        backends = Backend.objects.filter(gateway=attrs["api"])
        backend_dict = {backend.id: backend for backend in backends}

        # 校验后端服务数据是否完整
        for input_backend in attrs["backends"]:
            if input_backend["id"] not in backend_dict:
                raise serializers.ValidationError(
                    _("网关下不存在id为【{backend_id}】的后端服务。").format(backend_id=input_backend["id"])
                )

        input_backend_ids = set([backend["id"] for backend in attrs["backends"]])
        for backend in backends:
            if backend.id not in input_backend_ids:
                raise serializers.ValidationError(_("环境缺少【{backend_name}】的后端服务。").format(backend_name=backend.name))

        # 校验backend下类型选择的关联性
        for input_backend in attrs["backends"]:
            backend = backend_dict[input_backend["id"]]

            for host in input_backend["config"]["hosts"]:
                check_backend_host_scheme(backend, host)

        return attrs


def check_backend_host_scheme(backend, host):
    if host["scheme"] not in BACKEND_CONFIG_SCHEME_MAP[backend.type]:
        raise serializers.ValidationError(
            _("后端服务【{backend_name}】的配置Scheme【{scheme}】不合法。").format(backend_name=backend.name, scheme=host["scheme"])
        )


class StageVarsSLZ(serializers.Serializer):
    api = serializers.HiddenField(default=CurrentGatewayDefault())
    vars = serializers.DictField(
        label="环境变量",
        child=serializers.CharField(allow_blank=True, required=True),
        default=dict,
    )

    class Meta:
        validators = [StageVarsValidator()]


class StageBackendOutputSLZ(serializers.Serializer):
    id = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    config = serializers.SerializerMethodField()

    def get_id(self, obj):
        return obj.backend.id

    def get_name(self, obj):
        return obj.backend.name

    def get_config(self, obj):
        return obj.config


class BackendConfigInputSLZ(BaseBackendConfigSLZ):
    def validate(self, attrs):
        # 查询网关下所有的backend
        backend = self.context["backend"]

        for host in attrs["hosts"]:
            check_backend_host_scheme(backend, host)

        return attrs


class StagePartialInputSLZ(serializers.Serializer):
    description = serializers.CharField(allow_blank=True, allow_null=True, max_length=512)


class StageStatusInputSLZ(serializers.Serializer):
    status = serializers.ChoiceField(choices=[(0, "INACTIVE")])
