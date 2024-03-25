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
from django.conf import settings
from django.core.management import BaseCommand
from packaging import version

from apigateway.biz.releaser import release
from apigateway.biz.resource_version import ResourceVersionHandler
from apigateway.biz.resource_version_diff import ResourceDifferHandler
from apigateway.core.constants import StageStatusEnum
from apigateway.core.models import Gateway, Release, ResourceVersion, Stage
from apigateway.utils import time
from apigateway.utils.redis_utils import Lock


class Command(BaseCommand):
    """批量对比网关发布资源及发布"""

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", dest="dry_run", required=False)
        parser.add_argument("--more", action="store_true", dest="more", required=False)
        parser.add_argument("--no-pub", action="store_true", dest="no_pub", required=False)

    def handle(self, dry_run: bool, more: bool, no_pub: bool, **options):
        stages = Stage.objects.filter(status=StageStatusEnum.ACTIVE.value).all()

        statistics_diff_result = []

        gateway_to_make_new_version = {}

        for stage in stages:
            if not stage.gateway.is_active:
                continue
            # 查询当前网关的最新版本
            latest_version = ResourceVersion.objects.get_latest_version(stage.gateway_id)
            if not latest_version:
                continue

            # 查询当前网关是否需要创建版本(是否有变更)
            resource_has_update = ResourceVersionHandler.need_new_version(stage.gateway_id)

            resource_diff_data = {}
            if resource_has_update:
                # 如果有差异，进行对比
                resource_diff_data = self._get_diff_data(stage, latest_version)

            # 最新资源和最新版本相比是否有更新
            resource_has_update = (
                self._len_dict(resource_diff_data.get("source_diff"))
                + self._len_dict(resource_diff_data.get("target_diff"))
                > 0
            )

            # 查询当前环境发布的版本
            resource_version_id = Release.objects.get_released_resource_version_id(stage.gateway_id, stage.name)

            # 当前最新版本和当前环境发布版本是否一致
            release_version_same = resource_version_id == latest_version.id if latest_version else True

            need_make_new_resource_version = True

            need_release = True

            # 如果当前最新资源相比最新版本有更新并且最新版本和发布的版本不一致，生成新版本不发布
            # 如果当前资源相比最新版本有更新并且最新版本和发布的版本一致，生成版本不发布
            if resource_has_update:
                need_release = False

            # 如果当前资源相比最新版本无更新并且最新版本和发布版本不一致，生成版本不发布
            # 如果当前资源相比最新版本无更新并且最新版本和发布版本一致， 生成并发布
            if not resource_has_update and not release_version_same:
                need_release = False

            gateway_to_make_new_version[stage.gateway] = latest_version

            statistics_diff_result.append(
                {
                    "stage": stage,
                    "need_make_new_version": need_make_new_resource_version,
                    "need_release": need_release,
                    "latest_version": latest_version,
                    "diff_data": resource_diff_data,
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

        if dry_run:
            return

        # 创建版本
        version_to_id = self._make_versions(gateway_to_make_new_version)

        if no_pub:
            return

        # 开始发布
        self._make_versions_publish(statistics_diff_result, version_to_id)

    def _output_more_info(self, gateway_to_make_new_version, statistics_diff_result):
        """输出更详细信息"""

        for gateway, latest_version in gateway_to_make_new_version.items():
            self.stdout.write(
                f"{gateway.name}:"
                f"\nlatest:{latest_version.object_display}"
                f"\nnew:{self._get_next_version(latest_version.object_display)}\n"
            )
        for diff_stage_info in statistics_diff_result:
            if not diff_stage_info["need_release"]:
                gateway_stage_info = diff_stage_info["stage"].gateway.name + "_" + diff_stage_info["stage"].name
                diff_data = diff_stage_info["diff_data"]
                release_version_same = diff_stage_info["release_version_same"]
                self.stdout.write(
                    f"{gateway_stage_info} diff data:{diff_data},release_version_same: {release_version_same}"
                )

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

        new_version = self._get_next_version(latest_version.object_display)

        version_data = {
            "version": new_version,
            "comment": "apigw upgrade 1.13",
        }
        return ResourceVersionHandler.create_resource_version(gateway, version_data, "apigw_system_admin")

    def _make_versions(self, gateway_to_make_new_version):
        # 创建版本
        self.stdout.write("start make new version........")

        version_to_id = {}
        for gateway, latest_version in gateway_to_make_new_version.items():
            new_version = self._make_gateway_new_version(gateway, latest_version)
            version_to_id[new_version.version] = new_version.id
            self.stdout.write(f" make gateway[{gateway.name} old:{latest_version}] new version: {new_version.version}")

        self.stdout.write("end make new version success")
        return version_to_id

    def _make_versions_publish(self, statistics_diff_result, version_to_id):
        self.stdout.write("begin publish gateways........")
        for diff_stage_info in statistics_diff_result:
            if not diff_stage_info["need_release"]:
                continue
            if diff_stage_info["need_release"]:
                new_version = self._get_next_version(diff_stage_info["latest_version"].object_display)
                resource_version_id = version_to_id.get(new_version)
                if not resource_version_id:
                    gateway_stage_info = diff_stage_info["stage"].gateway.name + "_" + diff_stage_info["stage"].name
                    self.stdout.write(f"{gateway_stage_info} can't find resource_version_id by version:{new_version}")
                    continue
                self._make_version_release(diff_stage_info["stage"], resource_version_id)
        self.stdout.write("end publish gateways........")

    def _get_next_version(self, current_version: str) -> str:
        try:
            std_version = version.parse(current_version)
            # 避免版本冲突
            return f"{std_version.major}.{std_version.minor}.{std_version.micro + 1}-alpha6666"
        except version.InvalidVersion:
            now = time.now_datetime()
            now_str = time.format(now, fmt="YYYYMMDDHHmmss")
            return current_version + f".{now_str}"

    def _len_dict(self, result) -> int:
        if not result:
            return 0
        return len(result)

    def _get_diff_data(self, stage: Stage, latest_version: ResourceVersion):
        resource_diff_data = {}

        source_resource_data = ResourceVersionHandler().get_data_by_id_or_new(stage.gateway, latest_version.id)
        target_resource_data = ResourceVersionHandler().get_data_by_id_or_new(stage.gateway, None)

        diff_data = self._diff_resource_version_data(
            source_resource_data,
            target_resource_data,
        )
        resource_has_update = len(diff_data["add"]) > 0 or len(diff_data["delete"]) > 0 or len(diff_data["update"]) > 0

        if resource_has_update:
            if len(diff_data["add"]) > 0 and diff_data["add"][0]:
                resource_diff_data = {
                    "source_diff": diff_data["add"][0].get("source", {}).get("diff", {}),
                    "target_diff": diff_data["add"][0].get("target", {}).get("diff", {}),
                }

            if (
                len(diff_data["delete"]) > 0
                and diff_data["delete"][0]
                and (
                    self._len_dict(resource_diff_data.get("source_diff"))
                    + self._len_dict(resource_diff_data.get("target_diff"))
                    == 0
                )
            ):
                resource_diff_data = {
                    "source_diff": diff_data["delete"][0].get("source", {}).get("diff", {}),
                    "target_diff": diff_data["delete"][0].get("target", {}).get("diff", {}),
                }

            if (
                len(diff_data["update"]) > 0
                and diff_data["update"][0]
                and (
                    self._len_dict(resource_diff_data.get("source_diff"))
                    + self._len_dict(resource_diff_data.get("target_diff"))
                    == 0
                )
            ):
                resource_diff_data = {
                    "source_diff": diff_data["update"][0].get("source", {}).get("diff", {}),
                    "target_diff": diff_data["update"][0].get("target", {}).get("diff", {}),
                }
        return resource_diff_data

    def _diff_resource_version_data(self, source_data: list, target_data: list) -> dict:
        source_data_map = {}
        target_data_map = {}
        for item in source_data:
            resource_id = item["id"]
            item["doc_updated_time"] = ""
            source_data_map[resource_id] = item
        for item in target_data:
            resource_id = item["id"]
            item["doc_updated_time"] = ""
            target_data_map[resource_id] = item

        resource_add = []
        resource_delete = []
        resource_update = []

        for resource_id, source_resource_data_raw in source_data_map.items():
            source_resource_differ = ResourceDifferHandler.parse_obj(source_resource_data_raw)
            target_resource_data = target_data_map.pop(resource_id, None)

            # 目标版本中资源不存在，资源被删除
            if not target_resource_data:
                resource_delete.append(source_resource_differ.dict())
                continue

            target_resource_differ = ResourceDifferHandler.parse_obj(target_resource_data)
            source_diff_value, target_diff_value = source_resource_differ.diff(target_resource_differ)

            # 资源无变化，忽略此资源
            if not source_diff_value and not target_diff_value:
                continue

            # 资源有变化，记录资源差异
            source_resource_data = source_resource_differ.dict()
            target_resource_data = target_resource_differ.dict()
            source_resource_data["diff"] = source_diff_value
            target_resource_data["diff"] = target_diff_value
            resource_update.append(
                {
                    "source": source_resource_data,
                    "target": target_resource_data,
                }
            )

        # 目标版本中，新增的资源
        if target_data_map:
            for target_resource_data in target_data_map.values():
                target_resource_differ = ResourceDifferHandler.parse_obj(target_resource_data)
                resource_add.append(target_resource_differ.dict())

        return {
            "add": sorted(resource_add, key=lambda x: x["path"]),
            "delete": sorted(resource_delete, key=lambda x: x["path"]),
            "update": sorted(resource_update, key=lambda x: x["target"]["path"]),
        }
