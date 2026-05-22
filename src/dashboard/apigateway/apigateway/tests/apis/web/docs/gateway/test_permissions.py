# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2025 Tencent. All rights reserved.
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
from rest_framework.permissions import IsAuthenticated

from apigateway.apis.web.docs.gateway.gateway.views import GatewayRetrieveApi
from apigateway.apis.web.docs.gateway.gateway_sdk.views import SDKListApi, SDKUsageExampleApi
from apigateway.apis.web.docs.gateway.resource.doc.views import DocRetrieveApi
from apigateway.apis.web.docs.gateway.resource.views import ResourceListApi
from apigateway.apis.web.docs.gateway.stage.views import StageListApi
from apigateway.common.permissions import GatewayDisplayablePermission


class TestDocsGatewayPermissionClasses:
    def test_permission_classes_contains_authenticated(self):
        view_classes = [
            GatewayRetrieveApi,
            SDKListApi,
            SDKUsageExampleApi,
            DocRetrieveApi,
            ResourceListApi,
            StageListApi,
        ]

        for view_class in view_classes:
            assert IsAuthenticated in view_class.permission_classes
            assert GatewayDisplayablePermission in view_class.permission_classes
