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

from apigateway.controller.crds.release_data.base import PluginData


class TestPluginData:
    @pytest.mark.parametrize(
        "type_code, binding_scope_type, expected",
        [
            (
                "bk-rate-limit",
                "stage",
                "bk-stage-rate-limit",
            ),
            (
                "bk-rate-limit",
                "resource",
                "bk-resource-rate-limit",
            ),
            (
                "foo",
                "stage",
                "foo",
            ),
        ],
    )
    def test_name(self, type_code, binding_scope_type, expected):
        p = PluginData(
            type_code=type_code,
            config={},
            binding_scope_type=binding_scope_type,
        )

        assert p.name == expected
