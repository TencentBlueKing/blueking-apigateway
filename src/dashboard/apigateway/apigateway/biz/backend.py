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
from typing import Any, Dict

from django.db import transaction

from apigateway.core.models import Backend, BackendConfig


class BackendHandler:
    @staticmethod
    @transaction.atomic
    def create(data: Dict[str, Any], created_by: str) -> Backend:
        """创建后端服务"""
        backend = Backend(
            gateway=data["gateway"],
            type=data["type"],
            name=data["name"],
            description=data["description"],
            created_by=created_by,
            updated_by=created_by,
        )
        backend.save()

        backend_configs = []
        for config in data["configs"]:
            backend_config = BackendConfig(
                gateway=data["gateway"],
                backend_id=backend.id,
                stage_id=config["stage_id"],
                config={key: value for key, value in config.items() if key != "stage_id"},
                created_by=created_by,
                updated_by=created_by,
            )
            backend_configs.append(backend_config)

        BackendConfig.objects.bulk_create(backend_configs)

        return backend

    @staticmethod
    @transaction.atomic
    def update(backend: Backend, data: Dict[str, Any], updated_by: str) -> Backend:
        """更新后端服务"""
        backend.type = data["type"]
        backend.name = data["name"]
        backend.description = data["description"]
        backend.updated_by = updated_by
        backend.save()

        backend_configs = BackendConfig.objects.filter(backend_id=backend.id)
        stage_configs = {config.stage_id: config for config in backend_configs}

        backend_configs = []
        for config in data["configs"]:
            backend_config = stage_configs[config["stage_id"]]
            backend_config.config = {key: value for key, value in config.items() if key != "stage_id"}
            backend_config.updated_by = updated_by

            backend_configs.append(backend_config)

        BackendConfig.objects.bulk_update(backend_configs, fields=["config", "updated_by"])

        return backend
