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
from typing import Optional

from django.utils.translation import gettext as _
from rest_framework import serializers

from apigateway.apps.resource.serializers import ResourceExportConditionSLZ
from apigateway.apps.support.constants import DocArchiveTypeEnum, DocLanguageEnum
from apigateway.apps.support.models import ResourceDoc
from apigateway.core.models import Resource


class ResourceDocSLZ(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    resource_doc_link = serializers.CharField(read_only=True)
    language = serializers.ChoiceField(choices=DocLanguageEnum.get_django_choices(), default=DocLanguageEnum.ZH.value)

    class Meta:
        model = ResourceDoc
        fields = [
            "id",
            "type",
            "language",
            "content",
            "resource_doc_link",
        ]

    def validate_language(self, value):
        # 不允许编辑文档的语言
        if self.instance:
            return self.instance.language

        api_id = self.context["api_id"]
        resource_id = self.context["resource_id"]
        if ResourceDoc.objects.filter(api_id=api_id, resource_id=resource_id, language=value).exists():
            raise serializers.ValidationError(_("该资源的 {value} 文档已存在。").format(value=value))

        return value


class ResourceDocExportConditionSLZ(ResourceExportConditionSLZ):
    file_type = serializers.ChoiceField(
        choices=DocArchiveTypeEnum.get_django_choices(),
        default=DocArchiveTypeEnum.ZIP.value,
    )


class ArchiveDocParseSLZ(serializers.Serializer):
    file = serializers.FileField(required=True, help_text="导入的归档文档文件")


class ArchiveDocParseResultSLZ(serializers.Serializer):
    filename = serializers.CharField(read_only=True)
    id = serializers.IntegerField(allow_null=True, source="resource_id", read_only=True)
    name = serializers.CharField(source="resource_name", read_only=True)
    method = serializers.SerializerMethodField()
    path = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    resource_doc_id = serializers.IntegerField(allow_null=True, read_only=True)
    resource_doc_language = serializers.CharField(source="language.value", read_only=True)
    resource_doc_content_changed = serializers.BooleanField(read_only=True, source="has_changed")

    def get_method(self, obj):
        return self._get_resource_field(obj, "method", "")

    def get_path(self, obj):
        return self._get_resource_field(obj, "path", "")

    def get_description(self, obj):
        return self._get_resource_field(obj, "description", "")

    def _get_resource_field(self, obj, field, default=None) -> Optional[Resource]:
        if not obj.resource_id:
            return default

        resource = self.context["resource_id_to_object"].get(obj.resource_id)
        if not resource:
            return default

        return getattr(resource, field, default)


class SelectedResourceDocSLZ(serializers.Serializer):
    language = serializers.ChoiceField(choices=DocLanguageEnum.get_django_choices())
    resource_name = serializers.CharField()
    resource_id = serializers.HiddenField(default=None)

    def validate(self, data):
        data["resource_id"] = self._get_resource_id(data["resource_name"])
        return data

    def _get_resource_id(self, resource_name: str) -> int:
        resource_id = self.context["resource_name_to_id"].get(resource_name)
        if not resource_id:
            raise serializers.ValidationError(_("资源 {resource_name} 不存在。").format(resource_name=resource_name))
        return resource_id


class ImportResourceDocsByArchiveSLZ(serializers.Serializer):
    selected_resource_docs = serializers.JSONField(binary=True)
    file = serializers.FileField(required=True, help_text="导入的归档文档文件")

    def validate_selected_resource_docs(self, value):
        slz = SelectedResourceDocSLZ(data=value, many=True, context=self.context)
        slz.is_valid(raise_exception=True)
        return slz.validated_data


class ImportResourceDocsBySwaggerSLZ(serializers.Serializer):
    selected_resource_docs = serializers.ListField(child=SelectedResourceDocSLZ(), allow_empty=False)
    swagger = serializers.CharField()

    def validate_selected_resource_docs(self, value):
        languages = {item["language"] for item in value}
        if len(languages) != 1:
            raise serializers.ValidationError(_("通过 swagger 方式导入资源文档，选中资源文档的语言应一致。"))
        return value

    def validate(self, data):
        data["language"] = data["selected_resource_docs"][0]["language"]

        return data
