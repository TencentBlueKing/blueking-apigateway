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
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from apigateway.apps.esb.bkcore.models import ComponentSystem, DocCategory
from apigateway.apps.esb.constants import SYSTEM_NAME_PATTERN
from apigateway.apps.esb.mixins import OfficialWriteFields
from apigateway.common.i18n.field import SerializerTranslatedField
from apigateway.common.mixins.serializers import ExtensibleFieldMixin


class SystemSLZ(ExtensibleFieldMixin, OfficialWriteFields, serializers.ModelSerializer):
    board = serializers.HiddenField(default=settings.ESB_DEFAULT_BOARD)
    doc_category_id = serializers.IntegerField()
    doc_category_name = SerializerTranslatedField(translated_fields={"en": "doc_category_name_en"}, read_only=True)
    maintainers = serializers.ListField(child=serializers.CharField(), allow_empty=True)
    component_count = serializers.IntegerField(read_only=True, required=False)
    is_official = serializers.BooleanField(read_only=True)
    name = serializers.RegexField(SYSTEM_NAME_PATTERN, label="名称", max_length=64)
    timeout = serializers.IntegerField(label="超时时长", allow_null=True, required=False, min_value=1, max_value=600)
    description = SerializerTranslatedField(default_field="description_i18n", allow_blank=True, max_length=128)
    comment = SerializerTranslatedField(default_field="comment_i18n", allow_blank=True, required=False)

    class Meta:
        model = ComponentSystem
        fields = (
            "board",
            "id",
            "name",
            "description",
            "description_en",
            "comment",
            "timeout",
            "maintainers",
            "doc_category_id",
            "doc_category_name",
            "component_count",
            "is_official",
        )
        extra_kwargs = {
            "description_en": {
                "required": False,
            }
        }
        non_model_fields = ["doc_category_id", "doc_category_name", "doc_category"]
        official_write_fields = [
            "timeout",
            "maintainers",
        ]
        lookup_field = "id"
        validators = [
            UniqueTogetherValidator(
                queryset=ComponentSystem.objects.all(),
                fields=["board", "name"],
                message=gettext_lazy("系统名称需唯一。"),
            )
        ]

    def to_internal_value(self, data):
        data = super().to_internal_value(data)
        data["doc_category"] = self._get_doc_category(data["board"], data["doc_category_id"])
        return data

    def _get_doc_category(self, board: str, doc_category_id: int) -> DocCategory:
        try:
            return DocCategory.objects.get(board=board, id=doc_category_id)
        except DocCategory.DoesNotExist:
            raise serializers.ValidationError(
                {
                    "doc_category_id": _("文档分类【id={doc_category_id}】不存在。").format(
                        doc_category_id=doc_category_id
                    ),
                }
            )

    def to_representation(self, instance) -> dict:
        self._enrich_instance(instance)
        return super().to_representation(instance)

    def _enrich_instance(self, instance):
        doc_category = self.context["system_id_to_doc_category_map"].get(instance.id)
        if doc_category is None:
            doc_category = DocCategory.objects.get_default_doc_category(instance.board)
        instance.doc_category_id = doc_category["id"]
        instance.doc_category_name = doc_category["name"]
        instance.doc_category_name_en = doc_category["name_en"]

        if "system_id_to_channel_count_map" in self.context:
            instance.component_count = self.context["system_id_to_channel_count_map"].get(instance.id, 0)
