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

from rest_framework import serializers

from apigateway.apis.web.constants import PLUGIN_MERGE_TYPE
from apigateway.apps.plugin.constants import PluginBindingScopeEnum
from apigateway.biz.constants import SEMVER_PATTERN
from apigateway.biz.validators import ResourceVersionValidator
from apigateway.common.fields import CurrentGatewayDefault
from apigateway.core.constants import ResourceVersionSchemaEnum, ResourceVersionTypeEnum


class ResourceVersionCreateInputSLZ(serializers.Serializer):
    gateway = serializers.HiddenField(default=CurrentGatewayDefault())
    version = serializers.RegexField(SEMVER_PATTERN, max_length=64, required=True, help_text="版本号")
    comment = serializers.CharField(allow_blank=True, required=False, help_text="版本日志")

    class Meta:
        validators = [ResourceVersionValidator()]


class ResourceInfoSLZ(serializers.Serializer):
    name = serializers.CharField(help_text="资源名称")
    method = serializers.CharField(help_text="前端请求方法")
    path = serializers.CharField(help_text="前端请求路径")
    description = serializers.CharField(help_text="资源描述", required=False)
    description_en = serializers.CharField(help_text="资源英文描述", required=False)
    gateway_label_ids = serializers.ListSerializer(
        source="api_labels", required=False, allow_empty=True, child=serializers.IntegerField(), help_text="标签列表"
    )
    match_subpath = serializers.BooleanField(help_text="是否匹配所有子路径", required=False)
    enable_websocket = serializers.BooleanField(help_text="是否开启 websocket", required=False)
    is_public = serializers.BooleanField(help_text="是否公开", required=False)
    allow_apply_permission = serializers.BooleanField(
        help_text="是否允许应用在开发者中心申请访问资源的权限", required=False
    )
    doc_updated_time = serializers.SerializerMethodField(help_text="资源文档更新时间")

    proxy = serializers.SerializerMethodField(help_text="后端配置")

    contexts = serializers.DictField(help_text="资源认证等相关配置")

    plugins = serializers.SerializerMethodField(help_text="绑定插件")

    def get_doc_updated_time(self, obj):
        return self.context["resource_doc_updated_time"].get(obj["id"], "")

    def get_proxy(self, obj):
        proxy = {
            # 后端配置
            "config": obj["proxy"]["config"]
        }
        backend_id = obj["proxy"].get("backend_id", None)
        if backend_id:
            # 后端服务
            backend_info = {"id": backend_id, "name": self.context["resource_backends"][backend_id].name}

            # 后端服务配置
            if "resource_backend_configs" in self.context:
                backend_info["config"] = self.context["resource_backend_configs"][backend_id].config

            proxy["backend"] = backend_info

        return proxy

    def get_plugins(self, obj):
        stage_plugins = self.context.get("stage_plugins", {})
        # v2 才有plugin数据
        if not self.context["is_schema_v2"]:
            return list(stage_plugins.values())

        plugins = []
        override_plugins = set()
        for plugin in obj.get("plugins", []):
            plugin_type = plugin["type"]
            plugin["binding_type"] = PluginBindingScopeEnum.RESOURCE.value

            # 根据 rules 配置确定是否资源插件配置覆盖环境插件配置
            # 如果类型是merge， 同一个类型的环境 + 资源插件将会同时存在
            # 如果类型是override， 同一个类型的环境插件将会被资源插件覆盖
            if not (stage_plugins.get(plugin_type) and PLUGIN_MERGE_TYPE.get(plugin_type, "") == "merge"):
                override_plugins.add(plugin_type)

            plugins.append(plugin)

        plugins.extend(
            [plugin for plugin_type, plugin in stage_plugins.items() if plugin_type not in override_plugins]
        )

        return plugins


class ResourceVersionRetrieveOutputSLZ(serializers.Serializer):
    id = serializers.IntegerField(help_text="id")
    version = serializers.CharField(source="object_display", help_text="版本号")
    comment = serializers.CharField(help_text="版本日志")
    schema_version = serializers.ChoiceField(
        choices=ResourceVersionSchemaEnum.get_choices(), help_text="版本数据schema版本:1.0(旧)/2.0(新)"
    )
    resources = serializers.ListField(
        source="data", child=ResourceInfoSLZ(), allow_empty=True, help_text="版本资源列表"
    )
    created_time = serializers.DateTimeField(help_text="创建时间")
    created_by = serializers.CharField(help_text="创建人")


class ResourceVersionListInputSLZ(serializers.Serializer):
    keyword = serializers.CharField(allow_blank=True, required=False, help_text="资源版本筛选条件，支持模糊匹配")


class ResourceVersionListOutputSLZ(serializers.Serializer):
    id = serializers.IntegerField(help_text="id")
    released_stages = serializers.SerializerMethodField(help_text="已发布的环境列表")
    sdk_count = serializers.SerializerMethodField(help_text="生成skd数量")
    version = serializers.SerializerMethodField(help_text="版本号")
    schema_version = serializers.CharField(help_text="资源版本协议版本：1.0/2.0")
    comment = serializers.CharField(help_text="版本日志")
    created_time = serializers.DateTimeField(help_text="创建时间")
    created_by = serializers.CharField(help_text="创建人")

    def get_released_stages(self, obj):
        return self.context["released_stages"].get(obj["id"], [])

    def get_sdk_count(self, obj):
        return self.context["resource_version_ids_sdk_count"].get(obj["id"], 0)

    def get_version(self, obj):
        version = obj.get("version")
        if not version:
            # 兼容历史数据
            name = obj.get("name")
            title = obj.get("title")
            return f"{title}({name})"
        return version


class NeedNewVersionOutputSLZ(serializers.Serializer):
    need_new_version = serializers.BooleanField(help_text="是否需要生成版本")


class ResourceVersionDiffQueryInputSLZ(serializers.Serializer):
    source_resource_version_id = serializers.IntegerField(allow_null=True, help_text="对比源的版本号id")
    target_resource_version_id = serializers.IntegerField(allow_null=True, help_text="对比目标的版本号id")


class ResourceVersionResourceSLZ(serializers.Serializer):
    id = serializers.IntegerField(help_text="id")
    name = serializers.CharField(help_text="资源名称")
    method = serializers.CharField(help_text="请求方法")
    path = serializers.CharField(help_text="请求路径")
    diff = serializers.DictField(help_text="对比差异", allow_null=True)


class ResourceVersionDiffOutputSLZ(serializers.Serializer):
    add = ResourceVersionResourceSLZ()
    delete = ResourceVersionResourceSLZ()
    update = serializers.DictField(child=ResourceVersionResourceSLZ())


class NextProgrammableDeployVersionGetInputSLZ(serializers.Serializer):
    stage_name = serializers.IntegerField(required=True, help_text="环境name")
    version_type = serializers.ChoiceField(
        choices=ResourceVersionTypeEnum.get_choices(), help_text="版本类型：major/minor/patch"
    )
