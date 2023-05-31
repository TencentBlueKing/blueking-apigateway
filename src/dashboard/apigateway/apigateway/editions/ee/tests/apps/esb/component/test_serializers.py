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
from rest_framework.exceptions import ValidationError

from apigateway.apps.esb.bkcore.models import ComponentSystem, ESBChannel, ESBChannelExtend
from apigateway.apps.esb.component.serializers import (
    ComponentReleaseHistorySLZ,
    ComponentResourceBindingSLZ,
    ESBChannelDetailSLZ,
    ESBChannelSLZ,
)

pytestmark = [pytest.mark.django_db]


class TestESBChannelSLZ:
    @pytest.fixture
    def mock_channel_data(self):
        return {
            "name": "test",
            "description": "desc",
            "method": "POST",
            "path": "/echo",
            "component_codename": "generic.test.echo",
            "permission_level": "normal",
            "verified_user_required": True,
            "timeout": 30,
            "config": {"name": "test"},
            "is_active": True,
        }

    @pytest.mark.parametrize(
        "data, expected",
        [
            (
                {
                    "description": "desc",
                    "method": "",
                    "path": "/echo",
                    "name": "echo",
                    "component_codename": "generic.test.echo",
                    "permission_level": "unlimited",
                    "verified_user_required": True,
                    "timeout": None,
                    "config": {"name": "test"},
                    "is_active": True,
                    "data_type": 1,
                },
                {
                    "description": "desc",
                    "method": "",
                    "path": "/echo",
                    "name": "echo",
                    "component_codename": "generic.test.echo",
                    "permission_level": "unlimited",
                    "verified_user_required": True,
                    "timeout": None,
                    "is_active": True,
                    "is_official": True,
                    "api_url": "/api/c/compapi/echo",
                    "doc_link": "/test/",
                    "is_created": True,
                    "has_updated": True,
                },
            )
        ],
    )
    def test_to_representation(self, settings, data, expected):
        settings.BK_COMPONENT_API_URL = ""
        settings.COMPONENT_DOC_URL_TMPL = "/test/"

        system = G(ComponentSystem)
        channel = G(ESBChannel, system=system, **data)
        expected.update(
            {
                "id": channel.id,
                "system_id": system.id,
                "system_name": system.name,
            }
        )
        slz = ESBChannelSLZ(channel, context={"latest_release_time": None})
        data = slz.data
        data.pop("updated_time")
        assert data == expected

    @pytest.mark.parametrize(
        "data, expected, will_error",
        [
            (
                {
                    "name": "get_echo_data",
                    "description": "desc",
                    "method": "POST",
                    "path": "/echo/",
                    "component_codename": "generic.test.echo",
                    "permission_level": "normal",
                    "verified_user_required": True,
                    "timeout": 30,
                    "config": {"name": "test"},
                    "is_active": True,
                },
                {
                    "description": "desc",
                    "method": "POST",
                    "path": "/echo/",
                    "component_codename": "generic.test.echo",
                    "permission_level": "normal",
                    "verified_user_required": True,
                    "timeout": 30,
                    "config": {"name": "test"},
                    "name": "get_echo_data",
                    "is_active": True,
                },
                False,
            )
        ],
    )
    def test_validate(self, data, expected, will_error):
        system = G(ComponentSystem, board="test")
        data["system_id"] = system.id

        slz = ESBChannelSLZ(data=data)

        slz.is_valid()
        expected.update(
            {
                "system_id": system.id,
                "system": system,
                "board": "test",
            }
        )
        assert slz.validated_data == expected

    def test_to_internal_value(self, mock_channel_data):
        system = G(ComponentSystem)
        mock_channel_data["system_id"] = system.id

        slz = ESBChannelSLZ(data=mock_channel_data)
        slz.is_valid()
        assert not bool(slz.errors)

        # system deleted and not exist
        system.delete()
        slz = ESBChannelSLZ(data=mock_channel_data)
        slz.is_valid()

        assert slz.errors

    def test_update(self):
        channel = G(ESBChannel, config={})
        slz = ESBChannelSLZ(data=None)

        # config fields not exist
        slz.update(channel, {"config": {"name": "test"}})
        assert ESBChannel.objects.get(id=channel.id).config == {}

        # config fields exist
        G(ESBChannelExtend, component=channel, config_fields=[{"key": "test"}])
        slz.update(channel, {"config": {"name": "test"}})
        assert ESBChannel.objects.get(id=channel.id).config == {"name": "test"}

    def test_unique_together(self, mock_channel_data):
        system = G(ComponentSystem, board="test")
        G(ESBChannel, board="test", method="GET", path="/echo/unique/")

        mock_channel_data.update(
            {
                "system_id": system.id,
                "method": "GET",
                "path": "/echo/unique/",
            }
        )
        slz = ESBChannelSLZ(data=mock_channel_data)
        slz.is_valid()
        assert slz.errors

    def test_unique_name(self, mock_channel_data, unique_id):
        board = unique_id
        system = G(ComponentSystem, board=board)
        channel = G(ESBChannel, board=board, name="echo", method="GET", path="/echo/", system=system)

        # create, name different, ok
        mock_channel_data.update(
            {
                "system_id": system.id,
                "name": "echo2",
            }
        )
        slz = ESBChannelSLZ(data=mock_channel_data)
        slz.is_valid(raise_exception=True)

        # create, name same, error
        mock_channel_data.update(
            {
                "system_id": system.id,
                "name": "echo",
            }
        )
        slz = ESBChannelSLZ(data=mock_channel_data)
        with pytest.raises(ValidationError):
            slz.is_valid(raise_exception=True)

        # update, name and id same, ok
        mock_channel_data.update(
            {
                "id": channel.id,
                "system_id": system.id,
                "name": "echo",
            }
        )
        slz = ESBChannelSLZ(channel, data=mock_channel_data)
        slz.is_valid(raise_exception=True)

    def test_validate_method(self, mock_channel_data, unique_id):
        board = unique_id
        system = G(ComponentSystem, board=board)
        c1 = G(ESBChannel, board=board, method="GET", path="/echo/", system=system)
        c2 = G(ESBChannel, board=board, method="", path="/echo/any/", system=system)

        mock_channel_data.update(
            {
                "board": board,
                "system_id": system.id,
            }
        )

        # method GET exists, error
        mock_channel_data.update(
            {
                "method": "",
                "path": "/echo/",
            }
        )
        slz = ESBChannelSLZ(data=mock_channel_data)
        with pytest.raises(ValidationError):
            slz.is_valid(raise_exception=True)

        # update, ok
        slz = ESBChannelSLZ(c1, data=mock_channel_data)
        slz.is_valid(raise_exception=True)

        # method "" exists, error
        mock_channel_data.update(
            {
                "method": "GET",
                "path": "/echo/any/",
            }
        )
        slz = ESBChannelSLZ(data=mock_channel_data)
        with pytest.raises(ValidationError):
            slz.is_valid(raise_exception=True)

        # update, ok
        slz = ESBChannelSLZ(c2, data=mock_channel_data)
        slz.is_valid(raise_exception=True)


class TestESBChannelDetailSLZ:
    def test_meta(self):
        slz = ESBChannelDetailSLZ(data=None)
        assert "config_fields" in slz.Meta.fields

        slz = ESBChannelSLZ(data=None)
        assert "config_fields" not in slz.Meta.fields

    def test_get_config_fields(self):
        slz = ESBChannelDetailSLZ(data=None)

        # config fields not exist
        channel = G(ESBChannel, config={"name": "test"})
        result = slz.get_config_fields(channel)
        assert result is None

        # config fields exist
        G(ESBChannelExtend, component=channel, config_fields=[{"variable": "name", "default": "", "type": "string"}])
        result = slz.get_config_fields(channel)
        assert result == [{"variable": "name", "label": "name", "type": "string", "default": "test"}]


class TestComponentResourceBindingSLZ:
    @pytest.mark.parametrize(
        "data, expected",
        [
            (
                {
                    "id": 1,
                    "name": "echo",
                    "extend_data": {
                        "system_name": "DEMO",
                        "component_id": 10,
                        "component_name": "component_echo",
                        "component_method": "GET",
                        "component_path": "/echo/",
                        "component_permission_level": "unlimited",
                    },
                },
                {
                    "resource_id": 1,
                    "resource_name": "echo",
                    "system_name": "DEMO",
                    "component_id": 10,
                    "component_name": "component_echo",
                    "component_method": "GET",
                    "component_path": "/echo/",
                    "component_permission_level": "unlimited",
                },
            ),
            (
                {
                    "id": None,
                    "name": "echo",
                    "extend_data": {
                        "system_name": "DEMO",
                        "component_id": None,
                        "component_name": "component_echo",
                        "component_method": "GET",
                        "component_path": "/echo/",
                        "component_permission_level": "unlimited",
                    },
                },
                {
                    "resource_id": None,
                    "resource_name": "echo",
                    "system_name": "DEMO",
                    "component_id": None,
                    "component_name": "component_echo",
                    "component_method": "GET",
                    "component_path": "/echo/",
                    "component_permission_level": "unlimited",
                },
            ),
        ],
    )
    def test_to_representation(self, data, expected):
        slz = ComponentResourceBindingSLZ(data)
        assert slz.data == expected


class TestComponentReleaseHistorySLZ:
    @pytest.mark.parametrize(
        "data, resource_version_id_to_fields, expected",
        [
            (
                {
                    "id": 1,
                    "created_time": datetime.datetime(2020, 10, 10, 12, 30, 00),
                    "created_by": "admin",
                    "status": "success",
                    "message": "ok",
                    "resource_version_id": 10,
                },
                {
                    10: {
                        "name": "bk-esb-demo",
                        "title": "v1",
                        "version": "1.0.0",
                    }
                },
                {
                    "id": 1,
                    "created_time": "2020-10-10 12:30:00",
                    "resource_version_name": "bk-esb-demo",
                    "resource_version_title": "v1",
                    "resource_version_display": "1.0.0(v1)",
                    "created_by": "admin",
                    "status": "success",
                    "message": "ok",
                },
            )
        ],
    )
    def test_to_representation(self, data, resource_version_id_to_fields, expected):
        slz = ComponentReleaseHistorySLZ(
            data,
            context={
                "resource_version_id_to_fields": resource_version_id_to_fields,
            },
        )
        assert slz.data == expected
