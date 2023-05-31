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
from django.test import TestCase
from rest_framework import serializers

from apigateway.utils.serializers import CustomFieldsSerializer, set_default_to_context


class UserSerializer(CustomFieldsSerializer):
    name = serializers.CharField()


class TestCustomFieldsSerializer(TestCase):
    def test__init(self):
        data = [
            {
                "add_fields": {"age": serializers.IntegerField()},
                "expected": ["name", "age"],
            },
            {
                "add_fields": {"height": serializers.IntegerField()},
                "expected": ["name", "height"],
            },
        ]
        for test in data:
            slz = UserSerializer(add_fields=test["add_fields"])
            self.assertEqual([field_name for field_name, _ in slz.fields.items()], test["expected"])


def test_set_default_to_context():
    class ColorSLZ(serializers.Serializer):
        color = serializers.CharField()

        def validate(self, data):
            data["existed"] = data["color"] in self._get_existed_colors()
            return data

        @set_default_to_context(context_key="existed_colors")
        def _get_existed_colors(self):
            self.context.setdefault("count", 0)
            self.context["count"] = self.context["count"] + 1

            return {"green": True}

    slz = ColorSLZ(data={"color": "red"})
    slz.is_valid(raise_exception=True)
    assert slz.validated_data == {"color": "red", "existed": False}
    assert slz.context["count"] == 1

    slz = ColorSLZ(data=[{"color": "red"}, {"color": "green"}], many=True)
    slz.is_valid(raise_exception=True)
    assert slz.validated_data == [{"color": "red", "existed": False}, {"color": "green", "existed": True}]
    assert slz.context["count"] == 1
