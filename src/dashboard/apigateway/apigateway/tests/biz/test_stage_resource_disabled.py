# -*- coding: utf-8
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
from django_dynamic_fixture import G

from apigateway.biz.stage_resource_disabled import StageResourceDisabledHandler
from apigateway.core.models import Resource, Stage, StageResourceDisabled


class TestStageResourceDisabledHandler:
    def test_filter_disabled_stages_by_gateway(self, fake_gateway):
        resource1 = G(Resource, gateway=fake_gateway)
        resource2 = G(Resource, gateway=fake_gateway)
        stage_prod = G(Stage, gateway=fake_gateway, name="prod")
        stage_test = G(Stage, gateway=fake_gateway, name="test")

        G(StageResourceDisabled, resource=resource1, stage=stage_prod)
        G(StageResourceDisabled, resource=resource2, stage=stage_prod)
        G(StageResourceDisabled, resource=resource1, stage=stage_test)

        result = StageResourceDisabledHandler.filter_disabled_stages_by_gateway(fake_gateway)
        assert result == {
            resource1.id: [
                {
                    "id": stage_prod.id,
                    "name": stage_prod.name,
                },
                {
                    "id": stage_test.id,
                    "name": stage_test.name,
                },
            ],
            resource2.id: [
                {
                    "id": stage_prod.id,
                    "name": stage_prod.name,
                },
            ],
        }
