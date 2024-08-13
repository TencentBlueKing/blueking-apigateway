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
import json
import operator
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

from django.db import transaction
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, serializers, status

from apigateway.apis.web.constants import ExportTypeEnum
from apigateway.apps.audit.constants import OpTypeEnum
from apigateway.apps.plugin.constants import PluginBindingScopeEnum
from apigateway.apps.plugin.models import PluginBinding
from apigateway.apps.support.constants import DocLanguageEnum
from apigateway.biz.audit import Auditor
from apigateway.biz.backend import BackendHandler
from apigateway.biz.plugin_binding import PluginBindingHandler
from apigateway.biz.resource import ResourceHandler
from apigateway.biz.resource.importer import ResourceDataConvertor, ResourceImportValidator, ResourcesImporter
from apigateway.biz.resource.importer.openapi import OpenAPIExportManager, OpenAPIImportManager
from apigateway.biz.resource.savers import ResourcesSaver
from apigateway.biz.resource_doc.importer import DocImporter
from apigateway.biz.resource_doc.importer.parsers import OpenAPIParser
from apigateway.biz.resource_doc.resource_doc import ResourceDocHandler
from apigateway.biz.resource_label import ResourceLabelHandler
from apigateway.biz.resource_version import ResourceVersionHandler
from apigateway.common.contexts import ResourceAuthContext
from apigateway.core.constants import STAGE_VAR_PATTERN
from apigateway.core.models import BackendConfig, Proxy, Resource, Stage
from apigateway.utils.django import get_model_dict
from apigateway.utils.responses import DownloadableResponse, FailJsonResponse, OKJsonResponse

from .serializers import (
    BackendPathCheckInputSLZ,
    BackendPathCheckOutputSLZ,
    ResourceBatchDestroyInputSLZ,
    ResourceBatchUpdateInputSLZ,
    ResourceExportInputSLZ,
    ResourceExportOutputSLZ,
    ResourceImportCheckFailOutputSLZ,
    ResourceImportCheckInputSLZ,
    ResourceImportDocPreviewInputSLZ,
    ResourceImportInfoSLZ,
    ResourceImportInputSLZ,
    ResourceInputSLZ,
    ResourceLabelUpdateInputSLZ,
    ResourceListOutputSLZ,
    ResourceOutputSLZ,
    ResourceQueryInputSLZ,
    ResourceWithVerifiedUserRequiredOutputSLZ,
)


class ResourceQuerySetMixin:
    def get_queryset(self):
        return Resource.objects.filter(gateway=self.request.gateway)


class BackendHostIsEmpty(Exception):
    """后端服务地址为空，如新创建的 prod 环境默认后端的地址"""


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取资源列表，分页",
        query_serializer=ResourceQueryInputSLZ,
        responses={status.HTTP_200_OK: ResourceListOutputSLZ(many=True)},
        tags=["WebAPI.Resource"],
    ),
)
@method_decorator(
    name="post",
    decorator=swagger_auto_schema(
        operation_description="新建资源",
        responses={status.HTTP_201_CREATED: ""},
        request_body=ResourceInputSLZ,
        tags=["WebAPI.Resource"],
    ),
)
class ResourceListCreateApi(ResourceQuerySetMixin, generics.ListCreateAPIView):
    def list(self, request, *args, **kwargs):
        slz = ResourceQueryInputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        queryset = ResourceHandler.filter_by_resource_filter_condition(
            gateway_id=request.gateway.id,
            condition=slz.validated_data,
        )

        page = self.paginate_queryset(queryset)
        resource_ids = [resource.id for resource in page]

        slz = ResourceListOutputSLZ(
            page,
            many=True,
            context={
                "labels": ResourceLabelHandler.get_labels(resource_ids),
                "docs": ResourceDocHandler.get_docs(resource_ids),
                "backends": BackendHandler.get_id_to_instance(request.gateway.id),
                "proxies": {proxy.resource_id: proxy for proxy in Proxy.objects.filter(resource_id__in=resource_ids)},
                "plugin_counts": PluginBindingHandler.get_resource_ids_plugin_binding_count(
                    gateway_id=request.gateway.id, resource_ids=resource_ids
                ),
                "latest_version_created_time": ResourceVersionHandler.get_latest_created_time(request.gateway.id),
            },
        )
        return self.get_paginated_response(slz.data)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        slz = ResourceInputSLZ(
            data=request.data,
            context={
                "gateway": request.gateway,
                "stages": Stage.objects.filter(gateway=request.gateway),
            },
        )
        slz.is_valid(raise_exception=True)

        saver = ResourcesSaver.from_resources(
            gateway=request.gateway,
            resources=[slz.validated_data],
            username=request.user.username,
        )
        resources = saver.save()
        instance = resources[0]

        Auditor.record_resource_op_success(
            op_type=OpTypeEnum.CREATE,
            username=request.user.username,
            gateway_id=request.gateway.id,
            instance_id=instance.id,
            instance_name=instance.identity,
            data_before={},
            data_after=get_model_dict(instance),
        )

        return OKJsonResponse(status=status.HTTP_201_CREATED)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取指定资源信息",
        responses={status.HTTP_200_OK: ResourceOutputSLZ()},
        tags=["WebAPI.Resource"],
    ),
)
@method_decorator(
    name="put",
    decorator=swagger_auto_schema(
        operation_description="更新资源",
        responses={status.HTTP_204_NO_CONTENT: ""},
        request_body=ResourceInputSLZ,
        tags=["WebAPI.Resource"],
    ),
)
@method_decorator(
    name="delete",
    decorator=swagger_auto_schema(
        operation_description="删除资源", responses={status.HTTP_204_NO_CONTENT: ""}, tags=["WebAPI.Resource"]
    ),
)
class ResourceRetrieveUpdateDestroyApi(ResourceQuerySetMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ResourceInputSLZ
    lookup_field = "id"

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        slz = ResourceOutputSLZ(
            instance,
            context={
                "auth_config": ResourceAuthContext().get_config(instance.id),
                "labels": ResourceLabelHandler.get_labels([instance.id]),
                "proxy": Proxy.objects.get(resource_id=instance.id),
                "resource_id_to_schema": ResourceHandler.get_id_to_schema([instance.id]),
            },
        )
        return OKJsonResponse(data=slz.data)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        data_before = get_model_dict(instance)

        slz = self.get_serializer(
            instance,
            data=request.data,
            context={
                "gateway": request.gateway,
                "stages": Stage.objects.filter(gateway=request.gateway),
            },
        )
        slz.is_valid(raise_exception=True)

        saver = ResourcesSaver.from_resources(
            gateway=request.gateway,
            resources=[slz.validated_data],
            username=request.user.username,
        )
        resources = saver.save()
        instance = resources[0]

        Auditor.record_resource_op_success(
            op_type=OpTypeEnum.MODIFY,
            username=request.user.username,
            gateway_id=request.gateway.id,
            instance_id=instance.id,
            instance_name=instance.identity,
            data_before=data_before,
            data_after=get_model_dict(instance),
        )

        return OKJsonResponse(status=status.HTTP_204_NO_CONTENT)

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        data_before = get_model_dict(instance)
        instance_id = instance.id

        ResourceHandler.delete_resources([instance_id])

        Auditor.record_resource_op_success(
            op_type=OpTypeEnum.DELETE,
            username=request.user.username,
            gateway_id=request.gateway.id,
            instance_id=instance_id,
            instance_name=instance.identity,
            data_before=data_before,
            data_after={},
        )

        return OKJsonResponse(status=status.HTTP_204_NO_CONTENT)


@method_decorator(
    name="put",
    decorator=swagger_auto_schema(
        operation_description="批量更新资源，如是否公开、是否允许申请资源权限",
        responses={status.HTTP_204_NO_CONTENT: ""},
        request_body=ResourceBatchUpdateInputSLZ,
        tags=["WebAPI.Resource"],
    ),
)
@method_decorator(
    name="delete",
    decorator=swagger_auto_schema(
        operation_description="批量删除资源",
        responses={status.HTTP_204_NO_CONTENT: ""},
        request_body=ResourceBatchDestroyInputSLZ,
        tags=["WebAPI.Resource"],
    ),
)
class ResourceBatchUpdateDestroyApi(ResourceQuerySetMixin, generics.UpdateAPIView, generics.DestroyAPIView):
    serializer_class = ResourceBatchUpdateInputSLZ

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        slz = self.get_serializer(data=request.data, context={"gateway_id": request.gateway.id})
        slz.is_valid(raise_exception=True)

        queryset = self.get_queryset().filter(id__in=slz.validated_data["ids"])
        queryset.update(
            is_public=slz.validated_data["is_public"],
            allow_apply_permission=slz.validated_data["allow_apply_permission"],
            updated_by=request.user.username,
        )
        label_ids = slz.validated_data.get("label_ids")
        if slz.validated_data["is_update_labels"]:
            ResourceHandler.batch_update_resource_labels(
                gateway=request.gateway,
                resource_ids=slz.validated_data["ids"],
                label_ids=label_ids,
            )

        Auditor.record_resource_op_success(
            op_type=OpTypeEnum.MODIFY,
            username=request.user.username,
            gateway_id=request.gateway.id,
            instance_id=";".join([str(resource.id) for resource in queryset]),
            instance_name=";".join([resource.identity for resource in queryset]),
            comment="批量更新资源",
            data_before={},
            data_after={
                "is_public": slz.validated_data["is_public"],
                "allow_apply_permission": slz.validated_data["allow_apply_permission"],
                "label_ids": label_ids,
            },
        )

        return OKJsonResponse(status=status.HTTP_204_NO_CONTENT)

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        slz = ResourceBatchDestroyInputSLZ(data=request.data, context={"gateway_id": request.gateway.id})
        slz.is_valid(raise_exception=True)

        queryset = self.get_queryset().filter(id__in=slz.validated_data["ids"])

        resource_ids = [resource.id for resource in queryset]
        resource_identities = [resource.identity for resource in queryset]

        ResourceHandler.delete_resources(resource_ids)

        Auditor.record_resource_op_success(
            op_type=OpTypeEnum.DELETE,
            username=request.user.username,
            gateway_id=request.gateway.id,
            instance_id=";".join(map(str, resource_ids)),
            instance_name=";".join(resource_identities),
            comment="批量删除资源",
            data_before=resource_ids,
            data_after=[],
        )

        return OKJsonResponse(status=status.HTTP_204_NO_CONTENT)


@method_decorator(
    name="put",
    decorator=swagger_auto_schema(
        operation_description="更新资源标签",
        responses={status.HTTP_204_NO_CONTENT: ""},
        request_body=ResourceLabelUpdateInputSLZ,
        tags=["WebAPI.Resource"],
    ),
)
class ResourceLabelUpdateApi(ResourceQuerySetMixin, generics.UpdateAPIView):
    serializer_class = ResourceLabelUpdateInputSLZ
    lookup_url_kwarg = "resource_id"
    lookup_field = "id"

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        slz = self.get_serializer(data=request.data, context={"gateway_id": request.gateway.id})
        slz.is_valid(raise_exception=True)

        instance = self.get_object()
        ResourceHandler.save_resource_labels(
            gateway=request.gateway,
            resource=instance,
            label_ids=slz.validated_data["label_ids"],
        )

        # 更新标签也要更新资源的更新时间
        instance.save()

        return OKJsonResponse(status=status.HTTP_204_NO_CONTENT)


class ResourceImportCheckApi(generics.CreateAPIView):
    @swagger_auto_schema(
        operation_description="导入资源检查，导入资源前，检查资源配置是否正确",
        request_body=ResourceImportCheckInputSLZ,
        responses={
            status.HTTP_200_OK: ResourceImportInfoSLZ(many=True),
            status.HTTP_400_BAD_REQUEST: ResourceImportCheckFailOutputSLZ(many=True),
        },
        tags=["WebAPI.Resource"],
    )
    def post(self, request, *args, **kwargs):
        """导入资源检查"""
        slz = ResourceImportCheckInputSLZ(
            data=request.data,
            context={
                "gateway": request.gateway,
            },
        )
        slz.is_valid(raise_exception=True)

        try:
            openapi_manager = OpenAPIImportManager.load_from_content(request.gateway, slz.validated_data["content"])
        except Exception as err:
            raise serializers.ValidationError(
                {"content": _("导入内容为无效的 json/yaml 数据，{err}。").format(err=err)}
            )

        validate_err_list = openapi_manager.validate()

        if len(validate_err_list) != 0:
            slz = ResourceImportCheckFailOutputSLZ(
                instance=validate_err_list,
                many=True,
            )
            return FailJsonResponse(
                status=status.HTTP_400_BAD_REQUEST, code="INVALID", data=slz.data, message="validate fail"
            )

        resource_data_list = openapi_manager.get_resource_list()
        resource_ids = [resource_data.resource.id for resource_data in resource_data_list if resource_data.resource]
        slz = ResourceImportInfoSLZ(
            data=resource_data_list,
            many=True,
            context={
                "docs": ResourceDocHandler.get_docs_by_resource_ids(resource_ids),
            },
        )
        slz.is_valid()
        return OKJsonResponse(data=slz.data)


class ResourceImportApi(generics.CreateAPIView):
    @swagger_auto_schema(
        operation_description="yaml/json check之后的标准化资源数据导入",
        request_body=ResourceImportInputSLZ,
        responses={status.HTTP_204_NO_CONTENT: ""},
        tags=["WebAPI.Resource"],
    )
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        slz = ResourceImportInputSLZ(
            data=request.data,
            context={
                "gateway": request.gateway,
                "stages": Stage.objects.filter(gateway=request.gateway),
            },
        )
        slz.is_valid(raise_exception=True)

        resource_list = ResourceDataConvertor(request.gateway, slz.data.get("import_resources", [])).convert()

        validator = ResourceImportValidator(
            gateway=request.gateway,
            resource_data_list=resource_list,
            need_delete_unspecified_resources=False,
        )

        # 再次进行逻辑校验
        validate_err_list = validator.validate()
        if len(validate_err_list) > 0:
            error_dicts = [error.to_dict() for error in validate_err_list]
            raise serializers.ValidationError(
                {"content": _("validate err {err}。").format(err=json.dumps(error_dicts, indent=4))}
            )
        importer = ResourcesImporter.from_resources(
            gateway=request.gateway,
            resources=resource_list,
            need_delete_unspecified_resources=False,
            username=request.user.username,
        )
        importer.import_resources()
        # 如果生成文档还要再生成文档
        if slz.validated_data.get("doc_language"):
            exporter = OpenAPIExportManager(include_bk_apigateway_resource=False)
            # 生成openapi yaml
            content = exporter.export_openapi(slz.data.get("import_resources", []), file_type="yaml")
            parser = OpenAPIParser(gateway_id=request.gateway.id)
            docs = parser.parse(
                swagger=content,
                language=DocLanguageEnum(slz.validated_data["doc_language"]),
            )
            importer = DocImporter(
                gateway_id=request.gateway.id,
            )
            importer.import_docs(docs=docs)

        return OKJsonResponse(status=status.HTTP_204_NO_CONTENT)


class ResourceImportDocPreviewApi(generics.CreateAPIView):
    @swagger_auto_schema(
        operation_description="导入文档预览",
        request_body=ResourceImportDocPreviewInputSLZ,
        tags=["WebAPI.Resource"],
    )
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        slz = ResourceImportDocPreviewInputSLZ(
            data=request.data,
            context={
                "gateway": request.gateway,
                "stages": Stage.objects.filter(gateway=request.gateway),
            },
        )
        slz.is_valid(raise_exception=True)

        exporter = OpenAPIExportManager(include_bk_apigateway_resource=False)
        # 生成openapi yaml
        content = exporter.export_openapi([slz.data.get("review_resource")], file_type="yaml")
        parser = OpenAPIParser(gateway_id=request.gateway.id)
        docs = parser.parse(
            swagger=content,
            language=DocLanguageEnum(slz.validated_data["doc_language"]),
        )
        return OKJsonResponse(data={"doc": "" if len(docs) == 0 else docs[0].content})


class ResourceExportApi(generics.CreateAPIView):
    @swagger_auto_schema(
        operation_description="导出资源",
        request_body=ResourceExportInputSLZ,
        responses={status.HTTP_200_OK: ""},
        tags=["WebAPI.Resource"],
    )
    def post(self, request, *args, **kwargs):
        slz = ResourceExportInputSLZ(data=request.data)
        slz.is_valid(raise_exception=True)

        selected_resource_queryset = self._filter_selected_resources(
            export_type=slz.validated_data["export_type"],
            gateway_id=request.gateway.id,
            resource_filter_condition=slz.validated_data.get("resource_filter_condition", {}),
            resource_ids=slz.validated_data.get("resource_ids", []),
        )
        selected_resource_ids = list(selected_resource_queryset.values_list("id", flat=True))

        output_slz = ResourceExportOutputSLZ(
            selected_resource_queryset,
            many=True,
            context={
                "labels": ResourceLabelHandler.get_labels_by_gateway(request.gateway.id),
                "backends": BackendHandler.get_id_to_instance(gateway_id=request.gateway.id),
                "proxies": {
                    proxy.resource_id: proxy for proxy in Proxy.objects.filter(resource_id__in=selected_resource_ids)
                },
                "resource_id_to_plugin_bindings": PluginBinding.objects.query_scope_id_to_bindings(
                    gateway_id=request.gateway.id,
                    scope_type=PluginBindingScopeEnum.RESOURCE,
                    scope_ids=selected_resource_ids,
                ),
                "resource_id_to_schema": ResourceHandler.get_id_to_schema(selected_resource_ids),
                "auth_configs": ResourceAuthContext().get_resource_id_to_auth_config(selected_resource_ids),
            },
        )

        file_type = slz.validated_data["file_type"]
        exporter = OpenAPIExportManager()
        content = exporter.export_openapi(output_slz.data, file_type=file_type)

        # 导出的文件名，需满足规范：bk_产品名_功能名_文件名.后缀
        export_filename = f"bk_apigw_resources_{self.request.gateway.name}.{file_type}"

        return DownloadableResponse(content, filename=export_filename)

    def _filter_selected_resources(
        self,
        export_type: str,
        gateway_id: int,
        resource_filter_condition: Dict[str, Any],
        resource_ids: List[int],
    ):
        """获取待导出的资源"""
        if export_type == ExportTypeEnum.ALL.value:
            return Resource.objects.filter(gateway_id=gateway_id)

        if export_type == ExportTypeEnum.FILTERED.value:
            return ResourceHandler.filter_by_resource_filter_condition(gateway_id, resource_filter_condition or {})

        if export_type == ExportTypeEnum.SELECTED.value:
            return Resource.objects.filter(gateway_id=gateway_id, id__in=resource_ids)

        return Resource.objects.none()


class BackendPathCheckApi(ResourceQuerySetMixin, generics.RetrieveAPIView):
    serializer_class = BackendPathCheckInputSLZ

    @swagger_auto_schema(
        operation_description="资源后端地址检查，校验后端配置中的请求路径",
        query_serializer=BackendPathCheckInputSLZ,
        responses={status.HTTP_200_OK: BackendPathCheckOutputSLZ(many=True)},
        tags=["WebAPI.Resource"],
    )
    def get(self, request, *args, **kwargs):
        """校验后端配置中的请求路径"""
        slz = self.get_serializer(
            data=request.query_params,
            context={
                "stages": Stage.objects.filter(gateway=request.gateway),
            },
        )
        slz.is_valid(raise_exception=True)

        backend_id = slz.validated_data["backend_id"]
        backend_path = slz.validated_data.get("backend_config", {}).get("path", "")
        backend_hosts = self._get_backend_hosts(backend_id)

        result = []
        for stage in Stage.objects.filter(gateway=request.gateway):
            stage_vars = stage.vars
            result.append(
                {
                    "stage": {"id": stage.id, "name": stage.name},
                    "backend_urls": [
                        self._get_backend_url(host, backend_path, stage_vars)
                        # 如果没有指定后端服务，提供一个默认的后端地址字符串
                        for host in backend_hosts.get(stage.id, ["http://{backend-host}"])
                    ],
                }
            )

        slz = BackendPathCheckOutputSLZ(result, many=True)
        return OKJsonResponse(data=slz.data)

    def _get_backend_hosts(self, backend_id: Optional[int]) -> Dict[int, List[str]]:
        if not backend_id:
            return {}

        backend_configs = BackendConfig.objects.filter(gateway=self.request.gateway, backend_id=backend_id)
        backend_hosts = {}
        for backend_config in backend_configs:
            hosts = []
            for host in backend_config.config["hosts"]:
                if not host["host"]:
                    raise BackendHostIsEmpty(
                        _(
                            "网关环境 {stage_name} 下，后端服务 {backend_name} 的服务地址为空，请在 后端服务 -> 编辑 {backend_name} ，更新该环境的后端服务地址。"
                        ).format(
                            stage_name=backend_config.stage.name,
                            backend_name=backend_config.backend.name,
                        )
                    )

                hosts.append(f"{host['scheme']}://{host['host']}")

            backend_hosts[backend_config.stage_id] = hosts

        return backend_hosts

    def _get_backend_url(self, host: str, path: str, vars: Dict[str, Any]) -> str:
        url = urljoin(host, path)

        def replace(matched):
            return vars.get(matched.group(1), matched.group(0))

        return re.sub(STAGE_VAR_PATTERN, replace, url)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="过滤出需要认证用户的资源列表，免用户认证应用白名单插件，需要使用此数据过滤资源",
        responses={status.HTTP_200_OK: ResourceWithVerifiedUserRequiredOutputSLZ(many=True)},
        tags=["WebAPI.Resource"],
    ),
)
class ResourcesWithVerifiedUserRequiredApi(ResourceQuerySetMixin, generics.ListAPIView):
    def list(self, request, *args, **kwargs):
        """过滤出需要认证用户的资源列表"""
        resources = list(self.get_queryset().values("id", "name"))
        resource_ids = list(map(operator.itemgetter("id"), resources))
        auth_configs = ResourceAuthContext().get_resource_id_to_auth_config(resource_ids)

        matched_resources = [
            resource for resource in resources if auth_configs.get(resource["id"], {}).get("auth_verified_required")
        ]
        slz = ResourceWithVerifiedUserRequiredOutputSLZ(matched_resources, many=True)

        return OKJsonResponse(data=slz.data)
