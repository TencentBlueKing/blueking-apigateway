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
from apigateway.apps.label.models import APILabel
from apigateway.biz.gateway_label import GatewayLabelHandler


class TestGatewayLabelHandler:
    def test_save_labels(self, fake_gateway):
        GatewayLabelHandler.save_labels(fake_gateway, ["label1"])
        assert APILabel.objects.filter(gateway=fake_gateway).count() == 1

        GatewayLabelHandler.save_labels(fake_gateway, ["label1", "label2", "label3"])
        assert APILabel.objects.filter(gateway=fake_gateway).count() == 3

        GatewayLabelHandler.save_labels(fake_gateway, ["label2", "label3", "label4"])
        assert APILabel.objects.filter(gateway=fake_gateway).count() == 4
