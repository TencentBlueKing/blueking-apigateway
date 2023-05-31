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
from django.http import Http404

from common.errors import APIError
from esb import routers
from esb.routers import buffet_component_view


class TestGetChannelConf:
    @pytest.fixture(autouse=True)
    def setup_fixtures(self, mocker):
        self.channel_manager = mocker.patch.object(routers, "get_channel_manager").return_value
        self.components_manager = mocker.patch.object(routers, "get_components_manager").return_value

        self.path = ""
        self.request = mocker.MagicMock(method="GET")
        self.channel = mocker.MagicMock()
        self.path_vars = mocker.MagicMock()

    def mock_channel_conf(self, by_path=None, by_repath=None, path_vars=None):
        self.channel_manager.get_channel_by_path.return_value = by_path
        self.channel_manager.search_channel_by_repath.return_value = (by_repath, path_vars)

    def test_get_channel_by_path(self):
        self.mock_channel_conf(by_path=self.channel)

        channel = routers.get_channel_conf(self.path, self.request)

        self.channel_manager.get_channel_by_path.assert_called_once_with(self.path, self.request.method)
        assert channel == self.channel

    def test_search_channel_by_repath(self):
        self.mock_channel_conf(by_repath=self.channel, path_vars=self.path_vars)

        channel = routers.get_channel_conf(self.path, self.request)

        self.channel_manager.search_channel_by_repath.assert_called_once_with(self.path, self.request.method)
        assert channel == self.channel
        assert self.request.g.path_vars == self.path_vars

    def test_get_nothing(self):
        self.mock_channel_conf()

        with pytest.raises(Http404):
            routers.get_channel_conf(self.path, self.request)


class TestRouterView:
    @pytest.fixture(autouse=True)
    def setup_fixtures(self, mocker):
        self.path = "/"
        self.channel_type = "api"

        self.components_manager = mocker.patch.object(routers, "get_components_manager").return_value
        self.channel_manager = mocker.patch.object(routers, "get_channel_manager").return_value
        self.get_channel_conf = mocker.patch.object(routers, "get_channel_conf")
        self.channel_conf = self.get_channel_conf.return_value = self.make_channel_conf(mocker)
        self.request = mocker.MagicMock(method="GET")
        self.channel_manager.get_rewrite_path_by_path.return_value = None

    def make_channel_conf(self, mocker):
        channel_conf = mocker.MagicMock()

        channel_conf["channel_route"].is_active = True

        return channel_conf

    @pytest.mark.parametrize(
        "path, expected",
        [
            ("a", "/a/"),
            ("a/", "/a/"),
            ("/a", "/a/"),
            ("/a/", "/a/"),
            ("//a//", "/a/"),
        ],
    )
    def test_comp_path(self, mocker, path, expected):
        request = mocker.MagicMock()
        routers.router_view(self.channel_type, request, path)
        assert request.g.comp_path == expected

    def test_channel_is_not_active(self):
        self.channel_conf["channel_route"].is_active = False
        with pytest.raises(APIError, match=r".*inactive channel.*"):
            routers.router_view(self.channel_type, self.request, self.path)

    def test_comp_cls_not_found(self):
        self.components_manager.get_comp_by_name.return_value = None
        esb_channel = self.channel_conf["channel_route"]

        with pytest.raises(APIError, match=r".*component class not found.*"):
            routers.router_view(self.channel_type, self.request, self.path)

        self.components_manager.get_comp_by_name.assert_called_once()

    def test_set_request_validators(self, mocker):
        channel_obj = self.channel_conf["classes"][self.channel_type].return_value
        esb_channel = self.channel_conf["channel_route"]
        request_validators = [mocker.MagicMock()]
        esb_channel.request_validators = request_validators

        routers.router_view(self.channel_type, self.request, self.path)
        channel_obj.set_request_validators.assert_called_once_with(request_validators)

    def test_append_request_validators(self, mocker):
        channel_obj = self.channel_conf["classes"][self.channel_type].return_value
        esb_channel = self.channel_conf["channel_route"]
        request_validators = [mocker.MagicMock()]
        esb_channel.append_request_validators = request_validators

        routers.router_view(self.channel_type, self.request, self.path)
        channel_obj.append_request_validators.assert_called_once_with(request_validators)

    def test_timeout_time_from_timeout_handler(self, mocker, faker):
        sys_name = "test"
        self.components_manager.get_comp_by_name.return_value = mocker.MagicMock(sys_name=sys_name)

        timeout = faker.pyint(min_value=1)
        esb_channel = self.channel_conf["channel_route"]
        esb_channel.timeout = timeout

        routers.router_view(self.channel_type, self.request, self.path)

        assert self.request.g.timeout == timeout
        assert self.request.g.sys_name == sys_name

    def test_handle_request(self):
        channel_obj = self.channel_conf["classes"][self.channel_type].return_value

        routers.router_view(self.channel_type, self.request, self.path)

        channel_obj.handle_request.assert_called_once_with(self.request)


def test_buffet_component_view():
    with pytest.raises(APIError) as err:
        buffet_component_view(None, "/")

    assert err.value.code.prompt == "Not found, inactive buffet component"
