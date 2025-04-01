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

from rest_framework import serializers

from apigateway.apps.permission.constants import FormattedGrantDimensionEnum
from apigateway.biz.validators import BKAppCodeListValidator
from apigateway.utils.time import NeverExpiresTime


class GatewayRelatedAppsAddInputSLZ(serializers.Serializer):
    related_app_codes = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=False,
        required=True,
        max_length=10,
        validators=[BKAppCodeListValidator()],
    )

    class Meta:
        ref_name = "apigateway.apis.v2.sync.serializers.GatewayRelatedAppsAddInputSLZ"


class GatewayPermissionListInputSLZ(serializers.Serializer):
    bk_app_code = serializers.CharField(required=False)
    grant_dimension = serializers.ChoiceField(choices=FormattedGrantDimensionEnum.get_choices(), required=True)

    class Meta:
        ref_name = "apigateway.apis.v2.sync.serializers.GatewayPermissionListInputSLZ"


class GatewayPermissionListOutputSLZ(serializers.Serializer):
    # common fields
    bk_app_code = serializers.CharField()
    expires = serializers.SerializerMethodField()
    grant_dimension = serializers.ChoiceField(choices=FormattedGrantDimensionEnum.get_choices())

    # only for resource permission
    # grant_type = serializers.ChoiceField(choices=GrantTypeEnum.get_choices())
    resource_id = serializers.IntegerField(required=False)
    resource_name = serializers.CharField(required=False)

    def get_expires(self, obj):
        expires = (
            None
            if (not obj.get("expires") or NeverExpiresTime.is_never_expired(obj.get("expires")))
            else obj.get("expires")
        )
        return serializers.DateTimeField(allow_null=True, required=False).to_representation(expires)
