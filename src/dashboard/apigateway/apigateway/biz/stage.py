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

from typing import Any, Dict, List, Optional

from django.db import transaction
from django.utils.translation import gettext as _
from rest_framework import serializers

from apigateway.controller.publisher.publish import trigger_gateway_publish
from apigateway.core.constants import (
    DEFAULT_BACKEND_NAME,
    DEFAULT_STAGE_NAME,
    PublishSourceEnum,
    StageStatusEnum,
)
from apigateway.core.models import Backend, BackendConfig, Release, Stage
from apigateway.utils.time import now_datetime
from apigateway.utils.user_credentials import UserCredentials


class StageHandler:
    @staticmethod
    @transaction.atomic
    def create(data: Dict[str, Any], created_by: str) -> Stage:
        stage = Stage(
            gateway=data["gateway"],
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
                gateway=data["gateway"],
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
        stage.description = data["description"]
        stage.updated_by = updated_by
        stage.save()

        backends = {
            backend_config.backend_id: backend_config
            for backend_config in BackendConfig.objects.filter(gateway=stage.gateway, stage=stage)
        }

        now = now_datetime()
        for backend_config in data["backends"]:
            backend = backends[backend_config["id"]]
            backend.config = backend_config["config"]
            backend.updated_by = updated_by
            backend.updated_time = now

        BackendConfig.objects.bulk_update(backends.values(), fields=["config", "updated_by", "updated_time"])

        # 触发环境发布
        trigger_gateway_publish(PublishSourceEnum.STAGE_UPDATE, updated_by, stage.gateway.id, stage.id)

        return stage

    @staticmethod
    def delete(stage: Stage):
        # 删除stage CR  先删除crd，发布过程需要用到,发布过程中有用到release相关数据，这里需要同步发布
        trigger_gateway_publish(PublishSourceEnum.STAGE_DELETE, "admin", stage.gateway.id, stage.id, is_sync=True)

        with transaction.atomic():
            BackendConfig.objects.filter(gateway=stage.gateway, stage=stage).delete()

            # 2. delete release

            Release.objects.delete_by_stage_ids([stage.id])

            # 4. delete stages
            stage.delete()

    @staticmethod
    def set_status(stage: Stage, status: int, updated_by: str, user_credentials: Optional[UserCredentials] = None):
        stage.status = status
        stage.updated_by = updated_by
        stage.save()

        if status == StageStatusEnum.INACTIVE.value:
            # 触发环境发布
            trigger_gateway_publish(
                PublishSourceEnum.STAGE_DISABLE,
                updated_by,
                stage.gateway.id,
                stage.id,
                is_sync=True,
                user_credentials=user_credentials,
            )

    @staticmethod
    def delete_by_gateway_id(gateway_id):
        for stage in Stage.objects.filter(gateway_id=gateway_id):
            StageHandler.delete(stage)

    @staticmethod
    def create_default(gateway, created_by):
        """
        创建默认 stage，网关创建时，需要创建一个默认环境
        注意：
        1. 编程网关需要创建两个默认环境，一个 prod，一个 stag

        目前的返回值是创建的 prod stage 对象
        """
        stage = Stage.objects.create(
            gateway=gateway,
            name=DEFAULT_STAGE_NAME,
            description="正式环境",
            description_en="Prod",
            vars={},
            status=StageStatusEnum.INACTIVE.value,
            created_by=created_by,
            updated_by=created_by,
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

        if gateway.is_programmable:
            # create stage: stage for programmable gateway
            pre_stage = Stage.objects.create(
                gateway=gateway,
                name="stag",
                description="预发布环境",
                description_en="Stag for paas app",
                vars={},
                status=StageStatusEnum.INACTIVE.value,
                created_by=created_by,
                updated_by=created_by,
            )
            pre_backend_config = BackendConfig(
                gateway=gateway,
                backend=backend,
                stage=pre_stage,
                config={
                    "type": "node",
                    "timeout": 30,
                    "loadbalance": "roundrobin",
                    "hosts": [{"scheme": "http", "host": "", "weight": 100}],
                },
            )
            pre_backend_config.save()

        return stage

    @staticmethod
    def get_stage_ids(gateway, stage_names: List[str]) -> List[int]:
        name_to_id_map = Stage.objects.get_name_id_map(gateway)

        # 如果未指定 stage_names，则默认处理网关下所有环境
        if not stage_names:
            return list(name_to_id_map.values())

        stage_ids = set()
        for stage_name in stage_names:
            if stage_name not in name_to_id_map:
                raise serializers.ValidationError(
                    {"stage_names": _("环境【{stage_name}】不存在。").format(stage_name=stage_name)}
                )
            stage_ids.add(name_to_id_map[stage_name])
        return list(stage_ids)
