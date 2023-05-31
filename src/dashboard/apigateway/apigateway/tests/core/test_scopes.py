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

from apigateway.core.constants import ScopeTypeEnum
from apigateway.core.models import Stage
from apigateway.core.scopes import ScopeManager, StageScopeManager

pytestmark = pytest.mark.django_db


class TestScopeManager:
    def test_get_manager(self):
        manager = ScopeManager.get_manager(ScopeTypeEnum.STAGE.value)
        assert isinstance(manager, StageScopeManager)


class TestStageScopeManager:
    def test_get_scope_ids(self, fake_gateway):
        s = G(Stage, api=fake_gateway)

        manager = StageScopeManager()
        assert manager.get_scope_ids(fake_gateway.id, []) == [s.id]
        assert manager.get_scope_ids(fake_gateway.id, [{"name": s.name}]) == [s.id]
        assert manager.get_scope_ids(fake_gateway.id, [{"name": "not-exist"}]) == []
