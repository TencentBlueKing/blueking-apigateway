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

from typing import Any, Dict, Optional

from django.utils.translation import gettext as _
from django.db import transaction

from apigateway.apps.access_strategy.constants import AccessStrategyBindScopeEnum
from apigateway.apps.access_strategy.models import AccessStrategyBinding
from apigateway.core.constants import DEFAULT_BACKEND_NAME, DEFAULT_STAGE_NAME, StageStatusEnum
from apigateway.core.models import Backend, MicroGateway, Release, ReleaseHistory, Stage, BackendConfig
from apigateway.utils.time import now_datetime


class StageHandler:
    @staticmethod
    @transaction.atomic
    def create(data: Dict[str, Any], created_by: str) -> Stage:
        stage = Stage(
            api=data["api"],
            name=data["name"],
            description=data["description"],
            created_by=created_by,
            updated_by=created_by,
        )
        stage.save()

        # 创建后端配置
        backend_configs = []
        for backend in data["backends"]:
            backend_config = BackendConfig(
                gateway=data["api"],
                backend_id=backend["id"],
                stage=stage,
                config=backend["config"],
                created_by=created_by,
                updated_by=created_by,
            )
            backend_configs.append(backend_config)

        BackendConfig.objects.bulk_create(backend_configs)

        return stage

    @staticmethod
    @transaction.atomic
    def update(stage: Stage, data: Dict[str, Any], updated_by: str) -> Stage:
        stage.name = data["name"]
        stage.description = data["description"]
        stage.updated_by = updated_by
        stage.save()

        backends = {
            backend_config.backend_id: backend_config
            for backend_config in BackendConfig.objects.filter(gateway=stage.api, stage=stage)
        }

        for backend_config in data["backends"]:
            backend = backends[backend_config["id"]]
            backend.config = backend_config["config"]
            backend.updated_by = updated_by

        BackendConfig.objects.bulk_update(backends.values(), fields=["config", "updated_by"])

        return stage

    @staticmethod
    def delete(stage: Stage):
        with transaction.atomic():
            BackendConfig.objects.filter(gateway=stage.api, stage=stage).delete()

            # 2. delete release

            Release.objects.delete_by_stage_ids([stage.id])

            # 4. delete stages
            stage.delete()

            # 5. delete release-history

            ReleaseHistory.objects.delete_without_stage_related(stage.api.id)

        # TODO 删除stage CR

    @staticmethod
    def set_status(stage: Stage, status: int, updated_by: str):
        stage.status = status
        stage.updated_by = updated_by
        stage.save()

        # TODO 下架/上架发布

    @staticmethod
    def delete_by_gateway_id(gateway_id):
        for stage in Stage.objects.filter(api_id=gateway_id):
            StageHandler.delete(stage)

    @staticmethod
    def create_default(gateway, created_by):
        """
        创建默认 stage，网关创建时，需要创建一个默认环境
        """
        stage = Stage.objects.create(
            api=gateway,
            name=DEFAULT_STAGE_NAME,
            description="正式环境",
            description_en="Prod",
            vars={},
            status=StageStatusEnum.INACTIVE.value,
            created_by=created_by,
            updated_by=created_by,
            created_time=now_datetime(),
            updated_time=now_datetime(),
        )

        backend = Backend.objects.create(
            gateway=gateway,
            name=DEFAULT_BACKEND_NAME,
        )

        backend_config = BackendConfig(
            gateway=gateway,
            backend=backend,
            stage=stage,
            config={
                "type": "node",
                "timeout": 30,
                "loadbalance": "roundrobin",
                "hosts": [{"scheme": "http", "host": "", "weight": 100}],
            },
        )
        backend_config.save()

        return stage

    # TODO: move into get_id_to_micro_gateway_fields?
    @staticmethod
    def get_id_to_micro_gateway_id(gateway_id: int) -> Dict[int, Optional[str]]:
        return dict(Stage.objects.filter(api_id=gateway_id).values_list("id", "micro_gateway_id"))

    @staticmethod
    def get_id_to_micro_gateway_fields(gateway_id: int) -> Dict[int, Optional[Dict[str, Any]]]:
        id_to_micro_gateway_id = StageHandler().get_id_to_micro_gateway_id(gateway_id)
        result: Dict[int, Optional[Dict[str, Any]]] = {i: None for i in id_to_micro_gateway_id}

        valid_micro_gateway_ids = set(i for i in id_to_micro_gateway_id.values() if i is not None)
        if not valid_micro_gateway_ids:
            return result

        micro_gateway_id_to_fields = MicroGateway.objects.get_id_to_fields(valid_micro_gateway_ids)
        for id_, micro_gateway_id in id_to_micro_gateway_id.items():
            if micro_gateway_id is not None:
                result[id_] = micro_gateway_id_to_fields.get(micro_gateway_id)

        return result
