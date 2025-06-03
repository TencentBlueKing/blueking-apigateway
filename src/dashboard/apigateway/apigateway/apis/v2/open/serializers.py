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

from apigateway.apps.permission.constants import GrantDimensionEnum, PermissionApplyExpireDaysEnum
from apigateway.biz.permission import PermissionDimensionManager
from apigateway.common.i18n.field import SerializerTranslatedField


class GatewayListInputSLZ(serializers.Serializer):
    name = serializers.CharField(required=False, allow_blank=True)
    fuzzy = serializers.BooleanField(required=False)

    class Meta:
        ref_name = "apigateway.apis.v2.open.serializers.GatewayListInputSLZ"


class GatewayListOutputSLZ(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    description = SerializerTranslatedField(default_field="description_i18n", allow_blank=True, read_only=True)
    maintainers = serializers.SerializerMethodField()
    doc_maintainers = serializers.SerializerMethodField()

    def get_maintainers(self, obj):
        return obj.maintainers

    def get_doc_maintainers(self, obj):
        return obj.doc_maintainers

    class Meta:
        ref_name = "apigateway.apis.v2.open.serializers.GatewayListOutputSLZ"


class GatewayRetrieveOutputSLZ(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    description = SerializerTranslatedField(default_field="description_i18n", allow_blank=True, read_only=True)
    maintainers = serializers.SerializerMethodField()
    doc_maintainers = serializers.SerializerMethodField()

    def get_maintainers(self, obj):
        return obj.maintainers

    def get_doc_maintainers(self, obj):
        return obj.doc_maintainers

    class Meta:
        ref_name = "apigateway.apis.v2.open.serializers.GatewayRetrieveOutputSLZ"


class GatewayAppPermissionApplyInputSLZ(serializers.Serializer):
    """
    普通应用直接申请访问网关API的权限
    - 提供给普通应用的接口
    - 开源版申请权限，为保障权限有效性，可申请永久有效的权限
    - 暂支持按网关申请，不支持按资源申请
    """

    # target_app_code 与发送请求的应用账号一致，此 app_code 必定已存在，不需要重复校验
    target_app_code = serializers.CharField()
    reason = serializers.CharField(allow_blank=True, required=False, default="")
    expire_days = serializers.ChoiceField(
        choices=PermissionApplyExpireDaysEnum.get_choices(),
        required=False,
    )
    grant_dimension = serializers.ChoiceField(choices=[GrantDimensionEnum.API.value])

    def validate_target_app_code(self, value):
        request = self.context["request"]
        if request.app.app_code != value:
            raise serializers.ValidationError(
                _("应用【{app_code}】不能为其它应用【{value}】申请访问网关API的权限。").format(
                    app_code=request.app.app_code, value=value
                )
            )

        return value

    def validate(self, data):
        self._validate_allow_apply(data["target_app_code"], data["grant_dimension"])
        return data

    def _validate_allow_apply(self, bk_app_code: str, grant_dimension: str):
        """
        校验是否允许申请权限
        - 已拥有权限，且未过期，不能申请
        - 已存在待审批单据，不能申请
        """
        allow, reason = PermissionDimensionManager.get_manager(grant_dimension).allow_apply_permission(
            self.context["request"].gateway.id,
            bk_app_code,
        )
        if not allow:
            raise serializers.ValidationError(reason)
