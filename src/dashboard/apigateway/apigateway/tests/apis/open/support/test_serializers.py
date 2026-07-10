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
import pytest

from apigateway.apis.open.support.serializers import SDKGenerateV1SLZ


class TestSDKGenerateV1SLZ:
    def test_omitted_languages_defaults_to_python(self):
        slz = SDKGenerateV1SLZ(data={"resource_version": "1.0.0"})

        assert slz.is_valid()
        assert slz.validated_data["languages"] == ["python"]

    def test_legacy_version_is_ignored(self):
        slz = SDKGenerateV1SLZ(data={"resource_version": "1.0.0", "version": "9.9.9"})

        assert slz.is_valid()
        assert "version" not in slz.validated_data

    @pytest.mark.parametrize("language", ["python", "java", "go", "javascript", "rust"])
    def test_accepts_supported_languages(self, language):
        slz = SDKGenerateV1SLZ(data={"resource_version": "1.0.0", "languages": [language]})

        assert slz.is_valid()
