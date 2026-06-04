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
import pytest

from apigateway.apis.open.support.serializers import SDKGenerateV1SLZ


class TestSDKGenerateV1SLZ:
    @pytest.mark.parametrize(
        "version, is_valid",
        [
            ("", True),
            ("1.2.3", True),
            ("1.2.3-beta.1+build.1", True),
            ("v1.2.3", False),
            ("1.2", False),
            ("1.0.0');__import__('os').system('touch /tmp/sdk-version-pwned')#", False),
        ],
    )
    def test_validate_version(self, version, is_valid):
        slz = SDKGenerateV1SLZ(
            data={
                "resource_version": "1.0.0",
                "languages": ["python"],
                "version": version,
            },
        )

        assert slz.is_valid() is is_valid
        if not is_valid:
            assert "version" in slz.errors
