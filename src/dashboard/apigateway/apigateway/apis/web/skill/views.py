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
from typing import TYPE_CHECKING, Any, Dict, Optional

from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import generics, status

from apigateway.apps.audit.constants import OpTypeEnum
from apigateway.apps.rbac.constants import GatewayActionEnum
from apigateway.apps.skill.constants import SkillStatusEnum
from apigateway.biz.audit import Auditor
from apigateway.biz.skill import (
    SkillArchivedError,
    SkillHandler,
    SkillPackageInvalidError,
    SkillUploadForm,
    SkillVersionExistsError,
    SkillVersionNotNewerError,
    build_skill_package_files,
    build_skill_package_zip,
    check_skill_package,
    delete_skill,
    get_skill_audit_data,
    get_skill_package_filename,
    publish_gateway_skill,
    set_current_version,
    set_skill_status,
    update_skill_basic_info,
)
from apigateway.common.error_codes import error_codes
from apigateway.utils.responses import DownloadableResponse, OKJsonResponse

from .serializers import (
    SkillBasicInfoInputSLZ,
    SkillCurrentVersionUpdateInputSLZ,
    SkillFileListOutputSLZ,
    SkillListInputSLZ,
    SkillListOutputSLZ,
    SkillPackageCheckInputSLZ,
    SkillPackageCheckOutputSLZ,
    SkillPublishInputSLZ,
    SkillPublishOutputSLZ,
    SkillRetrieveOutputSLZ,
    SkillStatusUpdateInputSLZ,
    SkillTagListInputSLZ,
    SkillTagOutputSLZ,
    SkillValidationMessageOutputSLZ,
    SkillVersionOutputSLZ,
)

if TYPE_CHECKING:
    from apigateway.apps.skill.models import SkillMetadata

_STATUS_COMMENTS = {
    SkillStatusEnum.ARCHIVED.value: "归档 Skill",
    SkillStatusEnum.PUBLISHED.value: "恢复 Skill",
}


class SkillQuerySetMixin(generics.GenericAPIView):
    def get_skill(self) -> SkillMetadata:
        return SkillHandler.get_gateway_skill(self.request.gateway, self.kwargs["skill_id"])


def _publish(request, data: Dict[str, Any], skill_name: Optional[str] = None):
    form = SkillUploadForm(
        display_name=data["display_name"],
        display_name_en=data["display_name_en"],
        description=data["description"],
        tags=data["tags"],
        version=data["version"],
    )
    try:
        saved = publish_gateway_skill(
            request.gateway,
            data["file"],
            form,
            operator=request.user.username,
            overwrite=data["overwrite"],
            skill_name=skill_name,
        )
    except SkillPackageInvalidError as err:
        raise error_codes.INVALID_ARGUMENT.format(_("Skill 包校验不通过"), replace=True).set_data(
            {
                "errors": SkillValidationMessageOutputSLZ(err.errors, many=True).data,
                "warnings": SkillValidationMessageOutputSLZ(err.warnings, many=True).data,
            }
        )
    except SkillVersionExistsError as err:
        context = {"current_version_id": err.version.metadata.current_version_id}
        raise error_codes.CONFLICT.format(str(err), replace=True).set_data(
            SkillVersionOutputSLZ(err.version, context=context).data
        )
    except SkillVersionNotNewerError as err:
        raise error_codes.INVALID_ARGUMENT.format(str(err), replace=True)
    except SkillArchivedError as err:
        raise error_codes.FAILED_PRECONDITION.format(str(err), replace=True)

    if saved.created:
        op_type, comment = OpTypeEnum.CREATE, "创建 Skill"
    else:
        op_type, comment = OpTypeEnum.MODIFY, "覆盖 Skill 版本" if saved.overwritten else "发布 Skill 新版本"
    Auditor.record_skill_op_success(
        op_type=op_type,
        username=request.user.username,
        gateway_id=request.gateway.id,
        instance_id=saved.metadata.id,
        instance_name=saved.metadata.code,
        data_before=saved.data_before,
        data_after=get_skill_audit_data(saved.metadata),
        comment=comment,
    )
    return OKJsonResponse(
        status=status.HTTP_201_CREATED, data=SkillPublishOutputSLZ({"skill_id": saved.metadata.code}).data
    )


def _file_list_response(metadata: SkillMetadata, version_str: Optional[str]):
    version = SkillHandler.get_version(metadata, version_str)
    files = build_skill_package_files(metadata, version, with_declaration=True)
    data = {
        "name": metadata.name,
        "version": version.version,
        "files": [{"path": path, "content": content} for path, content in files],
    }
    return OKJsonResponse(data=SkillFileListOutputSLZ(data).data)


@method_decorator(
    name="get",
    decorator=extend_schema(
        description="获取网关 Skill 列表",
        parameters=[SkillListInputSLZ],
        responses={status.HTTP_200_OK: SkillListOutputSLZ(many=True)},
        tags=["WebAPI.Skill"],
    ),
)
@method_decorator(
    name="post",
    decorator=extend_schema(
        description="上传 Skill",
        request={"multipart/form-data": SkillPublishInputSLZ},
        responses={
            status.HTTP_201_CREATED: SkillPublishOutputSLZ(),
            status.HTTP_409_CONFLICT: SkillVersionOutputSLZ(),
        },
        tags=["WebAPI.Skill"],
    ),
)
class SkillListCreateApi(generics.ListCreateAPIView):
    gateway_action_map = {"GET": GatewayActionEnum.OPERATE_GATEWAY.value}

    def list(self, request, *args, **kwargs):
        slz = SkillListInputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)
        data = slz.validated_data

        queryset = SkillHandler.filter_queryset(
            SkillHandler.get_gateway_queryset(request.gateway),
            keyword=data.get("keyword"),
            tag=data.get("tag"),
            status=data.get("status"),
            match_gateway_name=False,
        )
        queryset = SkillHandler.order_queryset(SkillHandler.for_list(queryset), data["order_by"])

        page = self.paginate_queryset(queryset)
        return self.get_paginated_response(SkillListOutputSLZ(page, many=True).data)

    def create(self, request, *args, **kwargs):
        slz = SkillPublishInputSLZ(data=request.data)
        slz.is_valid(raise_exception=True)
        return _publish(request, slz.validated_data)


@method_decorator(
    name="get",
    decorator=extend_schema(
        description="获取网关 Skill 的标签",
        parameters=[SkillTagListInputSLZ],
        responses={status.HTTP_200_OK: SkillTagOutputSLZ(many=True)},
        tags=["WebAPI.Skill"],
    ),
)
class SkillTagListApi(generics.ListAPIView):
    gateway_action = GatewayActionEnum.OPERATE_GATEWAY.value

    def list(self, request, *args, **kwargs):
        slz = SkillTagListInputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        queryset = SkillHandler.get_gateway_queryset(request.gateway)
        tags = SkillHandler.list_tags(queryset, keyword=slz.validated_data.get("keyword"))
        return OKJsonResponse(data=SkillTagOutputSLZ(tags, many=True).data)


@method_decorator(
    name="post",
    decorator=extend_schema(
        description="预检 Skill 包",
        request={"multipart/form-data": SkillPackageCheckInputSLZ},
        responses={status.HTTP_200_OK: SkillPackageCheckOutputSLZ()},
        tags=["WebAPI.Skill"],
    ),
)
class SkillPackageCheckApi(generics.CreateAPIView):
    def create(self, request, *args, **kwargs):
        slz = SkillPackageCheckInputSLZ(data=request.data)
        slz.is_valid(raise_exception=True)

        skill_name = None
        if slz.validated_data.get("skill_id"):
            skill_name = SkillHandler.get_gateway_skill(request.gateway, slz.validated_data["skill_id"]).name
        result = check_skill_package(request.gateway, slz.validated_data["file"], skill_name=skill_name)
        return OKJsonResponse(data=SkillPackageCheckOutputSLZ(result).data)


@method_decorator(
    name="get",
    decorator=extend_schema(
        description="获取网关 Skill 详情",
        responses={status.HTTP_200_OK: SkillRetrieveOutputSLZ()},
        tags=["WebAPI.Skill"],
    ),
)
@method_decorator(
    name="put",
    decorator=extend_schema(
        description="更新 Skill 基本信息",
        request=SkillBasicInfoInputSLZ,
        responses={status.HTTP_204_NO_CONTENT: None},
        tags=["WebAPI.Skill"],
    ),
)
@method_decorator(
    name="delete",
    decorator=extend_schema(
        description="删除 Skill",
        responses={status.HTTP_204_NO_CONTENT: None},
        tags=["WebAPI.Skill"],
    ),
)
class SkillRetrieveUpdateDestroyApi(SkillQuerySetMixin, generics.RetrieveUpdateDestroyAPIView):
    http_method_names = ["get", "put", "delete", "head", "options"]

    def retrieve(self, request, *args, **kwargs):
        metadata = self.get_skill()
        context = {
            **SkillHandler.build_detail_context(metadata),
            "current_version_id": metadata.current_version_id,
        }
        return OKJsonResponse(data=SkillRetrieveOutputSLZ(metadata, context=context).data)

    def update(self, request, *args, **kwargs):
        metadata = self.get_skill()
        slz = SkillBasicInfoInputSLZ(data=request.data)
        slz.is_valid(raise_exception=True)

        data_before = get_skill_audit_data(metadata)
        update_skill_basic_info(metadata, operator=request.user.username, **slz.validated_data)

        Auditor.record_skill_op_success(
            op_type=OpTypeEnum.MODIFY,
            username=request.user.username,
            gateway_id=request.gateway.id,
            instance_id=metadata.id,
            instance_name=metadata.code,
            data_before=data_before,
            data_after=get_skill_audit_data(metadata),
            comment="更新 Skill 基本信息",
        )
        return OKJsonResponse(status=status.HTTP_204_NO_CONTENT)

    def destroy(self, request, *args, **kwargs):
        metadata = self.get_skill()
        data_before = get_skill_audit_data(metadata)
        metadata_id, code = metadata.id, metadata.code
        delete_skill(metadata)

        Auditor.record_skill_op_success(
            op_type=OpTypeEnum.DELETE,
            username=request.user.username,
            gateway_id=request.gateway.id,
            instance_id=metadata_id,
            instance_name=code,
            data_before=data_before,
            data_after={},
            comment="删除 Skill",
        )
        return OKJsonResponse(status=status.HTTP_204_NO_CONTENT)


@method_decorator(
    name="get",
    decorator=extend_schema(
        description="获取 Skill 历史版本",
        responses={status.HTTP_200_OK: SkillVersionOutputSLZ(many=True)},
        tags=["WebAPI.Skill"],
    ),
)
@method_decorator(
    name="post",
    decorator=extend_schema(
        description="发布 Skill 新版本",
        request={"multipart/form-data": SkillPublishInputSLZ},
        responses={
            status.HTTP_201_CREATED: SkillPublishOutputSLZ(),
            status.HTTP_409_CONFLICT: SkillVersionOutputSLZ(),
        },
        tags=["WebAPI.Skill"],
    ),
)
class SkillVersionListCreateApi(SkillQuerySetMixin, generics.ListCreateAPIView):
    def list(self, request, *args, **kwargs):
        metadata = self.get_skill()
        versions = SkillHandler.list_versions(metadata)
        slz = SkillVersionOutputSLZ(versions, many=True, context={"current_version_id": metadata.current_version_id})
        return OKJsonResponse(data=slz.data)

    def create(self, request, *args, **kwargs):
        metadata = self.get_skill()
        slz = SkillPublishInputSLZ(data=request.data)
        slz.is_valid(raise_exception=True)
        return _publish(request, slz.validated_data, skill_name=metadata.name)


@method_decorator(
    name="put",
    decorator=extend_schema(
        description="切换 Skill 线上版本",
        request=SkillCurrentVersionUpdateInputSLZ,
        responses={status.HTTP_204_NO_CONTENT: None},
        tags=["WebAPI.Skill"],
    ),
)
class SkillCurrentVersionUpdateApi(SkillQuerySetMixin, generics.UpdateAPIView):
    http_method_names = ["put", "options"]

    def update(self, request, *args, **kwargs):
        metadata = self.get_skill()
        slz = SkillCurrentVersionUpdateInputSLZ(data=request.data)
        slz.is_valid(raise_exception=True)
        version = SkillHandler.get_version(metadata, slz.validated_data["version"])

        data_before = get_skill_audit_data(metadata)
        set_current_version(metadata, version, operator=request.user.username)

        Auditor.record_skill_op_success(
            op_type=OpTypeEnum.MODIFY,
            username=request.user.username,
            gateway_id=request.gateway.id,
            instance_id=metadata.id,
            instance_name=metadata.code,
            data_before=data_before,
            data_after=get_skill_audit_data(metadata),
            comment="切换 Skill 线上版本",
        )
        return OKJsonResponse(status=status.HTTP_204_NO_CONTENT)


@method_decorator(
    name="put",
    decorator=extend_schema(
        description="更新 Skill 状态，如归档、恢复",
        request=SkillStatusUpdateInputSLZ,
        responses={status.HTTP_204_NO_CONTENT: None},
        tags=["WebAPI.Skill"],
    ),
)
class SkillUpdateStatusApi(SkillQuerySetMixin, generics.UpdateAPIView):
    http_method_names = ["put", "options"]

    def update(self, request, *args, **kwargs):
        metadata = self.get_skill()
        slz = SkillStatusUpdateInputSLZ(data=request.data)
        slz.is_valid(raise_exception=True)

        data_before = get_skill_audit_data(metadata)
        set_skill_status(metadata, slz.validated_data["status"], operator=request.user.username)

        Auditor.record_skill_op_success(
            op_type=OpTypeEnum.MODIFY,
            username=request.user.username,
            gateway_id=request.gateway.id,
            instance_id=metadata.id,
            instance_name=metadata.code,
            data_before=data_before,
            data_after=get_skill_audit_data(metadata),
            comment=_STATUS_COMMENTS[slz.validated_data["status"]],
        )
        return OKJsonResponse(status=status.HTTP_204_NO_CONTENT)


@method_decorator(
    name="get",
    decorator=extend_schema(
        description="获取 Skill 内容（含 declaration.yaml）",
        responses={status.HTTP_200_OK: SkillFileListOutputSLZ()},
        tags=["WebAPI.Skill"],
    ),
)
class SkillFileListApi(SkillQuerySetMixin, generics.RetrieveAPIView):
    def retrieve(self, request, *args, **kwargs):
        return _file_list_response(self.get_skill(), kwargs.get("version"))


@method_decorator(
    name="get",
    decorator=extend_schema(
        description="下载 Skill（含 declaration.yaml）",
        responses={status.HTTP_200_OK: OpenApiResponse(description="zip 文件")},
        tags=["WebAPI.Skill"],
    ),
)
class SkillDownloadApi(SkillQuerySetMixin, generics.RetrieveAPIView):
    def retrieve(self, request, *args, **kwargs):
        metadata = self.get_skill()
        version = SkillHandler.get_version(metadata, kwargs.get("version"))
        content = build_skill_package_zip(metadata, version, with_declaration=True)
        SkillHandler.increase_download_count(metadata.id)
        return DownloadableResponse(
            io.BytesIO(content), filename=get_skill_package_filename(metadata, version, with_declaration=True)
        )
