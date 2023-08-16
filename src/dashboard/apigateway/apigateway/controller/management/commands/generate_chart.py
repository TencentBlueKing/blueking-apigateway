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
import logging
import os
import shutil
from unittest.mock import MagicMock

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apigateway.controller.distributor.helm import HelmDistributor
from apigateway.core.models import Gateway, Release, Stage
from apigateway.utils.yaml import yaml_dumps

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    生成网关指定环境，当前发布版本的 chart

    仅用于测试
    """

    def add_arguments(self, parser):
        parser.add_argument("--api-name", type=str, help="网关名", required=True)
        parser.add_argument("--stage-name", type=str, default="prod", help="网关环境")
        parser.add_argument("--output-dir", type=str, default=settings.BASE_DIR, help="输出目录")
        parser.add_argument("--chart-file", type=str, default="chart.tgz", help="chart 文件名")
        parser.add_argument("--values-file", type=str, default="values.yaml", help="values 文件名")

    def _get_gateway(self, gateway_name: str) -> Gateway:
        try:
            return Gateway.objects.get(name=gateway_name)
        except Gateway.DoesNotExist:
            raise CommandError(f"网关【name={gateway_name}】不存在")

    def _get_stage(self, gateway: Gateway, stage_name: str) -> Stage:
        try:
            return Stage.objects.get(api=gateway, name=stage_name)
        except Stage.DoesNotExist:
            raise CommandError(f"网关【name={gateway.name}】下环境【name={stage_name}】不存在")

    def _get_release(self, gateway_name: str, stage_name: str) -> Release:
        gateway = self._get_gateway(gateway_name)
        stage = self._get_stage(gateway, stage_name)
        try:
            return Release.objects.get(gateway=gateway, stage=stage)
        except Release.DoesNotExist:
            raise CommandError(f"网关【name={gateway.name}】下环境【name={stage.name}】未发布")

    def handle(self, api_name: str, stage_name: str, output_dir: str, chart_file: str, values_file: str, **options):
        release = self._get_release(api_name, stage_name)
        stage = release.stage
        micro_gateway = stage.micro_gateway
        if not micro_gateway:
            raise CommandError("网关环境未绑定微网关实例")

        class FakeChartHelper:
            chart_path = os.path.join(output_dir, chart_file)

            def __getattr__(self, name):
                return MagicMock()

            def push_chart(self, chart_file: str, *args, **kwargs):
                shutil.move(chart_file, self.chart_path)

        class FakeReleaseHelper:
            def __getattr__(self, name):
                return MagicMock()

            def ensure_release(self, values: dict, *args, **kwargs):
                with open(os.path.join(output_dir, values_file), "w") as fp:
                    fp.write(yaml_dumps(values))

                return True, MagicMock()

        release_helper = FakeReleaseHelper()
        chart_helper = FakeChartHelper()
        distributor = HelmDistributor(
            generate_chart=True,
            release_helper=release_helper,  # type: ignore
            chart_helper=chart_helper,  # type: ignore
            release_callback=None,
        )

        is_success, err_msg = distributor.distribute(release, micro_gateway)
        assert is_success
        assert err_msg == ""
