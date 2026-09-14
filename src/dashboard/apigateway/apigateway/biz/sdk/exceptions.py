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
class SDKException(Exception):
    """
    SDK 异常
    """


class GenerateError(SDKException):
    """生成错误"""


class SDKGenerationError(GenerateError):
    def __init__(self, code: str, message: str, *, retryable: bool = False):
        self.code = code
        self.message = message
        self.retryable = retryable
        super().__init__(message)


class SDKArtifactConflict(SDKGenerationError):
    def __init__(self, message: str):
        super().__init__("artifact_conflict", message)


class LegacySDKVersionConflict(SDKGenerationError, ValueError):
    def __init__(self):
        super().__init__(
            "legacy_sdk_version_conflict",
            "This SDK version belongs to another resource version or generation item; "
            "create a new resource version before generating again.",
        )


class SDKConfigurationError(SDKException):
    """SDK worker or policy configuration is invalid."""


class SDKRepoConfigError(SDKConfigurationError):
    """SDK 配置错误"""
