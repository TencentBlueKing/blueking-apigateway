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
from typing import Dict, List

from django.conf import settings
from django.core.management import BaseCommand
from packaging import version

from apigateway.biz.releaser import release
from apigateway.biz.resource import ResourceHandler
from apigateway.biz.resource_version import ResourceVersionHandler
from apigateway.biz.resource_version_diff import ResourceDifferHandler
from apigateway.core.constants import GatewayStatusEnum, StageStatusEnum
from apigateway.core.models import Gateway, Release, Resource, ResourceVersion, Stage
from apigateway.utils import time
from apigateway.utils.redis_utils import Lock
from apigateway.utils.version import get_next_version


class Command(BaseCommand):
    """批量对比网关发布资源及发布"""

    def add_arguments(self, parser):
        parser.add_argument("--run", action="store_true", dest="run", required=False)
        parser.add_argument("--more", action="store_true", dest="more", required=False)
        parser.add_argument("--pub", action="store_true", dest="pub", required=False)

    def handle(self, run: bool, more: bool, pub: bool, **options):
        stages = Stage.objects.filter(
            status=StageStatusEnum.ACTIVE.value, gateway__status=GatewayStatusEnum.ACTIVE.value
        ).all()

        statistics_diff_result = []

        gateway_to_make_new_version = {}

        for stage in stages:
            # 查询当前网关的最新版本
            latest_version = ResourceVersion.objects.get_latest_version(stage.gateway_id)
            if not latest_version:
                continue

            # 查询当前环境发布的版本
            resource_version_id = Release.objects.get_released_resource_version_id(stage.gateway_id, stage.name)

            if not resource_version_id:
                continue

            # 判断对比资源是否有更新
            is_resource_has_update = self._get_resource_update(stage, latest_version)

            # 判断是否需要创建版本
            need_make_new_resource_version = self._is_need_make_new_version(is_resource_has_update, latest_version)
            if need_make_new_resource_version:
                gateway_to_make_new_version[stage.gateway] = latest_version

            # 判断是否需要进行发布
            # 当前最新版本和当前环境发布版本是否一致
            release_version_same = resource_version_id == latest_version.id
            need_release = self._is_need_release(
                is_resource_has_update, release_version_same, latest_version, resource_version_id
            )

            statistics_diff_result.append(
                {
                    "stage": stage,
                    "need_make_new_version": need_make_new_resource_version,
                    "need_release": need_release,
                    "latest_version": latest_version,
                    "diff_data": self._get_diff_data(stage, latest_version),
                    "release_version_same": release_version_same,
                }
            )

        # 总共需要打版本的网关数目
        total_gateway_count = len(gateway_to_make_new_version)
        self.stdout.write(
            f"总共需要打版本的网关总数：{total_gateway_count}\n",
        )

        # 总共需要发布的环境数目
        total_stage_need_publish = len(
            [diff_stage_info for diff_stage_info in statistics_diff_result if diff_stage_info["need_release"]]
        )

        self.stdout.write(f"总共需要发布的环境总数：{total_stage_need_publish}\n")
        self.stdout.write(f"总共不能发布的环境总数：{len(statistics_diff_result) - total_stage_need_publish}\n")

        if more:
            self._output_more_info(gateway_to_make_new_version, statistics_diff_result)

        if not run:
            return

        # 创建版本并发布
        self._make_version_and_publish(gateway_to_make_new_version, statistics_diff_result, pub)

    def _output_more_info(self, gateway_to_make_new_version, statistics_diff_result):
        """输出更详细信息"""

        for gateway, latest_version in gateway_to_make_new_version.items():
            self.stdout.write(
                f"{gateway.name}:"
                f"\nlatest:{latest_version.object_display}"
                f"\nnew:{self._get_next_version(gateway,latest_version)}\n"
            )
        for diff_stage_info in statistics_diff_result:
            need_release = diff_stage_info["need_release"]
            gateway_stage_info = diff_stage_info["stage"].gateway.name + "_" + diff_stage_info["stage"].name
            diff_data = diff_stage_info["diff_data"]
            release_version_same = diff_stage_info["release_version_same"]
            self.stdout.write(
                f"{gateway_stage_info}: need_release:{need_release},"
                f"release_version_same: {release_version_same},diff data:{diff_data}"
            )

    def _is_need_make_new_version(self, is_resource_has_update: bool, latest_version: ResourceVersion) -> bool:
        """判断是否需要进行创建版本"""

        # 如果是已经打过版本的则不需要重新再生成版本,考虑重复调用的情况
        # 如果是没有生成版本，则也不需要生成
        if latest_version.created_by == "apigw_system_admin" and not is_resource_has_update:
            return False

        # 如果当前最新版本已经是基于1.13创建的则也不需要
        if latest_version.is_schema_v2:
            return False

        return True

    def _is_need_release(
        self,
        is_resource_has_update: bool,
        release_version_same: bool,
        latest_version: ResourceVersion,
        release_resource_version_id: int,
    ) -> bool:
        """判断是否需要进行发布"""

        # 如果当前最新资源相比最新版本有更新并且最新版本和发布的版本不一致，生成新版本不发布
        # 如果当前资源相比最新版本有更新并且最新版本和发布的版本一致，生成版本不发布
        # 如果没有生成过版本则不需要发布
        # 如果最新发布的版本是v2，则也不需要发布

        release_resource_version = ResourceVersion.objects.get(id=release_resource_version_id)

        if is_resource_has_update or release_resource_version.is_schema_v2:
            return False

        # 重试场景
        if latest_version.created_by == "apigw_system_admin":
            # 如果当前资源最新版本和发布的版本一致则不用发布
            if release_version_same:
                return False

            # 获取真正的排除apigw_system_admin创建的最新版本
            real_latest_resource_version = self.get_real_latest_resource_version(latest_version)

            # 如果真正最新的版本和发布版本一致并且没有更新，则可以发布
            if not is_resource_has_update and (
                real_latest_resource_version and real_latest_resource_version.id == release_resource_version_id
            ):
                return True

            # 如果真正最新的版本和发布版本不一致，则不可以发布
            if real_latest_resource_version and real_latest_resource_version.id != release_resource_version_id:
                return False

        # 非重试场景
        # 如果最新资源没有更新，并且发布资源版本和最新资源一致，则可以发布
        elif not is_resource_has_update and release_version_same:
            return True

        return False

    def _get_resource_update(self, stage: Stage, latest_version: ResourceVersion):
        """判断资源是否有更新"""

        latest_version = self.get_real_latest_resource_version(latest_version)

        # 查询当前网关是否需要创建版本(是否有变更)
        resource_has_update = self.need_new_version(latest_version)

        resource_diff_data = {}
        if resource_has_update:
            # 如果有差异，进行对比

            resource_diff_data = self._get_diff_data(stage, latest_version)

        # 最新资源和最新版本相比是否有更新
        return (
            self._len_dict(resource_diff_data.get("source_diff"))
            + self._len_dict(resource_diff_data.get("target_diff"))
            > 0
        )

    def get_real_latest_resource_version(self, latest_version: ResourceVersion) -> ResourceVersion:
        """
        获取非升级之前的最新版本
        """

        # 重试场景,排除升级脚本创建的版本
        if latest_version.is_schema_v2:
            latest_version = (
                ResourceVersion.objects.filter(gateway_id=latest_version.gateway.id)
                .exclude(created_by="apigw_system_admin")
                .last()
            )

        return latest_version

    def need_new_version(self, latest_version: ResourceVersion):
        """
        是否需要创建新的资源版本
        """

        resource_last_updated_time = ResourceHandler.get_last_updated_time(latest_version.gateway.id)

        if not (latest_version or resource_last_updated_time):
            return False

        # 无资源版本
        if not latest_version:
            return True

        # 如果有最近更新的资源，最近的更新资源时间 > 最新版本生成时间
        if resource_last_updated_time and resource_last_updated_time > latest_version.created_time:
            return True

        # 版本中资源数量是否发生变化
        # some resource could be deleted
        resource_count = Resource.objects.filter(gateway_id=latest_version.gateway.id).count()
        if resource_count != len(latest_version.data):
            return True

        return False

    def _make_version_release(self, stage: Stage, resource_version_id: int):
        """进行环境版本发布"""

        try:
            with Lock(
                f"{stage.gateway.id}_{stage.id}",
                timeout=settings.REDIS_PUBLISH_LOCK_TIMEOUT,
                try_get_times=settings.REDIS_PUBLISH_LOCK_RETRY_GET_TIMES,
            ):
                # do release, will record audit log
                release(
                    gateway=stage.gateway,
                    stage_id=stage.id,
                    resource_version_id=resource_version_id,
                    comment="gateway upgrade into 1.13",
                    username="apigw_system_admin",
                )
                self.stdout.write(f"{stage.gateway.name}-{stage.name} release {resource_version_id} success")
        except Exception as err:
            self.stdout.write(f"{stage.gateway.name}-{stage.name} release {resource_version_id} fail:{err}\n")

    def _make_gateway_new_version(self, gateway: Gateway, latest_version: ResourceVersion) -> ResourceVersion:
        """对网关进行新建版本"""

        version_data = {
            "version": self._get_next_version(gateway, latest_version),
            "comment": "apigw upgrade 1.13",
        }
        return ResourceVersionHandler.create_resource_version(gateway, version_data, "apigw_system_admin")

    def _get_next_version(self, gateway: Gateway, latest_version: ResourceVersion) -> str:
        new_version = get_next_version(latest_version.object_display)
        # 如果是注册网关指定了版本，为了保持和之前版本一致需要特殊处理
        # eg: 1.2.0+20240307031201
        if "+" in latest_version.object_display:
            try:
                latest_version_std = version.parse(latest_version.version)
                now_str = time.format(time.now_datetime(), fmt="YYYYMMDDHHmmss")
                new_version = "%s+%s" % (latest_version_std.public, now_str)
            except version.InvalidVersion:
                pass

        # 如果版本有冲突
        if ResourceVersion.objects.get_id_by_version(gateway.id, new_version):
            new_version += ".alpha1"

        return new_version

    def _make_version_and_publish(self, gateway_to_make_new_version, statistics_diff_result, pub: bool):
        """创建版本并且按照网关维度进行发布"""

        self.stdout.write("start make version and publish........")

        gateway_id_to_stages_for_publish: Dict[int, List[Stage]] = {}

        stage_id_to_resource_version: Dict[int, ResourceVersion] = {}

        for diff_stage_info in statistics_diff_result:
            stage = diff_stage_info["stage"]
            if not diff_stage_info["need_release"]:
                continue
            stage_id_to_resource_version[stage.id] = diff_stage_info["latest_version"]
            if stage.gateway_id in gateway_id_to_stages_for_publish:
                gateway_id_to_stages_for_publish[stage.gateway_id].append(stage)
                continue
            gateway_id_to_stages_for_publish[stage.gateway_id] = [stage]

        # 需要创建版本的先创建版本然后再发布
        for gateway, latest_version in gateway_to_make_new_version.items():
            new_version = self._make_gateway_new_version(gateway, latest_version)
            self.stdout.write(f" make gateway[{gateway.name} old:{latest_version}] new version: {new_version.version}")

            # 开始进行发布
            if not pub:
                continue

            for stage in gateway_id_to_stages_for_publish.get(gateway.id, []):
                self._make_version_release(stage, new_version.id)

            if gateway.id in gateway_id_to_stages_for_publish:
                del gateway_id_to_stages_for_publish[gateway.id]

        if not pub:
            return

        # 不需要创建版本的发布
        for stages in gateway_id_to_stages_for_publish.values():  # noqa: F821
            for stage in stages:
                release_resource_version = stage_id_to_resource_version.get(stage.id, None)
                if not release_resource_version:
                    continue
                self._make_version_release(stage, release_resource_version.id)

        self.stdout.write("end make new version and publish")

    def _len_dict(self, result) -> int:
        if not result:
            return 0
        return len(result)

    def _has_diff(self, resource_diff_data) -> bool:
        return (
            self._len_dict(resource_diff_data.get("source_diff"))
            + self._len_dict(resource_diff_data.get("target_diff"))
            > 0
        )

    def _get_diff_data(self, stage: Stage, latest_version: ResourceVersion):
        """获取对比差异结果"""

        latest_version = self.get_real_latest_resource_version(latest_version)

        resource_diff_data = {}

        source_resource_data = ResourceVersionHandler().get_data_by_id_or_new(stage.gateway, latest_version.id)
        target_resource_data = ResourceVersionHandler().get_data_by_id_or_new(stage.gateway, None)

        diff_data = ResourceDifferHandler.diff_resource_version_data(
            source_resource_data,
            target_resource_data,
            {},
            {},
        )
        resource_has_update = len(diff_data["add"]) > 0 or len(diff_data["delete"]) > 0 or len(diff_data["update"]) > 0

        if resource_has_update:
            if len(diff_data["add"]) > 0 and diff_data["add"][0]:
                resource_diff_data = {
                    "source_diff": diff_data["add"][0].get("source", {}).get("diff", {}),
                    "target_diff": diff_data["add"][0].get("target", {}).get("diff", {}),
                }
                if self._has_diff(resource_diff_data):
                    return resource_diff_data

            if len(diff_data["delete"]) > 0 and diff_data["delete"][0]:
                resource_diff_data = {
                    "source_diff": diff_data["delete"][0].get("source", {}).get("diff", {}),
                    "target_diff": diff_data["delete"][0].get("target", {}).get("diff", {}),
                }
                if self._has_diff(resource_diff_data):
                    return resource_diff_data

            if len(diff_data["update"]) > 0 and diff_data["update"][0]:
                resource_diff_data = {
                    "source_diff": diff_data["update"][0].get("source", {}).get("diff", {}),
                    "target_diff": diff_data["update"][0].get("target", {}).get("diff", {}),
                }
        return resource_diff_data
