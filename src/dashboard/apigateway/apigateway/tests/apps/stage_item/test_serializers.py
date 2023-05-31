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

from apigateway.apps.stage_item import serializers
from apigateway.core.models import StageItem

pytestmark = pytest.mark.django_db


class TestStageItemSLZ:
    def test_to_representation(self, fake_gateway):
        instance = G(StageItem, api=fake_gateway)
        slz = serializers.StageItemSLZ(instance, context={"stage_item_configs": {"a": "b"}})

        assert slz.data == {
            "id": instance.id,
            "type": instance.type,
            "name": instance.name,
            "description": instance.description,
            "stage_item_configs": {"a": "b"},
        }

    def test_save(self, fake_gateway):
        params = {
            "type": "node",
            "name": "test",
            "description": "desc",
        }

        slz = serializers.StageItemSLZ(data=params, context={"api": fake_gateway})
        slz.is_valid(raise_exception=True)
        assert slz.validated_data == {
            "api": fake_gateway,
            "type": "node",
            "name": "test",
            "description": "desc",
        }

        assert slz.save() is not None


class TestListStageItemSLZ:
    def test_to_representation(self, fake_gateway):
        item = G(StageItem, api=fake_gateway, updated_time=None)

        slz = serializers.ListStageItemSLZ(
            [item],
            many=True,
            context={
                "stage_item_id_to_configured_stages": {item.id: [{"id": 1, "name": "a1"}]},
                "stage_id_to_fields": {1: {"id": 1, "name": "a1"}, 2: {"id": 2, "name": "a2"}},
                "stage_item_id_to_reference_instances": {},
            },
        )
        assert slz.data == [
            {
                "id": item.id,
                "type": item.type,
                "name": item.name,
                "description": item.description,
                "updated_time": None,
                "configured_stages": [{"id": 1, "name": "a1"}],
                "not_configured_stages": [{"id": 2, "name": "a2"}],
                "reference_instances": [],
            }
        ]


class TestListStageItemForStageSLZ:
    def test_to_representation(self, fake_gateway):
        item1 = G(StageItem, api=fake_gateway, updated_time=None)
        item2 = G(StageItem, api=fake_gateway, updated_time=None)

        slz = serializers.ListStageItemForStageSLZ(
            [item1, item2],
            many=True,
            context={"configured_item_ids": [item1.id]},
        )
        assert slz.data == [
            {
                "id": item1.id,
                "type": item1.type,
                "name": item1.name,
                "description": item1.description,
                "updated_time": None,
                "status": "configured",
            },
            {
                "id": item2.id,
                "type": item2.type,
                "name": item2.name,
                "description": item2.description,
                "updated_time": None,
                "status": "not_configured",
            },
        ]
