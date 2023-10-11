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
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status

from apigateway.apps.audit.constants import OpTypeEnum
from apigateway.apps.support.constants import DocLanguageEnum, DocSourceEnum, DocTypeEnum
from apigateway.apps.support.models import ResourceDoc
from apigateway.biz.resource_doc.resource_doc import ResourceDocHandler
from apigateway.core.models import Resource
from apigateway.utils.responses import OKJsonResponse

from .serializers import DocInputSLZ, DocOutputSLZ


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取指定资源的资源文档，包括中文、英文两份文档，如果文档未创建，返回文档模版",
        responses={status.HTTP_200_OK: DocOutputSLZ(many=True)},
        tags=["WebAPI.Resource.Doc"],
    ),
)
@method_decorator(
    name="post",
    decorator=swagger_auto_schema(
        operation_description="创建资源文档",
        responses={status.HTTP_201_CREATED: ""},
        request_body=DocInputSLZ,
        tags=["WebAPI.Resource.Doc"],
    ),
)
class DocListCreateApi(generics.ListCreateAPIView):
    serializer_class = DocInputSLZ

    def get_queryset(self):
        return ResourceDoc.objects.filter(gateway=self.request.gateway)

    def _get_resource(self):
        return get_object_or_404(Resource, gateway=self.request.gateway, id=self.kwargs["resource_id"])

    def list(self, request, gateway_id: int, resource_id: int, *args, **kwargs):
        """获取指定资源的资源文档"""
        queryset = self.get_queryset().filter(resource_id=resource_id)

        docs = [doc for doc in queryset]
        existed_languages = [doc.language for doc in docs]
        missing_languages = set(DocLanguageEnum.get_values()) - set(existed_languages)

        if missing_languages:
            # 如果语言对应文档不存在，则给出模版文档
            docs.extend(
                [
                    ResourceDoc(
                        language=language,
                        content=ResourceDocHandler.get_resource_doc_tmpl(request.gateway.name, language),
                    )
                    for language in missing_languages
                ]
            )

        slz = DocOutputSLZ(docs, many=True)
        return OKJsonResponse(data=slz.data)

    def create(self, request, *args, **kwargs):
        """创建资源文档"""
        resource = self._get_resource()

        slz = self.get_serializer(
            data=request.data,
            context={
                "gateway_id": request.gateway.id,
                "resource_id": resource.id,
            },
        )
        slz.is_valid(raise_exception=True)

        slz.save(
            gateway=request.gateway,
            resource_id=resource.id,
            type=DocTypeEnum.MARKDOWN.value,
            source=DocSourceEnum.CUSTOM.value,
            created_by=request.user.username,
            updated_by=request.user.username,
        )

        ResourceDocHandler.record_audit_log_success(
            username=request.user.username,
            gateway_id=request.gateway.id,
            op_type=OpTypeEnum.CREATE,
            instance_id=slz.instance.id,
            instance_name=f"{slz.instance.language}:{resource.name}",
        )

        return OKJsonResponse(status=status.HTTP_201_CREATED, data={"id": slz.instance.id})


@method_decorator(
    name="put",
    decorator=swagger_auto_schema(
        operation_description="更新资源文档",
        responses={status.HTTP_204_NO_CONTENT: ""},
        request_body=DocInputSLZ,
        tags=["WebAPI.Resource.Doc"],
    ),
)
@method_decorator(
    name="delete",
    decorator=swagger_auto_schema(
        operation_description="删除资源文档", responses={status.HTTP_204_NO_CONTENT: ""}, tags=["WebAPI.Resource.Doc"]
    ),
)
class DocUpdateDestroyApi(generics.UpdateAPIView, generics.DestroyAPIView):
    serializer_class = DocInputSLZ
    lookup_field = "id"

    def get_queryset(self):
        return ResourceDoc.objects.filter(gateway=self.request.gateway, resource_id=self.kwargs["resource_id"])

    def _get_resource(self):
        return get_object_or_404(Resource, gateway=self.request.gateway, id=self.kwargs["resource_id"])

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        resource = self._get_resource()

        slz = self.get_serializer(
            instance,
            data=request.data,
            context={
                "gateway_id": request.gateway.id,
                "resource_id": resource.id,
            },
        )
        slz.is_valid(raise_exception=True)

        slz.save(
            type=DocTypeEnum.MARKDOWN.value,
            source=DocSourceEnum.CUSTOM.value,
            updated_by=request.user.username,
        )

        ResourceDocHandler.record_audit_log_success(
            username=request.user.username,
            gateway_id=request.gateway.id,
            op_type=OpTypeEnum.MODIFY,
            instance_id=slz.instance.id,
            instance_name=f"{slz.instance.language}:{resource.name}",
        )

        return OKJsonResponse(status=status.HTTP_204_NO_CONTENT)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance_id = instance.id
        resource = self._get_resource()

        instance.delete()

        ResourceDocHandler.record_audit_log_success(
            username=request.user.username,
            gateway_id=request.gateway.id,
            op_type=OpTypeEnum.DELETE,
            instance_id=instance_id,
            instance_name=f"{instance.language}:{resource.name}",
        )

        return OKJsonResponse(status=status.HTTP_204_NO_CONTENT)
