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
import time

import jwt
import pytest

from apigateway.apis.controller.permissions import MicroGatewayInstancePermission
from apigateway.core.micro_gateway_config import MicroGatewayJWTAuth


@pytest.fixture
def mock_redis(mocker, settings):
    return mocker.MagicMock()


@pytest.fixture
def jwt_payload():
    now = int(time.time())
    return {
        "sub": "micro-gateway",
        "name": "operator1",
        "iat": now - 60,
        "exp": now + 60,
    }


@pytest.fixture
def jwt_request_meta(jwt_token):
    return {"HTTP_AUTHORIZATION": f"Bearer {jwt_token}"}


@pytest.fixture
def jwt_token(jwt_payload, micro_gateway):
    jwt_auth_info = MicroGatewayJWTAuth.from_micro_gateway_config(micro_gateway.config)
    return jwt.encode(
        jwt_payload,
        jwt_auth_info.secret_key,
        algorithm="HS256",
        headers={
            "alg": "HS256",
            "typ": "JWT",
        },
    ).decode()


class TestMicroGatewayInstancePermission:
    @pytest.fixture(autouse=True)
    def setup_request(self, mocker, jwt_token):
        self.request = mocker.MagicMock(META={})

    @pytest.fixture(autouse=True)
    def setup_view(self, mocker, micro_gateway):
        self.view = mocker.MagicMock(kwargs={"instance_id": micro_gateway.pk})

    @pytest.fixture(autouse=True)
    def setup_permission(self, mock_redis):
        self.permission = MicroGatewayInstancePermission(mock_redis)

    def test_instance_not_found(self, faker):
        self.view.kwargs["instance_id"] = faker.uuid4()
        assert not self.permission.has_permission(self.request, self.view)

    def test_no_permission_when_header_not_found(self):
        assert not self.permission.has_permission(self.request, self.view)

    def test_token_prefix_not_equal(self):
        self.request.META.update({"HTTP_AUTHORIZATION": "Token 123"})
        assert not self.permission.has_permission(self.request, self.view)

    def test_cached_result(self, mock_redis, micro_gateway, jwt_request_meta, jwt_token, jwt_payload, settings):
        self.request.META.update(jwt_request_meta)

        mock_redis.hgetall.return_value = {
            b"name": jwt_payload["name"],
            b"sub": jwt_payload["sub"],
            b"iat": f"{jwt_payload['iat']}".encode(),
            b"exp": f"{jwt_payload['exp']}".encode(),
        }
        assert self.permission.has_permission(self.request, self.view)

        mock_redis.hgetall.assert_called_once_with(
            f"{settings.REDIS_PREFIX}{self.permission.subject}:{micro_gateway.id}:{jwt_token}",
        )

    def test_decode_token_fail(self, mock_redis):
        self.request.META.update({"HTTP_AUTHORIZATION": "Bearer 123"})
        mock_redis.hgetall.return_value = None
        assert not self.permission.has_permission(self.request, self.view)

    @pytest.mark.parametrize(
        "subject, iat_offset_seconds, exp_offset_seconds",
        (
            ["macro-gateway", 0, 0],
            ["micro-gateway", 86400, 86400],
            ["micro-gateway", -86400, -86400],
        ),
    )
    def test_token_invalid(
        self,
        subject,
        iat_offset_seconds,
        exp_offset_seconds,
        jwt_payload,
        micro_gateway,
        mock_redis,
    ):
        mock_redis.hgetall.return_value = None

        jwt_payload["sub"] = subject
        jwt_payload["iat"] += iat_offset_seconds
        jwt_payload["exp"] += exp_offset_seconds

        jwt_auth_info = MicroGatewayJWTAuth.from_micro_gateway_config(micro_gateway.config)
        self.request.META.update(
            {
                "HTTP_AUTHORIZATION": "Bearer "
                + jwt.encode(
                    jwt_payload,
                    jwt_auth_info.secret_key,
                    algorithm="HS256",
                    headers={
                        "alg": "HS256",
                        "typ": "JWT",
                    },
                ).decode()
            }
        )

        assert not self.permission.has_permission(self.request, self.view)

    def test_token_valid(self, mock_redis, micro_gateway, jwt_request_meta, jwt_payload, jwt_token, mocker, settings):
        pipeline = mocker.MagicMock()
        mock_redis.pipeline.return_value.__enter__.return_value = pipeline
        mock_redis.hgetall.return_value = None
        self.request.META.update(jwt_request_meta)

        assert self.permission.has_permission(self.request, self.view)
        pipeline.hmset.assert_called_once_with(
            f"{settings.REDIS_PREFIX}{self.permission.subject}:{micro_gateway.id}:{jwt_token}",
            {
                "sub": jwt_payload["sub"],
                "name": jwt_payload["name"],
                "iat": jwt_payload["iat"],
                "exp": jwt_payload["exp"],
            },
        )
        pipeline.expire(mocker.ANY, mocker.ANY)
