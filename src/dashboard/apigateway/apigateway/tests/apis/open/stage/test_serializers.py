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
import pytest

from apigateway.apis.open.stage import serializers


class TestStageWithResourceVersionV1SLZ:
    @pytest.mark.parametrize(
        "stage_name, stage_release, expected",
        [
            (
                "prod",
                {},
                [
                    {
                        "name": "prod",
                        "resource_version": None,
                        "released": False,
                    }
                ],
            ),
            (
                "test",
                {
                    "resource_version": {
                        "title": "test",
                        "version": "1.0.1",
                    },
                },
                [
                    {
                        "name": "test",
                        "resource_version": {
                            "version": "1.0.1",
                        },
                        "released": True,
                    }
                ],
            ),
        ],
    )
    def test_to_representation(self, mocker, fake_stage, stage_name, stage_release, expected):
        mocker.patch(
            "apigateway.biz.stage.StageHandler.save_header_rewrite_plugin",
            return_value=None,
        )

        fake_stage.name = stage_name
        slz = serializers.StageWithResourceVersionV1SLZ(
            [fake_stage],
            many=True,
            context={
                "stage_release": {
                    fake_stage.id: stage_release,
                }
            },
        )
        assert slz.data == expected
