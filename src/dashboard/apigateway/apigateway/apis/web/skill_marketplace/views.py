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
import io

from django.utils.decorators import method_decorator
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import generics, status

from apigateway.apis.web.skill.serializers import (
    SkillFileListOutputSLZ,
    SkillTagOutputSLZ,
    SkillVersionOutputSLZ,
)
from apigateway.biz.skill import (
    SkillHandler,
    build_skill_package_files,
    build_skill_package_zip,
    get_skill_package_filename,
)
from apigateway.common.tenant.request import get_user_tenant_id
from apigateway.utils.responses import DownloadableResponse, OKJsonResponse

from .serializers import (
    SkillMarketplaceCountInputSLZ,
    SkillMarketplaceCountOutputSLZ,
    SkillMarketplaceListInputSLZ,
    SkillMarketplaceListOutputSLZ,
    SkillMarketplaceRetrieveOutputSLZ,
    SkillMarketplaceTagListInputSLZ,
)


@method_decorator(
    name="get",
    decorator=extend_schema(
        description="获取 Skill 市场列表",
        parameters=[SkillMarketplaceListInputSLZ],
        responses={status.HTTP_200_OK: SkillMarketplaceListOutputSLZ(many=True)},
        tags=["WebAPI.SkillMarketplace"],
    ),
)
class SkillMarketplaceSkillListApi(generics.ListAPIView):
    def list(self, request, *args, **kwargs):
        slz = SkillMarketplaceListInputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)
        data = slz.validated_data

        queryset = SkillHandler.get_market_queryset(get_user_tenant_id(request))
        queryset = SkillHandler.filter_queryset(
            queryset, keyword=data.get("keyword"), tag=data.get("tag"), skill_type=data.get("type")
        )
        queryset = SkillHandler.order_queryset(SkillHandler.for_list(queryset), data["order_by"])

        page = self.paginate_queryset(queryset)
        context = SkillHandler.build_list_context(page)
        return self.get_paginated_response(SkillMarketplaceListOutputSLZ(page, many=True, context=context).data)


@method_decorator(
    name="get",
    decorator=extend_schema(
        description="获取 Skill 市场各类型的数量",
        parameters=[SkillMarketplaceCountInputSLZ],
        responses={status.HTTP_200_OK: SkillMarketplaceCountOutputSLZ()},
        tags=["WebAPI.SkillMarketplace"],
    ),
)
class SkillMarketplaceSkillCountApi(generics.RetrieveAPIView):
    def retrieve(self, request, *args, **kwargs):
        slz = SkillMarketplaceCountInputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        queryset = SkillHandler.get_market_queryset(get_user_tenant_id(request))
        queryset = SkillHandler.filter_queryset(
            queryset, keyword=slz.validated_data.get("keyword"), tag=slz.validated_data.get("tag")
        )
        return OKJsonResponse(data=SkillHandler.count_by_type(queryset))


@method_decorator(
    name="get",
    decorator=extend_schema(
        description="获取 Skill 市场的标签",
        parameters=[SkillMarketplaceTagListInputSLZ],
        responses={status.HTTP_200_OK: SkillTagOutputSLZ(many=True)},
        tags=["WebAPI.SkillMarketplace"],
    ),
)
class SkillMarketplaceTagListApi(generics.ListAPIView):
    def list(self, request, *args, **kwargs):
        slz = SkillMarketplaceTagListInputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        queryset = SkillHandler.get_market_queryset(get_user_tenant_id(request))
        queryset = SkillHandler.filter_queryset(queryset, skill_type=slz.validated_data.get("type"))
        tags = SkillHandler.list_tags(queryset, keyword=slz.validated_data.get("keyword"))
        return OKJsonResponse(data=SkillTagOutputSLZ(tags, many=True).data)


@method_decorator(
    name="get",
    decorator=extend_schema(
        description="获取 Skill 市场的 Skill 详情",
        responses={status.HTTP_200_OK: SkillMarketplaceRetrieveOutputSLZ()},
        tags=["WebAPI.SkillMarketplace"],
    ),
)
class SkillMarketplaceSkillRetrieveApi(generics.RetrieveAPIView):
    def retrieve(self, request, *args, **kwargs):
        metadata = SkillHandler.get_market_skill(kwargs["skill_id"], get_user_tenant_id(request))
        context = {
            **SkillHandler.build_detail_context(metadata),
            "current_version_id": metadata.current_version_id,
        }
        return OKJsonResponse(data=SkillMarketplaceRetrieveOutputSLZ(metadata, context=context).data)


@method_decorator(
    name="get",
    decorator=extend_schema(
        description="获取 Skill 市场的历史版本",
        responses={status.HTTP_200_OK: SkillVersionOutputSLZ(many=True)},
        tags=["WebAPI.SkillMarketplace"],
    ),
)
class SkillMarketplaceSkillVersionListApi(generics.ListAPIView):
    def list(self, request, *args, **kwargs):
        metadata = SkillHandler.get_market_skill(kwargs["skill_id"], get_user_tenant_id(request))
        versions = SkillHandler.list_versions(metadata)
        slz = SkillVersionOutputSLZ(versions, many=True, context={"current_version_id": metadata.current_version_id})
        return OKJsonResponse(data=slz.data)


@method_decorator(
    name="get",
    decorator=extend_schema(
        description="获取 Skill 市场的 Skill 内容",
        responses={status.HTTP_200_OK: SkillFileListOutputSLZ()},
        tags=["WebAPI.SkillMarketplace"],
    ),
)
class SkillMarketplaceSkillFileListApi(generics.RetrieveAPIView):
    def retrieve(self, request, *args, **kwargs):
        metadata = SkillHandler.get_market_skill(kwargs["skill_id"], get_user_tenant_id(request))
        version = SkillHandler.get_version(metadata, kwargs.get("version"))
        version, files = build_skill_package_files(metadata, version)
        data = {
            "name": metadata.name,
            "version": version.version,
            "files": [{"path": path, "content": content} for path, content in files],
        }
        return OKJsonResponse(data=SkillFileListOutputSLZ(data).data)


@method_decorator(
    name="get",
    decorator=extend_schema(
        description="下载 Skill 市场的 Skill",
        responses={status.HTTP_200_OK: OpenApiResponse(description="zip 文件")},
        tags=["WebAPI.SkillMarketplace"],
    ),
)
class SkillMarketplaceSkillDownloadApi(generics.RetrieveAPIView):
    def retrieve(self, request, *args, **kwargs):
        metadata = SkillHandler.get_market_skill(kwargs["skill_id"], get_user_tenant_id(request))
        version = SkillHandler.get_version(metadata, kwargs.get("version"))
        version, content = build_skill_package_zip(metadata, version)
        SkillHandler.increase_download_count(metadata.id)
        return DownloadableResponse(io.BytesIO(content), filename=get_skill_package_filename(metadata, version))
