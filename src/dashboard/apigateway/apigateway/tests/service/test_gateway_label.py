#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关 (BlueKing - APIGateway) available.
# Copyright (C) 2025 Tencent. All rights reserved.
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
from apigateway.apps.label.models import APILabel
from apigateway.service.gateway_label import save_gateway_labels


def test_save_gateway_labels_creates_missing_labels(fake_gateway):
    save_gateway_labels(fake_gateway, ["label1", "label2"], username="admin")

    labels = {
        label.name: label for label in APILabel.objects.filter(gateway=fake_gateway, name__in=["label1", "label2"])
    }
    assert set(labels) == {"label1", "label2"}
    assert labels["label1"].created_by == "admin"
    assert labels["label1"].updated_by == "admin"


def test_save_gateway_labels_ignores_existing_labels(fake_gateway):
    APILabel.objects.create(gateway=fake_gateway, name="label1", created_by="old", updated_by="old")

    save_gateway_labels(fake_gateway, ["label1", "label2"], username="admin")

    labels = list(APILabel.objects.filter(gateway=fake_gateway).order_by("name"))
    assert [label.name for label in labels] == ["label1", "label2"]
    assert labels[0].created_by == "old"
    assert labels[0].updated_by == "old"
    assert labels[1].created_by == "admin"
    assert labels[1].updated_by == "admin"
