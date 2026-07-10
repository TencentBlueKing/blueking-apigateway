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
from apigateway.apps.support.constants import ProgrammingLanguageEnum
from apigateway.utils.factory import TypeFactory

from . import golang, java, python
from .base import BaseSDKManager
from .mixins import SDKManagerMixin

try:
    from .python_legacy import PythonLegacySDKManager
except ImportError:
    PythonLegacySDKManager = None

SDKManagerFactory = TypeFactory()

SDKManagerFactory.register(ProgrammingLanguageEnum.PYTHON.value, python.SDKManager)
SDKManagerFactory.register("golang", golang.SDKManager)
SDKManagerFactory.register(ProgrammingLanguageEnum.JAVA.value, java.SDKManager)

__all__ = [
    # constant
    # Enum
    # class
    "BaseSDKManager",
    "PythonLegacySDKManager",
    "SDKManagerFactory",
    "SDKManagerMixin",
    # functions
    # others
]
