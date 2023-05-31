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
from rest_framework import viewsets

from apigateway.apis.open.monitor import serializers
from apigateway.apps.monitor.constants import AlarmTypeEnum
from apigateway.apps.monitor.tasks import monitor_app_request, monitor_nginx_error, monitor_resource_backend
from apigateway.common.error_codes import error_codes
from apigateway.utils.responses import OKJsonResponse


class AlarmCallbackViewSet(viewsets.ViewSet):
    def callback(self, request, alarm_type: str, *args, **kwargs):
        slz = serializers.MonitorCallbackSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        if alarm_type == AlarmTypeEnum.RESOURCE_BACKEND.value:
            monitor_resource_backend.apply_async(args=(request.data,))
        elif alarm_type == AlarmTypeEnum.APP_REQUEST.value:
            monitor_app_request.apply_async(args=(request.data,))
        elif alarm_type == AlarmTypeEnum.NGINX_ERROR.value:
            monitor_nginx_error.apply_async(args=(request.data,))
        else:
            raise error_codes.INVALID_ARGS.format(f"不支持告警类型 {alarm_type}")

        return OKJsonResponse("OK")
