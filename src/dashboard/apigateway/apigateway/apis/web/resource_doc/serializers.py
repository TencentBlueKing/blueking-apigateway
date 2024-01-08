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

from apigateway.apis.web.constants import ExportTypeEnum
from apigateway.apps.support.constants import DocArchiveTypeEnum, DocLanguageEnum


class DocArchiveParseInputSLZ(serializers.Serializer):
    file = serializers.FileField(required=True, help_text="导入的归档文档文件")


class ArchiveParseOutputResourceSLZ(serializers.Serializer):
    id = serializers.IntegerField(read_only=True, help_text="资源 ID")
    name = serializers.CharField(read_only=True, help_text="资源名称")
    method = serializers.CharField(read_only=True, help_text="请求方法")
    path = serializers.CharField(read_only=True, help_text="请求路径")
    description = serializers.CharField(read_only=True, help_text="资源描述")


class ArchiveParseOutputResourceDocSLZ(serializers.Serializer):
    id = serializers.IntegerField(read_only=True, help_text="文档 ID")
    language = serializers.CharField(read_only=True, help_text="文档语言")


class DocArchiveParseOutputSLZ(serializers.Serializer):
    filename = serializers.CharField(read_only=True, help_text="归档文档文件名")
    language = serializers.CharField(source="language.value", read_only=True, help_text="文档语言")
    content_changed = serializers.BooleanField(read_only=True, help_text="文档内容是否发生变化")
    resource = ArchiveParseOutputResourceSLZ(allow_null=True, read_only=True, help_text="归档文档所属资源")
    resource_doc = ArchiveParseOutputResourceDocSLZ(allow_null=True, read_only=True, help_text="归档文档")


class SelectedResourceDocSLZ(serializers.Serializer):
    language = serializers.ChoiceField(choices=DocLanguageEnum.get_choices(), help_text="文档语言，en: 英文，zh: 中文")
    resource_name = serializers.CharField(help_text="资源名称")


class DocImportByArchiveInputSLZ(serializers.Serializer):
    selected_resource_docs = serializers.JSONField(binary=True, help_text="选中的资源文档")
    file = serializers.FileField(required=True, help_text="导入的归档文档文件")

    def validate_selected_resource_docs(self, value):
        slz = SelectedResourceDocSLZ(data=value, many=True)
        slz.is_valid(raise_exception=True)
        return slz.validated_data


class DocImportBySwaggerInputSLZ(serializers.Serializer):
    selected_resource_docs = serializers.ListField(
        child=SelectedResourceDocSLZ(), allow_empty=False, help_text="选中的资源文档"
    )
    language = serializers.ChoiceField(choices=DocLanguageEnum.get_choices(), help_text="文档语言，en: 英文，zh: 中文")
    swagger = serializers.CharField(help_text="导入的 Swagger 文档")


class ResourceFilterConditionSLZ(serializers.Serializer):
    """导出资源文档时，当导出类型为：已筛选资源时，此处为筛选条件"""

    name = serializers.CharField(allow_blank=True, required=False, help_text="资源名称，完整匹配")
    path = serializers.CharField(allow_blank=True, required=False, help_text="请求路径，完整匹配")
    method = serializers.CharField(allow_blank=True, required=False, help_text="请求方法，完整匹配")
    label_ids = serializers.ListField(child=serializers.IntegerField(), required=False, help_text="标签 ID 列表")
    backend_id = serializers.IntegerField(allow_null=True, required=False, help_text="后端服务 ID")
    backend_name = serializers.CharField(allow_blank=True, required=False, help_text="后端服务名称，完整匹配")
    keyword = serializers.CharField(
        allow_blank=True, required=False, help_text="筛选条件，支持模糊匹配资源名称，前端请求路径"
    )


class DocExportInputSLZ(serializers.Serializer):
    export_type = serializers.ChoiceField(
        choices=ExportTypeEnum.get_choices(),
        help_text="值为 all，不需其它参数；值为 filtered，支持 query/path/method/label_name 参数；值为 selected，支持 resource_ids 参数",
    )
    file_type = serializers.ChoiceField(
        choices=DocArchiveTypeEnum.get_choices(),
        default=DocArchiveTypeEnum.ZIP.value,
        help_text="导出的文件类型，tgz：tgz 归档文件，zip：zip 归档文件",
    )
    resource_filter_condition = ResourceFilterConditionSLZ(
        required=False, help_text="资源筛选条件，export_type 为 filtered 时，应提供当前的筛选条件"
    )
    resource_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=True,
        required=False,
        help_text="导出的资源 ID 列表，export_type 为 selected 时，应提供当前选择的资源 ID 列表",
    )
