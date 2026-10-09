#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) Tencent. All rights reserved.
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
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status

from apigateway.apis.web.docs.gateway.mixins import GatewayDocsPermissionMixin
from apigateway.apps.permission.constants import GrantDimensionEnum, PermissionApplyExpireDaysEnum
from apigateway.biz.permission import PermissionDimensionManager
from apigateway.biz.resource_version import ResourceVersionHandler
from apigateway.common.error_codes import error_codes
from apigateway.common.tenant.constants import TenantModeEnum
from apigateway.common.tenant.request import get_user_tenant_id
from apigateway.components.bkauth import get_app_tenant_info
from apigateway.components.bkpaas import get_paas_apps_by_username
from apigateway.service.bk_itsm import ItsmPermissionApplyHelper
from apigateway.utils.responses import OKJsonResponse

from .serializers import GatewayPermissionApplyInputSLZ, GatewayPermissionApplyOutputSLZ


@method_decorator(
    name="post",
    decorator=extend_schema(
        description="从 API 文档申请网关资源权限",
        request=GatewayPermissionApplyInputSLZ,
        responses={
            status.HTTP_201_CREATED: GatewayPermissionApplyOutputSLZ(),
            status.HTTP_409_CONFLICT: {"type": "object", "additionalProperties": True},
        },
        tags=["WebAPI.Docs.Permission"],
    ),
)
class GatewayPermissionApplyCreateApi(GatewayDocsPermissionMixin, generics.CreateAPIView):
    serializer_class = GatewayPermissionApplyInputSLZ

    def create(self, request, *args, **kwargs):
        slz = self.get_serializer(data=request.data)
        slz.is_valid(raise_exception=True)
        data = slz.validated_data

        bk_app_code = data["bk_app_code"]
        user_tenant_id = get_user_tenant_id(request)
        apps = get_paas_apps_by_username(request.user.username, user_tenant_id)
        if bk_app_code not in {app.get("code") for app in apps}:
            raise error_codes.INVALID_ARGUMENT.format(_("请选择当前用户有权限的蓝鲸应用。"))

        gateway = request.gateway
        if settings.ENABLE_MULTI_TENANT_MODE and gateway.tenant_mode != TenantModeEnum.GLOBAL.value:
            app_tenant_mode, app_tenant_id = get_app_tenant_info(bk_app_code)
            if app_tenant_mode != TenantModeEnum.GLOBAL.value and app_tenant_id != gateway.tenant_id:
                raise error_codes.NO_PERMISSION.format(
                    _("应用【{bk_app_code}】不属于网关【{gateway_name}】所在租户，不能申请该网关资源权限。").format(
                        bk_app_code=bk_app_code,
                        gateway_name=gateway.name,
                    ),
                    replace=True,
                )

        resource = self._get_applicable_resource(gateway.id, data["resource_name"])
        manager = PermissionDimensionManager.get_manager(GrantDimensionEnum.RESOURCE.value)
        record = manager.apply_permission(
            bk_app_code=bk_app_code,
            gateway=gateway,
            resource_ids=[resource["id"]],
            grant_dimension=GrantDimensionEnum.RESOURCE.value,
            reason=data["reason"],
            expire_days=PermissionApplyExpireDaysEnum.FOREVER.value,
            username=request.user.username,
        )

        output_slz = GatewayPermissionApplyOutputSLZ(
            {
                "record_id": record.id,
                "bk_app_code": bk_app_code,
                "gateway_name": gateway.name,
                "resource_name": resource["name"],
                "itsm_ticket_id": record.itsm_ticket_id or "",
                "itsm_ticket_url": ItsmPermissionApplyHelper.build_ticket_url(record.itsm_ticket_id),
            }
        )
        return OKJsonResponse(status=status.HTTP_201_CREATED, data=output_slz.data)

    @staticmethod
    def _get_applicable_resource(gateway_id: int, resource_name: str) -> Dict[str, Any]:
        resources = ResourceVersionHandler.get_released_public_resources(gateway_id)
        for resource in resources:
            if resource["name"] != resource_name:
                continue

            if (
                resource["app_verified_required"]
                and resource["resource_perm_required"]
                and resource["allow_apply_permission"]
            ):
                return resource
            break

        raise error_codes.NOT_FOUND.format(
            _("请检查资源是否已发布、公开、启用应用权限校验并允许申请权限。"),
            replace=True,
        )
