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
from django_dynamic_fixture import G

from apigateway.apps.label.models import APILabel, ResourceLabel
from apigateway.core.models import Gateway, Resource


class TestAPILabelManager:
    def get_labels(self):
        gateway = G(Gateway)

        l1 = G(APILabel, api=gateway)
        l2 = G(APILabel, api=gateway)

        data = [
            {
                "params": {
                    "api": gateway,
                    "ids": None,
                },
                "expected": [{"id": l1.id, "name": l1.name}, {"id": l2.id, "name": l2.name}],
            },
            {
                "params": {
                    "api": gateway,
                    "ids": [],
                },
                "expected": [],
            },
            {
                "params": {
                    "api": gateway,
                    "ids": [l2.id],
                },
                "expected": [{"id": l2.id, "name": l2.name}],
            },
        ]
        for test in data:
            result = APILabel.objects.get_labels(gateway=test["params"]["api"], ids=test["params"]["ids"])
            assert result == test["exptected"]

    def test_filter_by_label_name(self):
        gateway = G(Gateway)
        G(APILabel, api=gateway, name="label_1")
        G(APILabel, api=gateway, name="label_2")

        data = [
            {
                "api": gateway,
                "label_name": "label_1",
                "expected": {
                    "count": 1,
                },
            },
            {
                "api": gateway,
                "label_name": "label_2",
                "expected": {
                    "count": 1,
                },
            },
            {
                "api": gateway,
                "label_name": "label_3",
                "expected": {
                    "count": 0,
                },
            },
            {
                "api": gateway,
                "label_name": "",
                "expected": {
                    "count": 2,
                },
            },
        ]
        for test in data:
            result = APILabel.objects.filter_by_label_name(gateway=test["api"], label_name=test["label_name"])
            assert result.count() == test["expected"]["count"]

    def test_get_label_ids(self):
        gateway = G(Gateway)
        l1 = G(APILabel, api=gateway)
        l2 = G(APILabel, api=gateway)

        result = APILabel.objects.get_label_ids(gateway)
        assert result == [l1.id, l2.id]

    def test_get_name_id_map(self):
        gateway = G(Gateway)
        l1 = G(APILabel, api=gateway, name="t1")
        l2 = G(APILabel, api=gateway, name="t2")

        result = APILabel.objects.get_name_id_map(gateway)
        assert result == {
            l1.name: l1.id,
            l2.name: l2.id,
        }

    def test_save_labels(self, fake_gateway):
        l1 = G(APILabel, api=fake_gateway, name="T1")

        result = APILabel.objects.save_labels(fake_gateway, ["T1"], "")
        assert result == {"T1": l1.id}

        result = APILabel.objects.save_labels(fake_gateway, ["T1", "T2"], "")
        assert set(result.keys()) == {"T1", "T2"}


class TestResourceLabelManager(TestCase):
    def test_get_labels(self):
        gateway = G(Gateway)
        resource_1 = G(Resource, api=gateway)
        resource_2 = G(Resource, api=gateway)
        label_1 = G(APILabel, api=gateway, name="label_1")
        label_2 = G(APILabel, api=gateway, name="label_2")

        G(ResourceLabel, resource=resource_1, api_label=label_1)
        G(ResourceLabel, resource=resource_2, api_label=label_1)
        G(ResourceLabel, resource=resource_1, api_label=label_2)

        result = ResourceLabel.objects.get_labels([resource_1.id, resource_2.id])
        self.assertEqual(
            result,
            {
                resource_1.id: [
                    {
                        "id": label_1.id,
                        "name": label_1.name,
                    },
                    {
                        "id": label_2.id,
                        "name": label_2.name,
                    },
                ],
                resource_2.id: [
                    {
                        "id": label_1.id,
                        "name": label_1.name,
                    },
                ],
            },
        )

    def test_filter_resource_ids(self):
        gateway = G(Gateway)
        resource_1 = G(Resource, api=gateway)
        resource_2 = G(Resource, api=gateway)
        label_1 = G(APILabel, api=gateway, name="label_1")
        label_2 = G(APILabel, api=gateway, name="label_2")

        G(ResourceLabel, resource=resource_1, api_label=label_1)
        G(ResourceLabel, resource=resource_1, api_label=label_2)
        G(ResourceLabel, resource=resource_2, api_label=label_1)

        data = [
            {
                "api": gateway,
                "label_name": "label_1",
                "expected": [resource_1.id, resource_2.id],
            },
            {
                "api": gateway,
                "label_name": "label_2",
                "expected": [resource_1.id],
            },
            {
                "api": gateway,
                "label_name": "label_3",
                "expected": [],
            },
            {
                "api": gateway,
                "label_name": "",
                "expected": [resource_1.id, resource_2.id],
            },
        ]
        for test in data:
            result = ResourceLabel.objects.filter_resource_ids(gateway=test["api"], label_name=test["label_name"])
            self.assertEqual(set(result), set(test["expected"]))

    def test_filter_labels_by_gateway(self):
        gateway = G(Gateway)
        resource_1 = G(Resource, api=gateway)
        resource_2 = G(Resource, api=gateway)
        label_1 = G(APILabel, api=gateway, name="label_1")
        label_2 = G(APILabel, api=gateway, name="label_2")

        G(ResourceLabel, resource=resource_1, api_label=label_1)
        G(ResourceLabel, resource=resource_2, api_label=label_1)
        G(ResourceLabel, resource=resource_1, api_label=label_2)

        result = ResourceLabel.objects.filter_labels_by_gateway(gateway)
        self.assertEqual(
            result,
            {
                resource_1.id: [
                    {
                        "id": label_1.id,
                        "name": label_1.name,
                    },
                    {
                        "id": label_2.id,
                        "name": label_2.name,
                    },
                ],
                resource_2.id: [
                    {
                        "id": label_1.id,
                        "name": label_1.name,
                    },
                ],
            },
        )

    def test_get_api_label_ids(self):
        gateway = G(Gateway)

        resource_1 = G(Resource, api=gateway)
        resource_2 = G(Resource, api=gateway)
        label_1 = G(APILabel, api=gateway, name="label_1")
        label_2 = G(APILabel, api=gateway, name="label_2")

        G(ResourceLabel, resource=resource_1, api_label=label_1)
        G(ResourceLabel, resource=resource_1, api_label=label_2)

        data = [
            {
                "resource_id": resource_1.id,
                "expected": [label_1.id, label_2.id],
            },
            {
                "resource_id": resource_2.id,
                "expected": [],
            },
        ]

        for test in data:
            result = ResourceLabel.objects.get_api_label_ids(test["resource_id"])
            self.assertEqual(result, test["expected"])
