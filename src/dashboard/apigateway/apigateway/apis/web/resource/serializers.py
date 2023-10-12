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
from typing import Any, Dict, List, Optional

from django.conf import settings
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from apigateway.apis.web.constants import ExportTypeEnum
from apigateway.apis.web.resource.validators import BackendPathVarsValidator, PathVarsValidator
from apigateway.apps.support.constants import DocLanguageEnum
from apigateway.biz.constants import MAX_BACKEND_TIMEOUT_IN_SECOND, SwaggerFormatEnum
from apigateway.biz.gateway import GatewayHandler
from apigateway.biz.gateway_label import GatewayLabelHandler
from apigateway.biz.resource import ResourceHandler
from apigateway.biz.resource.importer.swagger import ResourceSwaggerImporter
from apigateway.biz.validators import MaxCountPerGatewayValidator
from apigateway.common.exceptions import SchemaValidationError
from apigateway.common.fields import CurrentGatewayDefault
from apigateway.core.constants import HTTP_METHOD_ANY, RESOURCE_METHOD_CHOICES
from apigateway.core.models import Backend, Gateway, Resource
from apigateway.core.utils import get_path_display

from .constants import MAX_LABEL_COUNT_PER_RESOURCE, PATH_PATTERN, RESOURCE_NAME_PATTERN


class ResourceQueryInputSLZ(serializers.Serializer):
    name = serializers.CharField(allow_blank=True, required=False, help_text="资源名称，完整匹配")
    path = serializers.CharField(allow_blank=True, required=False, help_text="资源前端请求路径，完整匹配")
    method = serializers.CharField(allow_blank=True, required=False, help_text="资源请求方法，完整匹配")
    label_ids = serializers.CharField(allow_blank=True, required=False, help_text="标签 ID，多个以逗号 , 分割")
    backend_id = serializers.IntegerField(allow_null=True, required=False, help_text="后端服务 ID")
    query = serializers.CharField(allow_blank=True, required=False, help_text="资源筛选条件，支持模糊匹配资源名称，前端请求路径")
    order_by = serializers.ChoiceField(
        choices=["-id", "name", "-name", "path", "-path", "updated_time", "-updated_time"],
        allow_blank=True,
        required=False,
        help_text="排序字段",
    )

    def validate_label_ids(self, value):
        if not value:
            return []

        try:
            return [int(x) for x in value.split(",")]
        except ValueError:
            raise serializers.ValidationError(_("标签 ID 请用逗号分割"))


class ResourceListOutputSLZ(serializers.ModelSerializer):
    path = serializers.CharField(source="path_display", read_only=True, help_text="前端请求路径")
    labels = serializers.SerializerMethodField(help_text="标签列表")
    docs = serializers.SerializerMethodField(help_text="资源文档列表")
    backend = serializers.SerializerMethodField(help_text="后端服务")
    has_updated = serializers.SerializerMethodField(help_text="相对上次发布，是否有更新，true：有更新，false：无更新")

    class Meta:
        model = Resource
        fields = [
            "id",
            "name",
            "description",
            "method",
            "path",
            "created_time",
            "updated_time",
            "backend",
            "labels",
            "docs",
            "has_updated",
        ]
        read_only_fields = fields

        extra_kwargs = {
            "id": {
                "help_text": "资源 ID",
            },
            "name": {
                "help_text": "资源名称",
            },
            "description": {
                "help_text": "资源描述",
            },
            "method": {
                "help_text": "资源请求方法",
            },
            "created_time": {
                "help_text": "资源创建时间",
            },
            "updated_time": {
                "help_text": "资源更新时间",
            },
        }

    def get_backend(self, obj):
        proxy = self.context["proxies"][obj.id]
        backend = self.context["backends"][proxy.backend_id]
        return {
            "id": backend.id,
            "name": backend.name,
        }

    def get_labels(self, obj):
        return self.context["labels"].get(obj.id, [])

    def get_docs(self, obj):
        return self.context["docs"].get(obj.id, [])

    def get_has_updated(self, obj):
        latest_version_created_time = self.context["latest_version_created_time"]
        return not (latest_version_created_time and latest_version_created_time > obj.updated_time)


class ResourceAuthConfigSLZ(serializers.Serializer):
    auth_verified_required = serializers.BooleanField(required=False, help_text="是否需要认证用户，true：需要，false：不需要")
    app_verified_required = serializers.BooleanField(required=False, help_text="是否需要认证应用，true：需要，false：不需要")
    resource_perm_required = serializers.BooleanField(required=False, help_text="是否需要校验资源权限，true：需要，false：不需要")


class HttpBackendConfigSLZ(serializers.Serializer):
    method = serializers.ChoiceField(choices=RESOURCE_METHOD_CHOICES, help_text="请求方法")
    path = serializers.RegexField(PATH_PATTERN, help_text="请求路径")
    match_subpath = serializers.BooleanField(required=False, help_text="是否匹配所有子路径")
    timeout = serializers.IntegerField(
        max_value=MAX_BACKEND_TIMEOUT_IN_SECOND, min_value=0, required=False, help_text="超时时间"
    )


class ResourceInputSLZ(serializers.ModelSerializer):
    gateway = serializers.HiddenField(default=CurrentGatewayDefault())
    name = serializers.RegexField(RESOURCE_NAME_PATTERN, max_length=256, required=True, help_text="资源名称")
    path = serializers.RegexField(PATH_PATTERN, max_length=2048, help_text="前端请求路径")
    auth_config = ResourceAuthConfigSLZ(help_text="认证配置")
    backend_id = serializers.IntegerField(help_text="后端服务 ID")
    backend_config = HttpBackendConfigSLZ(help_text="后端配置")
    label_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=True,
        required=False,
        max_length=MAX_LABEL_COUNT_PER_RESOURCE,
        help_text="标签 ID 列表",
    )

    class Meta:
        model = Resource
        fields = [
            "gateway",
            # 基本信息
            "name",
            "description",
            "description_en",
            "method",
            "path",
            "match_subpath",
            "is_public",
            "allow_apply_permission",
            # 认证配置
            "auth_config",
            # 后端配置
            "backend_id",
            "backend_config",
            # 标签
            "label_ids",
        ]
        lookup_field = "id"

        extra_kwargs = {
            "description": {
                "help_text": "资源描述",
            },
            "description_en": {
                "help_text": "资源英文描述，根据网关功能开关 ENABLE_I18N_SUPPORT 判断是否允许编辑此字段",
            },
            "method": {
                "help_text": "资源请求方法",
            },
            "match_subpath": {
                "help_text": "是否匹配所有子路径",
            },
            "is_public": {
                "help_text": "是否公开，true：公开，false：不公开",
            },
            "allow_apply_permission": {
                "help_text": "是否允许应用在开发者中心申请访问资源的权限",
            },
        }

        validators = [
            MaxCountPerGatewayValidator(
                Resource,
                max_count_callback=lambda gateway: GatewayHandler.get_max_resource_count(gateway),
                message=gettext_lazy("每个网关最多创建 {max_count} 个资源。"),
            ),
            UniqueTogetherValidator(
                queryset=Resource.objects.all(),
                fields=["gateway", "name"],
                message=gettext_lazy("网关下资源名称已经存在。"),
            ),
            UniqueTogetherValidator(
                queryset=Resource.objects.all(),
                fields=["gateway", "method", "path"],
                message=gettext_lazy("网关前端配置中，请求方法+请求路径已经存在。"),
            ),
            PathVarsValidator(),
            BackendPathVarsValidator(),
        ]

    def validate_description_en(self, value) -> Optional[str]:
        # description_en 为 None 时，文档中描述会展示 description 内容，
        # 因此，前端未传入有效 description_en 时，将其设置为 None
        return value or None

    def validate(self, data):
        self._validate_method(data["gateway"], data["path"], data["method"])
        self._validate_match_subpath(data)

        data["resource"] = self.instance
        data["backend"] = self._validate_backend_id(data["gateway"], data["backend_id"])

        return data

    def _validate_method(self, gateway: Gateway, path: str, method: str):
        """
        校验资源请求方法
        - 如果请求方法 method 为 ANY，则相同 path 下不能存在其他资源
        - 如果请求方法 method 不为 ANY，则校验 path 下不能存在 method 为 ANY 的资源
        """
        queryset = Resource.objects.filter(gateway_id=gateway.id, path=path)
        queryset = self._exclude_current_instance(queryset)

        if method == HTTP_METHOD_ANY:
            if queryset.exists():
                raise serializers.ValidationError(_("当前请求方法为 {method}，但相同请求路径下，其它请求方法已存在。").format(method=method))

        elif queryset.filter(method=HTTP_METHOD_ANY).exists():
            raise serializers.ValidationError(
                _("当前请求方法为 {method}，但相同请求路径下，请求方法 {method_any} 已存在。").format(
                    method=method,
                    method_any=HTTP_METHOD_ANY,
                )
            )

    def _validate_match_subpath(self, data):
        if data.get("match_subpath", False) != data["backend_config"].get("match_subpath", False):
            raise serializers.ValidationError(_("资源前端配置中的【匹配所有子路径】与后端配置中的【追加匹配的子路径】值必需相同。"))

    def _exclude_current_instance(self, queryset):
        if self.instance is not None:
            return queryset.exclude(pk=self.instance.pk)
        return queryset

    def _validate_backend_id(self, gateway: Gateway, backend_id: int) -> Backend:
        try:
            return Backend.objects.get(gateway=gateway, id=backend_id)
        except Backend.DoesNotExist:
            raise serializers.ValidationError(_("后端服务 (id={id}) 不存在。").format(id=backend_id))

    def validate_label_ids(self, value):
        gateway = self.context["gateway"]
        not_exist_ids = set(value) - set(GatewayLabelHandler.get_valid_ids(gateway.id, value))
        if not_exist_ids:
            raise serializers.ValidationError(_("标签不存在，id={ids}").format(ids=", ".join(map(str, not_exist_ids))))

        return value


class ResourceOutputSLZ(serializers.ModelSerializer):
    auth_config = serializers.SerializerMethodField(help_text="认证配置")
    backend_id = serializers.SerializerMethodField(help_text="后端服务 ID")
    backend_config = serializers.SerializerMethodField(help_text="后端配置")
    labels = serializers.SerializerMethodField(help_text="标签列表")

    class Meta:
        model = Resource
        fields = [
            "id",
            "name",
            "description",
            "description_en",
            "method",
            "path",
            "match_subpath",
            "is_public",
            "allow_apply_permission",
            "auth_config",
            "backend_id",
            "backend_config",
            "labels",
        ]
        read_only_fields = fields

        extra_kwargs = {
            "id": {
                "help_text": "资源 ID",
            },
            "name": {
                "help_text": "资源名称",
            },
            "description": {
                "help_text": "资源描述",
            },
            "description_en": {
                "help_text": "资源英文描述",
            },
            "method": {
                "help_text": "请求方法",
            },
            "path": {
                "help_text": "请求路径",
            },
            "match_subpath": {
                "help_text": "是否匹配所有子路径",
            },
            "is_public": {
                "help_text": "是否公开",
            },
            "allow_apply_permission": {
                "help_text": "是否允许应用在开发者中心申请访问资源的权限",
            },
        }

    def get_auth_config(self, obj):
        return self.context["auth_config"]

    def get_backend_id(self, obj):
        return self.context["proxy"].backend_id

    def get_backend_config(self, obj):
        return self.context["proxy"].config

    def get_labels(self, obj):
        return self.context["labels"].get(obj.id, [])


class ResourceBatchUpdateInputSLZ(serializers.Serializer):
    ids = serializers.ListField(child=serializers.IntegerField(min_value=1), help_text="资源 ID 列表")
    is_public = serializers.BooleanField(help_text="是否公开，true：公开，false：不公开")
    allow_apply_permission = serializers.BooleanField(help_text="是否允许应用在开发者中心申请访问资源的权限")

    def validate_ids(self, value):
        gateway_id = self.context["gateway_id"]
        not_exist_ids = set(value) - set(ResourceHandler.get_valid_ids(gateway_id, value))
        if not_exist_ids:
            raise serializers.ValidationError(_("资源不存在，id={ids}").format(ids=", ".join(map(str, not_exist_ids))))

        return value


class ResourceBatchDestroyInputSLZ(serializers.Serializer):
    ids = serializers.ListField(child=serializers.IntegerField(min_value=1), help_text="资源 ID 列表")

    def validate_ids(self, value):
        gateway_id = self.context["gateway_id"]
        not_exist_ids = set(value) - set(ResourceHandler.get_valid_ids(gateway_id, value))
        if not_exist_ids:
            raise serializers.ValidationError(_("资源不存在，id={ids}").format(ids=", ".join(map(str, not_exist_ids))))

        return value


class ResourceLabelUpdateInputSLZ(serializers.Serializer):
    label_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=True,
        max_length=MAX_LABEL_COUNT_PER_RESOURCE,
        help_text="标签 ID 列表",
    )

    def validate_label_ids(self, value):
        gateway_id = self.context["gateway_id"]
        not_exist_ids = set(value) - set(GatewayLabelHandler.get_valid_ids(gateway_id, value))
        if not_exist_ids:
            raise serializers.ValidationError(_("标签不存在，id={ids}").format(ids=", ".join(map(str, not_exist_ids))))

        return value


class ResourceDataSLZ(serializers.ModelSerializer):
    name = serializers.RegexField(RESOURCE_NAME_PATTERN, max_length=256, required=True, help_text="资源名称")
    path = serializers.RegexField(PATH_PATTERN, max_length=2048, help_text="请求路径")
    auth_config = ResourceAuthConfigSLZ(help_text="认证配置")
    backend_name = serializers.CharField(help_text="后端服务名称")
    backend_config = HttpBackendConfigSLZ(help_text="后端配置")
    labels = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=True,
        required=False,
        max_length=MAX_LABEL_COUNT_PER_RESOURCE,
        help_text="标签列表",
    )

    class Meta:
        model = Resource
        fields = [
            # 基本信息
            "name",
            "description",
            "description_en",
            "method",
            "path",
            "match_subpath",
            "is_public",
            "allow_apply_permission",
            # 认证配置
            "auth_config",
            # 后端配置
            "backend_name",
            "backend_config",
            # 标签
            "labels",
        ]

        extra_kwargs = {
            "description": {
                "help_text": "资源描述",
            },
            "description_en": {
                "help_text": "资源英文描述",
            },
            "method": {
                "help_text": "请求方法",
            },
            "path": {
                "help_text": "请求路径",
            },
            "match_subpath": {
                "help_text": "是否匹配所有子路径",
            },
            "is_public": {
                "help_text": "是否公开",
            },
            "allow_apply_permission": {
                "help_text": "是否允许应用在开发者中心申请访问资源的权限",
            },
        }

        validators = [
            PathVarsValidator(),
            BackendPathVarsValidator(),
        ]

    def validate_description_en(self, value) -> Optional[str]:
        # description_en 为 None 时，文档中描述会展示 description 内容，
        # 因此，前端未传入有效 description_en 时，将其设置为 None
        return value or None


class SelectedResourceSLZ(serializers.Serializer):
    """导入时选中的资源"""

    name = serializers.CharField(help_text="资源名称")


class ResourceImportInputSLZ(serializers.Serializer):
    content = serializers.CharField(allow_blank=False, required=True, help_text="导入内容，yaml/json 格式字符串")
    selected_resources = serializers.ListField(
        child=SelectedResourceSLZ(), allow_empty=False, allow_null=True, required=False, help_text="导入时选中的资源列表"
    )
    delete = serializers.BooleanField(default=False, help_text="是否删除未选中的资源，即已存在，但是未在 content 中的资源")

    def validate(self, data):
        data["resources"] = self._validate_content(data["content"])
        self._validate_label_count(data["resources"])

        return data

    def _validate_content(self, content: str):
        try:
            importer = ResourceSwaggerImporter(content)
        except Exception as err:
            raise serializers.ValidationError({"content": _("导入内容为无效的 json/yaml 数据，{err}。").format(err=err)})

        try:
            importer.validate()
        except SchemaValidationError as err:
            raise serializers.ValidationError({"content": _("导入内容不符合 swagger 2.0 协议，{err}。").format(err=err)})

        slz = ResourceDataSLZ(
            data=importer.get_resources(),
            many=True,
            context={
                "stages": self.context["stages"],
            },
        )
        slz.is_valid(raise_exception=True)
        return slz.validated_data

    def _validate_label_count(self, resources: List[Dict[str, Any]]):
        label_names = set()
        for resource in resources:
            label_names.update(resource.get("labels", []))

        if not label_names:
            return

        if len(label_names | set(self.context["exist_label_names"])) > settings.MAX_LABEL_COUNT_PER_GATEWAY:
            raise serializers.ValidationError(
                _("每个网关最多创建 {max_count} 个标签。").format(max_count=settings.MAX_LABEL_COUNT_PER_GATEWAY)
            )


class ResourceImportCheckInputSLZ(ResourceImportInputSLZ):
    doc_language = serializers.ChoiceField(
        choices=DocLanguageEnum.get_choices(), allow_blank=True, required=False, help_text="文档语言，en: 英文，zh: 中文"
    )


class ResourceImportCheckOutputSLZ(serializers.Serializer):
    id = serializers.SerializerMethodField(help_text="资源 ID")
    name = serializers.CharField(read_only=True, help_text="资源名称")
    description = serializers.CharField(read_only=True, help_text="资源描述")
    method = serializers.CharField(read_only=True, help_text="请求方法")
    path = serializers.SerializerMethodField(help_text="请求路径")
    doc = serializers.SerializerMethodField(help_text="资源文档")

    def get_id(self, obj):
        return obj.resource and obj.resource.id

    def get_path(self, obj):
        return get_path_display(obj.path, obj.match_subpath)

    def get_doc(self, obj):
        resource_id = self.get_id(obj)
        return self.context["docs"].get(resource_id, {"id": None, "language": self.context["doc_language"]})


class ResourceExportInputSLZ(serializers.Serializer):
    export_type = serializers.ChoiceField(
        choices=ExportTypeEnum.get_choices(),
        help_text="值为 all，不需其它参数；值为 filtered，支持 query/path/method/label_name 参数；值为 selected，支持 resource_ids 参数",
    )
    file_type = serializers.ChoiceField(
        choices=SwaggerFormatEnum.get_choices(), default=SwaggerFormatEnum.YAML.value, help_text="导出的文件类型，如 yaml/json"
    )
    resource_filter_condition = ResourceQueryInputSLZ(
        required=False, help_text="资源筛选条件，export_type 为 filtered 时，应提供当前的筛选条件"
    )
    resource_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=True,
        required=False,
        help_text="导出的资源 ID 列表，export_type 为 selected 时，应提供当前选择的资源 ID 列表",
    )


class ResourceExportOutputSLZ(serializers.Serializer):
    name = serializers.CharField(help_text="资源名称")
    description = serializers.CharField(help_text="资源描述")
    description_en = serializers.CharField(help_text="资源英文描述")
    method = serializers.CharField(help_text="请求方法")
    path = serializers.CharField(help_text="请求路径")
    match_subpath = serializers.BooleanField(help_text="是否匹配所有子路径")
    is_public = serializers.BooleanField(help_text="是否公开")
    allow_apply_permission = serializers.BooleanField(help_text="是否允许应用在开发者中心申请访问资源的权限")

    labels = serializers.SerializerMethodField(help_text="标签列表")
    backend_name = serializers.SerializerMethodField(help_text="后端服务名称")
    backend_config = serializers.SerializerMethodField(help_text="后端配置")
    auth_config = serializers.SerializerMethodField(help_text="认证配置")

    def get_labels(self, obj):
        labels = self.context["labels"].get(obj.id, [])
        return [label["name"] for label in labels]

    def get_backend_name(self, obj):
        proxy = self.context["proxies"][obj.id]
        return self.context["backends"][proxy.backend_id].name

    def get_backend_config(self, obj):
        proxy = self.context["proxies"][obj.id]
        return proxy.config

    def get_auth_config(self, obj):
        return self.context["auth_configs"][obj.id]


class BackendPathCheckInputSLZ(serializers.Serializer):
    path = serializers.RegexField(
        PATH_PATTERN,
        label="请求路径",
        required=False,
        allow_blank=True,
        error_messages={
            "invalid": gettext_lazy("斜线(/)开头的合法URL路径，不包含http(s)开头的域名。"),
        },
        help_text="请求路径",
    )
    backend_id = serializers.IntegerField(help_text="后端服务 ID")
    backend_path = serializers.RegexField(
        PATH_PATTERN,
        label="Path",
        error_messages={
            "invalid": gettext_lazy("斜线(/)开头的合法URL路径，不包含http(s)开头的域名。"),
        },
        help_text="后端服务的 path",
    )

    class Meta:
        validators = [
            BackendPathVarsValidator(check_stage_vars_exist=True),
        ]

    def to_internal_value(self, data):
        data = super().to_internal_value(data)
        data["backend_config"] = {"path": data["backend_path"]}
        return data


class BackendPathCheckOutputSLZ(serializers.Serializer):
    stage = serializers.DictField(read_only=True, help_text="环境信息")
    backend_urls = serializers.ListField(
        child=serializers.CharField(read_only=True), allow_empty=True, help_text="后端地址列表"
    )


class ResourceWithVerifiedUserRequiredOutputSLZ(serializers.Serializer):
    id = serializers.IntegerField(read_only=True, help_text="资源 ID")
    name = serializers.CharField(read_only=True, help_text="资源名称")
