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


class TestPluginTypeListApi:
    def test_list(self, request_view, fake_gateway, echo_plugin_type):
        response = request_view(
            "GET",
            "plugins.types",
            gateway=fake_gateway,
            path_params={
                "gateway_id": fake_gateway.id,
            },
            data={
                "scope": "stage_and_resource",
            },
        )

        assert response.status_code == 200

        result = response.json()
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
            data={
                "scope": "stage_and_resource",
            },
        )

        assert response.status_code == 200

        result = response.json()
        assert not result["data"]["results"]


class TestScopePluginConfigListApi:
    def test_list(
        self, request_view, fake_gateway, fake_stage, echo_plugin, echo_plugin_type, echo_plugin_stage_binding
    ):
        # setup with these 1 binding: echo_plugin_stage_binding
        response = request_view(
            "GET",
            "plugins.config.scope",
            gateway=fake_gateway,
            path_params={
                "gateway_id": fake_gateway.id,
                "scope_type": "stage",
                "scope_id": fake_stage.id,
            },
        )

        assert response.status_code == 200

        result = response.json()

        data = result["data"]
        assert len(data) == 1
        assert data[0]["name"] == echo_plugin_type.name


class TestPluginConfigCreateApi:
    @pytest.mark.parametrize(
        "config_tmpl, status_code",
        [
            ["{config}", 201],  # success
            ["", 400],  # config is None
            ["foo: bar", 400],  # config validate failure by schema
        ],
    )
    def test_create(
        self, request_view, fake_gateway, fake_stage, echo_plugin, echo_plugin_type, config_tmpl, status_code
    ):
        response = request_view(
            "POST",
            "plugins.config.create",
            gateway=fake_gateway,
            path_params={
                "gateway_id": fake_gateway.id,
                "scope_type": "stage",
                "scope_id": fake_stage.id,
                "code": echo_plugin_type.code,
            },
            data={
                "type_id": echo_plugin_type.pk,
                "description": "description",
                "name": "name",
                "yaml": config_tmpl.format(config=echo_plugin.yaml),
            },
        )
        assert response.status_code == status_code


class TestPluginConfigRetrieveUpdateDestroyApi:
    def test_retrieve(self, request_view, fake_gateway, fake_stage, echo_plugin, echo_plugin_type):
        response = request_view(
            "GET",
            "plugins.config.details",
            gateway=fake_gateway,
            path_params={
                "gateway_id": fake_gateway.id,
                "scope_type": "stage",
                "scope_id": fake_stage.id,
                "code": echo_plugin_type.code,
                "id": echo_plugin.id,
            },
        )

        assert response.status_code == 200

        result = response.json()

        plugin = result["data"]
        assert plugin["id"] == echo_plugin.pk

    @pytest.mark.parametrize(
        "config_tmpl, status_code",
        [
            ["{config}", 200],  # success
            ["", 400],  # config is None
            ["foo: bar", 400],  # config validate failure by schema
        ],
    )
    def test_update(
        self,
        request_view,
        fake_gateway,
        fake_stage,
        echo_plugin,
        echo_plugin_type,
        echo_plugin_stage_binding,
        config_tmpl,
        status_code,
    ):
        response = request_view(
            "PUT",
            "plugins.config.details",
            gateway=fake_gateway,
            path_params={
                "gateway_id": fake_gateway.id,
                "scope_type": "stage",
                "scope_id": fake_stage.id,
                "code": echo_plugin_type.code,
                "id": echo_plugin.id,
            },
            data={
                "type_id": echo_plugin_type.pk,
                "description": "description",
                "name": "name",
                "yaml": config_tmpl.format(config=echo_plugin.yaml),
            },
        )

        assert response.status_code == status_code

        if status_code == 200:
            result = response.json()
            plugin = result["data"]
            assert plugin["id"] == echo_plugin.pk
        # assert result["code"] == code

    def test_delete(
        self, request_view, fake_gateway, fake_stage, echo_plugin, echo_plugin_type, echo_plugin_stage_binding
    ):
        response = request_view(
            "DELETE",
            "plugins.config.details",
            gateway=fake_gateway,
            path_params={
                "gateway_id": fake_gateway.id,
                "scope_type": "stage",
                "scope_id": fake_stage.id,
                "code": echo_plugin_type.code,
                "id": echo_plugin.id,
            },
        )

        assert response.status_code == 204


class TestPluginFormRetrieveApi:
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
                    "code": echo_plugin_type.code,
                },
            )

        assert response.status_code == 200

        result = response.json()

        assert result["data"]["id"] == int(
            form_id_tmpl.format(
                default=echo_plugin_default_form,
                en=echo_plugin_en_form,
            )
        )


class TestPluginBindingListApi:
    def test_retrieve(
        self,
        request_view,
        fake_gateway,
        echo_plugin_type,
        fake_stage,
        fake_resource,
        echo_plugin_stage_binding,
        echo_plugin_resource_binding,
    ):
        # setup with these two bindings:
        # - echo_plugin_stage_binding
        # - echo_plugin_resource_binding
        response = request_view(
            "GET",
            "plugins.bindings",
            gateway=fake_gateway,
            path_params={
                "gateway_id": fake_gateway.id,
                "code": echo_plugin_type.code,
            },
        )

        assert response.status_code == 200

        result = response.json()

        data = result["data"]
        stages = data["stages"]
        resources = data["resources"]

        assert len(stages) == 1
        assert stages[0] == fake_stage.name

        assert len(resources) == 1
        assert resources[0] == fake_resource.name
