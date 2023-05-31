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

from unittest import mock

import pytest
from ddf import G

from apigateway.apps.docs.esb.doc.helpers import ComponentDocFactory
from apigateway.apps.esb.bkcore.models import ComponentDoc, ComponentSystem, ESBChannel

pytestmark = pytest.mark.django_db


class TestComponentDocFactory:
    def test_get_doc(self, mock_board, mocker):
        mocker.patch(
            "apigateway.apps.docs.esb.doc.helpers.ComponentDoc.doc_configs",
            new_callable=mock.PropertyMock(
                return_value={
                    "doc_type": "markdown",
                    "api_path": "/test",
                    "suggest_method": "GET",
                }
            ),
        )
        s = G(ComponentSystem, board=mock_board, name="system-doc-test")
        c = G(
            ESBChannel,
            board=mock_board,
            system=s,
            name="component-doc-test",
            is_active=True,
        )
        cd = G(
            ComponentDoc,
            board=mock_board,
            component=c,
            content="test",
        )
        mocker.patch(
            "apigateway.apps.docs.esb.doc.helpers.ComponentDoc.objects.get_api_doc",
            return_value=cd,
        )

        helper = ComponentDocFactory(mock_board, s.name, c.name)

        assert helper.api_doc is not None
        assert helper.component_config is not None

        doc = helper.get_doc()

        assert doc["type"] == "markdown"
        assert doc["content"].endswith("test")
