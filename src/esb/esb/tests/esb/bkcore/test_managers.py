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
import datetime

import pytest
from ddf import G

from esb.bkcore.constants import DataTypeEnum
from esb.bkcore.models import AppComponentPermission, DocCategory, ESBChannel, System

pytestmark = pytest.mark.django_db


class TestSystemManager:
    def test_get_name_to_obj_map(self):
        system = G(System)
        result = System.objects.get_name_to_obj_map()

        assert system.name in result
        assert len(result) >= 1

    def test_get_official_ids(self, mocker, unique_id):
        G(System, data_type=DataTypeEnum.OFFICIAL_PUBLIC.value)

        assert len(System.objects.get_official_ids()) >= 1


class TestESBChannelManager:
    def test_get_best_matched_channel(self, faker):
        path1 = f"/{faker.unique.pystr()}"

        # method is GET
        channel = G(ESBChannel, method="GET", path=path1)
        assert channel == ESBChannel.objects.get_best_matched_channel("GET", [path1])

        # method not GET/POST
        channel = G(ESBChannel, method="PUT", path=path1)
        assert channel == ESBChannel.objects.get_best_matched_channel("PUT", [path1])

        # method is ""
        path2 = f"/{faker.unique.pystr()}"
        channel = G(ESBChannel, method="", path=path2)

        assert channel == ESBChannel.objects.get_best_matched_channel("GET", [path2])
        assert channel == ESBChannel.objects.get_best_matched_channel("POST", [path2])
        assert ESBChannel.objects.get_best_matched_channel("PUT", [path2]) is None

    def test_get_field_values(self):
        system = G(System)
        channel = G(ESBChannel, system=system)

        result = ESBChannel.objects.get_field_values(channel.id)
        assert result == {"name": channel.name, "system_name": system.name}

        # not exist
        result = ESBChannel.objects.get_field_values(0)
        assert result is None

    def test_filter_channels(self):
        system = G(System)

        G(ESBChannel, system=system, is_public=True, is_active=True)

        assert ESBChannel.objects.filter_channels(system_ids=[system.id], is_public=True, is_active=True).count() == 1


class TestAppComponentPermissionManager:
    def test_has_permission(self, faker):
        c1 = G(ESBChannel)
        c2 = G(ESBChannel)

        bk_app_code = faker.pystr()

        p1 = G(
            AppComponentPermission,
            bk_app_code=bk_app_code,
            component_id=c1.id,
            expires=faker.past_datetime(tzinfo=datetime.timezone.utc),
        )
        p2 = G(
            AppComponentPermission,
            bk_app_code=bk_app_code,
            component_id=c2.id,
            expires=faker.future_datetime(tzinfo=datetime.timezone.utc),
        )

        assert AppComponentPermission.objects.has_permission(bk_app_code, c1.id) is True
        assert AppComponentPermission.objects.has_permission(bk_app_code, c2.id) is True
        assert AppComponentPermission.objects.has_permission("app-not-exist", c1.id) is False


class TestDocCategoryManager:
    def test_get_name_to_obj_map(self):
        category = G(DocCategory)
        result = DocCategory.objects.get_name_to_obj_map()

        assert category.name in result
        assert len(result) >= 1
