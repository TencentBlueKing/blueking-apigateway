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

from apigateway.core.constants import APIHostingTypeEnum
from apigateway.core.management.commands.update_gateway_hosting_type import Command
from apigateway.core.models import Gateway

pytestmark = pytest.mark.django_db


class TestCommand:
    def test_handle(self, fake_gateway):
        fake_gateway.name = f"foo-{fake_gateway.id}"
        fake_gateway.hosting_type = APIHostingTypeEnum.MICRO.value
        fake_gateway.save()

        Command().handle(False, fake_gateway.name, hosting_type=1, dry_run=False)
        assert Gateway.objects.get(name=fake_gateway.name).hosting_type == 1

        Command().handle(False, fake_gateway.name, hosting_type=0, dry_run=False)
        assert Gateway.objects.get(name=fake_gateway.name).hosting_type == 0
