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
import pytest

from apigateway.apps.support.api_sdk.generators.swagger import PythonTemplateGenerator


@pytest.fixture
def python_generator(sdk_context):
    return PythonTemplateGenerator(context=sdk_context)


def test_python_generator(public_api_resources, output_dir, tmpdir, python_generator: PythonTemplateGenerator):
    python_generator.generate(output_dir, public_api_resources)
    assert tmpdir.join("setup.py").exists()
