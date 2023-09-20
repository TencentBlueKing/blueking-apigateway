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
from tempfile import TemporaryDirectory

import pytest

from apigateway.apps.support.api_sdk.packagers.archive import TgzPackager
from apigateway.utils.archivefile import TgzArchiveFile


class TestTgzPackager:
    @pytest.fixture(autouse=True)
    def setup_packager(self, sdk_context):
        self.packer = TgzPackager(
            context=sdk_context,
        )

    def test_pack(self, output_dir_files, output_dir):
        files = self.packer.pack(output_dir)

        assert len(files) == 1

        file = files[0]
        archive = TgzArchiveFile()

        with TemporaryDirectory() as target_dir, open(file, "rb") as fp:
            structures = archive.extractall(target_dir, fp)

        assert not output_dir_files - structures.keys()
