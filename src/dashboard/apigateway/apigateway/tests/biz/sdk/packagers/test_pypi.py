#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2025 Tencent. All rights reserved.
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

from apigateway.biz.sdk.packagers.pypi import SourcePackager


@pytest.fixture
def packager(faker, sdk_context):
    return SourcePackager(
        context=sdk_context,
    )


def test_pack(output_dir, python_setup_script, python_setup_history, packager: SourcePackager):
    packager.pack(output_dir)

    python_setup_history = python_setup_history.read()
    assert "setup.py sdist" in python_setup_history
