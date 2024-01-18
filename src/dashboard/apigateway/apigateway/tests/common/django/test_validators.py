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

from apigateway.common.django.validators import NameValidator


class TestNameValidator:
    class GatewaySLZ(serializers.Serializer):
        name = serializers.CharField(validators=[NameValidator()])

    @pytest.mark.parametrize(
        "name, will_error",
        [
            ("abc", False),
            ("abc-", True),
            ("abc--", True),
            ("abc_", True),
            ("abc__", True),
        ],
    )
    def test_validate(self, settings, name, will_error):
        slz = self.GatewaySLZ(data={"name": name})
        slz.is_valid()

        if will_error:
            assert slz.errors
        else:
            assert not slz.errors
