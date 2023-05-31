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
class SDKException(Exception):
    """
    SDK 异常
    """


class GenerateError(SDKException):
    """生成错误"""


class DistributeError(SDKException):
    """发布错误"""


class PackError(SDKException):
    """打包错误"""


class ResourcesIsEmpty(Exception):
    """网关下无资源"""


class TooManySDKVersion(Exception):
    """SDK 版本过多"""

    def __init__(self, max_count):
        self.max_count = max_count
