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
from django_dynamic_fixture import G

from apigateway.biz.stage import StageHandler
from apigateway.core.models import Gateway


class TestStageHandler:
    @pytest.fixture(autouse=True)
    def setup_fixtures(self):
        self.gateway = G(Gateway)

    @pytest.mark.parametrize(
        "stage_names, expected, will_error",
        [
            ([], [1, 2], False),
            (["prod"], [1], False),
            (["stag"], None, True),
        ],
    )
    def test_get_stage_ids(self, mocker, fake_request, fake_gateway, stage_names, expected, will_error):
        mocker.patch(
            "apigateway.biz.stage.Stage.objects.get_name_id_map",
            return_value={"prod": 1, "test": 2},
        )

        if will_error:
            with pytest.raises(Exception):
                StageHandler.get_stage_ids(fake_gateway, stage_names)
            return

        result = StageHandler.get_stage_ids(fake_gateway, stage_names)
        assert expected == sorted(result)
