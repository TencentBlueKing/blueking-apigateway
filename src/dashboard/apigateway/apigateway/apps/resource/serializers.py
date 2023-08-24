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

from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueTogetherValidator
from tencent_apigateway_common.i18n.field import SerializerTranslatedField

from apigateway.apps.label.models import ResourceLabel
from apigateway.apps.resource.validators import PathVarsValidator, ProxyPathVarsValidator
from apigateway.apps.stage.serializers import HostSLZ, TransformHeadersSLZ, UpstreamsSLZ
from apigateway.biz.resource import ResourceHandler
from apigateway.biz.resource_url import ResourceURLHandler
from apigateway.biz.validators import MaxCountPerGatewayValidator
from apigateway.common.contexts import ResourceAuthContext
from apigateway.common.fields import CurrentGatewayDefault
from apigateway.common.mixins.serializers import ExtensibleFieldMixin
from apigateway.core.constants import (
    HEADER_KEY_PATTERN,
    HTTP_METHOD_ANY,
    MAX_BACKEND_TIMEOUT_IN_SECOND,
    MAX_LABEL_COUNT_PER_RESOURCE,
    PATH_PATTERN,
    RESOURCE_DOMAIN_PATTERN,
    RESOURCE_METHOD_CHOICES,
    RESOURCE_NAME_PATTERN,
    BackendConfigTypeEnum,
    ExportTypeEnum,
    ProxyTypeEnum,
    SwaggerFormatEnum,
)
from apigateway.core.models import Resource, StageResourceDisabled
from apigateway.core.utils import get_path_display, get_resource_url


class ResourceHostSLZ(HostSLZ):
    host = serializers.RegexField(RESOURCE_DOMAIN_PATTERN)


class ResourceUpstreamsSLZ(UpstreamsSLZ):
    hosts = serializers.ListField(child=ResourceHostSLZ())


class QueryResourceSLZ(serializers.Serializer):
    query = serializers.CharField(allow_blank=True, required=False)
    path = serializers.CharField(allow_blank=True, required=False)
    method = serializers.CharField(allow_blank=True, required=False)
    label_name = serializers.CharField(allow_blank=True, required=False)
    order_by = serializers.ChoiceField(
        choices=["path", "-path", "name", "-name", "updated_time", "-updated_time"],
        allow_blank=True,
        required=False,
    )


class ListResourceSLZ(serializers.ModelSerializer):
    labels = serializers.SerializerMethodField()
    is_created = serializers.SerializerMethodField(help_text="新建且未发布")
    has_updated = serializers.SerializerMethodField(help_text="相对上次发布，有更新")
    path = serializers.CharField(source="path_display", read_only=True)
    released_stage_count = serializers.SerializerMethodField()
    unreleased_stage_count = serializers.SerializerMethodField()
    resource_doc_languages = serializers.SerializerMethodField()
    description = SerializerTranslatedField(default_field="description_i18n")

    class Meta:
        model = Resource
        fields = [
            "id",
            "name",
            "description",
            "description_en",
            "method",
            "path",
            "updated_time",
            "labels",
            "is_created",
            "has_updated",
            "released_stage_count",
            "unreleased_stage_count",
            "resource_doc_languages",
        ]
        read_only_fields = ["name", "description", "method", "path", "updated_time"]

    def get_labels(self, obj):
        return self.context["resource_labels"].get(obj.id, [])

    def get_has_updated(self, obj):
        latest_resource_version = self.context["latest_resource_version"]
        return not latest_resource_version or latest_resource_version.created_time < obj.updated_time

    def get_is_created(self, obj):
        """
        未发布，且新创建的资源，展示“新创建”标记
        """
        if not self.get_has_updated(obj):
            return False
        # 更新时间与创建时间差别不到 1 秒，则认为是新创建
        return (obj.updated_time - obj.created_time).total_seconds() < 1

    def get_released_stage_count(self, obj):
        return self.context["resource_released_stage_count"].get(obj.id, 0)

    def get_unreleased_stage_count(self, obj):
        return self.context["stage_count"] - self.context["resource_released_stage_count"].get(obj.id, 0)

    def get_resource_doc_languages(self, obj):
        return self.context["doc_languages_of_resources"].get(obj.id, [])


class BaseProxyHTTPConfigSLZ(serializers.Serializer):
    method = serializers.ChoiceField(choices=RESOURCE_METHOD_CHOICES)
    path = serializers.RegexField(PATH_PATTERN)
    match_subpath = serializers.BooleanField(required=False)
    transform_headers = TransformHeadersSLZ(required=False)


class DefaultProxyHTTPConfigSLZ(BaseProxyHTTPConfigSLZ):
    """默认类型的资源 Proxy HTTP 配置"""

    timeout = serializers.IntegerField(max_value=MAX_BACKEND_TIMEOUT_IN_SECOND, min_value=0)
    upstreams = ResourceUpstreamsSLZ(allow_empty=True)


class BackendServiceProxyHTTPConfigSLZ(BaseProxyHTTPConfigSLZ):
    """后端服务类型的资源 Proxy HTTP 配置"""

    # timeout = TimeoutSLZ(allow_null=True, required=False)


class ResourceProxyMockConfigSLZ(serializers.Serializer):
    code = serializers.IntegerField(min_value=0)
    body = serializers.CharField(allow_blank=True)
    headers = serializers.DictField(child=serializers.CharField())

    def validate_headers(self, value):
        for key in value:
            if not HEADER_KEY_PATTERN.match(key):
                raise serializers.ValidationError(_("Header 键由字母、数字、连接符（-）组成，长度小于100个字符。"))
        return value


class AuthConfigSLZ(serializers.Serializer):
    auth_verified_required = serializers.BooleanField()
    app_verified_required = serializers.BooleanField(required=False)
    resource_perm_required = serializers.BooleanField(required=False)


class ProxyConfigsSLZ(serializers.Serializer):
    backend_config_type = serializers.ChoiceField(
        choices=BackendConfigTypeEnum.get_choices(),
        default=BackendConfigTypeEnum.DEFAULT.value,
    )
    backend_service_id = serializers.IntegerField(min_value=1, allow_null=True, required=False)
    http = serializers.DictField(label="后端配置-HTTP", required=False)
    mock = ResourceProxyMockConfigSLZ(label="后端配置-Mock", required=False)

    class Meta:
        http_serializer: Dict[str, serializers.Serializer] = {
            # NOTE: 暂不支持自定义后端类型
            BackendConfigTypeEnum.DEFAULT.value: DefaultProxyHTTPConfigSLZ(),
            BackendConfigTypeEnum.EXISTED.value: BackendServiceProxyHTTPConfigSLZ(),
        }

    def to_internal_value(self, data):
        # 过滤掉值为空的数据
        return super().to_internal_value({k: v for k, v in data.items() if v})

    def validate(self, data):
        if data.get("http"):
            data["http"] = self._validate_http(data["backend_config_type"], data.get("http"))

        data["backend_service_id"] = self._validate_backend_service_id(
            data["backend_config_type"],
            data.get("backend_service_id"),
        )

        return data

    def _validate_http(self, backend_config_type: str, http: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        if not http:
            return {}

        serializer = self.Meta.http_serializer[backend_config_type]
        try:
            return serializer.run_validation(http)  # type: ignore
        except ValidationError as err:
            raise ValidationError({"http": err.detail})

    def _validate_backend_service_id(
        self,
        backend_config_type: str,
        backend_service_id: Optional[int],
    ) -> Optional[int]:
        if backend_config_type != BackendConfigTypeEnum.EXISTED.value:
            return None

        if not backend_service_id:
            raise ValidationError("backend_service_id is required")

        return backend_service_id


class ResourceSLZ(ExtensibleFieldMixin, serializers.ModelSerializer):
    api = serializers.HiddenField(default=CurrentGatewayDefault())
    name = serializers.RegexField(RESOURCE_NAME_PATTERN, max_length=256, required=True)
    path = serializers.RegexField(PATH_PATTERN, max_length=2048)
    label_ids = serializers.ListField(label="标签ID", child=serializers.IntegerField(), allow_empty=True, required=False)
    proxy_type = serializers.ChoiceField(choices=ProxyTypeEnum.get_choices())
    proxy_configs = ProxyConfigsSLZ()
    auth_config = AuthConfigSLZ(label="安全设置中的认证配置")
    disabled_stage_ids = serializers.ListField(
        label="禁用环境ID", child=serializers.IntegerField(), allow_empty=True, required=False
    )
    description = SerializerTranslatedField(
        default_field="description_i18n",
        allow_blank=True,
        max_length=512,
        allow_null=True,
        required=False,
    )

    class Meta:
        ref_name = "apps.resource"
        model = Resource
        fields = [
            "api",
            # 基本信息
            "id",
            "name",
            "description",
            "description_en",
            "is_public",
            "allow_apply_permission",
            "match_subpath",
            "label_ids",
            # 前端配置
            "method",
            "path",
            # 后端配置
            "proxy_type",
            "proxy_configs",
            # 安全设置之认证配置
            "auth_config",
            # 禁用环境
            "disabled_stage_ids",
        ]
        extra_kwargs = {
            "description_en": {
                "required": False,
            }
        }
        non_model_fields = [
            "label_ids",
            "proxy_type",
            "proxy_configs",
            "auth_config",
            "disabled_stage_ids",
        ]
        lookup_field = "id"

        validators = [
            MaxCountPerGatewayValidator(
                Resource,
                max_count_callback=lambda gateway: gateway.max_resource_count,
                message=gettext_lazy("每个网关最多创建 {max_count} 个资源。"),
            ),
            UniqueTogetherValidator(
                queryset=Resource.objects.all(),
                fields=["api", "method", "path"],
                message=gettext_lazy("网关前端配置中，请求路径+请求方法已经存在。"),
            ),
            UniqueTogetherValidator(
                queryset=Resource.objects.all(),
                fields=["api", "name"],
                message=gettext_lazy("网关下资源名称已经存在。"),
            ),
            PathVarsValidator(),
            ProxyPathVarsValidator(),
        ]

    def validate_label_ids(self, value):
        if len(value) > MAX_LABEL_COUNT_PER_RESOURCE:
            raise serializers.ValidationError(_("每个资源最多关联 {count} 个标签。").format(count=MAX_LABEL_COUNT_PER_RESOURCE))
        return value

    def validate_description_en(self, value) -> Optional[str]:
        # description_en 为 None 时，文档中描述会展示 description 内容，
        # 因此，前端未传入有效 description_en 时，将其设置为 None
        return value or None

    def validate(self, data):
        if not data.get("proxy_configs", {}).get(data["proxy_type"]):
            raise serializers.ValidationError(
                _("类型为 {proxy_type} 的后端配置不能为空。").format(proxy_type=data["proxy_type"].upper())
            )

        self._validate_method(data["api"], data["path"], data["method"])
        self._validate_match_subpath(data)

        return data

    def _exclude_current_instance(self, queryset):
        if self.instance is not None:
            return queryset.exclude(pk=self.instance.pk)
        return queryset

    def _validate_method(self, gateway, path, method):
        """
        校验资源请求方法
        - 如果请求方法 method 为 ANY，则相同 path 下不能存在其他资源
        - 如果请求方法 method 不为 ANY，则校验 path 下不能存在 method 为 ANY 的资源
        """
        if method == HTTP_METHOD_ANY:
            queryset = Resource.objects.filter(api_id=gateway.id, path=path)
            queryset = self._exclude_current_instance(queryset)
            if queryset.exists():
                raise serializers.ValidationError(_("当前请求方法为 {method}，但相同请求路径下，其它请求方法已存在。").format(method=method))
        else:
            queryset = Resource.objects.filter(api_id=gateway.id, path=path, method=HTTP_METHOD_ANY)
            queryset = self._exclude_current_instance(queryset)
            if queryset.exists():
                raise serializers.ValidationError(
                    _("当前请求方法为 {method}，但相同请求路径下，请求方法 {method_any} 已存在。").format(
                        method=method,
                        method_any=HTTP_METHOD_ANY,
                    )
                )

    def _validate_match_subpath(self, data):
        if data["proxy_type"] != ProxyTypeEnum.HTTP.value:
            return

        proxy_config = data.get("proxy_configs", {}).get(data["proxy_type"])
        if data.get("match_subpath", False) != proxy_config.get("match_subpath", False):
            raise serializers.ValidationError(_("资源前端配置中的【匹配所有子路径】与后端配置中的【追加匹配的子路径】值必需相同。"))

    def to_representation(self, instance):
        # proxy
        proxy_configs = ResourceHandler().get_proxy_configs(instance)
        instance.proxy_type = proxy_configs["type"]
        instance.proxy_configs = proxy_configs["configs"]
        instance.proxy_configs.update(
            backend_config_type=proxy_configs["backend_config_type"],
            backend_service_id=proxy_configs["backend_service_id"],
        )

        # resource auth config
        instance.auth_config = ResourceAuthContext().get_config(instance.id)

        # resource lables
        labels = ResourceLabel.objects.get_labels([instance.id]).get(instance.id, [])
        instance.label_ids = [label["id"] for label in labels]

        # disabled stages
        instance.disabled_stage_ids = [
            stage["id"] for stage in StageResourceDisabled.objects.get_disabled_stages(instance.id)
        ]

        return super().to_representation(instance)


class BatchUpdateResourceSLZ(serializers.Serializer):
    ids = serializers.ListField(child=serializers.IntegerField(min_value=1))
    is_public = serializers.BooleanField()
    allow_apply_permission = serializers.BooleanField()


class BatchDestroyResourceSLZ(serializers.Serializer):
    ids = serializers.ListField(child=serializers.IntegerField(min_value=1))


class ResourceURLSLZ(serializers.Serializer):
    stage_name = serializers.CharField()
    url = serializers.CharField()


class CheckProxyPathSLZ(serializers.Serializer):
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
    proxy_path = serializers.RegexField(
        PATH_PATTERN,
        label="Path",
        error_messages={
            "invalid": gettext_lazy("斜线(/)开头的合法URL路径，不包含http(s)开头的域名。"),
        },
    )

    class Meta:
        validators = [
            ProxyPathVarsValidator(check_stage_vars_exist=True),
        ]

    def to_internal_value(self, data):
        data = super().to_internal_value(data)
        return {
            "path": data.get("path", ""),
            "proxy_type": ProxyTypeEnum.HTTP.value,
            "proxy_configs": {
                "http": {
                    "path": data["proxy_path"],
                }
            },
        }


class SelectedResourceSLZ(serializers.Serializer):
    """导入时选中的资源"""

    name = serializers.CharField()


class ResourceImportSLZ(serializers.Serializer):
    content = serializers.CharField(label="", allow_blank=False, required=True)
    selected_resources = serializers.ListField(
        child=SelectedResourceSLZ(), allow_empty=False, allow_null=True, required=False
    )


class CheckImportResourceSLZ(serializers.ModelSerializer):
    id = serializers.IntegerField(allow_null=True, required=False)
    name = serializers.RegexField(RESOURCE_NAME_PATTERN, max_length=256, required=True)
    path = serializers.RegexField(PATH_PATTERN, max_length=2048)
    match_subpath = serializers.BooleanField(required=False)
    labels = serializers.ListField(child=serializers.CharField(max_length=32), allow_empty=True, required=False)
    proxy_type = serializers.ChoiceField(choices=ProxyTypeEnum.get_choices())
    proxy_configs = ProxyConfigsSLZ()
    auth_config = AuthConfigSLZ()
    disabled_stages = serializers.ListField(child=serializers.CharField(), allow_empty=True, required=False)
    resource_doc_id = serializers.IntegerField(allow_null=True, required=False)
    resource_doc_language = serializers.CharField(default="", allow_blank=True)
    # 原样保留扩展数据，方便 ESB 组件同步时，关联组件ID等数据
    extend_data = serializers.DictField(allow_empty=True, required=False, write_only=True)
    description = SerializerTranslatedField(
        default_field="description_i18n", allow_blank=True, allow_null=True, max_length=512, required=False
    )

    class Meta:
        model = Resource
        fields = [
            "id",
            # 基本信息
            "name",
            "description",
            "description_en",
            "is_public",
            "allow_apply_permission",
            "labels",
            # 前端配置
            "method",
            "path",
            "match_subpath",
            # 后端配置
            "proxy_type",
            "proxy_configs",
            # 安全设置之认证配置
            "auth_config",
            # 禁用环境
            "disabled_stages",
            # 资源文档
            "resource_doc_id",
            "resource_doc_language",
            # 扩展数据
            "extend_data",
        ]
        extra_kwargs = {
            "description_en": {
                "required": False,
            }
        }

        validators = [
            PathVarsValidator(),
            ProxyPathVarsValidator(),
        ]

    def to_internal_value(self, data):
        self._instance_id = data.get("id")

        data.update(
            {
                "resource_doc_id": self._get_resource_doc_id(self._instance_id),
                "resource_doc_language": self.context.get("resource_doc_language", ""),
            }
        )

        return super().to_internal_value(data)

    def validate(self, data):
        self._validate_proxy_config(data)

        self._validate_method(data["path"], data["method"])
        self._validate_match_subpath(data)

        return data

    def _validate_method(self, path, method):
        if path in self.context["resource_path_method_to_id"]:
            method_to_id = self.context["resource_path_method_to_id"][path]
            method_exclude_current_instance = [
                method for method, rid in method_to_id.items() if (not self._instance_id or self._instance_id != rid)
            ]

            if method == HTTP_METHOD_ANY:
                if method_exclude_current_instance:
                    raise serializers.ValidationError(
                        _("请求路径【{path}】下，存在 {method} 及其它请求方法。").format(path=path, method=method)
                    )
            elif method in method_exclude_current_instance:
                raise serializers.ValidationError(
                    _("请求路径【{path}】下，请求方法 {method} 已存在。").format(path=path, method=method)
                )
            elif HTTP_METHOD_ANY in method_exclude_current_instance:
                raise serializers.ValidationError(
                    _("请求路径【{path}】下，请求方法 {method_any} 已存在。").format(path=path, method_any=HTTP_METHOD_ANY),
                )

        self.context["resource_path_method_to_id"].setdefault(path, {})
        self.context["resource_path_method_to_id"][path][method] = self._instance_id

    def _validate_match_subpath(self, data):
        if data["proxy_type"] != ProxyTypeEnum.HTTP.value:
            return

        proxy_config = data.get("proxy_configs", {}).get(data["proxy_type"])
        if data.get("match_subpath", False) != proxy_config.get("match_subpath", False):
            raise serializers.ValidationError(_("资源前端配置中的 matchSubpath 与后端配置中的 matchSubpath 值必需相同。"))

    def _validate_proxy_config(self, data):
        if not data.get("proxy_configs", {}).get(data["proxy_type"]):
            raise serializers.ValidationError(
                _("类型为 {proxy_type} 的后端配置不能为空。").format(proxy_type=data["proxy_type"].upper())
            )

    def _get_resource_doc_id(self, resource_id: Optional[int]) -> Optional[int]:
        resource_doc_language = self.context.get("resource_doc_language")
        if not (resource_id and resource_doc_language):
            return None

        resource_doc_key = f"{resource_id}:{resource_doc_language}"
        return self.context["resource_doc_key_to_id"].get(resource_doc_key)

    def validate_labels(self, value):
        if len(value) > MAX_LABEL_COUNT_PER_RESOURCE:
            raise serializers.ValidationError(_("每个资源最多关联 {count} 个标签。").format(count=MAX_LABEL_COUNT_PER_RESOURCE))
        return value

    def validate_disabled_stages(self, value) -> List[str]:
        if not value:
            return []

        return list(set(value) & self.context["stage_name_set"])


class ResourceExportConditionSLZ(QueryResourceSLZ):
    export_type = serializers.ChoiceField(
        choices=ExportTypeEnum.get_choices(),
        help_text="值为 all，不需其它参数；值为 filtered，支持 query/path/method/label_name 参数；值为 selected，支持 resource_ids 参数",
    )
    resource_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=True,
        required=False,
        help_text='export_type 值为已选资源 "selected" 时，此项必填',
    )
    file_type = serializers.ChoiceField(
        choices=SwaggerFormatEnum.get_choices(),
        default=SwaggerFormatEnum.YAML.value,
    )
    order_by = None

    def validate(self, data):
        if data["export_type"] == ExportTypeEnum.SELECTED.value and not data["resource_ids"]:
            raise serializers.ValidationError(_("导出已选中资源时，已选中资源不能为空。"))
        return data

    def get_exported_resource(self):
        """获取被导出的资源"""
        data = self.validated_data
        gateway = self.context["gateway"]

        if data["export_type"] == ExportTypeEnum.ALL.value:
            return ResourceHandler().filter_resource(gateway=gateway)

        elif data["export_type"] == ExportTypeEnum.FILTERED.value:
            return ResourceHandler().filter_resource(
                gateway=gateway,
                query=data.get("query"),
                path=data.get("path"),
                method=data.get("method"),
                label_name=data.get("label_name"),
                fuzzy=True,
            )

        elif data["export_type"] == ExportTypeEnum.SELECTED.value:
            return Resource.objects.filter(api_id=gateway.id, id__in=data["resource_ids"])

        return Resource.objects.none()


class ExportResourceSLZ(serializers.Serializer):
    name = serializers.CharField()
    description = serializers.CharField()
    description_en = serializers.CharField()
    method = serializers.CharField()
    path = serializers.CharField()
    match_subpath = serializers.BooleanField()
    is_public = serializers.BooleanField()
    allow_apply_permission = serializers.BooleanField()

    labels = serializers.SerializerMethodField()
    proxy_type = serializers.SerializerMethodField()
    proxy_configs = serializers.SerializerMethodField()
    auth_config = serializers.SerializerMethodField()
    disabled_stages = serializers.SerializerMethodField()

    def get_labels(self, obj):
        labels = self.context["resource_labels"].get(obj.id, [])
        return [label["name"] for label in labels]

    def get_proxy_type(self, obj):
        return self.context["proxies"][obj.proxy_id]["type"]

    def get_proxy_configs(self, obj):
        proxy_type = self.get_proxy_type(obj)
        return {
            proxy_type: self.context["proxies"][obj.proxy_id]["config"],
        }

    def get_auth_config(self, obj):
        return self.context["resource_auth_configs"][obj.id]

    def get_disabled_stages(self, obj):
        stages = self.context["disabled_stages"].get(obj.id, [])
        return [stage["name"] for stage in stages]


class ResourceReleaseStageSLZ(serializers.Serializer):
    stage_id = serializers.IntegerField(source="id")
    stage_name = serializers.CharField(source="name")
    stage_release_status = serializers.SerializerMethodField()
    resource_version_id = serializers.SerializerMethodField()
    resource_version_name = serializers.SerializerMethodField()
    resource_version_title = serializers.SerializerMethodField()
    resource_version_display = serializers.SerializerMethodField()
    resource_id = serializers.SerializerMethodField()
    resource_url = serializers.SerializerMethodField()

    def get_stage_release_status(self, obj):
        return obj.id in self.context["resource_released_stages"]

    def get_resource_version_id(self, obj):
        return self._get_released_stage_info(obj, "resource_version_id")

    def get_resource_version_name(self, obj):
        return self._get_released_stage_info(obj, "resource_version_name") or ""

    def get_resource_version_title(self, obj):
        return self._get_released_stage_info(obj, "resource_version_title") or ""

    def get_resource_version_display(self, obj):
        return self._get_released_stage_info(obj, "resource_version_display") or ""

    def get_resource_id(self, obj):
        released_resource = self._get_released_stage_info(obj, "released_resource")
        if not released_resource:
            return None

        return released_resource.resource_id

    def get_resource_url(self, obj):
        released_resource = self._get_released_stage_info(obj, "released_resource")
        if not released_resource:
            return ""

        resource_data = released_resource.data
        return get_resource_url(
            resource_url_tmpl=ResourceURLHandler.get_resource_url_tmpl(self.context["api_name"], obj.name),
            gateway_name=self.context["api_name"],
            stage_name=obj.name,
            resource_path=get_path_display(resource_data["path"], resource_data.get("match_subpath", False)),
        )

    def _get_released_stage_info(self, obj, attr):
        released_stage = self.context["resource_released_stages"].get(obj.id)
        if not released_stage:
            return None

        return released_stage.get(attr)


class UpdateResourceLabelsSLZ(serializers.Serializer):
    label_ids = serializers.ListField(
        child=serializers.IntegerField(), allow_empty=True, max_length=MAX_LABEL_COUNT_PER_RESOURCE
    )
