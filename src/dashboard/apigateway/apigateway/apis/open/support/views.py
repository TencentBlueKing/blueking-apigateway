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

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets

from apigateway.apis.open.permissions import (
    OpenAPIGatewayRelatedAppPermission,
)
from apigateway.apis.open.support import serializers
from apigateway.apps.support.api_sdk import exceptions
from apigateway.apps.support.api_sdk.helper import SDKHelper
from apigateway.common.error_codes import error_codes
from apigateway.core.models import ResourceVersion
from apigateway.utils.responses import V1OKJsonResponse

logger = logging.getLogger(__name__)


class SDKGenerateViewSet(viewsets.ViewSet):
    permission_classes = [OpenAPIGatewayRelatedAppPermission]

    @transaction.atomic
    @swagger_auto_schema(
        # todo: 是否需要将 support 改成 sdk？目前只有 sdk 相关的
        tags=["OpenAPI.Support"],
    )
    def generate(self, request, gateway_name: str, *args, **kwargs):
        """创建资源版本对应的 SDK"""

        slz = serializers.SDKGenerateV1SLZ(data=request.data)
        slz.is_valid(raise_exception=True)

        resource_version = get_object_or_404(
            ResourceVersion, gateway=request.gateway, version=slz.data["resource_version"]
        )
        results = []
        with SDKHelper(resource_version=resource_version) as helper:
            for language in slz.data["languages"]:
                try:
                    info = helper.create(
                        language=language,
                        version=slz.data["version"] or resource_version.version,
                        operator=None,
                    )
                    results.append(
                        {
                            "name": info.sdk.name,
                            "version": info.sdk.version_number,
                            "url": info.sdk.url,
                        }
                    )
                except exceptions.ResourcesIsEmpty:
                    raise error_codes.INTERNAL.format(_("网关下无资源，无法生成 SDK。"), replace=True)
                except exceptions.GenerateError:
                    raise error_codes.INTERNAL.format(_("网关 SDK 生成失败，请联系管理员。"), replace=True)
                except exceptions.PackError:
                    raise error_codes.INTERNAL.format(_("网关 SDK 打包失败，请联系管理员。"), replace=True)
                except exceptions.DistributeError:
                    raise error_codes.INTERNAL.format(_("网关 SDK 发布失败，请联系管理员。"), replace=True)
                except exceptions.TooManySDKVersion as err:
                    raise error_codes.INTERNAL.format(
                        _("同一资源版本，最多只能生成 {count} 个 SDK。").format(count=err.max_count), replace=True
                    )
                except Exception:
                    logger.exception(
                        "create sdk failed for gateway %s, release %s", gateway_name, resource_version.version
                    )
                    raise error_codes.INTERNAL.format(_("网关 SDK 创建失败，请联系管理员。"), replace=True)

        return V1OKJsonResponse("OK", data=results)
