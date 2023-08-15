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
from django.utils.translation import override


class TestPluginViewSet:
    @pytest.mark.parametrize(
        "config_tmpl, code",
        [
            ["{config}", 201],  # success
            ["", 400],  # config is None
            ["foo: bar", 400],  # config validate failure by schema
        ],
    )
    def test_create(self, request_view, fake_gateway, echo_plugin, echo_plugin_type, config_tmpl, code):
        response = request_view(
            "POST",
            "plugins.config",
            gateway=fake_gateway,
            path_params={
                "gateway_id": fake_gateway.id,
            },
            data={
                "type_id": echo_plugin_type.pk,
                "description": "description",
                "name": "name",
                "yaml": config_tmpl.format(config=echo_plugin.yaml),
            },
        )

        # result = response.json()
        # assert result["code"] == code
        assert response.status_code == code

    def test_list(self, request_view, fake_gateway, echo_plugin):
        response = request_view(
            "GET",
            "plugins.config",
            gateway=fake_gateway,
            path_params={
                "gateway_id": fake_gateway.id,
            },
        )

        result = response.json()
        assert result["code"] == 0

        plugins = result["data"]["results"]
        assert plugins

        assert plugins[0]["id"] == echo_plugin.pk

    @pytest.mark.parametrize(
        "config_tmpl, code",
        [
            ["{config}", 200],  # success
            ["", 400],  # config is None
            ["foo: bar", 400],  # config validate failure by schema
        ],
    )
    def test_update(self, request_view, fake_gateway, echo_plugin, echo_plugin_type, config_tmpl, code):
        response = request_view(
            "PUT",
            "plugins.config.details",
            gateway=fake_gateway,
            path_params={
                "gateway_id": fake_gateway.id,
                "id": echo_plugin.id,
            },
            data={
                "type_id": echo_plugin_type.pk,
                "description": "description",
                "name": "name",
                "yaml": config_tmpl.format(config=echo_plugin.yaml),
            },
        )

        # result = response.json()
        # assert result["code"] == code
        assert response.status_code == code

    def test_retrieve(self, request_view, fake_gateway, echo_plugin):
        response = request_view(
            "GET",
            "plugins.config.details",
            gateway=fake_gateway,
            path_params={
                "gateway_id": fake_gateway.id,
                "id": echo_plugin.id,
            },
        )

        result = response.json()
        assert result["code"] == 0

        plugin = result["data"]

        assert plugin["id"] == echo_plugin.pk

    def test_delete(self, request_view, fake_gateway, echo_plugin):
        response = request_view(
            "DELETE",
            "plugins.config.details",
            gateway=fake_gateway,
            path_params={
                "gateway_id": fake_gateway.id,
                "id": echo_plugin.id,
            },
        )

        assert response.status_code == 204


class TestPluginTypeViewSet:
    def test_list(self, request_view, fake_gateway, echo_plugin_type):
        response = request_view(
            "GET",
            "plugins.types",
            gateway=fake_gateway,
            path_params={
                "gateway_id": fake_gateway.id,
            },
        )

        result = response.json()
        assert result["code"] == 0
        assert result["data"]["results"][0]["id"] == echo_plugin_type.id

    def test_list_exclude_hidden(self, request_view, fake_gateway, echo_plugin_type):
        echo_plugin_type.is_public = False
        echo_plugin_type.save()

        response = request_view(
            "GET",
            "plugins.types",
            gateway=fake_gateway,
            path_params={
                "gateway_id": fake_gateway.id,
            },
        )

        result = response.json()
        assert result["code"] == 0

        assert not result["data"]["results"]


class TestPluginFormViewSet:
    @pytest.mark.parametrize(
        "language, form_id_tmpl",
        [
            [None, "{default.pk}"],
            ["zh", "{default.pk}"],
            ["jp", "{default.pk}"],
            ["en", "{en.pk}"],
        ],
    )
    def test_retrieve_form_by_language(
        self,
        fake_gateway,
        request_view,
        echo_plugin_type,
        echo_plugin_default_form,
        echo_plugin_en_form,
        language,
        form_id_tmpl,
    ):
        with override(language):
            response = request_view(
                "GET",
                "plugins.forms",
                gateway=fake_gateway,
                path_params={
                    "gateway_id": fake_gateway.id,
                    "type_id": echo_plugin_type.id,
                },
            )

        result = response.json()

        assert result["code"] == 0
        assert result["data"]["id"] == int(
            form_id_tmpl.format(
                default=echo_plugin_default_form,
                en=echo_plugin_en_form,
            )
        )
