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
from django.conf import settings
from rest_framework import serializers
from tencent_apigateway_common.i18n.field import SerializerTranslatedField


class SystemSLZ(serializers.Serializer):
    name = serializers.CharField(read_only=True)
    description = serializers.CharField(allow_blank=True, read_only=True)

    class Meta:
        ref_name = "apis.web.docs.esb.system.SystemSLZ"


class SystemCategorySLZ(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    systems = serializers.ListField(child=SystemSLZ(), read_only=True)


class SystemListOutputSLZ(serializers.Serializer):
    board = serializers.CharField(read_only=True)
    board_label = serializers.CharField(read_only=True)
    categories = serializers.ListField(child=SystemCategorySLZ(), read_only=True)


class SystemRetrieveOutputSLZ(serializers.Serializer):
    name = serializers.CharField()
    description = SerializerTranslatedField(translated_fields={"en": "description_en"}, default_field="description")
    comment = SerializerTranslatedField(translated_fields={"en": "comment_en"}, default_field="comment")
    maintainers = serializers.SerializerMethodField()

    def get_maintainers(self, obj):
        return settings.ESB_MANAGERS
