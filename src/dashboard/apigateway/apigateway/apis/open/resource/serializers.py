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

from apigateway.common.fields import CurrentGatewayDefault


class ResourceSyncOutputSLZ(serializers.Serializer):
    added = serializers.ListField(child=serializers.DictField())
    updated = serializers.ListField(child=serializers.DictField())
    deleted = serializers.ListField(child=serializers.DictField())


class ResourceImportInputSLZ(serializers.Serializer):
    gateway = serializers.HiddenField(default=CurrentGatewayDefault())
    content = serializers.CharField(allow_blank=False, required=True, help_text="导入内容，yaml/json 格式字符串")

    class Meta:
        ref_name = "apis.open.resource.ResourceImportInputSLZ"
