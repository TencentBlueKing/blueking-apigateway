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


class AICompletionInputSLZ(serializers.Serializer):
    type = serializers.ChoiceField(
        choices=AIContentTypeEnum.get_choices(),
        required=True,
        help_text="ai content type",
    )
    content = serializers.CharField(required=True, help_text="ai content")
    enable_streaming = serializers.BooleanField(default=False, help_text="开启流式返回")
