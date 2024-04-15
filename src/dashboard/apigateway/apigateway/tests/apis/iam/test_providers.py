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
from iam.collection import FancyDict
from iam.resource.provider import ListResult
from iam.resource.utils import Page

from apigateway.apis.iam.providers import (
    GatewayProvider,
    fetch_gateway_id_in_filter,
)
from apigateway.iam.models import IAMGradeManager


class TestFetchGatewayIdInFilter:
    @pytest.mark.parametrize(
        "filter_obj, expected_gateway_id, expected_result",
        [
            (
                {},
                None,
                {"results": [], "count": 0},
            ),
            (
                {"parent": {"type": "foo", "id": "1"}},
                None,
                {"results": [], "count": 0},
            ),
            (
                {"parent": {"type": "gateway", "id": "2"}},
                2,
                {"results": [1], "count": 1},
            ),
        ],
    )
    def test(self, mocker, filter_obj, expected_gateway_id, expected_result):
        mock_func = mocker.MagicMock(return_value=ListResult(results=[1], count=1))
        mock_self = FancyDict()

        result = fetch_gateway_id_in_filter(mock_func)(mock_self, filter_obj)
        assert result.to_dict() == expected_result
        assert getattr(mock_self, "gateway_id_in_filter", None) == expected_gateway_id


class TestGatewayProvider:
    def test_list_instance(self, fake_gateway):
        G(IAMGradeManager, gateway=fake_gateway)

        result = GatewayProvider().list_instance(None, Page(limit=10, offset=0))
        assert result.count > 0
        assert str(fake_gateway.id) in [r["id"] for r in result.results]

    def test_fetch_instance_info(self, fake_gateway, mocker):
        provider = GatewayProvider()
        mocker.patch.object(provider, "_fetch_gateway_approvers", return_value={})

        result = provider.fetch_instance_info(FancyDict(ids=[str(fake_gateway.id)]))
        assert result.count == 1
        assert result.results[0]["id"] == str(fake_gateway.id)

    def test_search_instance(self, fake_gateway, unique_id):
        fake_gateway.name = unique_id
        fake_gateway.save()

        G(IAMGradeManager, gateway=fake_gateway)

        result = GatewayProvider().search_instance(FancyDict(keyword=unique_id), Page(limit=10, offset=0))
        assert result.count == 1
        assert result.results[0]["id"] == str(fake_gateway.id)
