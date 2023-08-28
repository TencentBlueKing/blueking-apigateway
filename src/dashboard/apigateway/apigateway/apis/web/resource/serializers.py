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

from apigateway.apis.web.resource.validators import BackendPathVarsValidator, PathVarsValidator
from apigateway.apps.support.constants import DocLanguageEnum
from apigateway.biz.gateway import GatewayHandler
from apigateway.biz.resource.importer.swagger import ResourceSwaggerImporter
from apigateway.biz.validators import MaxCountPerGatewayValidator
from apigateway.common.exceptions import SchemaValidationError
from apigateway.common.fields import CurrentGatewayDefault
from apigateway.core.constants import (
    HTTP_METHOD_ANY,
    MAX_BACKEND_TIMEOUT_IN_SECOND,
    MAX_LABEL_COUNT_PER_RESOURCE,
    PATH_PATTERN,
    RESOURCE_METHOD_CHOICES,
    RESOURCE_NAME_PATTERN,
    ExportTypeEnum,
    SwaggerFormatEnum,
)
from apigateway.core.models import Backend, Gateway, Resource, Stage
from apigateway.core.utils import get_path_display


class ResourceQueryInputSLZ(serializers.Serializer):
    name = serializers.CharField(allow_blank=True, required=False)
    path = serializers.CharField(allow_blank=True, required=False)
    method = serializers.CharField(allow_blank=True, required=False)
    label_ids = serializers.CharField(allow_blank=True, required=False)
    query = serializers.CharField(allow_blank=True, required=False)
    order_by = serializers.ChoiceField(
        choices=["-id", "name", "-name", "path", "-path", "updated_time", "-updated_time"],
        allow_blank=True,
        required=False,
    )


class ResourceListOutputSLZ(serializers.ModelSerializer):
    path = serializers.CharField(source="path_display", read_only=True)
    labels = serializers.SerializerMethodField()
    docs = serializers.SerializerMethodField()
    has_updated = serializers.SerializerMethodField(help_text="相对上次发布，有更新")

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
            "labels",
            "docs",
            "has_updated",
        ]
        read_only_fields = fields

    def get_labels(self, obj):
        return self.context["labels"].get(obj.id, [])

    def get_docs(self, obj):
        return self.context["docs"].get(obj.id, [])

    def get_has_updated(self, obj):
        latest_version_created_time = self.context["latest_version_created_time"]
        return not (latest_version_created_time and latest_version_created_time > obj.updated_time)


class ResourceAuthConfigSLZ(serializers.Serializer):
    auth_verified_required = serializers.BooleanField()
    app_verified_required = serializers.BooleanField(required=False)
    resource_perm_required = serializers.BooleanField(required=False)


class HttpBackendConfigSLZ(serializers.Serializer):
    method = serializers.ChoiceField(choices=RESOURCE_METHOD_CHOICES)
    path = serializers.RegexField(PATH_PATTERN)
    match_subpath = serializers.BooleanField(required=False)
    timeout = serializers.IntegerField(max_value=MAX_BACKEND_TIMEOUT_IN_SECOND, min_value=0, required=False)


class ResourceInputSLZ(serializers.ModelSerializer):
    api = serializers.HiddenField(default=CurrentGatewayDefault())
    name = serializers.RegexField(RESOURCE_NAME_PATTERN, max_length=256, required=True)
    path = serializers.RegexField(PATH_PATTERN, max_length=2048)
    auth_config = ResourceAuthConfigSLZ()
    backend_id = serializers.IntegerField()
    backend_config = HttpBackendConfigSLZ()
    label_ids = serializers.ListField(
        child=serializers.IntegerField(), allow_empty=True, required=False, max_length=MAX_LABEL_COUNT_PER_RESOURCE
    )

    class Meta:
        model = Resource
        fields = [
            "api",
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

        validators = [
            MaxCountPerGatewayValidator(
                Resource,
                max_count_callback=lambda gateway: GatewayHandler.get_max_resource_count(gateway),
                message=gettext_lazy("每个网关最多创建 {max_count} 个资源。"),
            ),
            UniqueTogetherValidator(
                queryset=Resource.objects.all(),
                fields=["api", "name"],
                message=gettext_lazy("网关下资源名称已经存在。"),
            ),
            UniqueTogetherValidator(
                queryset=Resource.objects.all(),
                fields=["api", "method", "path"],
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
        self._validate_method(data["api"], data["path"], data["method"])
        self._validate_match_subpath(data)

        data["resource"] = self.instance
        data["backend"] = self._validate_backend_id(data["api"], data["backend_id"])

        return data

    def _validate_method(self, gateway: Gateway, path: str, method: str):
        """
        校验资源请求方法
        - 如果请求方法 method 为 ANY，则相同 path 下不能存在其他资源
        - 如果请求方法 method 不为 ANY，则校验 path 下不能存在 method 为 ANY 的资源
        """
        queryset = Resource.objects.filter(api_id=gateway.id, path=path)
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


class ResourceOutputSLZ(serializers.ModelSerializer):
    auth_config = serializers.SerializerMethodField()
    backend_id = serializers.SerializerMethodField()
    backend_config = serializers.SerializerMethodField()
    labels = serializers.SerializerMethodField()

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

    def get_auth_config(self, obj):
        return self.context["auth_config"]

    def get_backend_id(self, obj):
        return self.context["proxy"].backend_id

    def get_backend_config(self, obj):
        return self.context["proxy"].config

    def get_labels(self, obj):
        return self.context["labels"].get(obj.id, [])


class ResourceBatchUpdateInputSLZ(serializers.Serializer):
    ids = serializers.ListField(child=serializers.IntegerField(min_value=1))
    is_public = serializers.BooleanField()
    allow_apply_permission = serializers.BooleanField()


class ResourceBatchDestroyInputSLZ(serializers.Serializer):
    ids = serializers.ListField(child=serializers.IntegerField(min_value=1))


class ResourceLabelUpdateInputSLZ(serializers.Serializer):
    label_ids = serializers.ListField(
        child=serializers.IntegerField(), allow_empty=True, max_length=MAX_LABEL_COUNT_PER_RESOURCE
    )


class ResourceDataSLZ(serializers.ModelSerializer):
    api = serializers.HiddenField(default=CurrentGatewayDefault())
    name = serializers.RegexField(RESOURCE_NAME_PATTERN, max_length=256, required=True)
    path = serializers.RegexField(PATH_PATTERN, max_length=2048)
    auth_config = ResourceAuthConfigSLZ()
    backend_id = serializers.IntegerField()
    backend_config = HttpBackendConfigSLZ()
    labels = serializers.ListField(
        child=serializers.CharField(), allow_empty=True, required=False, max_length=MAX_LABEL_COUNT_PER_RESOURCE
    )
    proxy_configs = serializers.DictField(required=False)

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
            "backend_id",
            "backend_config",
            # 标签
            "labels",
            # 兼容旧版数据
            "proxy_configs",
        ]

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

    name = serializers.CharField()


class ResourceImportInputSLZ(serializers.Serializer):
    content = serializers.CharField(allow_blank=False, required=True)
    selected_resources = serializers.ListField(
        child=SelectedResourceSLZ(), allow_empty=False, allow_null=True, required=False
    )
    delete = serializers.BooleanField(default=False)

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
                "api": self.context["api"],
                "stages": Stage.objects.filter(api=self.context["api"]),
            },
        )
        slz.is_valid(raise_exception=True)
        return slz.validated_data

    def _validate_label_count(self, resources: List[Dict[str, Any]]):
        label_names = set()
        for resource in resources:
            label_names.update(resource.get("labels", []))

        if len(label_names) > settings.MAX_LABEL_COUNT_PER_GATEWAY:
            raise serializers.ValidationError(
                _("每个网关最多创建 {max_count} 个标签。").format(max_count=settings.MAX_LABEL_COUNT_PER_GATEWAY)
            )


class ResourceImportCheckInputSLZ(ResourceImportInputSLZ):
    doc_language = serializers.ChoiceField(choices=DocLanguageEnum.get_choices(), allow_blank=True, required=False)


class ResourceImportCheckOutputSLZ(serializers.Serializer):
    id = serializers.SerializerMethodField()
    name = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)
    method = serializers.CharField(read_only=True)
    path = serializers.SerializerMethodField()
    doc = serializers.SerializerMethodField()

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
        choices=SwaggerFormatEnum.get_choices(),
        default=SwaggerFormatEnum.YAML.value,
    )
    resource_filter_condition = ResourceQueryInputSLZ(required=False)
    resource_ids = serializers.ListField(child=serializers.IntegerField(), allow_empty=True, required=False)


class ResourceExportOutputSLZ(serializers.Serializer):
    name = serializers.CharField()
    description = serializers.CharField()
    description_en = serializers.CharField()
    method = serializers.CharField()
    path = serializers.CharField()
    match_subpath = serializers.BooleanField()
    is_public = serializers.BooleanField()
    allow_apply_permission = serializers.BooleanField()

    labels = serializers.SerializerMethodField()
    backend_name = serializers.SerializerMethodField()
    Backend_config = serializers.SerializerMethodField()
    auth_config = serializers.SerializerMethodField()

    # 兼容旧版 yaml 逻辑，保留几个小版本，在某一大版本可删除
    proxy_type = serializers.SerializerMethodField()
    proxy_configs = serializers.SerializerMethodField()

    def get_labels(self, obj):
        labels = self.context["labels"].get(obj.id, [])
        return [label["name"] for label in labels]

    def get_backend_name(self, obj):
        proxy = self.context["proxies"][obj.id]
        return self.context["backends"].get(proxy.backend_id, "")

    def get_backend_config(self, obj):
        proxy = self.context["proxies"][obj.id]
        return proxy.config

    def get_auth_config(self, obj):
        return self.context["auth_configs"][obj.id]

    def get_proxy_type(self, obj):
        proxy = self.context["proxies"][obj.id]
        return proxy.type

    def get_proxy_configs(self, obj):
        return self.get_backend_config(obj)


class BackendPathCheckInputSLZ(serializers.Serializer):
    api = serializers.HiddenField(default=CurrentGatewayDefault())
    path = serializers.RegexField(
        PATH_PATTERN,
        label="请求路径",
        required=False,
        allow_blank=True,
        error_messages={
            "invalid": gettext_lazy("斜线(/)开头的合法URL路径，不包含http(s)开头的域名。"),
        },
    )
    backend_id = serializers.IntegerField(required=False)
    backend_path = serializers.RegexField(
        PATH_PATTERN,
        label="Path",
        error_messages={
            "invalid": gettext_lazy("斜线(/)开头的合法URL路径，不包含http(s)开头的域名。"),
        },
    )

    class Meta:
        validators = [
            BackendPathVarsValidator(check_stage_vars_exist=True),
        ]

    def to_internal_value(self, data):
        data = super().to_internal_value(data)
        return {
            "path": data.get("path", ""),
            "backend_config": {
                "path": data["backend_path"],
            },
        }


class BackendPathCheckOutputSLZ(serializers.Serializer):
    stage = serializers.DictField(read_only=True)
    backend_urls = serializers.ListField(child=serializers.CharField(read_only=True), allow_empty=True)


class ResourceWithVerifiedUserRequiredOutputSLZ(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
