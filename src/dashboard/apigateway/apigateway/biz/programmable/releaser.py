# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关 (BlueKing - APIGateway) available.
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
from typing import Any, Dict, List, Optional

from django.conf import settings

from apigateway.apps.audit.constants import OpTypeEnum
from apigateway.apps.programmable_gateway.models import ProgrammableGatewayDeployHistory
from apigateway.biz.audit import Auditor
from apigateway.biz.release import ReleaseHandler
from apigateway.biz.released_resource import ReleasedResourceHandler
from apigateway.common.tenant.user_credentials import UserCredentials
from apigateway.components.bkpaas import (
    deploy_paas_app,
    get_paas_deployment_result,
    get_paas_offline_result,
    set_paas_stage_env,
)
from apigateway.core.constants import (
    PublishSourceEnum,
    ReleaseHistoryStatusEnum,
)
from apigateway.core.models import (
    Gateway,
    ReleaseHistory,
    Stage,
)
from apigateway.utils.django import get_model_dict


class ProgrammableGatewayReleaser:
    @staticmethod
    def deploy(
        gateway: Gateway,
        stage_id: int,
        branch: str,
        version_type: str,
        commit_id: str,
        version: str,
        comment: str,
        user_credentials: Optional[UserCredentials] = None,
        username: str = "",
    ) -> str:
        """
        编程网关部署
        """
        stage = Stage.objects.get(id=stage_id)

        # 调用 pass 平台接口设置环境变量：版本号 + 版本日志
        set_paas_stage_env(
            app_code=gateway.name,
            module="default",
            stage=stage.name,
            env={
                # "1.0.0+prod": 代码模版有通过版本号和环境名拼接的方式获取版本号，所以这里需要去掉
                "BK_APIGW_RELEASE_VERSION": version.split("+")[0],  # 不带环境 name
                "BK_APIGW_RELEASE_COMMENT": comment,
            },
            user_credentials=user_credentials,
        )

        # 调用 pass 平台部署接口
        deploy_id = deploy_paas_app(
            app_code=gateway.name,
            module="default",
            env=stage.name,
            revision=commit_id,
            branch=branch,
            version_type=version_type,
            user_credentials=user_credentials,
        )

        # 创建部署历史
        instance = ProgrammableGatewayDeployHistory.objects.create(
            gateway=gateway,
            stage=stage,
            branch=branch,
            version=version,
            commit_id=commit_id,
            deploy_id=deploy_id,
            created_by=username,
            source=PublishSourceEnum.VERSION_PUBLISH.value,
        )

        # record audit log
        Auditor.record_release_op_success(
            op_type=OpTypeEnum.CREATE,
            username=username or settings.GATEWAY_DEFAULT_CREATOR,
            gateway_id=gateway.id,
            instance_id=instance.id,
            instance_name=f"{stage.name}:{version}",
            data_before={},
            data_after=get_model_dict(instance),
        )
        return deploy_id

    @staticmethod
    def _get_paas_deploy_result(
        gateway: Gateway, deploy_history: ProgrammableGatewayDeployHistory, user_credentials: UserCredentials
    ) -> Dict[str, Any]:
        """查询 paas 的 deploy 结果"""
        # 查询 paas 部署结果
        is_offline = deploy_history.source != PublishSourceEnum.VERSION_PUBLISH.value
        if not is_offline:
            return get_paas_deployment_result(
                app_code=gateway.name,
                module="default",
                deploy_id=deploy_history.deploy_id,
                user_credentials=user_credentials,
            )
        return get_paas_offline_result(
            app_code=gateway.name,
            module="default",
            deploy_id=deploy_history.deploy_id,
            user_credentials=user_credentials,
        )

    @staticmethod
    def get_stage_deploy_status(gateway: Gateway, stage_id: int, user_credentials: UserCredentials) -> Dict[str, Any]:
        """查询 stage 的 deploy 状态"""
        latest_deploy_history = ProgrammableGatewayDeployHistory()
        last_deploy_history = ProgrammableGatewayDeployHistory()
        # 查询当前 deploy 历史
        deploy_history = (
            ProgrammableGatewayDeployHistory.objects.filter(
                gateway=gateway,
                stage_id=stage_id,
            )
            .order_by("-id")
            .first()
        )
        stage_release = ReleasedResourceHandler.get_stage_release(gateway, [stage_id]).get(stage_id)
        # 正在发布版本状态
        latest_publish_status = ""
        latest_history_id = 0
        # 当前生效版本状态
        last_publish_status = ""
        if stage_release:
            # 优先使用与 stage_release 匹配的记录
            last_deploy_history = (
                ProgrammableGatewayDeployHistory.objects.filter(
                    gateway=gateway, stage_id=stage_id, version=stage_release["resource_version_display"]
                ).first()
                or deploy_history  # 回退到最新记录
            )
            # 查询当前生效环境的 release history
            last_release_history = ReleaseHistory.objects.filter(
                gateway=gateway, stage_id=stage_id, resource_version__version=stage_release["resource_version_display"]
            ).first()
            if last_release_history:
                last_publish_status = ReleaseHandler.get_release_status(last_release_history.id)

            # 如果 stage_release 的版本和 deploy_history 的第一个不一致，说明正在发布
            if stage_release["resource_version_display"] != deploy_history.version:
                latest_deploy_history = deploy_history
                latest_publish_status = ReleaseHistoryStatusEnum.DOING.value

        if deploy_history and latest_publish_status != "":
            if not deploy_history.publish_id:
                latest_publish_status = ReleaseHistoryStatusEnum.DOING.value
            else:
                latest_publish_status = ReleaseHandler.get_release_status(deploy_history.publish_id)
                latest_history_id = deploy_history.publish_id

        if deploy_history:
            result = ProgrammableGatewayReleaser._get_paas_deploy_result(gateway, deploy_history, user_credentials)
            # 正在发布的话需要判断是否失败
            if latest_publish_status != "" and result.get("status", "") == "failed":
                latest_publish_status = ReleaseHistoryStatusEnum.FAILURE.value

            # 第一次发布
            if last_publish_status == "" and result.get("status", "") == "failed":
                last_deploy_history = deploy_history
                last_publish_status = ReleaseHistoryStatusEnum.FAILURE.value
            elif last_publish_status == "" and result.get("status", "") != "failed":
                latest_deploy_history = deploy_history
                if deploy_history.publish_id:
                    latest_publish_status = ReleaseHandler.get_release_status(deploy_history.publish_id)
                else:
                    latest_publish_status = ReleaseHistoryStatusEnum.DOING.value
        return {
            "latest_deploy_history": latest_deploy_history,
            "latest_history_id": latest_history_id,
            "latest_publish_status": latest_publish_status,
            "last_publish_status": last_publish_status,
            "last_deploy_history": last_deploy_history,
        }

    @staticmethod
    def batch_get_stage_deploy_status(
        gateway: Gateway, stage_ids: List[int], user_credentials: UserCredentials
    ) -> dict[int, dict[str, Any]]:
        """批量查询 stage 的 deploy 状态"""
        return {
            stage_id: ProgrammableGatewayReleaser.get_stage_deploy_status(gateway, stage_id, user_credentials)
            for stage_id in stage_ids
        }
