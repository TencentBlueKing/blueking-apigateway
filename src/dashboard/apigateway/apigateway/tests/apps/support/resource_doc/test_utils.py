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

from apigateway.apps.support.resource_doc import utils


@pytest.mark.parametrize(
    "api_name, language",
    [
        (
            "bk-user",
            "zh",
        ),
        (
            "bk-user",
            "en",
        ),
    ],
)
def test_get_resource_doc_tmpl(api_name, language):
    result = utils.get_resource_doc_tmpl(api_name, language)
    assert result != ""


@pytest.mark.parametrize(
    "mock_api, mock_resource, mock_doc_link, resource_id, expected",
    [
        (
            {
                "is_active_and_public": False,
            },
            {},
            {},
            1,
            "",
        ),
        (
            {
                "is_active_and_public": True,
            },
            {},
            {},
            1,
            "",
        ),
        (
            {
                "is_active_and_public": True,
            },
            {
                "is_public": False,
            },
            {},
            1,
            "",
        ),
        (
            {
                "is_active_and_public": True,
            },
            {
                "is_public": True,
            },
            {
                1: "http://demo.example.com",
            },
            1,
            "http://demo.example.com",
        ),
    ],
)
def test_get_resource_doc_link(mocker, mock_api, mock_resource, mock_doc_link, resource_id, expected):
    api = mocker.MagicMock(**mock_api)
    mocker.patch(
        "apigateway.apps.support.resource_doc.utils.ReleasedResource.objects.get_latest_released_resource",
        return_value=mock_resource,
    )
    mocker.patch(
        "apigateway.apps.support.resource_doc.utils.ReleasedResource.objects.get_latest_doc_link",
        return_value=mock_doc_link,
    )

    result = utils.get_resource_doc_link(api, resource_id)
    assert result == expected
