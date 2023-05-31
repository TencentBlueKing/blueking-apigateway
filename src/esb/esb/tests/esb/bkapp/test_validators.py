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

from common.base_utils import FancyDict
from common.base_validators import ValidationError
from esb.bkapp.validators import (
    AccessTokenValidator,
    AppAuthValidator,
    AppSecretValidator,
    SelfAppCodeAppSecret,
    SignatureValidator,
)


class TestAppAuthValidator:
    @pytest.fixture
    def patched_request(self, fake_request):
        fake_request.apigw = FancyDict(enabled=False)
        fake_request.g = FancyDict(authorization={})
        return fake_request

    def test_validate_with_apigw(self, fake_request):
        fake_request.apigw = FancyDict(enabled=True)
        validator = AppAuthValidator()

        # ok
        fake_request.g = FancyDict(is_app_verified=True)
        assert validator.validate(fake_request) is None

        # error
        fake_request.g = FancyDict(is_app_verified=False)
        with pytest.raises(ValidationError):
            validator.validate(fake_request)

    def test_validate_with_access_token(self, patched_request, mocker, faker):
        validator = AppAuthValidator()
        app_code = faker.pystr()

        # access_token validate ok
        mock_validate = mocker.patch("esb.bkapp.validators.AccessTokenValidator.validate")
        mocker.patch("esb.bkapp.validators.AccessTokenValidator.get_bk_app_code", return_value=app_code)
        mock_set_request_current_app = mocker.patch.object(validator, "_set_request_current_app")

        patched_request.g = FancyDict(authorization={"access_token": faker.pystr()})
        validator.validate(patched_request)
        mock_validate.assert_called_once_with(patched_request)
        mock_set_request_current_app.assert_called_once_with(patched_request, app_code)

        # access_token validate error
        patched_request.g = FancyDict(authorization={"access_token": faker.pystr()})
        mock_validate = mocker.patch("esb.bkapp.validators.AccessTokenValidator.validate", side_effect=ValidationError)
        with pytest.raises(ValidationError):
            validator.validate(patched_request)
        mock_validate.assert_called_once_with(patched_request)

    def test_validate_with_app_secret(self, patched_request, mocker):
        validator = AppAuthValidator(verified_type="app_secret")

        # validate ok
        mock_validate = mocker.patch("esb.bkapp.validators.AppSecretValidator.validate")
        assert validator.validate(patched_request) is None
        mock_validate.assert_called_once_with(patched_request)

        # validate error
        mock_validate = mocker.patch("esb.bkapp.validators.AppSecretValidator.validate", side_effect=ValidationError)
        with pytest.raises(ValidationError):
            validator.validate(patched_request)
        mock_validate.assert_called_once_with(patched_request)

    def test_validate_with_signature(self, patched_request, mocker):
        validator = AppAuthValidator(verified_type="signature")

        # validate ok
        mock_validate = mocker.patch("esb.bkapp.validators.SignatureValidator.validate")
        assert validator.validate(patched_request) is None
        mock_validate.assert_called_once_with(patched_request)

        # validate error
        mock_validate = mocker.patch("esb.bkapp.validators.SignatureValidator.validate", side_effect=ValidationError)
        with pytest.raises(ValidationError):
            validator.validate(patched_request)
        mock_validate.assert_called_once_with(patched_request)

    def test_validate_with_signature_or_app_secret(self, patched_request, mocker, faker):
        validator = AppAuthValidator(verified_type="signature_or_app_secret")
        patched_request.g = FancyDict(authorization={})

        # validate with signature
        patched_request.GET = {"bk_signature": faker.pystr(min_chars=1)}
        mock_validate = mocker.patch("esb.bkapp.validators.SignatureValidator.validate")
        assert validator.validate(patched_request) is None
        mock_validate.assert_called_once_with(patched_request)

        # validate with app_secret
        patched_request.GET = {}
        patched_request.g = FancyDict(authorization={"bk_app_secret": faker.pystr(min_chars=1)})
        mock_validate = mocker.patch("esb.bkapp.validators.AppSecretValidator.validate")
        assert validator.validate(patched_request) is None
        mock_validate.assert_called_once_with(patched_request)

        # signature and app_secret is empty
        patched_request.GET = {}
        patched_request.g = FancyDict(authorization={})
        with pytest.raises(ValidationError):
            validator.validate(patched_request)

    def test_validate_error(self, patched_request):
        validator = AppAuthValidator(verified_type="unknown")
        patched_request.g = FancyDict(authorization={})

        with pytest.raises(ValidationError):
            validator.validate(patched_request)

    def test_set_request_current_app(self, patched_request, faker):
        validator = AppAuthValidator()
        app_code = faker.pystr()

        validator._set_request_current_app(patched_request, app_code)
        assert patched_request.g.app_code == app_code


class TestAccessTokenValidator:
    @pytest.fixture
    def patched_request(self, fake_request):
        fake_request.apigw = FancyDict(enabled=False)
        fake_request.g = FancyDict(authorization={"access_token": "test"})
        return fake_request

    def test_validate(self, mocker, patched_request):
        mocker.patch(
            "esb.bkapp.validators.AccessTokenValidator._verify_access_token",
            return_value=("app-test", "admin"),
        )
        validator = AccessTokenValidator()
        validator.validate(patched_request)

        assert validator._validated_data == {
            "bk_app_code": "app-test",
            "bk_username": "admin",
        }

    def test_validated_data(self):
        validator = AccessTokenValidator()
        with pytest.raises(ValidationError):
            validator.validated_data

        validator._validated_data = {"a": "b"}
        assert validator.validated_data == {"a": "b"}

    def test_get_bk_app_code(self):
        validator = AccessTokenValidator()
        validator._validated_data = {"bk_app_code": "app-test"}
        assert validator.get_bk_app_code() == "app-test"

    def test_get_username(self):
        validator = AccessTokenValidator()

        validator._validated_data = {"bk_username": ""}
        with pytest.raises(ValidationError):
            validator.get_bk_username()

        validator._validated_data = {"bk_username": "admin"}
        assert validator.get_bk_username() == "admin"

    def test_verify_access_token(self, disable_ttl_cache_tools, mocker, faker):
        access_token = faker.pystr(min_chars=1)

        mock_invoke = mocker.patch(
            "components.bk.apisv2.bk_ssm.verify_access_token.VerifyAccessToken.invoke", return_value={"result": False}
        )
        with pytest.raises(ValidationError):
            AccessTokenValidator._verify_access_token(access_token)
        mock_invoke.assert_called_once_with(kwargs={"access_token": access_token})

        mock_invoke = mocker.patch(
            "components.bk.apisv2.bk_ssm.verify_access_token.VerifyAccessToken.invoke",
            return_value={
                "result": True,
                "data": {
                    "bk_app_code": "app-test",
                    "identity": {
                        "username": "admin",
                    },
                },
            },
        )
        bk_app_code, bk_username = AccessTokenValidator._verify_access_token(access_token)
        assert bk_app_code == "app-test"
        assert bk_username == "admin"
        mock_invoke.assert_called_once_with(kwargs={"access_token": access_token})

        # 测试缓存是否禁用
        AccessTokenValidator._verify_access_token(access_token)
        mock_invoke.called_count == 2


class TestAppSecretValidator:
    @pytest.mark.parametrize(
        "authorization, verify_result, expected",
        [
            (
                {"bk_app_secret": "valid-secret1"},
                (True, "ok"),
                None,
            ),
            (
                {"app_secret": "valid-secret2"},
                (True, "ok"),
                None,
            ),
            (
                {"bk_app_secret": "not-valid-secret"},
                (False, "error"),
                ValidationError,
            ),
            (
                {},
                (True, "error"),
                ValidationError,
            ),
        ],
    )
    def test_validate(self, mocker, fake_request, faker, authorization, verify_result, expected):
        validator = AppSecretValidator()
        app_code = faker.pystr(min_chars=1)
        app_secret = authorization.get("bk_app_secret") or authorization.get("app_secret")

        mock_verify_app_secret = mocker.patch(
            "esb.bkapp.validators.BKAuthHelper.verify_app_secret",
            return_value=verify_result,
        )
        fake_request.g = FancyDict(app_code=app_code, authorization=authorization)

        if expected is None:
            assert validator.validate(fake_request) is None
            mock_verify_app_secret.assert_called_once_with(app_code, app_secret)
            return

        with pytest.raises(ValidationError):
            validator.validate(fake_request)


class TestSignatureValidator:
    @pytest.mark.parametrize(
        "method, path, params, signature, app_secrets, expected",
        [
            (
                "GET",
                "/echo/",
                {
                    "abc": "xyz",
                    "bk_nonce": 12345,
                    "bk_timestamp": 1936162716,
                },
                "8lzxAJAoNX4D3O1QXfDpH+TzD20=",
                ["valid-secret"],
                True,
            ),
            (
                "GET",
                "/echo/",
                {
                    "abc": "xyz",
                    "bk_nonce": 12345,
                    "bk_timestamp": 1936162716,
                },
                "8lzxAJAoNX4D3O1QXfDpH+TzD20=",
                ["invalid-secret"],
                False,
            ),
            (
                "GET",
                "/echo/",
                {
                    "abc": "xyz",
                    "bk_nonce": 12345,
                    "bk_timestamp": 1936162716,
                },
                "8lzxAJAoNX4D3O1QXfDpH+TzD20=",
                ["invalid-secret", "valid-secret"],
                True,
            ),
        ],
    )
    def test_verify_signature(self, method, path, params, signature, app_secrets, expected):
        validator = SignatureValidator()
        result = validator.verify_signature(method, path, params, signature, app_secrets)
        assert result == expected


class TestSelfAppCodeAppSecret:
    @pytest.mark.parametrize(
        "app_code, app_secret, settings_app_code, settings_app_secret, will_error",
        [
            ("", "my-secret", "my-app", "my-secret", True),
            ("my-app", "", "my-app", "my-secret", True),
            ("my-app", "invalid-secret", "my-app", "my-secret", True),
            ("my-app", "my-secret", "my-app", "my-secret", False),
        ],
    )
    def test_validate(
        self, settings, fake_request, app_code, app_secret, settings_app_code, settings_app_secret, will_error
    ):
        settings.BK_APP_CODE = settings_app_code
        settings.BK_APP_SECRET = settings_app_secret

        fake_request.g = FancyDict(app_code=app_code, authorization={"bk_app_secret": app_secret})

        validator = SelfAppCodeAppSecret()

        if will_error:
            with pytest.raises(ValidationError):
                validator.validate(fake_request)
            return

        assert validator.validate(fake_request) is None
