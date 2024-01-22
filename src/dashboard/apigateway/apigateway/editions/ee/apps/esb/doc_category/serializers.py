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
from django.utils.translation import gettext_lazy
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from apigateway.apps.esb.bkcore.models import DocCategory
from apigateway.apps.esb.mixins import OfficialWriteFields
from apigateway.common.i18n.field import SerializerTranslatedField


class DocCategorySLZ(OfficialWriteFields, serializers.ModelSerializer):
    board = serializers.HiddenField(default=settings.ESB_DEFAULT_BOARD)
    system_count = serializers.IntegerField(read_only=True, required=False)
    is_official = serializers.BooleanField(read_only=True)
    name = SerializerTranslatedField(default_field="name_i18n", max_length=32)

    class Meta:
        model = DocCategory
        fields = (
            "board",
            "id",
            "name",
            "priority",
            "is_official",
            "updated_time",
            "system_count",
        )
        read_only_fields = ("id", "updated_time")
        official_write_fields = [
            "priority",
        ]
        lookup_field = "id"

        validators = [
            UniqueTogetherValidator(
                queryset=DocCategory.objects.all(),
                fields=["board", "name"],
                message=gettext_lazy("文档分类中名称已存在。"),
            ),
        ]

    def to_representation(self, instance):
        if "system_counts" in self.context:
            instance.system_count = self.context["system_counts"].get(instance.id, 0)

        return super().to_representation(instance)
