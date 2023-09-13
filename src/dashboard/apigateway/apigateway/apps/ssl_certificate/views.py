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
from django.db import transaction
from django.db.models import Q
from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets

from apigateway.apps.ssl_certificate import serializers
from apigateway.core.models import SslCertificate, SslCertificateBinding
from apigateway.utils.crypto import CertificateChecker
from apigateway.utils.responses import OKJsonResponse


@method_decorator(
    name="retrieve",
    decorator=swagger_auto_schema(
        tags=["WebAPI.SSLCertificate"],
        responses={status.HTTP_200_OK: serializers.SSLCertificateSLZ},
        operation_description="retrieve ssl certificate",
    ),
)
@method_decorator(
    name="create",
    decorator=swagger_auto_schema(
        tags=["WebAPI.SSLCertificate"],
        request_body=serializers.SSLCertificateSLZ,
        responses={status.HTTP_200_OK: serializers.SSLCertificateSLZ},
        operation_description="create ssl certificate",
    ),
)
@method_decorator(
    name="update",
    decorator=swagger_auto_schema(
        tags=["WebAPI.SSLCertificate"],
        request_body=serializers.SSLCertificateSLZ,
        responses={status.HTTP_200_OK: serializers.SSLCertificateSLZ},
        operation_description="update ssl certificate",
    ),
)
@method_decorator(
    name="destroy",
    decorator=swagger_auto_schema(
        tags=["WebAPI.SSLCertificate"],
        responses={status.HTTP_200_OK: ""},
        operation_description="delete ssl certificate",
    ),
)
class SSLCertificateViewSet(viewsets.ModelViewSet):
    lookup_field = "id"
    serializer_class = serializers.SSLCertificateSLZ

    def get_queryset(self):
        return SslCertificate.objects.filter(gateway=self.request.gateway)

    @swagger_auto_schema(
        query_serializer=serializers.QuerySSLCertificateSLZ,
        responses={status.HTTP_200_OK: serializers.ListSSLCertificateSLZ(many=True)},
        tags=["WebAPI.SSLCertificate"],
    )
    def list(self, request, *args, **kwargs):
        slz = serializers.QuerySSLCertificateSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        queryset = self.get_queryset()
        queryset = queryset.filter(type=data["type"])
        if data.get("query"):
            queryset = queryset.filter(Q(name__contains=data["query"]) | Q(snis__contains=data["query"]))
        queryset = queryset.order_by(data.get("order_by") or "-updated_time")

        page = self.paginate_queryset(queryset)

        slz = serializers.ListSSLCertificateSLZ(page, many=True)
        return self.get_paginated_response(slz.data)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user.username, updated_by=self.request.user.username)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user.username)

    def perform_destroy(self, instance):
        SslCertificate.objects.delete_by_id(instance.id)


class SSLCertificateBindScopesViewSet(viewsets.ModelViewSet):
    lookup_field = "id"

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: ""},
        request_body=serializers.BindOrUnbindScopesSLZ,
        tags=["WebAPI.SSLCertificate"],
    )
    @transaction.atomic
    def bind(self, request, *args, **kwargs):
        """证书，绑定 scope 对象"""
        slz = serializers.BindOrUnbindScopesSLZ(data=request.data, context={"gateway_id": self.request.gateway.id})
        slz.is_valid(raise_exception=True)

        for scope_id in slz.validated_data["scope_ids"]:
            binding, created = SslCertificateBinding.objects.update_or_create(
                gateway=self.request.gateway,
                scope_type=slz.validated_data["scope_type"],
                scope_id=scope_id,
                ssl_certificate_id=slz.validated_data["ssl_certificate_id"],
                defaults={
                    "updated_by": request.user.username,
                },
            )
            if created:
                binding.created_by = request.user.username
                binding.save(update_fields=["created_by"])

        # 仅绑定用户当前指定的对象，删除未指定的绑定
        SslCertificateBinding.objects.filter(
            gateway=self.request.gateway,
            scope_type=slz.validated_data["scope_type"],
            ssl_certificate_id=slz.validated_data["ssl_certificate_id"],
        ).exclude(scope_id__in=slz.validated_data["scope_ids"]).delete()

        return OKJsonResponse()

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: ""},
        request_body=serializers.BindOrUnbindScopesSLZ,
        tags=["WebAPI.SSLCertificate"],
    )
    @transaction.atomic
    def unbind(self, request, *args, **kwargs):
        """证书，解绑 scope 对象"""
        slz = serializers.BindOrUnbindScopesSLZ(data=request.data, context={"gateway_id": self.request.gateway.id})
        slz.is_valid(raise_exception=True)

        SslCertificateBinding.objects.filter(
            gateway=self.request.gateway,
            ssl_certificate_id=slz.validated_data["ssl_certificate_id"],
            scope_type=slz.validated_data["scope_type"],
            scope_id__in=slz.validated_data["scope_ids"],
        ).delete()

        return OKJsonResponse()

    @swagger_auto_schema(
        query_serializer=serializers.QuerySSLCertificateBindingSLZ,
        responses={status.HTTP_200_OK: serializers.ListSSLCertificateBindingSLZ(many=True)},
        tags=["WebAPI.SSLCertificate"],
    )
    def list(self, request, *args, **kwargs):
        slz = serializers.QuerySSLCertificateBindingSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        queryset = SslCertificateBinding.objects.filter(
            gateway=self.request.gateway, scope_type=slz.validated_data["scope_type"]
        )
        if slz.validated_data.get("scope_id"):
            queryset = queryset.filter(scope_id=slz.validated_data["scope_id"])
        if slz.validated_data.get("ssl_certificate_id"):
            queryset = queryset.filter(ssl_certificate_id=slz.validated_data["ssl_certificate_id"])

        queryset = queryset.values("scope_type", "scope_id", "ssl_certificate_id")
        page = self.paginate_queryset(queryset)

        serializer = serializers.ListSSLCertificateBindingSLZ(page, many=True)
        return self.get_paginated_response(serializer.data)


class ScopeBindSSLCertificateViewSet(viewsets.ViewSet):
    @swagger_auto_schema(
        responses={status.HTTP_200_OK: ""},
        request_body=serializers.BindOrUnbindSSLCertificatesSLZ,
        tags=["WebAPI.SSLCertificate"],
    )
    @transaction.atomic
    def bind(self, request, *args, **kwargs):
        """scope 对象，绑定证书"""
        slz = serializers.BindOrUnbindSSLCertificatesSLZ(
            data=request.data, context={"gateway_id": self.request.gateway.id}
        )
        slz.is_valid(raise_exception=True)

        valid_scope_id = slz.validated_data["scope_id"]
        for ssl_certificate_id in slz.validated_data["ssl_certificate_ids"]:
            binding, created = SslCertificateBinding.objects.update_or_create(
                gateway=self.request.gateway,
                scope_type=slz.validated_data["scope_type"],
                scope_id=valid_scope_id,
                ssl_certificate_id=ssl_certificate_id,
                defaults={
                    "updated_by": request.user.username,
                },
            )
            if created:
                binding.created_by = request.user.username
                binding.save(update_fields=["created_by"])

        # 仅绑定用户当前指定的对象，删除未指定的绑定
        SslCertificateBinding.objects.filter(
            gateway=self.request.gateway,
            scope_type=slz.validated_data["scope_type"],
            scope_id=valid_scope_id,
        ).exclude(ssl_certificate_id__in=slz.validated_data["ssl_certificate_ids"]).delete()

        return OKJsonResponse()

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: ""},
        request_body=serializers.BindOrUnbindSSLCertificatesSLZ,
        tags=["WebAPI.SSLCertificate"],
    )
    @transaction.atomic
    def unbind(self, request, *args, **kwargs):
        """scope 对象，解绑证书"""
        slz = serializers.BindOrUnbindSSLCertificatesSLZ(
            data=request.data, context={"gateway_id": self.request.gateway.id}
        )
        slz.is_valid(raise_exception=True)

        SslCertificateBinding.objects.filter(
            gateway=self.request.gateway,
            scope_type=slz.validated_data["scope_type"],
            scope_id=slz.validated_data["scope_id"],
            ssl_certificate_id__in=slz.validated_data["ssl_certificate_ids"],
        ).delete()

        return OKJsonResponse()


class CheckCertViewSet(viewsets.ViewSet):
    @swagger_auto_schema(
        request_body=serializers.CheckCertSLZ,
        responses={status.HTTP_200_OK: ""},
        tags=["SslCertificate"],
    )
    def check_cert(self, request, *args, **kwargs):
        slz = serializers.CheckCertSLZ(data=request.data)
        slz.is_valid(raise_exception=True)

        checker = CertificateChecker(**slz.validated_data)
        return OKJsonResponse(data=checker.check())
