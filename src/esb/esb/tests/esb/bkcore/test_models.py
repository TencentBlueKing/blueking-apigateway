# -*- coding: utf-8 -*-
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
from ddf import G

from esb.bkcore.constants import PermissionLevelEnum
from esb.bkcore.models import ESBChannel

pytestmark = pytest.mark.django_db


class TestESBChannel:
    def test_channel_conf(self):
        channel = G(ESBChannel, permission_level=PermissionLevelEnum.UNLIMITED.value)
        assert channel.channel_conf == {"id": channel.id, "permission_level": PermissionLevelEnum.UNLIMITED.value}

    @pytest.mark.parametrize(
        "path, expected",
        [
            ("/test/test/", "/api/c/compapi/test/test/"),
        ],
    )
    def test_api_path(self, path, expected):
        channel = G(ESBChannel, path=path)
        assert channel.api_path == expected

    @pytest.mark.parametrize(
        "component_codename, expected",
        [
            ("generic.v2.test.test", "v2"),
            ("generic.test.test", ""),
        ],
    )
    def test_api_version(self, component_codename, expected):
        channel = G(ESBChannel, component_codename=component_codename)
        assert channel.api_version == expected

    @pytest.mark.parametrize(
        "permission_level, expected",
        [
            (PermissionLevelEnum.UNLIMITED.value, False),
            (PermissionLevelEnum.NORMAL.value, True),
            (PermissionLevelEnum.SENSITIVE.value, True),
            (PermissionLevelEnum.SPECIAL.value, True),
        ],
    )
    def test_component_permission_required(self, permission_level, expected):
        channel = G(ESBChannel, permission_level=permission_level)
        assert channel.component_permission_required == expected

    @pytest.mark.parametrize(
        "system_timeout, channel_timeout, expected",
        [
            (None, 10, 10),
            (20, None, 20),
            (None, None, 5),
        ],
    )
    def test_get_real_timeout(self, settings, system_timeout, channel_timeout, expected):
        settings.REQUEST_TIMEOUT_SECS = 5

        channel = G(ESBChannel, timeout=channel_timeout)
        assert channel.get_real_timeout(system_timeout) == expected
