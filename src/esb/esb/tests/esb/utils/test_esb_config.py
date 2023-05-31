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

from components.component import ApiChannelForAPIS
from esb.utils.esb_config import EsbConfigParser


class TestEsbConfigParser:
    @pytest.fixture(autouse=True)
    def setup_fixture(self):
        self.parser = EsbConfigParser()

    def test_get_default_channel_classes(self):
        assert self.parser.get_default_channel_classes() == {"api": ApiChannelForAPIS}

    def test_get_rewrite_channels(self):
        assert "/v2/cmsi/send_mail/" in self.parser.get_rewrite_channels()

    def test_get_channels(self):
        assert len(self.parser.get_channels()) > 0

    def test_get_channels_mapping(self):
        assert ":/cmsi/send_mail/" in self.parser.get_channels_mapping()

    @pytest.mark.parametrize(
        "method, path, expected",
        [
            (None, "/echo/", ":/echo/"),
            ("", "/echo/", ":/echo/"),
            ("POST", "/echo/", "POST:/echo/"),
        ],
    )
    def test_get_channel_key(self, method, path, expected):
        assert self.parser.get_channel_key(method, path) == expected

    def test_get_doc_common_args(self):
        assert "bk_app_secret" in self.parser.get_doc_common_args()

    def test_get_component_groups(self):
        assert len(self.parser.get_component_groups()) > 0
