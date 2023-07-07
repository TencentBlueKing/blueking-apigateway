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

from apigateway.apps.docs.gateway.sdk import views
from apigateway.apps.docs.gateway.sdk.helpers import DummyResourceForSDK
from apigateway.tests.utils.testing import get_response_json


class TestSDKViewSet:
    @pytest.mark.parametrize(
        "mocked_sdks, params, expected",
        [
            (
                [
                    {
                        "api_id": 1,
                        "api_name": "test",
                        "api_description": "desc",
                        "user_auth_type": "open",
                        "language": "python",
                        "sdk_name": "bkapigw-test",
                        "sdk_version_number": "20201118161729",
                        "sdk_download_url": "http://bking.com/bkapigw-test-20201118161729.tar.gz",
                        "sdk_install_command": "pip install bkapigw-test",
                        "resource_version_name": "test",
                        "resource_version_title": "title",
                        "resource_version_display": "test(title)",
                        "released_stages": [
                            {
                                "id": 1,
                                "name": "prod",
                            },
                        ],
                    },
                ],
                {
                    "language": "python",
                },
                [
                    {
                        "api_id": 1,
                        "api_name": "test",
                        "api_description": "desc",
                        "user_auth_type": "open",
                        "user_auth_type_display": "open",
                        "language": "python",
                        "sdk_name": "bkapigw-test",
                        "sdk_version_number": "20201118161729",
                        "sdk_download_url": "http://bking.com/bkapigw-test-20201118161729.tar.gz",
                        "sdk_install_command": "pip install bkapigw-test",
                        "resource_version_name": "test",
                        "resource_version_title": "title",
                        "resource_version_display": "test(title)",
                        "released_stages": [
                            {
                                "id": 1,
                                "name": "prod",
                            },
                        ],
                    },
                ],
            ),
        ],
    )
    def test_list(self, mocker, request_factory, mocked_sdks, params, expected):
        mocked_get_latest_sdks = mocker.patch(
            "apigateway.apps.docs.gateway.sdk.views.support_helper.get_latest_sdks",
            return_value=mocked_sdks,
        )

        request = request_factory.get("", data=params)
        view = views.SDKViewSet.as_view({"get": "list"})
        response = view(request)
        result = get_response_json(response)

        assert result["code"] == 0
        assert result["data"] == expected

        mocked_get_latest_sdks.assert_called_once_with(
            language=params["language"],
        )

    @pytest.mark.parametrize(
        "mocked_api, mocked_sdks, api_name, params, expected",
        [
            (
                {
                    "id": 1,
                },
                [
                    {
                        "stage_name": "prod",
                        "resource_version_name": "20201118162329",
                        "resource_version_title": "v1",
                        "resource_version_display": "20201118162329(v1)",
                        "language": "python",
                        "sdk_name": "bkapigw-test",
                        "sdk_version_number": "20201118161729",
                        "sdk_download_url": "http://bking.com/bkapigw-test-20201118161729.tar.gz",
                        "sdk_install_command": "pip install bkapigw-test",
                    }
                ],
                "api-test",
                {
                    "language": "python",
                },
                [
                    {
                        "stage_name": "prod",
                        "resource_version_name": "20201118162329",
                        "resource_version_title": "v1",
                        "resource_version_display": "20201118162329(v1)",
                        "language": "python",
                        "sdk_name": "bkapigw-test",
                        "sdk_version_number": "20201118161729",
                        "sdk_download_url": "http://bking.com/bkapigw-test-20201118161729.tar.gz",
                        "sdk_install_command": "pip install bkapigw-test",
                    }
                ],
            )
        ],
    )
    def test_list_api_sdks(
        self,
        mocker,
        request_factory,
        mocked_api,
        mocked_sdks,
        api_name,
        params,
        expected,
    ):
        mocked_get_gateway_by_name = mocker.patch(
            "apigateway.apps.docs.gateway.sdk.views.support_helper.get_gateway_by_name",
            return_value=mocked_api,
        )

        mocked_get_stage_sdks = mocker.patch(
            "apigateway.apps.docs.gateway.sdk.views.support_helper.get_stage_sdks",
            return_value=mocked_sdks,
        )

        request = request_factory.get("", data=params)
        view = views.SDKViewSet.as_view({"get": "list_api_sdks"})
        response = view(request, api_name)
        result = get_response_json(response)

        assert result["code"] == 0
        assert result["data"] == expected

        mocked_get_gateway_by_name.assert_called_once_with(api_name)
        mocked_get_stage_sdks.assert_called_once_with(mocked_api["id"], language=params["language"])

    @pytest.mark.parametrize(
        "mocked_sdk, mocked_resource_for_sdk, mocked_rendered_string, params, expected",
        [
            (
                {
                    "api_id": 1,
                    "api_name": "api-test",
                    "sdk_created_time": "",
                },
                DummyResourceForSDK(),
                "test",
                {
                    "language": "python",
                },
                {
                    "content": "test",
                },
            )
        ],
    )
    def test_get_usage_example(
        self,
        mocker,
        request_factory,
        mocked_sdk,
        mocked_resource_for_sdk,
        mocked_rendered_string,
        params,
        expected,
    ):
        mocked_get_latest_sdks = mocker.patch(
            "apigateway.apps.docs.gateway.sdk.views.support_helper.get_latest_sdks",
            return_value=[mocked_sdk],
        )

        mocked_released_resource_for_sdk = mocker.patch(
            "apigateway.apps.docs.gateway.sdk.views.ReleasedResourceForSDK",
            return_value=mocked_resource_for_sdk,
        )

        mocked_render_string = mocker.patch(
            "apigateway.apps.docs.gateway.sdk.views.render_to_string",
            return_value=mocked_rendered_string,
        )

        api_name = "api-test"
        stage_name = "prod"
        resource_name = "resource_test"

        request = request_factory.get("", data=params)
        view = views.SDKViewSet.as_view({"get": "get_usage_example"})
        response = view(request, api_name, stage_name, resource_name)
        result = get_response_json(response)

        assert result["code"] == 0
        assert result["data"] == expected

        mocked_get_latest_sdks.assert_called_once_with(
            language=params["language"],
            gateway_name=api_name,
        )
        mocked_released_resource_for_sdk.assert_called_once_with(
            api_id=mocked_sdk["api_id"],
            api_name=mocked_sdk["api_name"],
            stage_name=stage_name,
            resource_name=resource_name,
            sdk_created_time_str=mocked_sdk["sdk_created_time"],
        )
        mocked_render_string.assert_called_once()

    @pytest.mark.parametrize(
        "mocked_rendered_string, params, expected",
        [
            (
                "test",
                {
                    "language": "python",
                },
                {
                    "content": "test",
                },
            ),
        ],
    )
    def test_get_doc(
        self,
        mocker,
        request_factory,
        mocked_rendered_string,
        params,
        expected,
    ):
        mocked_render_string = mocker.patch(
            "apigateway.apps.docs.gateway.sdk.views.render_to_string",
            return_value=mocked_rendered_string,
        )

        request = request_factory.get("", data=params)
        view = views.SDKViewSet.as_view({"get": "get_doc"})
        response = view(request)
        result = get_response_json(response)

        assert result["code"] == 0
        assert result["data"] == expected

        mocked_render_string.assert_called_once()
