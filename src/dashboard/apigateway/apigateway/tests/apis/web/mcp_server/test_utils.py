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
from ddf import G

from apigateway.apis.web.mcp_server.utils import get_valid_resource_names
from apigateway.common.error_codes import APIError
from apigateway.core.models import Gateway, Release, Stage


class TestGetValidResourceNames:
    def test_get_valid_resource_names(self, fake_gateway, fake_stage, fake_resource_version):
        G(Release, gateway=fake_gateway, stage=fake_stage, resource_version=fake_resource_version)

        expected_resource_names = {resource["name"] for resource in fake_resource_version.data}

        resource_names = get_valid_resource_names(fake_gateway.id, fake_stage.id)
        assert resource_names == expected_resource_names

    def test_get_valid_resource_names_no_release(
        self,
    ):
        fake_gateway = G(Gateway, id=1)
        fake_stage = G(Stage, id=1)

        with pytest.raises(APIError):
            get_valid_resource_names(fake_gateway.id, fake_stage.id)
