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

from apigateway.apps.support.constants import DocLanguageEnum
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


class BatchTranslateInputSLZ(serializers.Serializer):
    """批量翻译输入序列化器"""

    doc_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1), required=True, help_text="需要翻译的文档ID列表"
    )
    target_language = serializers.ChoiceField(
        choices=DocLanguageEnum.get_choices(),
        required=False,
        allow_null=True,
        help_text="目标语言，如果不指定则自动检测并翻译为相反语言",
    )

    class Meta:
        ref_name = "apigateway.apis.web.ai_completion.serializers.BatchTranslateInputSLZ"

    def validate_doc_ids(self, value):
        """验证文档ID列表"""
        if not value:
            raise serializers.ValidationError("文档ID列表不能为空")

        if len(value) > 100:
            raise serializers.ValidationError("一次最多只能翻译100个文档")

        return value


class BatchTranslateOutputSLZ(serializers.Serializer):
    """批量翻译输出序列化器"""

    message = serializers.CharField(help_text="任务信息")
    doc_count = serializers.IntegerField(help_text="文档数量")

    class Meta:
        ref_name = "apigateway.apis.web.ai_completion.serializers.BatchTranslateOutputSLZ"
