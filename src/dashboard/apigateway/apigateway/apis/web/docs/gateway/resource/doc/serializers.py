# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2025 Tencent. All rights reserved.
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


class DocInputSLZ(serializers.Serializer):
    stage_name = serializers.CharField(help_text="网关环境名称")

    class Meta:
        ref_name = "apigateway.apis.web.docs.gateway.resource.doc.serializers.DocInputSLZ"


class DocOutputSLZ(serializers.Serializer):
    type = serializers.CharField(help_text="文档类型，如 markdown")
    content = serializers.CharField(help_text="文档内容")
    updated_time = serializers.DateTimeField(help_text="文档更新时间")

    class Meta:
        ref_name = "apigateway.apis.web.docs.gateway.resource.doc.serializers.DocOutputSLZ"
