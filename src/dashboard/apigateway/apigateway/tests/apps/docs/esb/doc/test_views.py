# -*- coding: utf-8 -*-
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

from apigateway.apps.docs.esb.doc import views
from apigateway.tests.utils.testing import get_response_json

pytestmark = pytest.mark.django_db


class TestDocViewSet:
    @pytest.mark.parametrize(
        "mocked_doc, board, system_name, component_name, expected",
        [
            (
                {
                    "type": "rst",
                    "content": "test",
                },
                "open",
                "system-test",
                "component_test",
                {
                    "type": "rst",
                    "content": "test",
                    "updated_time": None,
                },
            ),
        ],
    )
    def test_retrieve(
        self,
        mocker,
        request_factory,
        mocked_doc,
        board,
        system_name,
        component_name,
        expected,
    ):
        mocked_get_doc = mocker.patch(
            "apigateway.apps.docs.esb.doc.views.ComponentDocFactory.get_doc",
            return_value=mocked_doc,
        )

        request = request_factory.get("")
        view = views.DocViewSet.as_view({"get": "retrieve"})
        response = view(request, board, system_name, component_name)
        result = get_response_json(response)

        assert result["code"] == 0
        assert result["data"] == expected

        mocked_get_doc.assert_called_once_with()
