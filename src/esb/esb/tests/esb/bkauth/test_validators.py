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
import datetime

import pytest
from ddf import G

from common.base_utils import FancyDict
from common.base_validators import ValidationError
from esb.bkauth.validators import BaseUserAuthValidator, UserAuthValidator, VerifiedUserRequiredValidator
from esb.bkcore.models import AccessToken

pytestmark = pytest.mark.django_db


class TestBaseUserAuthValidator:
    def test_validate_bk_token(self, fake_request, mocker):
        mocker.patch("esb.bkauth.validators.BaseUserAuthValidator._verify_bk_token", return_value="admin")
        fake_request.g = FancyDict({"app_code": "fake-app-code"})
        validator = BaseUserAuthValidator()
        validator.validate_bk_token(fake_request, "fake-token")
        assert fake_request.g.current_user_username == "admin"
        assert fake_request.g.current_user_verified is True

    def test_verify_bk_token(self, fake_request, mocker):
        validator = BaseUserAuthValidator()

        mocker.patch("components.bk.apis.bk_login.is_login.IsLogin.invoke", return_value={"result": False})
        with pytest.raises(ValidationError):
            validator._verify_bk_token("fake-bk-token", "fake-app-code")

        mocker.patch(
            "components.bk.apis.bk_login.is_login.IsLogin.invoke",
            return_value={"result": True, "data": {"username": "admin"}},
        )
        result = validator._verify_bk_token("fake-bk-token", "fake-app-code")
        assert result == "admin"

    def test_validate_access_token(self, mocker, fake_request, unique_id, faker):
        mocker.patch(
            "esb.bkauth.validators.BaseUserAuthValidator.sync_current_username",
            return_value=None,
        )

        bk_app_code = unique_id
        username = faker.user_name()
        token = G(
            AccessToken,
            bk_app_code=bk_app_code,
            user_id=username,
            expires=faker.future_datetime(tzinfo=datetime.timezone.utc),
        )

        validator = BaseUserAuthValidator()
        assert validator.validate_access_token(fake_request, bk_app_code, token.access_token) is None

    def test_validate_access_token_error(self, mocker, fake_request, unique_id, faker):
        validator = BaseUserAuthValidator()

        with pytest.raises(ValidationError):
            validator.validate_access_token(fake_request, "", unique_id)

        with pytest.raises(ValidationError):
            validator.validate_access_token(fake_request, unique_id, "")

        with pytest.raises(ValidationError):
            validator.validate_access_token(fake_request, unique_id, unique_id)

        G(
            AccessToken,
            bk_app_code=unique_id,
            access_token=unique_id,
            expires=faker.past_datetime(tzinfo=datetime.timezone.utc),
        )
        with pytest.raises(ValidationError):
            validator.validate_access_token(fake_request, unique_id, unique_id)

    @pytest.mark.parametrize(
        "username, verified",
        [
            ("admin", True),
            ("admin", False),
            ("", False),
        ],
    )
    def test_sync_current_username(self, fake_request, username, verified):
        fake_request.g = FancyDict()
        validator = BaseUserAuthValidator()
        validator.sync_current_username(fake_request, username, verified)
        assert fake_request.g.current_user_username == username
        assert fake_request.g.current_user_verified == verified


class TestUserAuthValidator:
    @pytest.fixture()
    def patched_request(self, fake_request):
        fake_request.g = FancyDict(app_code="my-color", kwargs={})
        fake_request.apigw = FancyDict(enabled=False)
        return fake_request

    def test_validate_with_apigw(self, patched_request, mocker, faker):
        patched_request.apigw = FancyDict(enabled=True)
        username = faker.user_name()
        validator = UserAuthValidator()

        # user verified
        patched_request.g.current_user_verified = True
        patched_request.g.current_user_username = username
        assert validator.validate(patched_request) is None

        # user not verified, username is not empty
        patched_request.g.current_user_verified = False
        patched_request.g.current_user_username = username
        assert validator.validate(patched_request) is None

        # user not verified
        patched_request.g.current_user_verified = False
        patched_request.g.current_user_username = ""
        with pytest.raises(ValidationError):
            validator.validate(patched_request)

    def test_validate_with_access_token(self, patched_request, mocker, faker):
        access_token = faker.pystr(min_chars=1)
        username = faker.user_name()

        patched_request.g.update(authorization={"access_token": access_token})

        validator = UserAuthValidator()

        # validate ok
        mock_validate = mocker.patch("esb.bkauth.validators.AccessTokenValidator.validate")
        mocker.patch("esb.bkauth.validators.AccessTokenValidator.get_bk_username", return_value=username)
        mock_sync_current_username = mocker.patch.object(validator, "sync_current_username")

        validator.validate(patched_request)
        mock_validate.assert_called_once_with(patched_request)
        mock_sync_current_username.assert_called_once_with(patched_request, username, verified=True)

        # validate error
        mock_validate = mocker.patch(
            "esb.bkauth.validators.AccessTokenValidator.validate", side_effect=ValidationError
        )
        mock_sync_current_username.reset_mock()
        with pytest.raises(ValidationError):
            validator.validate(patched_request)
        mock_validate.assert_called_once_with(patched_request)
        mock_sync_current_username.assert_not_called()

        # validate ok, but get_bk_username error
        mock_validate = mocker.patch("esb.bkauth.validators.AccessTokenValidator.validate")
        mocker.patch("esb.bkauth.validators.AccessTokenValidator.get_bk_username", side_effect=ValidationError)
        with pytest.raises(ValidationError):
            validator.validate(patched_request)
        mock_validate.assert_called_once_with(patched_request)
        mock_sync_current_username.assert_not_called()

    def test_validate_with_bk_token(self, patched_request, mocker, faker):
        bk_token = faker.pystr(min_chars=1)
        patched_request.g.update(authorization={"bk_token": bk_token})

        validator = UserAuthValidator()
        mocked_validate_bk_token = mocker.patch("esb.bkauth.validators.UserAuthValidator.validate_bk_token")
        assert validator.validate(patched_request) is None
        mocked_validate_bk_token.assert_called_once_with(patched_request, bk_token)

    @pytest.mark.parametrize(
        "authorization, is_skip_user_auth, expected, expected_error",
        [
            (
                {"bk_username": "admin"},
                True,
                "admin",
                None,
            ),
            (
                {"username": "admin"},
                True,
                "admin",
                None,
            ),
            (
                {"bk_username": ""},
                True,
                None,
                ValidationError,
            ),
            (
                {"username": "admin"},
                False,
                None,
                ValidationError,
            ),
        ],
    )
    def test_validate_with_username(
        self, patched_request, mocker, authorization, is_skip_user_auth, expected, expected_error
    ):
        patched_request.g.update(authorization=authorization)
        mocker.patch(
            "esb.bkauth.validators.FunctionControllerClient.is_skip_user_auth",
            return_value=is_skip_user_auth,
        )

        validator = UserAuthValidator()
        mock_sync_current_username = mocker.patch.object(validator, "sync_current_username")

        if not expected_error:
            assert validator.validate(patched_request) is None
            mock_sync_current_username.assert_called_once_with(patched_request, expected, verified=False)
            return

        with pytest.raises(ValidationError):
            validator.validate(patched_request)


class TestVerifiedUserRequiredValidator:
    @pytest.fixture()
    def patched_request(self, fake_request):
        fake_request.g = FancyDict(
            {
                "authorization": {
                    "bk_token": "fake-bk-token",
                },
            }
        )
        fake_request.apigw = FancyDict(enabled=False)
        return fake_request

    def test_validate(self, patched_request, mocker):
        validator = VerifiedUserRequiredValidator()
        mocked_validate_bk_token = mocker.patch(
            "esb.bkauth.validators.VerifiedUserRequiredValidator.validate_bk_token",
            return_value=None,
        )
        assert validator.validate(patched_request) is None
        mocked_validate_bk_token.assert_called_once()

        patched_request.g.authorization = {}
        patched_request.COOKIES = {}
        with pytest.raises(ValidationError):
            validator.validate(patched_request)

    def test_validate_with_apigw_enabled(self, patched_request):
        patched_request.apigw = FancyDict(enabled=True)
        validator = VerifiedUserRequiredValidator()

        patched_request.g = FancyDict(current_user_username="admin", current_user_verified=True)
        assert validator.validate(patched_request) is None

        patched_request.g = FancyDict(current_user_username="admin", current_user_verified=False)
        with pytest.raises(ValidationError):
            validator.validate(patched_request)
