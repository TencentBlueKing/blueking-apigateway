# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) Tencent. All rights reserved.
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

from apigateway.apis.sdk_fields import SDKGenerationLanguageField
from apigateway.apps.support.constants import (
    ProgrammingLanguageEnum,
    SDKArtifactTypeEnum,
    SDKGenerationItemStatusEnum,
    SDKNativePublicationStatusEnum,
)
from apigateway.apps.support.models import GatewaySDK, SDKGenerationItem
from apigateway.common.fields import CurrentGatewayDefault


class GatewaySDKGenerateInputSLZ(serializers.Serializer):
    gateway = serializers.HiddenField(default=CurrentGatewayDefault())
    resource_version_id = serializers.IntegerField(required=True, help_text="资源版本号id")
    languages = serializers.ListField(
        child=SDKGenerationLanguageField(),
        allow_empty=False,
        required=True,
        help_text="SDK 语言列表",
    )

    class Meta:
        ref_name = "apigateway.apis.web.sdk.serializers.GatewaySDKGenerateInputSLZ"


class GatewaySDKQueryInputSLZ(serializers.Serializer):
    language = serializers.ChoiceField(
        choices=ProgrammingLanguageEnum.get_choices(), required=False, help_text="sdk语言"
    )
    version_number = serializers.CharField(required=False, allow_blank=True, help_text="sdk版本号")
    resource_version_id = serializers.IntegerField(allow_null=True, required=False, help_text="资源版本号id")
    keyword = serializers.CharField(allow_blank=True, required=False, help_text="查询关键字，支持模糊匹配")

    class Meta:
        ref_name = "apigateway.apis.web.sdk.serializers.GatewaySDKQueryInputSLZ"


class ResourceVersionInfoSlz(serializers.Serializer):
    id = serializers.IntegerField(help_text="资源版本号id")
    version = serializers.CharField(help_text="资源版本")

    class Meta:
        ref_name = "apigateway.apis.web.sdk.serializers.ResourceVersionInfoSlz"


class SDKArtifactOutputSLZ(serializers.Serializer):
    distributor = serializers.CharField()
    type = serializers.CharField()
    filename = serializers.CharField()
    url = serializers.CharField()
    package_reference = serializers.CharField()
    size = serializers.IntegerField()
    sha256 = serializers.CharField()
    status = serializers.CharField()


class SDKGenerationItemOutputSLZ(serializers.Serializer):
    id = serializers.IntegerField()
    language = serializers.CharField()
    status = serializers.CharField()
    native_status = serializers.CharField()
    attempt_count = serializers.IntegerField()
    error = serializers.DictField(allow_null=True)
    native_error = serializers.DictField(allow_null=True)
    download_url = serializers.CharField(allow_blank=True)
    artifacts = SDKArtifactOutputSLZ(many=True)


class SDKGenerationTaskOutputSLZ(serializers.Serializer):
    id = serializers.IntegerField()
    status = serializers.CharField()
    resource_version = ResourceVersionInfoSlz()
    items = SDKGenerationItemOutputSLZ(many=True)


class GatewaySDKListOutputSLZ(serializers.Serializer):
    id = serializers.IntegerField(allow_null=True, help_text="sdk id")
    generation_task_id = serializers.IntegerField(allow_null=True)
    generation_item_id = serializers.IntegerField(allow_null=True)
    resource_version = ResourceVersionInfoSlz(help_text="sdk资源版本信息")
    version_number = serializers.CharField(help_text="sdk版本号")
    language = serializers.CharField(help_text="sdk语言")
    name = serializers.CharField(help_text="sdk名称")
    status = serializers.CharField()
    native_status = serializers.CharField()
    error = serializers.DictField(allow_null=True)
    native_error = serializers.DictField(allow_null=True)
    download_url = serializers.CharField(allow_blank=True, allow_null=True, help_text="sdk下载url")
    created_by = serializers.CharField(allow_blank=True, allow_null=True, help_text="SDK 创建者")
    created_time = serializers.DateTimeField(help_text="sdk创建时间")
    updated_time = serializers.DateTimeField(help_text="sdk更新时间")

    class Meta:
        ref_name = "apigateway.apis.web.sdk.serializers.GatewaySDKListOutputSLZ"

    def to_representation(self, instance):
        if isinstance(instance, SDKGenerationItem):
            instance = self._generation_item_data(instance)
        elif isinstance(instance, GatewaySDK):
            instance = self._legacy_sdk_data(instance)
        return super().to_representation(instance)

    @staticmethod
    def _error(code: str, message: str) -> dict[str, str] | None:
        return {"code": code, "message": message} if code or message else None

    @classmethod
    def _generation_item_data(cls, item: SDKGenerationItem) -> dict:
        resource_version = item.task.resource_version
        gateway_sdk = item.gateway_sdk if item.gateway_sdk_id else None
        artifacts = item.successful_artifacts
        preferred_types = {
            "python": SDKArtifactTypeEnum.WHEEL.value,
            "java": SDKArtifactTypeEnum.DISTRIBUTION_ZIP.value,
            "go": SDKArtifactTypeEnum.GO_ZIP.value,
            "javascript": SDKArtifactTypeEnum.NPM_TGZ.value,
        }
        preferred = next(
            (artifact for artifact in artifacts if artifact.artifact_type == preferred_types[item.language]),
            artifacts[0] if artifacts else None,
        )
        return {
            "id": gateway_sdk.id if gateway_sdk else None,
            "generation_task_id": item.task_id,
            "generation_item_id": item.id,
            "resource_version": {"id": resource_version.id, "version": resource_version.version},
            "version_number": resource_version.version,
            "language": item.language,
            "name": gateway_sdk.name
            if gateway_sdk
            else item.config_snapshot.get("project_name", f"bkapi-openapi-{item.task.gateway.name}"),
            "status": item.status,
            "native_status": item.native_status,
            "error": cls._error(item.error_code, item.error_message),
            "native_error": cls._error(item.native_error_code, item.native_error_message),
            "download_url": preferred.url if preferred else (gateway_sdk.url if gateway_sdk else None),
            "created_by": item.created_by,
            "created_time": item.created_time,
            "updated_time": item.updated_time,
        }

    @staticmethod
    def _legacy_sdk_data(sdk: GatewaySDK) -> dict:
        return {
            "id": sdk.id,
            "generation_task_id": None,
            "generation_item_id": None,
            "resource_version": {"id": sdk.resource_version_id, "version": sdk.resource_version.version},
            "version_number": sdk.version_number,
            "language": sdk.language,
            "name": sdk.name,
            "status": SDKGenerationItemStatusEnum.SUCCESS.value,
            "native_status": SDKNativePublicationStatusEnum.NOT_REQUIRED.value,
            "error": None,
            "native_error": None,
            "download_url": sdk.url,
            "created_by": sdk.created_by,
            "created_time": sdk.created_time,
            "updated_time": sdk.updated_time,
        }
