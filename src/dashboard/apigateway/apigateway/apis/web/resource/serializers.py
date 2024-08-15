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
from typing import List, Optional

from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from apigateway.apis.web.constants import ExportTypeEnum
from apigateway.apis.web.resource.validators import BackendPathVarsValidator, PathVarsValidator
from apigateway.apps.plugin.models import PluginConfig
from apigateway.apps.support.constants import DocLanguageEnum
from apigateway.biz.constants import MAX_BACKEND_TIMEOUT_IN_SECOND, OpenAPIFormatEnum
from apigateway.biz.gateway import GatewayHandler
from apigateway.biz.gateway_label import GatewayLabelHandler
from apigateway.biz.resource import ResourceHandler
from apigateway.biz.validators import MaxCountPerGatewayValidator
from apigateway.common.django.validators import NameValidator
from apigateway.common.fields import CurrentGatewayDefault
from apigateway.core.constants import HTTP_METHOD_ANY, RESOURCE_METHOD_CHOICES
from apigateway.core.models import Backend, Gateway, Resource
from apigateway.core.utils import get_path_display

from .constants import MAX_LABEL_COUNT_PER_RESOURCE, PATH_PATTERN, RESOURCE_NAME_PATTERN
from .legacy_serializers import LegacyTransformHeadersSLZ, LegacyUpstreamsSLZ


class ResourceQueryInputSLZ(serializers.Serializer):
    name = serializers.CharField(allow_blank=True, required=False, help_text="资源名称，完整匹配")
    path = serializers.CharField(allow_blank=True, required=False, help_text="资源前端请求路径，完整匹配")
    method = serializers.CharField(allow_blank=True, required=False, help_text="资源请求方法，完整匹配")
    label_ids = serializers.CharField(allow_blank=True, required=False, help_text="标签 ID，多个以逗号 , 分割")
    backend_id = serializers.IntegerField(allow_null=True, required=False, help_text="后端服务 ID")
    backend_name = serializers.CharField(allow_blank=True, required=False, help_text="后端服务名称，完整匹配")
    keyword = serializers.CharField(
        allow_blank=True, required=False, help_text="资源筛选条件，支持模糊匹配资源名称，前端请求路径"
    )
    order_by = serializers.ChoiceField(
        choices=["-id", "name", "-name", "path", "-path", "updated_time", "-updated_time"],
        allow_blank=True,
        default="-updated_time",
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
    plugin_count = serializers.SerializerMethodField(help_text="插件数量")

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
            "plugin_count",
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
        # FIXME: only true when released and updated_time > latest_version_created_time
        if not latest_version_created_time:
            return False

        return latest_version_created_time < obj.updated_time

    def get_plugin_count(self, obj):
        return self.context["plugin_counts"].get(obj.id, 0)


class ResourceAuthConfigSLZ(serializers.Serializer):
    auth_verified_required = serializers.BooleanField(
        required=False, help_text="是否需要认证用户，true：需要，false：不需要"
    )
    app_verified_required = serializers.BooleanField(
        required=False, help_text="是否需要认证应用，true：需要，false：不需要"
    )
    resource_perm_required = serializers.BooleanField(
        required=False, help_text="是否需要校验资源权限，true：需要，false：不需要"
    )


class HttpBackendConfigSLZ(serializers.Serializer):
    method = serializers.ChoiceField(choices=RESOURCE_METHOD_CHOICES, help_text="请求方法")
    path = serializers.RegexField(PATH_PATTERN, help_text="请求路径")
    match_subpath = serializers.BooleanField(required=False, help_text="是否匹配所有子路径")
    timeout = serializers.IntegerField(
        max_value=MAX_BACKEND_TIMEOUT_IN_SECOND, min_value=0, required=False, help_text="超时时间"
    )
    # 1.13 版本：兼容旧版 (api_version=0.1) 资源 yaml 通过 openapi 导入
    legacy_upstreams = LegacyUpstreamsSLZ(
        allow_null=True, required=False, help_text="旧版 upstreams，管理端不需要处理"
    )
    legacy_transform_headers = LegacyTransformHeadersSLZ(
        allow_null=True, required=False, help_text="旧版 transform_headers，管理端不需要处理"
    )


class HttpBackendSLZ(serializers.Serializer):
    id = serializers.IntegerField(help_text="后端服务 ID")
    config = HttpBackendConfigSLZ(help_text="后端配置")


class ResourceInputSLZ(serializers.ModelSerializer):
    gateway = serializers.HiddenField(default=CurrentGatewayDefault())
    name = serializers.RegexField(
        RESOURCE_NAME_PATTERN,
        max_length=256,
        required=True,
        help_text="资源名称",
        validators=[NameValidator()],
    )
    path = serializers.RegexField(PATH_PATTERN, max_length=2048, help_text="前端请求路径")
    auth_config = ResourceAuthConfigSLZ(help_text="认证配置")
    backend = HttpBackendSLZ(help_text="后端服务")
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
            # 资源后端
            "backend",
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
                max_count_callback=lambda gateway: GatewayHandler.get_max_resource_count(gateway.name),
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

        # 为方便使用 ResourcesSaver 统一处理数据，对 backend 数据进行转换
        data["backend_config"] = data["backend"]["config"]
        # NOTE: 使用 backend 对象覆盖了原有的 backend 输入数据
        data["backend"] = self._validate_backend_id(data["gateway"], data["backend"]["id"])

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
                raise serializers.ValidationError(
                    _("当前请求方法为 {method}，但相同请求路径下，其它请求方法已存在。").format(method=method)
                )

        elif queryset.filter(method=HTTP_METHOD_ANY).exists():
            raise serializers.ValidationError(
                _("当前请求方法为 {method}，但相同请求路径下，请求方法 {method_any} 已存在。").format(
                    method=method,
                    method_any=HTTP_METHOD_ANY,
                )
            )

    def _validate_match_subpath(self, data):
        if data.get("match_subpath", False) != data["backend"]["config"].get("match_subpath", False):
            raise serializers.ValidationError(
                _("资源前端配置中的【匹配所有子路径】与后端配置中的【追加匹配的子路径】值必需相同。")
            )

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
    backend = serializers.SerializerMethodField(help_text="后端服务")
    labels = serializers.SerializerMethodField(help_text="标签列表")
    schema = serializers.SerializerMethodField(help_text="参数协议")

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
            "backend",
            "labels",
            "schema",
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

    def get_backend(self, obj):
        return {
            "id": self.context["proxy"].backend_id,
            "config": self.context["proxy"].config,
        }

    def get_labels(self, obj):
        return self.context["labels"].get(obj.id, [])

    def get_schema(self, obj):
        resource_schema = self.context["resource_id_to_schema"].get(obj.id)
        if resource_schema:
            return resource_schema.schema

        return {}


class ResourceBatchUpdateInputSLZ(serializers.Serializer):
    ids = serializers.ListField(child=serializers.IntegerField(min_value=1), help_text="资源 ID 列表")
    is_public = serializers.BooleanField(help_text="是否公开，true：公开，false：不公开")
    allow_apply_permission = serializers.BooleanField(help_text="是否允许应用在开发者中心申请访问资源的权限")
    is_update_labels = serializers.BooleanField(
        help_text="是否批量修改标签，true:需要批量修改标签，false：不批量修改标签", required=False, default=False
    )
    label_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=True,
        required=False,
        max_length=MAX_LABEL_COUNT_PER_RESOURCE,
        help_text="标签 ID 列表",
    )

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


class PluginConfigImportSLZ(serializers.Serializer):
    type = serializers.CharField(help_text="插件类型")
    yaml = serializers.CharField(allow_blank=True, help_text="插件 yaml 格式配置")


class ResourceDataImportSLZ(serializers.ModelSerializer):
    name = serializers.RegexField(
        RESOURCE_NAME_PATTERN,
        max_length=256,
        required=True,
        help_text="资源名称",
        validators=[NameValidator()],
    )
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
    plugin_configs = serializers.ListField(
        child=PluginConfigImportSLZ(),
        allow_empty=True,
        allow_null=True,
        required=False,
        help_text="插件配置列表",
    )
    openapi_schema = serializers.DictField(allow_empty=True, required=False)

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
            # 插件配置
            "plugin_configs",
            # 接口协议
            "openapi_schema",
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


class ResourceImportInputSLZ(serializers.Serializer):
    gateway = serializers.HiddenField(default=CurrentGatewayDefault())
    import_resources = serializers.ListField(
        child=ResourceDataImportSLZ(),
        allow_null=True,
        required=False,
        help_text="导入的资源列表",
    )
    doc_language = serializers.ChoiceField(
        choices=DocLanguageEnum.get_choices(),
        allow_blank=True,
        required=False,
        help_text="文档语言，en: 英文，zh: 中文",
    )


class ResourceImportDocPreviewInputSLZ(serializers.Serializer):
    gateway = serializers.HiddenField(default=CurrentGatewayDefault())
    review_resource = ResourceDataImportSLZ(required=True, help_text="要预览的资源")
    doc_language = serializers.ChoiceField(
        choices=DocLanguageEnum.get_choices(),
        allow_blank=True,
        required=False,
        help_text="文档语言，en: 英文，zh: 中文",
    )


class ResourceImportCheckInputSLZ(serializers.Serializer):
    content = serializers.CharField(allow_blank=False, required=True, help_text="导入内容，yaml/json 格式字符串")


class ResourceImportCheckFailOutputSLZ(serializers.Serializer):
    message = serializers.CharField(read_only=True, help_text="check失败信息")
    json_path = serializers.CharField(read_only=True, help_text="对应的path")


class ResourceImportInfoSLZ(serializers.Serializer):
    id = serializers.SerializerMethodField(help_text="资源 ID")
    name = serializers.CharField(read_only=True, help_text="资源名称")
    description = serializers.CharField(read_only=True, help_text="资源描述")
    description_en = serializers.CharField(help_text="资源英文描述")
    method = serializers.CharField(read_only=True, help_text="请求方法")
    path = serializers.CharField(help_text="请求路径")
    path_display = serializers.SerializerMethodField(required=False, help_text="请求路径(需要体现是否匹配所有子路径)")
    match_subpath = serializers.BooleanField(help_text="是否匹配所有子路径")
    is_public = serializers.BooleanField(help_text="是否公开")
    allow_apply_permission = serializers.BooleanField(help_text="是否允许应用在开发者中心申请访问资源的权限")

    doc = serializers.SerializerMethodField(help_text="资源文档列表，zh和en")
    auth_config = ResourceAuthConfigSLZ(help_text="认证配置")
    backend = serializers.SerializerMethodField(help_text="后端服务")
    labels = serializers.SerializerMethodField(help_text="参数协议")
    openapi_schema = serializers.SerializerMethodField(help_text="参数协议")
    plugin_configs = serializers.ListField(
        child=PluginConfigImportSLZ(),
        allow_empty=True,
        allow_null=True,
        required=False,
        help_text="插件配置列表",
    )

    def get_id(self, obj):
        return obj.resource and obj.resource.id

    def get_path_display(self, obj):
        return get_path_display(obj.path, obj.match_subpath)

    def get_doc(self, obj):
        resource_id = self.get_id(obj)
        return self.context["docs"].get(resource_id, [])

    def get_backend(self, obj):
        return {
            "name": obj.backend.name,
            "config": {
                "method": obj.backend_config.method,
                "path": obj.backend_config.path,
                "match_subpath": obj.backend_config.match_subpath,
                "timeout": obj.backend_config.timeout,
            },
        }

    def get_labels(self, obj):
        return obj.metadata.get("labels", [])

    def get_openapi_schema(self, obj):
        return obj.openapi_schema


class ResourceExportInputSLZ(serializers.Serializer):
    export_type = serializers.ChoiceField(
        choices=ExportTypeEnum.get_choices(),
        help_text="值为 all，不需其它参数；值为 filtered，支持 query/path/method/label_name 参数；值为 selected，支持 resource_ids 参数",
    )
    file_type = serializers.ChoiceField(
        choices=OpenAPIFormatEnum.get_choices(),
        default=OpenAPIFormatEnum.YAML.value,
        help_text="导出的文件类型，如 yaml/json",
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
    backend = serializers.SerializerMethodField(help_text="后端服务")
    plugin_configs = serializers.SerializerMethodField(help_text="插件配置")
    auth_config = serializers.SerializerMethodField(help_text="认证配置")
    openapi_schema = serializers.SerializerMethodField(help_text="参数协议")

    def get_labels(self, obj):
        labels = self.context["labels"].get(obj.id, [])
        return [label["name"] for label in labels]

    def get_backend(self, obj):
        proxy = self.context["proxies"][obj.id]
        return {
            "name": self.context["backends"][proxy.backend_id].name,
            "config": proxy.config,
        }

    def get_auth_config(self, obj):
        return self.context["auth_configs"][obj.id]

    def get_plugin_configs(self, obj) -> List[PluginConfig]:
        return [binding.config for binding in self.context["resource_id_to_plugin_bindings"].get(obj.id, [])]

    def get_openapi_schema(self, obj):
        schema = self.context["resource_id_to_schema"].get(obj.id)
        if schema:
            return schema.schema
        return {}


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
