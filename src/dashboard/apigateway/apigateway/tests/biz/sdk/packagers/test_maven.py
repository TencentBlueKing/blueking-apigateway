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
from unittest.mock import MagicMock, patch

import pytest

from apigateway.apps.support.constants import ProgrammingLanguageEnum
from apigateway.biz.sdk.packagers import MavenSourcePackager


@pytest.fixture
def sdk_context(sdk_context):
    sdk_context.language = ProgrammingLanguageEnum.JAVA
    return sdk_context


@pytest.fixture
def packager(sdk_context):
    return MavenSourcePackager(context=sdk_context)


def _create_jar_file(output_dir):
    target_dir = output_dir.join("target")
    target_dir.mkdir()
    jar_file = target_dir.join("test.jar")
    jar_file.write("fake jar content")


def test_pack_with_mirror_url(settings, output_dir, tmpdir, sdk_context):
    mirror_url = "https://maven.aliyun.com/repository/public"
    settings.MAVEN_MIRRORS_CONFIG = {
        "default": {
            "mirror_url": mirror_url,
        }
    }
    packager = MavenSourcePackager(context=sdk_context)
    _create_jar_file(tmpdir)

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        packager.pack(output_dir)

    command = mock_run.call_args[0][0]
    assert f"-DmirrorUrl={mirror_url}" in command


def test_pack_with_default_mirror_url(settings, output_dir, tmpdir, packager):
    _create_jar_file(tmpdir)

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        packager.pack(output_dir)

    command = mock_run.call_args[0][0]
    assert f"-DmirrorUrl={settings.MAVEN_MIRRORS_CONFIG['default']['mirror_url']}" in command
