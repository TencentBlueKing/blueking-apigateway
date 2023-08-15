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

from django.conf import settings
from django.utils.translation import gettext as _

from apigateway.apps.audit.constants import OpObjectTypeEnum, OpStatusEnum, OpTypeEnum
from apigateway.apps.audit.utils import record_audit_log
from apigateway.apps.plugin.constants import PluginBindingScopeEnum
from apigateway.common.contexts import StageProxyHTTPContext, StageRateLimitContext
from apigateway.common.plugin.header_rewrite import HeaderRewriteConvertor
from apigateway.core.constants import DEFAULT_STAGE_NAME, ContextScopeTypeEnum, StageStatusEnum
from apigateway.core.models import Context, MicroGateway, Release, ReleaseHistory, Stage
from apigateway.utils.time import now_datetime


class StageHandler:
    @staticmethod
    def delete_by_gateway_id(gateway_id):
        stage_ids = list(Stage.objects.filter(api_id=gateway_id).values_list("id", flat=True))
        if not stage_ids:
            return

        StageHandler().delete_stages(gateway_id, stage_ids)

    @staticmethod
    def delete_stages(gateway_id, stage_ids):
        # 1. delete proxy http config/rate-limit config

        Context.objects.delete_by_scope_ids(
            scope_type=ContextScopeTypeEnum.STAGE.value,
            scope_ids=stage_ids,
        )

        # 2. delete release

        Release.objects.delete_by_stage_ids(stage_ids)

        # 4. delete stages
        Stage.objects.filter(id__in=stage_ids).delete()

        # 5. delete release-history

        ReleaseHistory.objects.delete_without_stage_related(gateway_id)

    @staticmethod
    def save_related_data(stage, proxy_http_config: dict, rate_limit_config: Optional[dict]):
        # 1. save proxy http config
        StageProxyHTTPContext().save(stage.id, proxy_http_config)

        # 2. save rate-limit config
        if rate_limit_config is not None:
            StageRateLimitContext().save(stage.id, rate_limit_config)

        # 3. create or update header rewrite plugin config
        stage_transform_headers = proxy_http_config.get("transform_headers") or {}
        stage_config = HeaderRewriteConvertor.transform_headers_to_plugin_config(stage_transform_headers)
        HeaderRewriteConvertor.alter_plugin(stage.api_id, PluginBindingScopeEnum.STAGE.value, stage.id, stage_config)

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

        # 保存关联数据
        StageHandler().save_related_data(
            stage,
            proxy_http_config={
                "timeout": 30,
                "upstreams": settings.DEFAULT_STAGE_UPSTREAMS,
                "transform_headers": {
                    "set": {},
                    "delete": [],
                },
            },
            rate_limit_config=settings.DEFAULT_STAGE_RATE_LIMIT_CONFIG,
        )

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

    @staticmethod
    def add_create_audit_log(gateway, stage, username: str):
        record_audit_log(
            username=username,
            op_type=OpTypeEnum.CREATE.value,
            op_status=OpStatusEnum.SUCCESS.value,
            op_object_group=gateway.id,
            op_object_type=OpObjectTypeEnum.STAGE.value,
            op_object_id=stage.id,
            op_object=stage.name,
            comment=_("创建环境"),
        )

    @staticmethod
    def add_update_audit_log(gateway, stage, username: str):
        record_audit_log(
            username=username,
            op_type=OpTypeEnum.MODIFY.value,
            op_status=OpStatusEnum.SUCCESS.value,
            op_object_group=gateway.id,
            op_object_type=OpObjectTypeEnum.STAGE.value,
            op_object_id=stage.id,
            op_object=stage.name,
            comment=_("更新环境"),
        )
