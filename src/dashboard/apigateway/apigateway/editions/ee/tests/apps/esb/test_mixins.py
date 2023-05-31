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

from apigateway.apps.esb.mixins import OfficialWriteFields


class TestOfficialWriteFields:
    class Record:
        name = ""
        title = ""

        def __init__(self, is_official: bool):
            self.is_official = is_official

    class RecordSLZ(serializers.Serializer):
        def update(self, instance, validated_data):
            return validated_data

    class OfficialWriteFieldsSLZ(OfficialWriteFields, RecordSLZ):
        name = serializers.CharField()
        title = serializers.CharField()

        class Meta:
            official_write_fields = ["title"]

    @pytest.mark.parametrize(
        "is_official, data, expected",
        [
            (
                False,
                {"name": "a", "title": "a"},
                {"name": "a", "title": "a"},
            ),
            (
                True,
                {"name": "a", "title": "a"},
                {"title": "a"},
            ),
        ],
    )
    def test_update(self, is_official, data, expected):
        record = self.Record(is_official)
        slz = self.OfficialWriteFieldsSLZ(instance=record, data=data)
        slz.is_valid()
        result = slz.save()
        assert result == expected
