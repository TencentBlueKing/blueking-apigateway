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
from apigateway.biz.esb.sdk.models import DocTemplates, DummySDKDocContext, SDKDocContext


class TestSDKDocContext:
    def test(self, mock_board):
        ctx = SDKDocContext(mock_board, "cc", "test")

        assert ctx.as_dict() == {
            "board": mock_board,
            "system_name": "cc",
            "component_name": "test",
            "package_prefix": "blueking.component.open",
        }


class TestDummySDKDocContext:
    def test(self, settings, mock_board):
        settings.ESB_BOARD_CONFIGS = {settings.ESB_DEFAULT_BOARD: settings.ESB_BOARD_CONFIGS[mock_board]}

        ctx = DummySDKDocContext()

        assert ctx.as_dict() == {
            "board": settings.ESB_DEFAULT_BOARD,
            "system_name": "cc",
            "component_name": "search_business",
            "package_prefix": "blueking.component.open",
        }


class TestDocTemplates:
    def test(self, mock_board):
        doc_templates = DocTemplates(mock_board, "en", "python")
        assert doc_templates.templates
