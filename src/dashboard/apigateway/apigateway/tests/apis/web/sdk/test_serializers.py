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

from apigateway.apis.web.sdk.serializers import GatewaySDKGenerateInputSLZ, GatewaySDKListOutputSLZ
from apigateway.tests.utils.testing import dummy_time


class TestGatewaySDKGenerateInputSLZ:
    @pytest.mark.parametrize(
        "languages, is_valid",
        [
            (["python"], True),
            (["python", "java", "go", "javascript"], True),
            (["rust"], False),
            ([], False),
            (["unknown"], False),
        ],
    )
    def test_validate_languages(self, fake_gateway, languages, is_valid):
        slz = GatewaySDKGenerateInputSLZ(
            data={
                "resource_version_id": 1,
                "languages": languages,
            },
            context={"gateway": fake_gateway},
        )

        assert slz.is_valid() is is_valid
        if not is_valid:
            assert "languages" in slz.errors

    def test_languages_are_required(self, fake_gateway):
        slz = GatewaySDKGenerateInputSLZ(data={"resource_version_id": 1}, context={"gateway": fake_gateway})

        assert not slz.is_valid()
        assert "languages" in slz.errors

    def test_legacy_golang_is_normalized(self, fake_gateway):
        slz = GatewaySDKGenerateInputSLZ(
            data={"resource_version_id": 1, "languages": ["golang"]},
            context={"gateway": fake_gateway},
        )

        assert slz.is_valid()
        assert slz.validated_data["languages"] == ["go"]


class TestSDKListOutputSLZ:
    def test_created_by_help_text(self):
        slz = GatewaySDKListOutputSLZ()
        assert slz.fields["created_by"].help_text == "SDK 创建者"

    def test_to_representation(self):
        row = {
            "id": None,
            "generation_task_id": 17,
            "generation_item_id": 38,
            "resource_version": {"id": 12, "version": "1.2.3"},
            "version_number": "1.2.3",
            "language": "python",
            "name": "bkapi-openapi-demo",
            "status": "failed",
            "native_status": "not_required",
            "error": {"code": "build_failed", "message": "wheel build failed"},
            "native_error": None,
            "download_url": None,
            "created_by": "test",
            "created_time": dummy_time.time,
            "updated_time": dummy_time.time,
        }

        assert GatewaySDKListOutputSLZ(instance=row).data == {
            **row,
            "created_time": dummy_time.str,
            "updated_time": dummy_time.str,
        }
