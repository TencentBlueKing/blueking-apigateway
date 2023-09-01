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
from ddf import G

from apigateway.apps.label.models import APILabel, ResourceLabel
from apigateway.biz.resource_label import ResourceLabelHandler


class TestResourceLabelHandler:
    def test_get_labels_by_gateway(self, fake_resource):
        label_1 = G(APILabel, gateway=fake_resource.api, name="label1")
        label_2 = G(APILabel, gateway=fake_resource.api, name="label2")

        G(ResourceLabel, resource=fake_resource, api_label=label_1)
        G(ResourceLabel, resource=fake_resource, api_label=label_2)

        resource_labels = ResourceLabelHandler.get_labels_by_gateway(fake_resource.api.id)
        assert resource_labels == {
            fake_resource.id: [
                {"id": label_1.id, "name": label_1.name},
                {"id": label_2.id, "name": label_2.name},
            ]
        }

    def test_get_labels(self, fake_resource):
        label_1 = G(APILabel, gateway=fake_resource.api, name="label1")
        label_2 = G(APILabel, gateway=fake_resource.api, name="label2")

        G(ResourceLabel, resource=fake_resource, api_label=label_1)
        G(ResourceLabel, resource=fake_resource, api_label=label_2)

        resource_labels = ResourceLabelHandler.get_labels([fake_resource.id])
        assert resource_labels == {
            fake_resource.id: [
                {"id": label_1.id, "name": label_1.name},
                {"id": label_2.id, "name": label_2.name},
            ]
        }
