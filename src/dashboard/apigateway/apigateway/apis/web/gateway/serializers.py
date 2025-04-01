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

from apigateway.biz.constants import APP_CODE_PATTERN
from apigateway.biz.gateway import GatewayHandler
from apigateway.biz.gateway_type import GatewayTypeHandler
from apigateway.common.django.validators import NameValidator
from apigateway.common.i18n.field import SerializerTranslatedField
from apigateway.core.constants import (
    GatewayStatusEnum,
)
from apigateway.core.models import Gateway
from apigateway.utils.crypto import calculate_fingerprint

from .constants import GATEWAY_NAME_PATTERN
from .validators import ReservedGatewayNameValidator
from ..constants import GatewayAPIDocTypeEnum


class GatewayListInputSLZ(serializers.Serializer):
    keyword = serializers.CharField(allow_blank=True, required=False, help_text="网关筛选条件，支持模糊匹配网关名称")
    order_by = serializers.ChoiceField(
        choices=["-updated_time", "updated_time", "-created_time", "created_time", "name", "-name"],
        default="-updated_time",
        help_text="排序方式",
    )


class GatewayListOutputSLZ(serializers.Serializer):
    id = serializers.IntegerField(read_only=True, help_text="网关 ID")
    name = serializers.CharField(read_only=True, help_text="网关名称")
    description = SerializerTranslatedField(
        allow_blank=True, default_field="description_i18n", read_only=True, help_text="网关描述"
    )
    status = serializers.ChoiceField(
        choices=GatewayStatusEnum.get_choices(), read_only=True, help_text="网关状态，0: 已停用，1：启用中"
    )
    is_public = serializers.BooleanField(read_only=True, help_text="是否公开，true：公开，false：不公开")
    created_by = serializers.CharField(allow_blank=True, allow_null=True, read_only=True, help_text="创建人")
    created_time = serializers.DateTimeField(allow_null=True, read_only=True, help_text="创建时间")
    updated_time = serializers.DateTimeField(allow_null=True, read_only=True, help_text="更新时间")
    is_official = serializers.SerializerMethodField(help_text="是否为官方网关，true：官方网关，false：非官方网关")
    resource_count = serializers.SerializerMethodField(help_text="网关下资源的数量")
    stages = serializers.SerializerMethodField(help_text="网关环境列表，其中的 released 表示环境是否已发布")

    def get_is_official(self, obj):
        if obj.id not in self.context["gateway_auth_configs"]:
            return False

        return GatewayTypeHandler.is_official(self.context["gateway_auth_configs"][obj.id].gateway_type)

    def get_resource_count(self, obj):
        return self.context["resource_count"].get(obj.id, 0)

    def get_stages(self, obj):
        return self.context["stages"].get(obj.id, [])


class GatewayCreateInputSLZ(serializers.ModelSerializer):
    name = serializers.RegexField(
        GATEWAY_NAME_PATTERN,
        label="网关名称",
        max_length=64,
        validators=[ReservedGatewayNameValidator(), NameValidator()],
        help_text="网关名称",
    )
    maintainers = serializers.ListField(child=serializers.CharField(), allow_empty=True, help_text="网关维护人员")
    developers = serializers.ListField(
        child=serializers.CharField(), allow_empty=True, default=list, help_text="网关开发者"
    )
    bk_app_codes = serializers.ListField(
        child=serializers.RegexField(APP_CODE_PATTERN), allow_empty=True, required=False, help_text="网关关联的应用"
    )

    class Meta:
        model = Gateway
        fields = (
            "name",
            "description",
            "maintainers",
            "developers",
            "is_public",
            "bk_app_codes",
        )
        lookup_field = "id"

        extra_kwargs = {
            "description": {
                "help_text": "网关描述",
            },
            "is_public": {
                "help_text": "是否公开，true：公开，false:不公开",
            },
        }

        # 使用 UniqueTogetherValidator，方便错误提示信息统一处理
        # 使用 UniqueValidator，错误提示中包含了字段名："参数校验失败: Name: 网关名称已经存在"
        validators = [
            UniqueTogetherValidator(
                queryset=Gateway.objects.all(),
                fields=["name"],
                message=gettext_lazy("网关名称已经存在。"),
            )
        ]

    def _add_creator_to_maintainers(self, data):
        # 创建者无网关权限，仅作为标记，维护人员有权限
        # 因此，如果创建者不在维护人中，默认添加到维护人中
        if self.context["created_by"] not in data["maintainers"]:
            data["maintainers"].append(self.context["created_by"])
        return data

    def to_internal_value(self, data):
        data = super().to_internal_value(data)
        return self._add_creator_to_maintainers(data)


class GatewayRetrieveOutputSLZ(serializers.ModelSerializer):
    maintainers = serializers.ListField(child=serializers.CharField(), allow_empty=True, help_text="网关维护人员")
    doc_maintainers = serializers.JSONField(help_text="网关文档联系人")
    developers = serializers.ListField(
        child=serializers.CharField(), allow_empty=True, default=list, help_text="网关开发者"
    )
    public_key = serializers.CharField(label="网关公钥", source="jwt.public_key", help_text="网关公钥")
    description = SerializerTranslatedField(
        default_field="description_i18n", allow_blank=True, allow_null=True, help_text="网关描述"
    )
    is_official = serializers.SerializerMethodField(help_text="是否为官方网关，true：官方网关，false：非官方网关")
    api_domain = serializers.SerializerMethodField(help_text="网关访问域名")
    docs_url = serializers.SerializerMethodField(help_text="文档地址")
    public_key_fingerprint = serializers.SerializerMethodField(help_text="公钥(指纹)")
    allow_update_gateway_auth = serializers.SerializerMethodField(help_text="是否允许更新网关认证配置")
    bk_app_codes = serializers.SerializerMethodField(help_text="网关关联的应用")
    related_app_codes = serializers.SerializerMethodField(help_text="关联的APP")

    class Meta:
        model = Gateway
        fields = (
            "id",
            "name",
            "description",
            "maintainers",
            "doc_maintainers",
            "developers",
            "status",
            "is_public",
            "created_by",
            "created_time",
            "updated_time",
            "public_key",
            "is_official",
            "allow_update_gateway_auth",
            "api_domain",
            "docs_url",
            "public_key_fingerprint",
            "bk_app_codes",
            "related_app_codes",
        )
        read_only_fields = fields
        lookup_field = "id"

        extra_kwargs = {
            "id": {
                "help_text": "网关ID",
            },
            "name": {
                "help_text": "网关名称",
            },
            "status": {
                "help_text": "网关状态，0：已停用，1：启用中",
            },
            "is_public": {
                "help_text": "是否公开, true: 公开,false: 不公开",
            },
            "created_by": {
                "help_text": "创建人",
            },
            "created_time": {
                "help_text": "创建时间",
            },
        }

    def get_api_domain(self, obj):
        return GatewayHandler.get_api_domain(obj)

    def get_docs_url(self, obj):
        return GatewayHandler.get_docs_url(obj)

    def get_public_key_fingerprint(self, obj):
        return calculate_fingerprint(obj.jwt.public_key)

    def get_allow_update_gateway_auth(self, obj):
        return self.context["auth_config"].allow_update_gateway_auth

    def get_is_official(self, obj):
        return GatewayTypeHandler.is_official(self.context["auth_config"].gateway_type)

    def get_bk_app_codes(self, obj):
        return self.context["bk_app_codes"]

    def get_related_app_codes(self, obj):
        return self.context["related_app_codes"]


class GatewayAPIDocSlZ(serializers.Serializer):
    type = serializers.ChoiceField(
        choices=GatewayAPIDocTypeEnum.get_choices(), allow_blank=True, required=False, help_text="联系人类型"
    )
    contacts = serializers.ListField(child=serializers.CharField(), allow_empty=True, help_text="联系人")
    service_number_name = serializers.CharField(allow_blank=True, required=False, help_text="服务号名称")
    service_number_link = serializers.CharField(allow_blank=True, required=False, help_text="服务号链接")

    def validate(self, data):
        if data.get("type") == GatewayAPIDocTypeEnum.USER.value:
            if not data.get("contacts"):
                raise serializers.ValidationError(_("联系人不可为空。"))

        elif data.get("type") == GatewayAPIDocTypeEnum.SERVICE_NUMBER.value:
            if not data.get("service_number_name"):
                raise serializers.ValidationError(_("服务号名称不可为空。"))
            if not data.get("service_number_link"):
                raise serializers.ValidationError(_("服务号链接不可为空。"))
        return data


class GatewayUpdateInputSLZ(serializers.ModelSerializer):
    maintainers = serializers.ListField(child=serializers.CharField(), allow_empty=True, help_text="网关维护人员")
    doc_maintainers = GatewayAPIDocSlZ(help_text="网关文档联系人")

    developers = serializers.ListField(
        child=serializers.CharField(), allow_empty=True, default=list, help_text="网关开发者"
    )
    bk_app_codes = serializers.ListField(
        child=serializers.RegexField(APP_CODE_PATTERN),
        allow_empty=True,
        required=False,
        help_text="网关相关的应用列表",
    )
    related_app_codes = serializers.ListField(
        child=serializers.RegexField(APP_CODE_PATTERN),
        allow_empty=True,
        required=False,
        help_text="管理网关的应用列表",
    )

    class Meta:
        model = Gateway
        fields = (
            "description",
            "maintainers",
            "doc_maintainers",
            "developers",
            "is_public",
            "bk_app_codes",
            "related_app_codes",
        )
        lookup_field = "id"

        extra_kwargs = {
            "description": {
                "help_text": "网关描述",
            },
            "is_public": {
                "help_text": "是否公开，true：公开，false：不公开",
            },
        }


class GatewayUpdateStatusInputSLZ(serializers.ModelSerializer):
    class Meta:
        model = Gateway
        fields = ("status",)
        lookup_field = "id"

        extra_kwargs = {
            "status": {
                "help_text": "网关状态，0：停用，1：启用",
            },
        }
        ref_name = "apigateway.apis.web.gateway.serializers.GatewayUpdateStatusInputSLZ"


class GatewayFeatureFlagsOutputSLZ(serializers.Serializer):
    feature_flags = serializers.DictField(help_text="网关特性集")
