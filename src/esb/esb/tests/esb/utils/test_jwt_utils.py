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
import textwrap
import time

import jwt
import pytest

from esb.utils import jwt_utils


class TestJWTKey:
    def test_generate(self):
        private_key, public_key = jwt_utils.JWTKey().generate()
        assert b"BEGIN RSA PRIVATE KEY" in private_key
        assert b"BEGIN PUBLIC KEY" in public_key


class TestJWTClient:
    @pytest.fixture
    def mock_private_key(self):
        return textwrap.dedent(
            """\
            -----BEGIN RSA PRIVATE KEY-----
            MIIEowIBAAKCAQEA0binE4XNouDDufAQnl6KMYC4vUIhnmzyt7jEq+Wv5v5EzSfr
            jnQEN6OudS0wHJytPHNZpoRCMnT9bgcCCGdEpq4EXykOoKb+WRbE1b6rShl8RT36
            XdcSyVfnxAJMXLO/+rotK3TA4YVYK73Y2myaIlDyyf+WsS5dNDPGHF0cUSjQ5Sh7
            6VGXKsDBqx+8nNWIrqrRUhCBYVwUzCJTtgay0va6tWf96aPpirf7C4/NsthbNwbm
            t4FG7TaAXhma2Ma4W7SVBsQx0HHbwKXYDOoyzQqFRJI7gV2K1eVY+GjmPt0Ytz/e
            rD8uDh5gXh+sTWt1OmY9COnNMOrszBKGrSY4AwIDAQABAoIBAQCb+S3hOiEu4uUO
            U3m4nu0+VdKPhzCDp9l4RCWZBrElJbQ7tFXfU2+ThduI8DuY+/lnPQ7O5gxphFK7
            UuDzKQKIyGEd+OYVGz2NOn7XzP+Nk5i10pty0TL6pbMMNv1d8J12NqLDcAjHcSmb
            Fo3CHQUhQnzfOIR1b9sHqP3NOH6H6G95fvIVs+Lm0StkA7LwG3xFE25eT0JpdnTn
            bqQvy66kDWc8Q61tKItHtuiLJ/xB/QE+EMhiCwBclWojlhyo4pZbBFo91eXmz+0A
            bAqxmzJWrV12RzsQH7aQLPnYiMrVkjwk2RFmggHrQVxulHQHMAR0iD02fiTlbAxD
            CdcVZzkRAoGBAOIVTZNv1736SlytSWmkokv4IP04nRG4sXvVDnp21lUwOEdDPllk
            JJiUHeSypNeRSRS6lHNr+frNnfKzGGQlZnA1/9CSWkYmgIW7qMszGdw8UilVi5UH
            bum9j9qQ30DhUDdYlNd7eX+vbhP7WGTO5ieuo3hyA6uZDA6bUI3iJAFJAoGBAO15
            FJiFdjXuDCE95gCYH60A0+txGOIw36zC74FKUwtJfKjlBPUSJGx6fX4gURg1NPuP
            +DUFHrvAb9GBjXqgyX5g/WTo+JK2lfasbL51I6T3Ydk6YFtiC8vy4fBZb/HbeQHg
            I+WYFkuzH1Um9LVDTnyumGjsXfGMRMYWYV8t2rrrAoGAebyQ1hf+KozQZ9DjW+BL
            h+6nDNLkOLujzhMuRaEhziM12qGJvCahUgtHgXL0MiNIH8JL107H/1WifCIVuy8s
            VrWs9sknlOh8ggZHYIs2nJFaiGlIzMmA3pm1ETK7FDt+rx6intkc1jVHZ7kKotWJ
            tsphuaRi945koKTfHlcrngkCgYBPWsKzJQYXh3CuOwz87djH6xrl9mkmTMax6II4
            ZinR/8CUf9NkQafCSDxfRVVUDZOi7L04mnlmrCuxiuVIMSqj/K0wZ1mJTVJXl87O
            5j3/BlvAR22jm+PtR0CRHJH39Cs/oTLdqjDpIvY5ckcbu14i9AUiKrpJ2WGyABCR
            ybTp+QKBgBdKFodNrPa6YONs29Y2ISEosodyLARhtViEh3PJ0jrO243Oo4nEcogG
            p+bZEKZn2VZtA99KRhc/cyd+AMeVCiuDI5vwTOb+4PnPw9xkFZRIbOSJqCpNG3c5
            P5Q+NEr1LhskfwMXm4DqDP3n8F0QkG380Bj2z7WBYfkkC3lqzRdC
            -----END RSA PRIVATE KEY-----"""
        )

    @pytest.fixture
    def mock_public_key(self):
        return textwrap.dedent(
            """\
            -----BEGIN PUBLIC KEY-----
            MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA0binE4XNouDDufAQnl6K
            MYC4vUIhnmzyt7jEq+Wv5v5EzSfrjnQEN6OudS0wHJytPHNZpoRCMnT9bgcCCGdE
            pq4EXykOoKb+WRbE1b6rShl8RT36XdcSyVfnxAJMXLO/+rotK3TA4YVYK73Y2mya
            IlDyyf+WsS5dNDPGHF0cUSjQ5Sh76VGXKsDBqx+8nNWIrqrRUhCBYVwUzCJTtgay
            0va6tWf96aPpirf7C4/NsthbNwbmt4FG7TaAXhma2Ma4W7SVBsQx0HHbwKXYDOoy
            zQqFRJI7gV2K1eVY+GjmPt0Ytz/erD8uDh5gXh+sTWt1OmY9COnNMOrszBKGrSY4
            AwIDAQAB
            -----END PUBLIC KEY-----"""
        )

    def test_encode(self, mock_private_key, mock_public_key, mocker):
        now = int(time.time())

        mocker.patch(
            "esb.utils.jwt_utils.JWTKey.get_private_key",
            return_value=mock_private_key,
        )
        mocker.patch("esb.utils.jwt_utils.time.time", return_value=now)
        mock_app = mocker.MagicMock(**{"as_json.return_value": {"bk_app_code": "test"}})
        mock_user = mocker.MagicMock(**{"as_json.return_value": {"bk_username": "admin"}})

        client = jwt_utils.JWTClient(mock_app, mock_user)
        result = client.encode()
        assert result != ""

        payload = jwt.decode(result, mock_public_key, algorithms="RS512")
        assert payload == {
            "app": {
                "bk_app_code": "test",
            },
            "user": {
                "bk_username": "admin",
            },
            "iss": "APIGW",
            "nbf": now - 300,
            "exp": now + 900,
        }
