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
import logging

from django.core.management.base import BaseCommand
from django.db import transaction

from apigateway.core.constants import DEFAULT_BACKEND_NAME
from apigateway.core.models import Backend, BackendConfig, Gateway, Stage
from apigateway.utils.django import get_object_or_None

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """新增环境

    如果环境不存在，则创建环境
    如果环境已存在，则跳过
    """

    def add_arguments(self, parser):
        parser.add_argument("--gateway", dest="gateway_name", required=True, help="gateway name")
        parser.add_argument("--name", type=str, dest="name", required=True)

    @transaction.atomic
    def handle(self, gateway_name: str, name: str, **options):
        gateway = Gateway.objects.get(name=gateway_name)
        stage = get_object_or_None(Stage, gateway=gateway, name=name)

        if stage:
            print(f"Stage [name={name}] exists and ignore")
            return

        stage = Stage(
            gateway=gateway,
            name=name,
            created_by="admin",
            updated_by="admin",
        )
        stage.save()

        backend, _ = Backend.objects.get_or_create(
            gateway=gateway,
            name=DEFAULT_BACKEND_NAME,
        )

        config = {
            "type": "node",
            "timeout": {"connect": 60, "read": 60, "send": 60},
            "loadbalance": "roundrobin",
            "hosts": [{"scheme": "http", "host": "0.0.0.1", "weight": 100}],
        }
        backend_config = BackendConfig(
            gateway=gateway,
            backend=backend,
            stage=stage,
            config=config,
        )
        backend_config.save()

        logger.info("Add stage [name=%s] success", name)
