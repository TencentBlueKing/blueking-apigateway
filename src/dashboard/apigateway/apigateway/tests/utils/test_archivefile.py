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
import tarfile
import tempfile
import zipfile

from apigateway.utils.archivefile import TgzArchiveFile, ZipArchiveFile


def _make_temp_files(output_dir, faker):
    os.makedirs(os.path.join(output_dir, "zh"))
    fp = open(os.path.join(output_dir, "zh", "get_user.md"), mode="w")
    fp.write(faker.pystr())
    fp.close()


class TestZipArchiveFile:
    def test_archive(self, faker):
        with tempfile.TemporaryDirectory() as output_dir:
            _make_temp_files(output_dir, faker)
            result = ZipArchiveFile().archive(output_dir, "test.zip", ["zh/get_user.md"])
            assert result == os.path.join(output_dir, "test.zip")

            with zipfile.ZipFile(result, mode="r") as zip_:
                assert zip_.namelist() == ["zh/get_user.md"]

    def test_extractall(self, faker):
        with tempfile.TemporaryDirectory() as output_dir:
            _make_temp_files(output_dir, faker)
            ZipArchiveFile().archive(output_dir, "test.zip", ["zh/get_user.md"])
            shutil.rmtree(os.path.join(output_dir, "zh"))

            result = ZipArchiveFile().extractall(output_dir, open(os.path.join(output_dir, "test.zip"), "rb"))
            assert result == {
                "zh/get_user.md": os.path.join(output_dir, "zh/get_user.md"),
            }
            assert os.path.exists(os.path.join(output_dir, "zh/get_user.md"))

    def test_get_names(self, faker):
        with tempfile.TemporaryDirectory() as output_dir:
            _make_temp_files(output_dir, faker)
            ZipArchiveFile().archive(output_dir, "test.zip", ["zh/get_user.md"])
            shutil.rmtree(os.path.join(output_dir, "zh"))
            result = ZipArchiveFile().get_names(open(os.path.join(output_dir, "test.zip"), "rb"))
            assert result == ["zh/get_user.md"]


class TestTgzArchiveFile:
    def test_archive(self, faker):
        with tempfile.TemporaryDirectory() as output_dir:
            _make_temp_files(output_dir, faker)
            result = TgzArchiveFile().archive(output_dir, "test.tgz", ["zh/get_user.md"])
            assert result == os.path.join(output_dir, "test.tgz")

            with tarfile.open(result, mode="r:gz") as tgz:
                assert tgz.getnames() == ["zh/get_user.md"]

    def test_extractall(self, faker):
        with tempfile.TemporaryDirectory() as output_dir:
            _make_temp_files(output_dir, faker)
            TgzArchiveFile().archive(output_dir, "test.tgz", ["zh/get_user.md"])
            shutil.rmtree(os.path.join(output_dir, "zh"))

            result = TgzArchiveFile().extractall(output_dir, open(os.path.join(output_dir, "test.tgz"), "rb"))
            assert result == {
                "zh/get_user.md": os.path.join(output_dir, "zh/get_user.md"),
            }
            assert os.path.exists(os.path.join(output_dir, "zh/get_user.md"))

    def test_get_names(self, faker):
        with tempfile.TemporaryDirectory() as output_dir:
            _make_temp_files(output_dir, faker)
            TgzArchiveFile().archive(output_dir, "test.tgz", ["zh/get_user.md"])
            shutil.rmtree(os.path.join(output_dir, "zh"))

            result = TgzArchiveFile().get_names(open(os.path.join(output_dir, "test.tgz"), "rb"))
            assert result == ["zh/get_user.md"]
