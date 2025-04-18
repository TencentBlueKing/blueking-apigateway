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
from rest_framework import serializers

from apigateway.apis.web.gateway.validators import ProgrammableGatewayNameValidator, ReservedGatewayNameValidator
from apigateway.core.constants import GatewayKindEnum


class TestReservedGatewayNameValidator:
    class GatewaySLZ(serializers.Serializer):
        name = serializers.CharField(validators=[ReservedGatewayNameValidator()])

    @pytest.mark.parametrize(
        "check_reserved_gateway_name, reserved_gateway_name_prefixes, api_name, will_error",
        [
            (False, ["bk-"], "api-test", False),
            (False, ["bk-"], "bk-api-test", False),
            (True, ["bk-"], "api-test", False),
            (True, ["bk-"], "bk-api-test", True),
            (True, ["bk_", "bk-"], "bk-api-test", True),
            (True, [], "test", False),
        ],
    )
    def test_validate(
        self, settings, check_reserved_gateway_name, reserved_gateway_name_prefixes, api_name, will_error
    ):
        settings.CHECK_RESERVED_GATEWAY_NAME = check_reserved_gateway_name
        settings.RESERVED_GATEWAY_NAME_PREFIXES = reserved_gateway_name_prefixes

        slz = self.GatewaySLZ(data={"name": api_name})
        slz.is_valid()

        if will_error:
            assert slz.errors
        else:
            assert not slz.errors


class TestProgrammableGatewayNameValidator:
    class GatewaySLZ(serializers.Serializer):
        name = serializers.CharField()
        kind = serializers.ChoiceField(choices=GatewayKindEnum.get_choices())

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.validators.append(ProgrammableGatewayNameValidator())

    @pytest.mark.parametrize(
        "kind, name, is_occupied, will_error",
        [
            (GatewayKindEnum.PROGRAMMABLE.value, "testapp", True, True),
            (GatewayKindEnum.PROGRAMMABLE.value, "testapp", False, False),
            (GatewayKindEnum.NORMAL.value, "testapp", True, False),
            (GatewayKindEnum.NORMAL.value, "testapp", False, False),
        ],
    )
    def test_validate(self, mocker, kind, name, is_occupied, will_error):
        mocker.patch("apigateway.apis.web.gateway.validators.is_app_code_occupied", return_value=is_occupied)

        slz = self.GatewaySLZ(data={"name": name, "kind": kind})

        if will_error:
            with pytest.raises(serializers.ValidationError):
                slz.is_valid(raise_exception=True)
        else:
            slz.is_valid()
            assert not slz.errors
