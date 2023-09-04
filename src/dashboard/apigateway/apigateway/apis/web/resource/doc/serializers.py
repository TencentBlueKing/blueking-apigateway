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

from apigateway.apps.support.constants import DocLanguageEnum
from apigateway.apps.support.models import ResourceDoc


class DocInputSLZ(serializers.ModelSerializer):
    language = serializers.ChoiceField(choices=DocLanguageEnum.get_choices())

    class Meta:
        model = ResourceDoc
        fields = ["language", "content"]

    def validate_language(self, value):
        gateway_id = self.context["gateway_id"]
        resource_id = self.context["resource_id"]
        queryset = ResourceDoc.objects.filter(gateway_id=gateway_id, resource_id=resource_id, language=value)
        if self.instance is not None:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError(_("该资源语言 {value} 的文档已存在。").format(value=value))

        return value


class DocOutputSLZ(serializers.ModelSerializer):
    class Meta:
        model = ResourceDoc
        fields = [
            "id",
            "language",
            "content",
        ]
        read_only_fields = fields
