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
from django.conf import settings
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueTogetherValidator

from apigateway.apis.web.constants import BACKEND_CONFIG_SCHEME_MAP
from apigateway.apis.web.serializers import BaseBackendConfigSLZ
from apigateway.biz.releaser import ReleaseValidationError
from apigateway.biz.validators import MaxCountPerGatewayValidator, PublishValidator
from apigateway.common.django.validators import NameValidator
from apigateway.common.fields import CurrentGatewayDefault
from apigateway.common.i18n.field import SerializerTranslatedField
from apigateway.core.constants import STAGE_NAME_PATTERN, PublishEventStatusEnum, ReleaseStatusEnum, StageStatusEnum
from apigateway.core.models import Backend, Stage
from apigateway.utils.version import is_version1_greater_than_version2

from .validators import StageVarsValidator


class StageOutputSLZ(serializers.ModelSerializer):
    release = serializers.SerializerMethodField(help_text="发布信息")
    resource_version = serializers.SerializerMethodField(help_text="当前生效资源版本")
    publish_id = serializers.SerializerMethodField(help_text="发布ID")
    publish_version = serializers.SerializerMethodField(help_text="正在发布的版本")
    publish_validate_msg = serializers.SerializerMethodField(help_text="发布校验结果,如果有值，则不能发布")
    new_resource_version = serializers.SerializerMethodField(help_text="新资源版本")
    description = SerializerTranslatedField(
        default_field="description_i18n",
        allow_blank=True,
        allow_null=True,
        max_length=512,
        required=False,
        help_text="描述",
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
            "release",
            "resource_version",
            "publish_id",
            "publish_version",
            "publish_validate_msg",
            "new_resource_version",
        )

    def get_release(self, obj):
        # 获取stage发布状态
        has_release = self.context["stage_release"].get(obj.id, {}).get("release_status", False)

        # 如果stage有发布，则获取其实时发布状态，否则则为未发布
        status = (
            self.context["stage_publish_status"].get(obj.id, {}).get("status", ReleaseStatusEnum.SUCCESS.value)
            if has_release
            else ReleaseStatusEnum.UNRELEASED.value
        )

        release_time = self.context["stage_release"].get(obj.id, {}).get("release_time", "")

        return {
            "status": status,
            "created_time": serializers.DateTimeField(allow_null=True, required=False).to_representation(release_time),
            "created_by": self.context["stage_release"].get(obj.id, {}).get("release_by", ""),
        }

    def get_resource_version(self, obj):
        return {
            "version": self.context["stage_release"].get(obj.id, {}).get("resource_version", {}).get("version", ""),
            "id": self.context["stage_release"].get(obj.id, {}).get("resource_version_id", 0),
            "schema_version": self.context["stage_release"].get(obj.id, {}).get("resource_version_schema_version", ""),
        }

    def get_publish_version(self, obj):
        """
        获取正在发布版本
        """
        latest_publish_info = self.context["stage_publish_status"].get(obj.id)
        if not latest_publish_info:
            return ""

        if latest_publish_info.get("status", "") != PublishEventStatusEnum.SUCCESS.value:
            return latest_publish_info.get("resource_version_display", "")

        return ""

    def get_publish_id(self, obj):
        return self.context["stage_publish_status"].get(obj.id, {}).get("publish_id", 0)

    def get_publish_validate_msg(self, obj):
        """
        获取发布校验结果
        """

        validate_err_message: str = ""

        publish_validator = PublishValidator(obj.gateway, obj)
        try:
            publish_validator()
        except (ValidationError, ReleaseValidationError) as err:
            validate_err_message = err.detail[0] if isinstance(err, ValidationError) else str(err)

        return validate_err_message

    def get_new_resource_version(self, obj):
        new_resource_version = self.context["new_resource_version"]
        stage_resource_version = self.get_resource_version(obj)["version"]

        if not stage_resource_version or is_version1_greater_than_version2(
            new_resource_version, stage_resource_version
        ):
            return new_resource_version

        return ""


class BackendSLZ(serializers.Serializer):
    id = serializers.IntegerField()
    config = BaseBackendConfigSLZ(help_text="配置")


class StageInputSLZ(serializers.Serializer):
    gateway = serializers.HiddenField(default=CurrentGatewayDefault())
    name = serializers.RegexField(
        STAGE_NAME_PATTERN,
        help_text="名称",
        validators=[NameValidator()],
    )
    description = serializers.CharField(
        allow_blank=True, allow_null=True, max_length=512, required=False, help_text="描述"
    )
    backends = serializers.ListField(child=BackendSLZ(), allow_empty=False, help_text="后端服务")

    class Meta:
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
        ]

    def validate(self, attrs):
        # 查询网关下所有的backend
        backends = Backend.objects.filter(gateway=attrs["gateway"])
        backend_dict = {backend.id: backend for backend in backends}

        # 校验后端服务数据是否完整
        for input_backend in attrs["backends"]:
            if input_backend["id"] not in backend_dict:
                raise serializers.ValidationError(
                    _("网关下不存在id为【{backend_id}】的后端服务。").format(backend_id=input_backend["id"])
                )

        input_backend_ids = {backend["id"] for backend in attrs["backends"]}
        for backend in backends:
            if backend.id not in input_backend_ids:
                raise serializers.ValidationError(
                    _("请求参数中，缺少后端服务【{backend_id}】的配置。").format(backend_name=backend.name)
                )

        # 校验backend下类型选择的关联性
        for input_backend in attrs["backends"]:
            backend = backend_dict[input_backend["id"]]

            for host in input_backend["config"]["hosts"]:
                check_backend_host_scheme(backend, host)

        return attrs


def check_backend_host_scheme(backend, host):
    if host["scheme"] not in BACKEND_CONFIG_SCHEME_MAP[backend.type]:
        raise serializers.ValidationError(
            _("后端服务【{backend_name}】的配置Scheme【{scheme}】不合法。").format(
                backend_name=backend.name, scheme=host["scheme"]
            )
        )


class StageVarsSLZ(serializers.Serializer):
    gateway = serializers.HiddenField(default=CurrentGatewayDefault())
    vars = serializers.DictField(
        label="环境变量",
        child=serializers.CharField(allow_blank=True, required=True),
        default=dict,
    )

    class Meta:
        validators = [StageVarsValidator()]


class StageBackendOutputSLZ(serializers.Serializer):
    id = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField(help_text="名称")
    config = serializers.SerializerMethodField(help_text="配置")

    def get_id(self, obj):
        return obj.backend.id

    def get_name(self, obj):
        return obj.backend.name

    def get_config(self, obj):
        return obj.config


class BackendConfigInputSLZ(BaseBackendConfigSLZ):
    def validate(self, attrs):
        backend = self.context["backend"]

        for host in attrs["hosts"]:
            check_backend_host_scheme(backend, host)

        return attrs


class StagePartialInputSLZ(serializers.Serializer):
    description = serializers.CharField(allow_blank=True, allow_null=True, max_length=512, help_text="描述")


class StageStatusInputSLZ(serializers.Serializer):
    status = serializers.ChoiceField(choices=[(StageStatusEnum.INACTIVE.value, "INACTIVE")], help_text="状态")
