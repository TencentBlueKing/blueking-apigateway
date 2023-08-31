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
import operator

from django.db import transaction
from django.utils.translation import gettext as _
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets

from apigateway.apps.audit.constants import OpObjectTypeEnum, OpStatusEnum, OpTypeEnum
from apigateway.apps.audit.utils import record_audit_log
from apigateway.apps.label.models import ResourceLabel
from apigateway.apps.resource import serializers
from apigateway.apps.resource.importer import ResourcesImporter
from apigateway.apps.resource.mixins import CreateResourceMixin, UpdateResourceMixin
from apigateway.apps.resource.swagger.swagger import ResourceSwaggerExporter
from apigateway.apps.support.models import ResourceDoc
from apigateway.biz.released_resource import get_resource_released_stage_count, get_resource_released_stages
from apigateway.biz.resource import ResourceHandler
from apigateway.biz.resource_url import ResourceURLHandler
from apigateway.common.contexts import ResourceAuthContext
from apigateway.core.models import Proxy, Resource, ResourceVersion, Stage, StageResourceDisabled
from apigateway.core.utils import get_resource_url
from apigateway.utils.responses import DownloadableResponse, V1OKJsonResponse
from apigateway.utils.swagger import PaginatedResponseSwaggerAutoSchema
from apigateway.utils.time import now_datetime


class BaseResourceViewSet(viewsets.ModelViewSet):
    lookup_field = "id"

    def get_queryset(self):
        return Resource.objects.filter(api=self.request.gateway)


class ResourceViewSet(BaseResourceViewSet, CreateResourceMixin, UpdateResourceMixin):
    serializer_class = serializers.ResourceSLZ

    @swagger_auto_schema(
        auto_schema=PaginatedResponseSwaggerAutoSchema,
        query_serializer=serializers.QueryResourceSLZ,
        responses={status.HTTP_200_OK: serializers.ListResourceSLZ(many=True)},
        tags=["Resource"],
    )
    def list(self, request, *args, **kwargs):
        slz = serializers.QueryResourceSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        queryset = ResourceHandler().filter_resource(
            gateway=request.gateway,
            query=data.get("query"),
            path=data.get("path"),
            method=data.get("method"),
            label_name=data.get("label_name"),
            order_by=data.get("order_by") or "-id",
            fuzzy=True,
        )
        page = self.paginate_queryset(queryset)

        resource_ids = [resource.id for resource in page]

        serializer = serializers.ListResourceSLZ(
            page,
            many=True,
            context={
                "resource_labels": ResourceLabel.objects.get_labels(resource_ids),
                "latest_resource_version": ResourceVersion.objects.get_latest_version(request.gateway.id),
                "resource_released_stage_count": get_resource_released_stage_count(request.gateway.id, resource_ids),
                "stage_count": Stage.objects.filter(api_id=request.gateway.id).count(),
                "doc_languages_of_resources": ResourceDoc.objects.get_doc_languages_of_resources(
                    gateway_id=request.gateway.id, resource_ids=resource_ids
                ),
            },
        )
        return V1OKJsonResponse("OK", data=self.paginator.get_paginated_data(serializer.data))

    @swagger_auto_schema(responses={status.HTTP_200_OK: ""}, request_body=serializers.ResourceSLZ, tags=["Resource"])
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        # 检查网关资源是否超限
        self._check_gateway_resource_limit(request.gateway)

        instance = self._create_resource(
            gateway=request.gateway,
            data=request.data,
            username=request.user.username,
        )

        return V1OKJsonResponse("OK", data={"id": instance.id})

    @swagger_auto_schema(responses={status.HTTP_200_OK: serializers.ResourceSLZ()}, tags=["Resource"])
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        slz = self.get_serializer(instance)
        return V1OKJsonResponse("OK", data=slz.data)

    @swagger_auto_schema(responses={status.HTTP_200_OK: ""}, request_body=serializers.ResourceSLZ, tags=["Resource"])
    @transaction.atomic
    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        self._update_resource(
            gateway=request.gateway,
            instance=instance,
            data=request.data,
            username=request.user.username,
        )

        return V1OKJsonResponse("OK")

    @swagger_auto_schema(responses={status.HTTP_200_OK: ""}, tags=["Resource"])
    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance_id = instance.id

        ResourceHandler().delete_resources([instance_id])

        record_audit_log(
            username=request.user.username,
            op_type=OpTypeEnum.DELETE.value,
            op_status=OpStatusEnum.SUCCESS.value,
            op_object_group=request.gateway.id,
            op_object_type=OpObjectTypeEnum.RESOURCE.value,
            op_object_id=instance_id,
            op_object=instance.identity,
            comment=_("删除资源"),
        )

        return V1OKJsonResponse("OK")


class ResourceImportExportViewSet(ResourceViewSet):
    @swagger_auto_schema(
        request_body=serializers.ResourceImportSLZ,
        responses={status.HTTP_200_OK: serializers.CheckImportResourceSLZ(many=True)},
        tags=["Resource"],
    )
    def import_resources_check(self, request, *args, **kwargs):
        """
        导入资源检查，检查导入配置
        """
        slz = serializers.ResourceImportSLZ(data=request.data)
        slz.is_valid(raise_exception=True)

        importer = ResourcesImporter(
            gateway=request.gateway,
            allow_overwrite=True,
            username=request.user.username,
        )
        importer.load_importing_resources_by_swagger(
            content=slz.validated_data["content"],
            resource_doc_language=request.data.get("resource_doc_language", ""),
        )

        return V1OKJsonResponse("OK", data=sorted(importer.imported_resources, key=lambda x: x["path"]))

    @swagger_auto_schema(
        request_body=serializers.ResourceImportSLZ, responses={status.HTTP_200_OK: ""}, tags=["Resource"]
    )
    @transaction.atomic
    def import_resources(self, request, *args, **kwargs):
        slz = serializers.ResourceImportSLZ(data=request.data)
        slz.is_valid(raise_exception=True)

        importer = ResourcesImporter(
            gateway=request.gateway,
            allow_overwrite=True,
            username=request.user.username,
        )
        importer.load_importing_resources_by_swagger(content=slz.validated_data["content"])
        importer.set_selected_resources(slz.validated_data.get("selected_resources"))
        importer.import_resources()

        return V1OKJsonResponse("OK")

    @swagger_auto_schema(
        request_body=serializers.ResourceExportConditionSLZ,
        responses={status.HTTP_200_OK: ""},
        tags=["Resource"],
    )
    def export_resources(self, request, *args, **kwargs):
        slz = serializers.ResourceExportConditionSLZ(data=request.data, context={"gateway": request.gateway})
        slz.is_valid(raise_exception=True)

        data = slz.validated_data
        queryset = slz.get_exported_resource()

        resource_ids = list(queryset.values_list("id", flat=True))
        queryset = queryset.order_by("path", "method")

        slz = serializers.ExportResourceSLZ(
            instance=queryset,
            many=True,
            context={
                "proxies": Proxy.objects.filter_proxies(resource_ids),
                "disabled_stages": StageResourceDisabled.objects.filter_disabled_stages_by_gateway(request.gateway),
                "resource_labels": ResourceLabel.objects.filter_labels_by_gateway(request.gateway),
                "resource_auth_configs": ResourceAuthContext().filter_scope_id_config_map(resource_ids),
            },
        )

        file_type = data["file_type"]
        exporter = ResourceSwaggerExporter()
        content = exporter.to_swagger(slz.data, file_type=file_type)

        # 导出的文件名，需满足规范：bk_产品名_功能名_文件名.后缀
        export_filename = f"bk_apigw_resources_{self.request.gateway.name}.{file_type}"

        return DownloadableResponse(content, filename=export_filename)


class ResourceBatchViewSet(BaseResourceViewSet):
    @swagger_auto_schema(
        responses={status.HTTP_200_OK: ""}, request_body=serializers.BatchUpdateResourceSLZ, tags=["Resource"]
    )
    @transaction.atomic
    def update(self, request, *args, **kwargs):
        slz = serializers.BatchUpdateResourceSLZ(data=request.data)
        slz.is_valid(raise_exception=True)

        resource_ids = slz.validated_data.pop("ids")
        queryset = self.get_queryset()
        queryset = queryset.filter(id__in=resource_ids)
        queryset.update(
            updated_by=request.user.username,
            updated_time=now_datetime(),
            **slz.validated_data,
        )

        record_audit_log(
            username=request.user.username,
            op_type=OpTypeEnum.MODIFY.value,
            op_status=OpStatusEnum.SUCCESS.value,
            op_object_group=request.gateway.id,
            op_object_type=OpObjectTypeEnum.RESOURCE.value,
            op_object_id=";".join([str(resource.id) for resource in queryset]),
            op_object=";".join([resource.identity for resource in queryset]),
            comment=_("批量更新资源"),
        )

        return V1OKJsonResponse("OK")

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: ""}, request_body=serializers.BatchDestroyResourceSLZ, tags=["Resource"]
    )
    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        slz = serializers.BatchDestroyResourceSLZ(data=request.data)
        slz.is_valid(raise_exception=True)

        queryset = self.get_queryset().filter(id__in=slz.validated_data["ids"])

        resource_ids = list(queryset.values_list("id", flat=True))
        resource_identities = [resource.identity for resource in queryset]

        ResourceHandler().delete_resources(resource_ids)

        record_audit_log(
            username=request.user.username,
            op_type=OpTypeEnum.DELETE.value,
            op_status=OpStatusEnum.SUCCESS.value,
            op_object_group=request.gateway.id,
            op_object_type=OpObjectTypeEnum.RESOURCE.value,
            op_object_id=";".join(map(str, resource_ids)),
            op_object=";".join(resource_identities),
            comment=_("批量删除资源"),
        )

        return V1OKJsonResponse("OK")


class ResourceURLViewSet(BaseResourceViewSet):
    """
    资源访问链接地址
    """

    @swagger_auto_schema(responses={status.HTTP_200_OK: serializers.ResourceURLSLZ(many=True)}, tags=["Resource"])
    def get(self, request, *args, **kwargs):
        # TODO: 目前，资源地址可编辑，展示资源地址列表时，应该展示已发布到环境的资源地址?

        instance = self.get_object()

        urls = []
        for stage_name in Stage.objects.filter(gateway=request.gateway).values_list("name", flat=True):
            urls.append(
                {
                    "stage_name": stage_name,
                    "url": get_resource_url(
                        resource_url_tmpl=ResourceURLHandler.get_resource_url_tmpl(request.gateway.name, stage_name),
                        gateway_name=request.gateway.name,
                        stage_name=stage_name,
                        resource_path=instance.path,
                    ),
                }
            )

        return V1OKJsonResponse("OK", data=urls)


class ResourceReleaseStageViewSet(BaseResourceViewSet):
    """
    获取资源在各环境的发布信息
    """

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: serializers.ResourceReleaseStageSLZ(many=True)},
        tags=["Resource"],
    )
    def get(self, request, *args, **kwargs):
        instance = self.get_object()

        stages = Stage.objects.filter(gateway=request.gateway).order_by("name")
        slz = serializers.ResourceReleaseStageSLZ(
            stages,
            context={
                "api_name": request.gateway.name,
                "resource_released_stages": get_resource_released_stages(
                    request.gateway.id,
                    instance.id,
                ),
            },
            many=True,
        )

        return V1OKJsonResponse("OK", data=slz.data)


class ProxyPathViewSet(BaseResourceViewSet):
    """
    检查 proxy-path 是否正确
    """

    serializer_class = serializers.CheckProxyPathSLZ

    @swagger_auto_schema(responses={status.HTTP_200_OK: ""}, tags=["Resource"])
    def check(self, request, *args, **kwargs):
        """
        校验后端配置中 HTTP 类型的 path
        """
        slz = self.get_serializer(data=request.query_params)
        slz.is_valid(raise_exception=True)
        return V1OKJsonResponse("OK")


class ResourceLabelViewSet(BaseResourceViewSet):
    @swagger_auto_schema(
        responses={status.HTTP_200_OK: ""}, request_body=serializers.UpdateResourceLabelsSLZ, tags=["Resource"]
    )
    @transaction.atomic
    def update(self, request, *args, **kwargs):
        slz = serializers.UpdateResourceLabelsSLZ(data=request.data)
        slz.is_valid(raise_exception=True)

        instance = self.get_object()
        ResourceHandler().save_labels(
            gateway=request.gateway,
            resource=instance,
            label_ids=slz.validated_data["label_ids"],
            delete_unspecified=True,
        )

        return V1OKJsonResponse()


class ResourceWithVerifiedUserRequiredViewSet(BaseResourceViewSet):
    @swagger_auto_schema(responses={status.HTTP_200_OK: ""}, tags=["Resource"])
    def list(self, request, *args, **kwargs):
        """过滤出需要认证用户的资源列表"""
        resources = list(self.get_queryset().values("id", "name"))
        resource_ids = list(map(operator.itemgetter("id"), resources))
        resource_id_to_auth_config = ResourceAuthContext().filter_scope_id_config_map(resource_ids)

        verified_user_required_resources = [
            resource
            for resource in resources
            if resource_id_to_auth_config.get(resource["id"], {}).get("auth_verified_required")
        ]

        return V1OKJsonResponse(data=sorted(verified_user_required_resources, key=operator.itemgetter("name")))
