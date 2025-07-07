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

from apigateway.biz.ai.constant import AIContentTypeEnum


class AICompletionContentInfo(serializers.Serializer):
    type = serializers.ChoiceField(
        choices=AIContentTypeEnum.get_choices(),
        required=True,
        help_text="ai content type",
    )
    input = serializers.CharField(required=True, help_text="ai content")
    enable_streaming = serializers.BooleanField(default=False, help_text="开启流式返回")

    class Meta:
        ref_name = "apigateway.apis.web.ai_completion.serializers.AICompletionContentInfo"


class AICompletionInputSLZ(serializers.Serializer):
    # 前端组件规定传入的参数必须放在一个名为inputs的对象中
    inputs = AICompletionContentInfo()

    class Meta:
        ref_name = "apigateway.apis.web.ai_completion.serializers.AICompletionInputSLZ"
