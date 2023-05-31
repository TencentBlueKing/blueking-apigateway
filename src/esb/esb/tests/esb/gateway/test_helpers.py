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
import jwt
import pytest

from common.errors import APIError
from esb.gateway.helpers import JWTClient, is_from_gateway_with_jwt


@pytest.mark.parametrize(
    "meta, expected",
    [
        ({}, False),
        ({"HTTP_X_BKAPI_JWT": "green"}, True),
    ],
)
def test_is_from_gateway_with_jwt(mocker, meta, expected):
    request = mocker.MagicMock(META=meta)
    result = is_from_gateway_with_jwt(request)
    assert result == expected


class TestJWTClient:
    @pytest.fixture
    def mock_request(self, mocker):
        request = mocker.MagicMock(META={})
        return request

    def test_init(self, mocker, mock_request, faker):
        bkapi_jwt = faker.pystr()
        bkapi_request_id = faker.pystr()
        mock_request.META = {
            "HTTP_X_BKAPI_JWT": bkapi_jwt,
            "HTTP_X_BKAPI_REQUEST_ID": bkapi_request_id,
        }

        mock_decode_jwt_content = mocker.patch.object(JWTClient, "decode_jwt_content")
        client = JWTClient(mock_request)
        assert client._jwt_payload == bkapi_jwt
        assert client._apigw_request_id == bkapi_request_id
        assert client.payload == {}
        assert client.enabled is True
        assert client.app is None
        assert client.user is None
        mock_decode_jwt_content.assert_called_once_with()

    def test_decode_jwt_content(self, mocker, faker, mock_request):
        mock_request.META = {}
        client = JWTClient(mock_request)

        # jwt payload is empty
        mock_get_public_key = mocker.patch("esb.gateway.helpers.JWTKey.get_public_key")
        client._jwt_payload = ""
        client.decode_jwt_content()
        mock_get_public_key.assert_not_called()

        # set jwt payload not empty
        jwt_payload = faker.color()
        jwt_public_key = faker.color()
        client._jwt_payload = jwt_payload

        # public key is empty
        mock_get_public_key = mocker.patch("esb.gateway.helpers.JWTKey.get_public_key", return_value="")
        with pytest.raises(APIError):
            client.decode_jwt_content()

        # decode error
        mock_get_public_key = mocker.patch("esb.gateway.helpers.JWTKey.get_public_key", return_value=jwt_public_key)
        mock_decode = mocker.patch("esb.gateway.helpers.jwt.decode", side_effect=jwt.DecodeError)
        with pytest.raises(APIError):
            client.decode_jwt_content()
        mock_get_public_key.assert_called_once_with()
        mock_decode.assert_called_once_with(jwt_payload, jwt_public_key, algorithms=["RS512"])

        # decode ok
        mock_get_public_key.reset_mock()
        mock_decode = mocker.patch(
            "esb.gateway.helpers.jwt.decode",
            return_value={"app": {"app_code": "my-color", "user": {"username": "admin"}}},
        )
        client.decode_jwt_content()
        mock_get_public_key.assert_called_once_with()
        mock_decode.assert_called_once_with(jwt_payload, jwt_public_key, algorithms=["RS512"])
        assert client.payload == {"app": {"app_code": "my-color", "user": {"username": "admin"}}}
