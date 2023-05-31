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

from apigateway.apps.feature.models import UserFeatureFlag

pytestmark = pytest.mark.django_db


class TestUserFeatureFlag:
    def test_get_feature_flags(self, settings, faker, unique_id):
        username = unique_id
        feature_name = faker.color_name()

        settings.DEFAULT_USER_FEATURE_FLAG = {feature_name: False}
        result = UserFeatureFlag.objects.get_feature_flags(username)
        assert result == {feature_name: False}

        G(UserFeatureFlag, username=username, name=feature_name, effect=True)
        result = UserFeatureFlag.objects.get_feature_flags(username)
        assert result == {feature_name: True}
