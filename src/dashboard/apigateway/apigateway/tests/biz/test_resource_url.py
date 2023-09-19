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
import json

from django_dynamic_fixture import G

from apigateway.biz.resource_url import ResourceURLHandler
from apigateway.core.models import Gateway, MicroGateway, Stage


class TestResourceURLHandler:
    def test_get_resource_url_tmpl(self, settings, unique_id):
        settings.API_RESOURCE_URL_TMPL = "http://bkapi.example.com/api/{api_name}/{stage_name}/{resource_path}"

        # 共享网关
        gateway = G(Gateway, name=unique_id)

        stage = G(Stage, gateway=gateway, name="prod")

        url = ResourceURLHandler.get_resource_url_tmpl(gateway.name, stage.name)
        assert url == "http://bkapi.example.com/api/{api_name}/{stage_name}/{resource_path}"

        # 微网关
        micro_gateway = G(
            MicroGateway, gateway=gateway, _config=json.dumps({"http": {"http_url": "http://myapi.example.com"}})
        )
        stage.micro_gateway = micro_gateway
        stage.save()

        tmpl = ResourceURLHandler.get_resource_url_tmpl(gateway.name, stage.name)
        assert tmpl == "http://myapi.example.com/{resource_path}"
