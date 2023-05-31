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

from common.base_utils import FancyDict
from common.errors import APIError
from esb.compperm.validators import ComponentPermValidator

pytestmark = pytest.mark.django_db


class TestComponentPermValidator:
    @pytest.mark.parametrize(
        "apigw_enabled, mock_esb_skip_comp_perm, mock_component_permission_required, mock_has_permission, will_error",
        [
            (
                True,
                False,
                True,
                False,
                False,
            ),
            (
                False,
                True,
                None,
                None,
                False,
            ),
            (
                False,
                False,
                False,
                None,
                False,
            ),
            (
                False,
                False,
                True,
                True,
                False,
            ),
            (
                False,
                False,
                True,
                False,
                True,
            ),
        ],
    )
    def test_validate(
        self,
        apigw_enabled,
        mock_esb_skip_comp_perm,
        mock_component_permission_required,
        mock_has_permission,
        will_error,
        mocker,
        fake_request,
    ):
        fake_request.__esb_skip_comp_perm__ = mock_esb_skip_comp_perm
        fake_request.apigw = FancyDict(enabled=apigw_enabled)
        fake_request.g = mock.MagicMock(
            app_code="test",
            channel_conf={
                "id": 1,
                "permission_level": "normal",
            },
        )
        mocker.patch(
            "esb.compperm.validators.ComponentPermValidator._is_component_permission_required",
            return_value=mock_component_permission_required,
        )
        mocker.patch(
            "esb.compperm.validators.AppComponentPermission.objects.has_permission",
            return_value=mock_has_permission,
        )

        validator = ComponentPermValidator()

        if will_error:
            with pytest.raises(APIError) as ex:
                validator.validate(fake_request)
            return

        assert validator.validate(fake_request) is None

    @pytest.mark.parametrize(
        "component_id, permission_level, expected",
        [
            (None, None, False),
            (1, None, False),
            (1, "unlimited", False),
            (1, "normal", True),
        ],
    )
    def test_is_component_permission_required(self, component_id, permission_level, expected):
        validator = ComponentPermValidator()
        result = validator._is_component_permission_required(component_id, permission_level)
        assert result == expected
