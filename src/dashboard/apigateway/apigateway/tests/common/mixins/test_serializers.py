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
from rest_framework import serializers

from apigateway.common.mixins.serializers import ExtensibleFieldMixin


class TestExtensibleFieldMixin:
    class Record:
        name = ""
        title = ""

    class RecordSLZ(serializers.Serializer):
        def create(self, validated_data):
            return validated_data

        def update(self, instance, validated_data):
            return validated_data

    class NonModelFieldsNoneSLZ(ExtensibleFieldMixin, RecordSLZ):
        name = serializers.CharField()
        title = serializers.CharField()

    class NonModelFieldsExistSLZ(ExtensibleFieldMixin, RecordSLZ):
        name = serializers.CharField()
        title = serializers.CharField()

        class Meta:
            non_model_fields = ["title"]

    @pytest.mark.parametrize(
        "slz_class, data, expected",
        [
            (
                NonModelFieldsNoneSLZ,
                {"name": "a", "title": "a"},
                {"name": "a", "title": "a"},
            ),
            (
                NonModelFieldsExistSLZ,
                {"name": "a", "title": "a"},
                {"name": "a"},
            ),
        ],
    )
    def test_create(self, slz_class, data, expected):
        slz = slz_class(data=data)
        slz.is_valid()
        result = slz.save()
        assert result == expected

    @pytest.mark.parametrize(
        "slz_class, data, expected",
        [
            (
                NonModelFieldsNoneSLZ,
                {"name": "a", "title": "a"},
                {"name": "a", "title": "a"},
            ),
            (
                NonModelFieldsExistSLZ,
                {"name": "a", "title": "a"},
                {"name": "a"},
            ),
        ],
    )
    def test_update(self, slz_class, data, expected):
        slz = slz_class(instance=TestExtensibleFieldMixin.Record(), data=data)
        slz.is_valid()
        result = slz.save()
        assert result == expected
