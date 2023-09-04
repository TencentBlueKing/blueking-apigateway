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
import os
import shutil
from subprocess import check_output

import pytest
from django.core.management import call_command

from apigateway.utils.yaml import yaml_load_all


def test_generate_chart(edge_gateway, edge_gateway_stage, edge_release, tmpdir):
    chart_file = "chart.tgz"
    values_file = "values.yaml"
    call_command(
        "generate_chart",
        "--gateway-name",
        edge_gateway.name,
        "--stage-name",
        edge_gateway_stage.name,
        "--output-dir",
        tmpdir,
        "--chart-file",
        chart_file,
        "--values-file",
        values_file,
    )

    helm_path = shutil.which("helm")
    if helm_path is None:
        pytest.skip("helm command not found")

    output = check_output(
        [
            helm_path,
            "template",
            os.path.join(tmpdir, chart_file),
            "-f",
            os.path.join(tmpdir, values_file),
        ]
    )

    # it should be a valid yaml
    yaml_load_all(output)
