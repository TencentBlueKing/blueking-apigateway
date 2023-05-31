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

from apigateway.apps.support.api_sdk.distributors.bkrepo import GenericDistributor
from apigateway.apps.support.api_sdk.exceptions import DistributeError


class TestGenericDistributor:
    @pytest.fixture(autouse=True)
    def setup(self, mocker, sdk_context):
        self.bkrepo_component = mocker.MagicMock()
        self.distributor = GenericDistributor(
            context=sdk_context,
            bkrepo=self.bkrepo_component,
        )

    def test_distribute_when_bkrepo_not_set(self, output_dir):
        self.distributor.bkrepo = None

        with pytest.raises(DistributeError):
            self.distributor.distribute(output_dir, [])

    def test_distribute_nothing(self, output_dir):
        result = self.distributor.distribute(output_dir, [])

        assert result.is_local

    def test_distribute(self, faker, output_dir, sdk_context):
        filepath = faker.file_path(depth=3, extension="tgz")
        download_url = faker.uri()
        self.bkrepo_component.generate_generic_download_url.return_value = download_url

        result = self.distributor.distribute(output_dir, [filepath])

        assert not result.is_local
        assert result.url == download_url

        config = sdk_context.config[sdk_context.language.value]
        self.bkrepo_component.upload_generic_file.assert_called_once_with(filepath, config["bkrepo_key"])
