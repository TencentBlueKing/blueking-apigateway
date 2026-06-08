#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关 (BlueKing - APIGateway) available.
# Copyright (C) Tencent. All rights reserved.
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
from ddf import G

from apigateway.apps.label.models import APILabel, ResourceLabel
from apigateway.service.resource import (
    ensure_gateway_labels,
    get_gateway_resource_id_to_labels,
    get_resource_id_to_labels,
    get_resource_id_to_labels_by_label_ids,
)


def test_get_gateway_resource_id_to_labels(fake_resource):
    label_1 = G(APILabel, gateway=fake_resource.gateway, name="label1")
    label_2 = G(APILabel, gateway=fake_resource.gateway, name="label2")

    G(ResourceLabel, resource=fake_resource, api_label=label_1)
    G(ResourceLabel, resource=fake_resource, api_label=label_2)

    assert get_gateway_resource_id_to_labels(fake_resource.gateway.id) == {
        fake_resource.id: [
            {"id": label_1.id, "name": label_1.name},
            {"id": label_2.id, "name": label_2.name},
        ]
    }


def test_get_resource_id_to_labels(fake_resource):
    label = G(APILabel, gateway=fake_resource.gateway, name="label1")
    G(ResourceLabel, resource=fake_resource, api_label=label)

    assert get_resource_id_to_labels([fake_resource.id]) == {fake_resource.id: [{"id": label.id, "name": label.name}]}


def test_get_resource_id_to_labels_by_label_ids(fake_resource):
    label_1 = G(APILabel, gateway=fake_resource.gateway, name="label1")
    label_2 = G(APILabel, gateway=fake_resource.gateway, name="label2")

    G(ResourceLabel, resource=fake_resource, api_label=label_1)
    G(ResourceLabel, resource=fake_resource, api_label=label_2)

    assert get_resource_id_to_labels_by_label_ids([label_1.id]) == {
        fake_resource.id: [{"id": label_1.id, "name": label_1.name}]
    }


def test_ensure_gateway_labels_creates_missing_labels(fake_gateway):
    ensure_gateway_labels(fake_gateway, ["label1", "label2"], username="admin")

    labels = {
        label.name: label for label in APILabel.objects.filter(gateway=fake_gateway, name__in=["label1", "label2"])
    }
    assert set(labels) == {"label1", "label2"}
    assert labels["label1"].created_by == "admin"
    assert labels["label1"].updated_by == "admin"


def test_ensure_gateway_labels_ignores_existing_labels(fake_gateway):
    APILabel.objects.create(gateway=fake_gateway, name="label1", created_by="old", updated_by="old")

    ensure_gateway_labels(fake_gateway, ["label1", "label2"], username="admin")

    labels = list(APILabel.objects.filter(gateway=fake_gateway).order_by("name"))
    assert [label.name for label in labels] == ["label1", "label2"]
    assert labels[0].created_by == "old"
    assert labels[0].updated_by == "old"
    assert labels[1].created_by == "admin"
    assert labels[1].updated_by == "admin"
