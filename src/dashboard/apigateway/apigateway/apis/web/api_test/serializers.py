# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2025 Tencent. All rights reserved.
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
from typing import Any, Dict

from django.conf import settings
from rest_framework import serializers

from apigateway.apps.support.constants import ProgrammingLanguageEnum
from apigateway.biz.gateway import GatewayHandler, GatewayTypeHandler
from apigateway.common.i18n.field import SerializerTranslatedField
from apigateway.core.constants import HTTP_METHOD_CHOICES, PLUGIN_GATEWAY_PREFIX


class AuthorizationSLZ(serializers.Serializer):
    bk_app_code = serializers.CharField(allow_blank=True, required=False, help_text="蓝鲸应用编码")
    bk_app_secret = serializers.CharField(allow_blank=True, required=False, help_text="蓝鲸应用密钥")
    bk_ticket = serializers.CharField(allow_blank=True, required=False, help_text="蓝鲸用户票据")
    bk_token = serializers.CharField(allow_blank=True, required=False, help_text="蓝鲸用户票据")
    uin = serializers.CharField(allow_blank=True, required=False, help_text="uin")
    skey = serializers.CharField(allow_blank=True, required=False, help_text="skey")

    class Meta:
        ref_name = "apigateway.apis.web.api_test.serializers.AuthorizationSLZ"

    def validate_uin(self, value):
        try:
            return value.lstrip("o0")
        except Exception:  # pylint: disable=broad-except
            return value

    def validate(self, data: Dict[str, str]) -> Dict[str, str]:
        return {k: v for k, v in data.items() if v}


class APITestInputSLZ(serializers.Serializer):
    stage_id = serializers.IntegerField(help_text="环境 ID")
    resource_id = serializers.IntegerField(help_text="资源 ID")
    method = serializers.ChoiceField(choices=HTTP_METHOD_CHOICES, help_text="HTTP 方法")
    subpath = serializers.CharField(allow_blank=True, required=False, help_text="子路径")
    headers = serializers.DictField(child=serializers.CharField(), allow_empty=True, help_text="请求头")
    path_params = serializers.DictField(child=serializers.CharField(), allow_empty=True, help_text="路径参数")
    query_params = serializers.DictField(child=serializers.CharField(), allow_empty=True, help_text="查询参数")
    body = serializers.CharField(allow_blank=True, required=False, help_text="请求体")
    use_test_app = serializers.BooleanField(help_text="是否使用测试应用")
    use_user_from_cookies = serializers.BooleanField(
        required=False, default=False, help_text="是否使用 cookies 中的用户信息"
    )
    authorization = AuthorizationSLZ(required=False, allow_null=True, help_text="认证信息")

    class Meta:
        ref_name = "apigateway.apis.web.api_test.serializers.APITestInputSLZ"

    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        data.setdefault("authorization", {})
        if data.get("use_test_app"):
            data["authorization"].update(settings.DEFAULT_TEST_APP)

        return data


class APITestOutputSLZ(serializers.Serializer):
    status_code = serializers.IntegerField(help_text="HTTP 状态码")
    proxy_time = serializers.IntegerField(help_text="网关代理耗时")
    size = serializers.FloatField(help_text="响应体大小")
    body = serializers.CharField(help_text="响应体内容")
    headers = serializers.DictField(help_text="响应头")

    class Meta:
        ref_name = "apigateway.apis.web.api_test.serializers.APITestOutputSLZ"


class APIDebugHistoriesListOutputSLZ(serializers.Serializer):
    id = serializers.IntegerField(read_only=True, help_text="测试历史ID")
    created_time = serializers.DateTimeField(allow_null=True, read_only=True, help_text="创建时间")
    gateway_id = serializers.IntegerField(read_only=True, help_text="网关ID")
    resource_name = serializers.CharField(read_only=True, help_text="资源名称")
    request = serializers.JSONField(help_text="请求参数")
    response = serializers.JSONField(help_text="返回结果")

    class Meta:
        ref_name = "apigateway.apis.web.api_test.serializers.APIDebugHistoriesListOutputSLZ"


class ApiTestDocsGatewayOutputSLZ(serializers.Serializer):
    id = serializers.IntegerField(help_text="网关 ID")
    name = serializers.CharField(help_text="网关名称")
    description = SerializerTranslatedField(default_field="description_i18n", allow_blank=True, help_text="网关描述")
    tenant_mode = serializers.CharField(read_only=True, help_text="租户模式")
    tenant_id = serializers.CharField(read_only=True, help_text="租户 ID")
    maintainers = serializers.ListField(help_text="网关负责人")
    doc_maintainers = serializers.JSONField(help_text="网关文档维护人员")
    is_official = serializers.SerializerMethodField(help_text="是否为官方网关, true: 是, false: 否")
    is_plugin_gateway = serializers.SerializerMethodField(help_text="是否为插件网关, true: 是, false: 否")
    api_url = serializers.SerializerMethodField(help_text="网关访问地址")
    sdks = serializers.SerializerMethodField(help_text="SDK")

    class Meta:
        ref_name = "apigateway.apis.web.api_test.serializers.ApiTestDocsGatewayOutputSLZ"

    def get_api_url(self, obj):
        return GatewayHandler.get_api_domain(obj)

    def get_is_official(self, obj):
        return GatewayTypeHandler.is_official(self.context["gateway_auth_configs"][obj.id].gateway_type)

    def get_is_plugin_gateway(self, obj):
        return obj.name.startswith(PLUGIN_GATEWAY_PREFIX)

    def get_sdks(self, obj):
        return self.context["gateway_sdks"].get(obj.id, [])


class ApiTestDocsSDKListInputSLZ(serializers.Serializer):
    language = serializers.ChoiceField(
        choices=ProgrammingLanguageEnum.get_choices(), help_text="SDK 编程语言，如 python"
    )

    class Meta:
        ref_name = "apigateway.apis.web.api_test.serializers.ApiTestDocsSDKListInputSLZ"


class ApiTestDocsStageSLZ(serializers.Serializer):
    id = serializers.IntegerField(read_only=True, help_text="网关环境 ID")
    name = serializers.CharField(read_only=True, help_text="网关环境名称")

    class Meta:
        ref_name = "apigateway.apis.web.api_test.serializers.ApiTestDocsStageSLZ"


class ApiTestDocsSDKSLZ(serializers.Serializer):
    name = serializers.CharField(read_only=True, help_text="SDK 名称")
    version = serializers.CharField(read_only=True, help_text="SDK 版本号")
    url = serializers.CharField(read_only=True, help_text="SDK 下载链接")
    install_command = serializers.CharField(read_only=True, help_text="SDK 安装命令")

    class Meta:
        ref_name = "apigateway.apis.web.api_test.serializers.ApiTestDocsSDKSLZ"


class ApiTestDocsResourceVersionSLZ(serializers.Serializer):
    id = serializers.IntegerField(read_only=True, help_text="资源版本 ID")
    version = serializers.CharField(read_only=True, help_text="资源版本号")

    class Meta:
        ref_name = "apigateway.apis.web.api_test.serializers.ApiTestDocsResourceVersionSLZ"


class ApiTestDocsStageSDKOutputSLZ(serializers.Serializer):
    stage = ApiTestDocsStageSLZ(help_text="网关环境")
    resource_version = ApiTestDocsResourceVersionSLZ(help_text="资源版本")
    sdk = ApiTestDocsSDKSLZ(allow_null=True, help_text="SDK")

    class Meta:
        ref_name = "apigateway.apis.web.api_test.serializers.ApiTestDocsStageSDKOutputSLZ"


class ApiTestDocsResourceListInputSLZ(serializers.Serializer):
    stage_name = serializers.CharField(help_text="网关环境名称")

    class Meta:
        ref_name = "apigateway.apis.web.api_test.serializers.ApiTestDocsResourceListInputSLZ"


class ApiTestDocsResourceOutputSLZ(serializers.Serializer):
    id = serializers.IntegerField(read_only=True, help_text="资源 ID")
    name = serializers.CharField(read_only=True, help_text="资源名称")
    description = SerializerTranslatedField(
        translated_fields={"en": "description_en"}, allow_blank=True, read_only=True, help_text="资源描述"
    )
    method = serializers.CharField(read_only=True, help_text="资源前端请求方法")
    path = serializers.CharField(read_only=True, help_text="资源前端请求路径")
    verified_user_required = serializers.BooleanField(read_only=True, help_text="是否需要认证用户")
    verified_app_required = serializers.BooleanField(read_only=True, help_text="是否需要认证应用")
    resource_perm_required = serializers.BooleanField(read_only=True, help_text="是否验证应用访问资源的权限")
    allow_apply_permission = serializers.BooleanField(read_only=True, help_text="是否需要申请权限")
    labels = serializers.SerializerMethodField(help_text="资源标签列表")

    class Meta:
        ref_name = "apigateway.apis.web.api_test.serializers.ApiTestDocsResourceOutputSLZ"

    def get_labels(self, obj):
        return self.context["labels"].get(obj.id, [])


class ApiTestDocsResourceDocInputSLZ(serializers.Serializer):
    stage_name = serializers.CharField(help_text="网关环境名称")

    class Meta:
        ref_name = "apigateway.apis.web.api_test.serializers.ApiTestDocsResourceDocInputSLZ"


class ApiTestDocsResourceDocOutputSLZ(serializers.Serializer):
    type = serializers.CharField(help_text="文档类型，如 markdown")
    content = serializers.CharField(help_text="文档内容")
    updated_time = serializers.DateTimeField(help_text="文档更新时间")

    class Meta:
        ref_name = "apigateway.apis.web.api_test.serializers.ApiTestDocsResourceDocOutputSLZ"
