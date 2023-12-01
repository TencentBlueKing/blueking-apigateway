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
from typing import Optional, Union

from apigateway.apps.audit.constants import OpObjectTypeEnum, OpStatusEnum, OpTypeEnum
from apigateway.common.audit.shortcuts import record_audit_log

# TODO:
# 1. FIXME: 导入 带来的变更目前没有记录审计 (很多事批量操作)
# 2. FIXME: openapi 单独带来的需要逐一确认有审计
# 3. FIXME: 批量的审计床上一条还是多条？目前有两个地方记录了，一条多个实例，可能无法检索


class Auditor:
    @staticmethod
    def record_gateway_op_success(
        op_type: OpTypeEnum,
        username: str,
        gateway_id: int,
        instance_id: int,
        instance_name: str,
        data_before: Union[list, dict, str, None] = None,
        data_after: Union[list, dict, str, None] = None,
        comment: Optional[str] = None,
    ):
        if comment is None:
            comment = {
                OpTypeEnum.CREATE: "创建网关",
                OpTypeEnum.MODIFY: "更新网关",
                OpTypeEnum.DELETE: "删除网关",
            }.get(op_type, "-")

        record_audit_log(
            username=username,
            op_type=op_type.value,
            op_status=OpStatusEnum.SUCCESS.value,
            op_object_group=gateway_id,
            op_object_type=OpObjectTypeEnum.GATEWAY.value,
            op_object_id=instance_id,
            op_object=instance_name,
            data_before=data_before,
            data_after=data_after,
            comment=comment,
        )

    @staticmethod
    def record_gateway_label_op_success(
        op_type: OpTypeEnum,
        username: str,
        gateway_id: int,
        instance_id: int,
        instance_name: str,
        data_before: Union[list, dict, str, None] = None,
        data_after: Union[list, dict, str, None] = None,
        comment: Optional[str] = None,
    ):
        if comment is None:
            comment = {
                OpTypeEnum.CREATE: "创建网关标签",
                OpTypeEnum.MODIFY: "更新网关标签",
                OpTypeEnum.DELETE: "删除网关标签",
            }.get(op_type, "-")

        record_audit_log(
            username=username,
            op_type=op_type.value,
            op_status=OpStatusEnum.SUCCESS.value,
            op_object_group=gateway_id,
            op_object_type=OpObjectTypeEnum.GATEWAY_LABEL.value,
            op_object_id=instance_id,
            op_object=instance_name,
            data_before=data_before,
            data_after=data_after,
            comment=comment,
        )

    @staticmethod
    def record_resource_doc_op_success(
        op_type: OpTypeEnum,
        username: str,
        gateway_id: int,
        instance_id: int,
        instance_name: str,
        data_before: Union[list, dict, str, None] = None,
        data_after: Union[list, dict, str, None] = None,
        comment: Optional[str] = None,
    ):
        if comment is None:
            comment = {
                OpTypeEnum.CREATE: "创建资源文档",
                OpTypeEnum.MODIFY: "更新资源文档",
                OpTypeEnum.DELETE: "删除资源文档",
            }.get(op_type, "-")

        record_audit_log(
            username=username,
            op_type=op_type.value,
            op_status=OpStatusEnum.SUCCESS.value,
            op_object_group=gateway_id,
            op_object_type=OpObjectTypeEnum.RESOURCE_DOC.value,
            op_object_id=instance_id,
            op_object=instance_name,
            data_before=data_before,
            data_after=data_after,
            comment=comment,
        )

    @staticmethod
    def record_resource_op_success(
        op_type: OpTypeEnum,
        username: str,
        gateway_id: int,
        instance_id: int,
        instance_name: str,
        data_before: Union[list, dict, str, None] = None,
        data_after: Union[list, dict, str, None] = None,
        comment: Optional[str] = None,
    ):
        if comment is None:
            comment = {
                OpTypeEnum.CREATE: "创建资源",
                OpTypeEnum.MODIFY: "更新资源",
                OpTypeEnum.DELETE: "删除资源",
            }.get(op_type, "-")
        # extras: 批量更新资源/批量删除资源

        record_audit_log(
            username=username,
            op_type=op_type.value,
            op_status=OpStatusEnum.SUCCESS.value,
            op_object_group=gateway_id,
            op_object_type=OpObjectTypeEnum.RESOURCE.value,
            op_object_id=instance_id,
            op_object=instance_name,
            data_before=data_before,
            data_after=data_after,
            comment=comment,
        )

    @staticmethod
    def record_backend_op_success(
        op_type: OpTypeEnum,
        username: str,
        gateway_id: int,
        instance_id: int,
        instance_name: str,
        data_before: Union[list, dict, str, None] = None,
        data_after: Union[list, dict, str, None] = None,
        comment: Optional[str] = None,
    ):
        if comment is None:
            comment = {
                OpTypeEnum.CREATE: "创建后端服务",
                OpTypeEnum.MODIFY: "更新后端服务",
                OpTypeEnum.DELETE: "删除后端服务",
            }.get(op_type, "-")

        record_audit_log(
            username=username,
            op_type=op_type.value,
            op_status=OpStatusEnum.SUCCESS.value,
            op_object_group=gateway_id,
            op_object_type=OpObjectTypeEnum.BACKEND.value,
            op_object_id=instance_id,
            op_object=instance_name,
            data_before=data_before,
            data_after=data_after,
            comment=comment,
        )

    @staticmethod
    def record_micro_gateway_op_success(
        op_type: OpTypeEnum,
        username: str,
        gateway_id: int,
        instance_id: int,
        instance_name: str,
        data_before: Union[list, dict, str, None] = None,
        data_after: Union[list, dict, str, None] = None,
        comment: Optional[str] = None,
    ):
        if comment is None:
            comment = {
                OpTypeEnum.CREATE: "创建微网关实例",
                OpTypeEnum.MODIFY: "更新微网关实例",
                OpTypeEnum.DELETE: "删除微网关实例",
            }.get(op_type, "-")

        record_audit_log(
            username=username,
            op_type=op_type.value,
            op_status=OpStatusEnum.SUCCESS.value,
            op_object_group=gateway_id,
            op_object_type=OpObjectTypeEnum.MICRO_GATEWAY.value,
            op_object_id=instance_id,
            op_object=instance_name,
            data_before=data_before,
            data_after=data_after,
            comment=comment,
        )

    @staticmethod
    def record_plugin_op_success(
        op_type: OpTypeEnum,
        username: str,
        gateway_id: int,
        instance_id: int,
        instance_name: str,
        data_before: Union[list, dict, str, None] = None,
        data_after: Union[list, dict, str, None] = None,
        comment: Optional[str] = None,
    ):
        if comment is None:
            comment = {
                OpTypeEnum.CREATE: "创建插件",
                OpTypeEnum.MODIFY: "更新插件",
                OpTypeEnum.DELETE: "删除插件",
            }.get(op_type, "-")

        record_audit_log(
            username=username,
            op_type=op_type.value,
            op_status=OpStatusEnum.SUCCESS.value,
            op_object_group=gateway_id,
            op_object_type=OpObjectTypeEnum.PLUGIN.value,
            op_object_id=instance_id,
            op_object=instance_name,
            data_before=data_before,
            data_after=data_after,
            comment=comment,
        )

    @staticmethod
    def record_stage_op_success(
        op_type: OpTypeEnum,
        username: str,
        gateway_id: int,
        instance_id: int,
        instance_name: str,
        data_before: Union[list, dict, str, None] = None,
        data_after: Union[list, dict, str, None] = None,
        comment: Optional[str] = None,
    ):
        if comment is None:
            comment = {
                OpTypeEnum.CREATE: "创建环境",
                OpTypeEnum.MODIFY: "更新环境",
                OpTypeEnum.DELETE: "删除环境",
            }.get(op_type, "-")
        # extra: 环境状态变更/更新环境变量

        record_audit_log(
            username=username,
            op_type=op_type.value,
            op_status=OpStatusEnum.SUCCESS.value,
            op_object_group=gateway_id,
            op_object_type=OpObjectTypeEnum.STAGE.value,
            op_object_id=instance_id,
            op_object=instance_name,
            data_before=data_before,
            data_after=data_after,
            comment=comment,
        )

    @staticmethod
    def record_release_op_success(
        op_type: OpTypeEnum,
        username: str,
        gateway_id: int,
        instance_id: int,
        instance_name: str,
        data_before: Union[list, dict, str, None] = None,
        data_after: Union[list, dict, str, None] = None,
        comment: Optional[str] = None,
    ):
        if comment is None:
            comment = {
                OpTypeEnum.CREATE: "版本发布",
            }.get(op_type, "-")

        record_audit_log(
            username=username,
            op_type=op_type.value,
            op_status=OpStatusEnum.SUCCESS.value,
            op_object_group=gateway_id,
            op_object_type=OpObjectTypeEnum.RELEASE.value,
            op_object_id=instance_id,
            op_object=instance_name,
            data_before=data_before,
            data_after=data_after,
            comment=comment,
        )

    @staticmethod
    def record_resource_version_op_success(
        op_type: OpTypeEnum,
        username: str,
        gateway_id: int,
        instance_id: int,
        instance_name: str,
        data_before: Union[list, dict, str, None] = None,
        data_after: Union[list, dict, str, None] = None,
        comment: Optional[str] = None,
    ):
        if comment is None:
            comment = {
                OpTypeEnum.CREATE: "生成版本",
            }.get(op_type, "-")

        record_audit_log(
            username=username,
            op_type=op_type.value,
            op_status=OpStatusEnum.SUCCESS.value,
            op_object_group=gateway_id,
            op_object_type=OpObjectTypeEnum.RESOURCE_VERSION.value,
            op_object_id=instance_id,
            op_object=instance_name,
            data_before=data_before,
            data_after=data_after,
            comment=comment,
        )

    @staticmethod
    def record_stage_backend_op_success(
        op_type: OpTypeEnum,
        username: str,
        gateway_id: int,
        instance_id: int,
        instance_name: str,
        data_before: Union[list, dict, str, None] = None,
        data_after: Union[list, dict, str, None] = None,
        comment: Optional[str] = None,
    ):
        if comment is None:
            comment = {
                OpTypeEnum.CREATE: "创建环境后端配置",
                OpTypeEnum.MODIFY: "更新环境后端配置",
                OpTypeEnum.DELETE: "删除环境后端配置",
            }.get(op_type, "-")

        record_audit_log(
            username=username,
            op_type=op_type.value,
            op_status=OpStatusEnum.SUCCESS.value,
            op_object_group=gateway_id,
            op_object_type=OpObjectTypeEnum.STAGE_BACKEND.value,
            op_object_id=instance_id,
            op_object=instance_name,
            data_before=data_before,
            data_after=data_after,
            comment=comment,
        )
