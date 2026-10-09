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

from rest_framework import serializers

from apigateway.biz.validators import BKAppCodeValidator, UserManagedBKAppCodeValidator


class GatewayPermissionApplyInputSLZ(serializers.Serializer):
    bk_app_code = serializers.CharField(
        required=True,
        validators=[BKAppCodeValidator(), UserManagedBKAppCodeValidator()],
        help_text="蓝鲸应用 ID",
    )
    resource_name = serializers.CharField(required=True, help_text="资源名称")
    reason = serializers.CharField(required=False, allow_blank=True, default="", help_text="申请原因")

    class Meta:
        ref_name = "apigateway.apis.web.docs.gateway.permission.serializers.GatewayPermissionApplyInputSLZ"


class GatewayPermissionApplyOutputSLZ(serializers.Serializer):
    record_id = serializers.IntegerField(read_only=True, help_text="申请记录 ID")
    bk_app_code = serializers.CharField(read_only=True, help_text="蓝鲸应用 ID")
    gateway_name = serializers.CharField(read_only=True, help_text="网关名称")
    resource_name = serializers.CharField(read_only=True, help_text="资源名称")
    itsm_ticket_id = serializers.CharField(read_only=True, allow_blank=True, help_text="关联的 ITSM 工单 ID")
    itsm_ticket_url = serializers.CharField(read_only=True, allow_blank=True, help_text="ITSM 单据中心链接")

    class Meta:
        ref_name = "apigateway.apis.web.docs.gateway.permission.serializers.GatewayPermissionApplyOutputSLZ"
