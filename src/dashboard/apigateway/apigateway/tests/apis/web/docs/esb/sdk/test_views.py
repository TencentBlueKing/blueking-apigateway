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
class TestSDKListApi:
    def test_list(self, mocker, faker, request_view):
        mocker.patch(
            "apigateway.apis.web.docs.esb.sdk.views.ESBSDKFetcher.get_sdk",
            return_value=mocker.MagicMock(
                board_label=faker.pystr(),
                sdk_name=faker.pystr(),
                sdk_description=faker.pystr(),
                sdk_version_number=faker.pystr(),
                sdk_download_url=faker.pystr(),
                sdk_install_command=faker.pystr(),
            ),
        )

        resp = request_view(
            method="GET",
            view_name="docs.esb.sdk.list",
            path_params={
                "board": "-",
            },
            data={
                "language": "python",
            },
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]


class TestSDKRetrieveApi:
    def test_retrieve(self, mock_board, mocker, faker, request_view):
        mocker.patch(
            "apigateway.apis.web.docs.esb.sdk.views.ESBSDKFetcher.get_sdk",
            return_value=None,
        )
        resp = request_view(
            method="GET",
            view_name="docs.esb.sdk.retrieve",
            path_params={
                "board": mock_board,
            },
            data={
                "language": "python",
            },
        )
        assert resp.status_code == 404

        mocker.patch(
            "apigateway.apis.web.docs.esb.sdk.views.ESBSDKFetcher.get_sdk",
            return_value=mocker.MagicMock(
                board_label=faker.pystr(),
                sdk_name=faker.pystr(),
                sdk_description=faker.pystr(),
                sdk_version_number=faker.pystr(),
                sdk_download_url=faker.pystr(),
                sdk_install_command=faker.pystr(),
            ),
        )
        resp = request_view(
            method="GET",
            view_name="docs.esb.sdk.retrieve",
            path_params={
                "board": mock_board,
            },
            data={
                "language": "python",
            },
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]


class TestSDKUsageExampleApi:
    def test_retrieve(self, mock_board, request_view):
        resp = request_view(
            method="GET",
            view_name="docs.esb.sdk.usage_example.retrieve",
            path_params={
                "board": mock_board,
            },
            data={
                "language": "python",
                "system_name": "foo",
                "component_name": "bar",
            },
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]


class TestSDKDocRetrieveApi:
    def test_retrieve(self, settings, mock_board, request_view):
        settings.ESB_BOARD_CONFIGS = {settings.ESB_DEFAULT_BOARD: settings.ESB_BOARD_CONFIGS[mock_board]}

        resp = request_view(
            method="GET",
            view_name="docs.esb.sdk.doc.retrieve",
            path_params={
                "board": "-",
            },
            data={
                "language": "python",
            },
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]
