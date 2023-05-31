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
from ddf import G
from rest_framework import serializers

from apigateway.apps.esb.bkcore.models import ComponentSystem, ESBChannel
from apigateway.apps.esb.validators import ComponentIDValidator

pytestmark = [pytest.mark.django_db]


class TestComponentIDValidator:
    class ComponentIDSLZ(serializers.Serializer):
        component_id = serializers.IntegerField(validators=[ComponentIDValidator()], allow_null=True, required=False)

    class ComponentIDsSLZ(serializers.Serializer):
        component_ids = serializers.ListField(
            child=serializers.IntegerField(),
            validators=[ComponentIDValidator()],
            allow_empty=True,
            required=False,
        )

    def test_validate(self):
        system = G(ComponentSystem)

        c1 = G(ESBChannel, system=system)
        c2 = G(ESBChannel, system=system)
        c3 = G(ESBChannel, system=G(ComponentSystem))

        data = [
            {
                "model": self.ComponentIDSLZ,
                "params": {
                    "component_id": c1.id,
                },
                "will_error": False,
            },
            {
                "model": self.ComponentIDSLZ,
                "params": {
                    "component_id": c3.id,
                },
                "will_error": True,
            },
            {
                "model": self.ComponentIDsSLZ,
                "params": {
                    "component_ids": [c1.id, c2.id],
                },
                "will_error": False,
            },
            {
                "model": self.ComponentIDsSLZ,
                "params": {
                    "component_ids": [c1.id, c3.id],
                },
                "will_error": True,
            },
            {
                "model": self.ComponentIDsSLZ,
                "params": {},
                "will_error": False,
            },
        ]
        for test in data:
            slz = test["model"](
                data=test["params"],
                context={
                    "system_id": system.id,
                },
            )
            slz.is_valid()
            if test["will_error"]:
                assert slz.errors
            else:
                assert not slz.errors
