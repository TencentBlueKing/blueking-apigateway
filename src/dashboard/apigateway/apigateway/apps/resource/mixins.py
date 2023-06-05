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
from typing import Any, Dict

from django.conf import settings
from django.utils.translation import gettext as _

from apigateway.apps.audit.constants import OpObjectTypeEnum, OpStatusEnum, OpTypeEnum
from apigateway.apps.audit.utils import record_audit_log
from apigateway.apps.resource import serializers
from apigateway.biz.resource import ResourceHandler
from apigateway.common.error_codes import error_codes
from apigateway.core.models import Gateway, Resource


class CreateResourceMixin:
    def _create_resource(self, gateway: Gateway, data: Dict[str, Any], username: str) -> Resource:
        slz = serializers.ResourceSLZ(data=data, context={"api": gateway})
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        # 检查网关的资源数量是否超限
        self._check_gateway_resource_limit(gateway)

        # 1. save resource, proxy_id can't be null, set a default value
        slz.save(
            proxy_id=0,
            created_by=username,
            updated_by=username,
        )

        # 2. create resource related data
        proxy_configs = data["proxy_configs"]
        ResourceHandler().save_related_data(
            gateway,
            slz.instance,
            proxy_type=data["proxy_type"],
            backend_config_type=proxy_configs.get("backend_config_type"),
            backend_service_id=proxy_configs.get("backend_service_id"),
            proxy_config=proxy_configs[data["proxy_type"]],
            auth_config=data["auth_config"],
            label_ids=data.get("label_ids", []),
            disabled_stage_ids=data.get("disabled_stage_ids", []),
        )

        # 3. record audit log
        record_audit_log(
            username=username,
            op_type=OpTypeEnum.CREATE.value,
            op_status=OpStatusEnum.SUCCESS.value,
            op_object_group=gateway.id,
            op_object_type=OpObjectTypeEnum.RESOURCE.value,
            op_object_id=slz.instance.id,
            op_object=slz.instance.identity,
            comment=_("创建资源"),
        )

        return slz.instance

    def _check_gateway_resource_limit(self, gateway: Gateway):
        max_resource_per_gateway = settings.API_GATEWAY_RESOURCE_LIMITS["gateway_resource_whitelist"].get(
            gateway.name, settings.API_GATEWAY_RESOURCE_LIMITS["max_resource_per_gateway"]
        )
        if Resource.objects.filter(api_id=gateway.id).count() >= max_resource_per_gateway:
            raise error_codes.VALIDATE_ERROR.format(
                f"The gateway [{gateway.name}] exceeds the limit of the number of resources that can be created."
                + f" The maximum limit is {max_resource_per_gateway}."
            )


class UpdateResourceMixin:
    def _update_resource(self, gateway: Gateway, instance: Resource, data: Dict[str, Any], username: str):
        slz = serializers.ResourceSLZ(instance, data=data, context={"api": gateway})
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        # 1. save resource
        slz.save(updated_by=username)

        # 2. save resource extend
        proxy_configs = data["proxy_configs"]
        ResourceHandler().save_related_data(
            gateway,
            instance,
            proxy_type=data["proxy_type"],
            backend_config_type=proxy_configs.get("backend_config_type"),
            backend_service_id=proxy_configs.get("backend_service_id"),
            proxy_config=proxy_configs[data["proxy_type"]],
            auth_config=data["auth_config"],
            label_ids=data.get("label_ids", []),
            disabled_stage_ids=data.get("disabled_stage_ids", []),
        )

        record_audit_log(
            username=username,
            op_type=OpTypeEnum.MODIFY.value,
            op_status=OpStatusEnum.SUCCESS.value,
            op_object_group=gateway.id,
            op_object_type=OpObjectTypeEnum.RESOURCE.value,
            op_object_id=slz.instance.id,
            op_object=slz.instance.identity,
            comment=_("更新资源"),
        )
