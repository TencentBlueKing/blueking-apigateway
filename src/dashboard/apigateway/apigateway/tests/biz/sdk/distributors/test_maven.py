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
from unittest.mock import MagicMock, patch

import pytest

from apigateway.apps.support.constants import ProgrammingLanguageEnum
from apigateway.biz.sdk.distributors.maven import MAVEN_CENTRAL_URL, MavenSourceDistributor
from apigateway.biz.sdk.exceptions import DistributeError


@pytest.fixture
def sdk_context(sdk_context):
    sdk_context.language = ProgrammingLanguageEnum.JAVA
    return sdk_context


@pytest.fixture
def maven_config_base(faker):
    return {
        "repository_url": faker.url(),
        "repository_id": "test-maven",
        "username": faker.user_name(),
        "password": faker.password(),
        "ssl_insecure": False,
        "mirror_url": "",
    }


@pytest.fixture
def distributor(faker, mocker, sdk_context, settings, maven_config_base):
    settings.MAVEN_MIRRORS_CONFIG = {
        MavenSourceDistributor.repository: maven_config_base,
    }

    return MavenSourceDistributor(context=sdk_context)


class TestMavenSourceDistributor:
    def test_enabled_with_repository_url(self, distributor):
        """测试配置了 repository_url 时 enabled 返回 True"""
        assert distributor.enabled() is True

    def test_enabled_without_repository_url(self, sdk_context, settings):
        """测试未配置 repository_url 时 enabled 返回 False"""
        settings.MAVEN_MIRRORS_CONFIG = {
            "default": {
                "repository_url": "",
                "repository_id": "",
                "username": "",
                "password": "",
            }
        }
        distributor = MavenSourceDistributor(context=sdk_context)
        assert distributor.enabled() is False

    def test_get_download_url(self, distributor):
        """测试获取下载 URL"""
        distributor.context.package = "test-sdk"
        distributor.context.version = "1.0.0"

        url = distributor.get_download_url()

        assert "com/tencent/bkapi/test-sdk/1.0.0/test-sdk-1.0.0.jar" in url

    def test_distribute_with_ssl_insecure(self, sdk_context, settings, output_dir, tmpdir, faker):
        """测试配置了 ssl_insecure 时命令包含 SSL 跳过参数"""
        settings.MAVEN_MIRRORS_CONFIG = {
            "default": {
                "repository_url": faker.url(),
                "repository_id": "test-maven",
                "username": faker.user_name(),
                "password": faker.password(),
                "ssl_insecure": True,
                "mirror_url": "",
            }
        }
        distributor = MavenSourceDistributor(context=sdk_context)

        # 创建一个假的 jar 文件
        jar_file = tmpdir.join("test.jar")
        jar_file.write("fake jar content")

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

            distributor.distribute(output_dir, [str(jar_file)])

            # 验证命令中包含 SSL 跳过参数
            call_args = mock_run.call_args
            command = call_args[0][0]
            assert "-Dmaven.wagon.http.ssl.insecure=true" in command
            assert "-Dmaven.wagon.http.ssl.allowall=true" in command

    def test_distribute_without_ssl_insecure(self, distributor, output_dir, tmpdir):
        """测试未配置 ssl_insecure 时命令不包含 SSL 跳过参数"""
        # 创建一个假的 jar 文件
        jar_file = tmpdir.join("test.jar")
        jar_file.write("fake jar content")

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

            distributor.distribute(output_dir, [str(jar_file)])

            # 验证命令中不包含 SSL 跳过参数
            call_args = mock_run.call_args
            command = call_args[0][0]
            assert "-Dmaven.wagon.http.ssl.insecure=true" not in command
            assert "-Dmaven.wagon.http.ssl.allowall=true" not in command

    def test_distribute_with_mirror_url(self, sdk_context, settings, output_dir, tmpdir, faker):
        """测试配置了镜像源时命令包含 -DmirrorUrl 参数"""
        mirror_url = "https://maven.aliyun.com/repository/public"
        settings.MAVEN_MIRRORS_CONFIG = {
            "default": {
                "repository_url": faker.url(),
                "repository_id": "test-maven",
                "username": faker.user_name(),
                "password": faker.password(),
                "ssl_insecure": False,
                "mirror_url": mirror_url,
            }
        }
        distributor = MavenSourceDistributor(context=sdk_context)

        # 创建一个假的 jar 文件
        jar_file = tmpdir.join("test.jar")
        jar_file.write("fake jar content")

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

            distributor.distribute(output_dir, [str(jar_file)])

            # 验证命令中包含自定义的镜像源 URL
            call_args = mock_run.call_args
            command = call_args[0][0]
            assert f"-DmirrorUrl={mirror_url}" in command

    def test_distribute_without_mirror_url_uses_default(self, distributor, output_dir, tmpdir):
        """测试未配置镜像源时使用 Maven Central 作为默认值"""
        # 创建一个假的 jar 文件
        jar_file = tmpdir.join("test.jar")
        jar_file.write("fake jar content")

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

            distributor.distribute(output_dir, [str(jar_file)])

            # 验证命令中使用了 Maven Central 作为默认镜像源
            call_args = mock_run.call_args
            command = call_args[0][0]
            assert f"-DmirrorUrl={MAVEN_CENTRAL_URL}" in command

    def test_distribute_empty_files(self, distributor, output_dir):
        """测试空文件列表时不执行任何操作"""
        result = distributor.distribute(output_dir, [])
        assert result.is_local is True
        assert result.url == ""

    def test_distribute_no_repository_url(self, sdk_context, settings, output_dir, tmpdir):
        """测试未配置 repository_url 时抛出异常"""
        settings.MAVEN_MIRRORS_CONFIG = {
            "default": {
                "repository_url": "",
                "repository_id": "",
                "username": "",
                "password": "",
            }
        }
        distributor = MavenSourceDistributor(context=sdk_context)

        jar_file = tmpdir.join("test.jar")
        jar_file.write("fake jar content")

        with pytest.raises(DistributeError):
            distributor.distribute(output_dir, [str(jar_file)])
