# -*- coding: utf-8 -*-
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
from django_dynamic_fixture import G

from apigateway.biz.resource import ResourceHandler
from apigateway.core import models
from apigateway.core.constants import GatewayStatusEnum, PublishEventNameTypeEnum, PublishEventStatusEnum

pytestmark = pytest.mark.django_db


class TestGateway:
    @pytest.mark.parametrize(
        "status, is_public, expected",
        [
            (GatewayStatusEnum.ACTIVE.value, True, True),
            (GatewayStatusEnum.INACTIVE.value, True, False),
            (GatewayStatusEnum.ACTIVE.value, False, False),
            (GatewayStatusEnum.INACTIVE.value, False, False),
        ],
    )
    def test_is_active_and_public(self, status, is_public, expected):
        gateway = G(models.Gateway, status=status, is_public=is_public)
        assert gateway.is_active_and_public == expected

    def test_is_programmable(self):
        gateway = G(models.Gateway, kind=models.GatewayKindEnum.PROGRAMMABLE.value)
        assert gateway.is_programmable

        gateway = G(models.Gateway)
        assert not gateway.is_programmable

    def test_extra_info_getter(self):
        # Test with empty extra_info
        gateway = G(models.Gateway, _extra_info={})
        assert gateway.extra_info == {}

        # Test with non-empty extra_info
        gateway = G(models.Gateway, _extra_info={"key": "value"})
        assert gateway.extra_info == {"key": "value"}

    def test_extra_info_setter_normal_gateway(self):
        gateway = G(models.Gateway)

        # Test setting empty dict
        gateway.extra_info = {}
        assert gateway._extra_info == {}

        # Test setting non-empty dict
        gateway.extra_info = {"key": "value"}
        assert gateway._extra_info == {}

        # Test setting None
        gateway.extra_info = None
        assert gateway._extra_info == {}

    def test_extra_info_setter_programmable_gateway(self):
        # Test for programmable gateway
        gateway = G(models.Gateway, kind=models.GatewayKindEnum.PROGRAMMABLE.value)

        # Test valid language and repository
        gateway.extra_info = {"language": "python", "repository": "https://example.com/repo"}
        assert gateway._extra_info == {"language": "python", "repository": "https://example.com/repo"}

        # Test invalid language
        with pytest.raises(ValueError, match="language should be one of \\[python, go\\]"):
            gateway.extra_info = {"language": "invalid", "repository": "https://example.com/repo"}

        # Test missing repository
        with pytest.raises(ValueError, match="repository is required"):
            gateway.extra_info = {"language": "python"}

    # def test_extra_info_setter_non_programmable_gateway(self):
    #     # Test for non-programmable gateway
    #     gateway = G(models.Gateway, kind=models.GatewayKindEnum.NORMAL.value)

    #     # Setting any extra info should result in empty dict
    #     gateway.extra_info = {"key": "value"}
    #     assert gateway._extra_info == {}


class TestResource:
    def test_snapshot(self, fake_resource):
        snapshot = ResourceHandler.snapshot(fake_resource, as_dict=True)
        assert snapshot
        assert isinstance(snapshot, dict)


class TestPublishEvent:
    @pytest.mark.parametrize(
        "name, expected",
        [
            (PublishEventNameTypeEnum.VALIDATE_CONFIGURATION.value, False),
            (PublishEventNameTypeEnum.LOAD_CONFIGURATION.value, True),
        ],
    )
    def test_is_last(self, name, expected):
        gateway = G(models.PublishEvent, name=name)
        assert gateway.is_last == expected

    @pytest.mark.parametrize(
        "name, status, expected",
        [
            # doing
            (PublishEventNameTypeEnum.VALIDATE_CONFIGURATION.value, PublishEventStatusEnum.DOING.value, True),
            (PublishEventNameTypeEnum.LOAD_CONFIGURATION.value, PublishEventStatusEnum.DOING.value, True),
            # not doing
            (PublishEventNameTypeEnum.VALIDATE_CONFIGURATION.value, PublishEventStatusEnum.PENDING.value, False),
            # not is_last and success
            (PublishEventNameTypeEnum.VALIDATE_CONFIGURATION.value, PublishEventStatusEnum.SUCCESS.value, True),
        ],
    )
    def test_is_running(self, name, status, expected):
        gateway = G(models.PublishEvent, name=name, status=status)
        assert gateway.is_running == expected
