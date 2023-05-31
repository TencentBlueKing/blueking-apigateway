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
from django.conf import settings
from tencent_apigateway_common.pypi.pip import PipHelper
from tencent_apigateway_common.pypi.registry import SimplePypiRegistry

from apigateway.apps.docs.esb.sdk_helpers import PythonSDKManager


class SimplePythonSDKManager(PythonSDKManager):
    def __init__(self, board: str, index_url: str = ""):
        super().__init__(board)

        self.index_url = index_url or getattr(settings, "PYPI_MIRRORS_REPOSITORY", "")
        self.sdk = self._search_sdk()
        # TODO: 此处重置了父类中 has_sdk 的含义，导致排查问题困难，
        # 此部分考虑需要有SDK 而实际无 sdk 时直接触发异常，或者分两个配置
        self.has_sdk = self.sdk is not None

    def _search_sdk(self):
        if not self.index_url:
            return None

        registry = SimplePypiRegistry(self.index_url)
        return registry.search(self.sdk_name)

    def get_sdk_version_number(self):
        if not self.sdk or not self.sdk.version:
            return ""
        return self.sdk.version

    def get_sdk_download_url(self):
        if not self.sdk:
            return ""
        return self.sdk.url

    def get_sdk_install_command(self):
        helper = PipHelper(extra_index_url=self.index_url)
        return helper.install_command(
            self.sdk_name,
            self.get_sdk_version_number(),
        )
