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
from django.urls import path

from apigateway.apps.ssl_certificate.views import (
    CheckCertViewSet,
    ScopeBindSSLCertificateViewSet,
    SSLCertificateBindScopesViewSet,
    SSLCertificateViewSet,
)

urlpatterns = [
    path("", SSLCertificateViewSet.as_view({"get": "list", "post": "create"}), name="apigateway.apps.ssl_certificate"),
    path(
        "<int:id>/",
        SSLCertificateViewSet.as_view({"get": "retrieve", "put": "update", "delete": "destroy"}),
        name="apigateway.apps.ssl_certificate.detail",
    ),
    # binding
    path(
        "bindings/",
        SSLCertificateBindScopesViewSet.as_view({"get": "list"}),
        name="ssl_certificates.binding",
    ),
    path(
        "bindings/scopes/",
        SSLCertificateBindScopesViewSet.as_view({"post": "bind", "delete": "unbind"}),
        name="ssl_certificates.binding.scope",
    ),
    path(
        "bindings/ssl-certificates/",
        ScopeBindSSLCertificateViewSet.as_view({"post": "bind", "delete": "unbind"}),
        name="ssl_certificates.binding.ssl_certificate",
    ),
    # check cert
    path(
        "check-cert/",
        CheckCertViewSet.as_view({"post": "check_cert"}),
        name="ssl_certificates.check_cert",
    ),
]
