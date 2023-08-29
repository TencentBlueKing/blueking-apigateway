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
from django.utils.translation import override

from apigateway.apps.plugin.constants import PluginBindingScopeEnum
from apigateway.apps.plugin.models import PluginBinding, PluginConfig, PluginForm
from apigateway.core.models import Resource, Stage

pytestmark = pytest.mark.django_db


class TestPluginBindingManager:
    def test_bulk_update_or_create(self, fake_gateway, fake_plugin_config):
        binding1 = PluginBinding(gateway=fake_gateway, scope_type="resource", scope_id=1, config=fake_plugin_config)
        binding2 = G(PluginBinding, gateway=fake_gateway, config=None, scope_id=2)
        binding2.config = fake_plugin_config
        binding2.scope_id = 3

        PluginBinding.objects.bulk_update_or_create([binding1, binding2], fields=["config", "scope_type"])

        assert PluginBinding.objects.filter(gateway=fake_gateway).count() == 2

        binding2 = PluginBinding.objects.get(pk=binding2.pk)
        assert binding2.config == fake_plugin_config
        assert binding2.scope_id == 2

    def test_create_or_update_bindings(self, fake_gateway):
        config = G(PluginConfig, gateway=fake_gateway)
        r1 = G(Resource, api=fake_gateway)
        r2 = G(Resource, api=fake_gateway)
        G(PluginBinding, gateway=fake_gateway, scope_id=r1.id, scope_type="resource")

        PluginBinding.objects.create_or_update_bindings(
            gateway=fake_gateway,
            config=config,
            scope_type="resource",
            scope_ids=[r1.id, r2.id],
            username="admin",
        )
        assert PluginBinding.objects.filter(gateway=fake_gateway).count() == 2

    def test_get_valid_scope_ids(self, fake_gateway):
        r = G(Resource, api=fake_gateway)
        s = G(Stage, api=fake_gateway)

        result = PluginBinding.objects.get_valid_scope_ids(
            fake_gateway.id, scope_type="resource", scope_ids=[r.id, r.id + 1]
        )
        assert result == [r.id]

        result = PluginBinding.objects.get_valid_scope_ids(
            fake_gateway.id, scope_type="stage", scope_ids=[s.id, s.id + 1]
        )
        assert result == [s.id]

    def test_query_scope_id_to_bindings(self, fake_gateway, fake_plugin_config):
        binding1 = G(PluginBinding, gateway=fake_gateway, scope_type="resource", scope_id=1, config=fake_plugin_config)
        binding2 = G(PluginBinding, gateway=fake_gateway, scope_type="resource", scope_id=2, config=fake_plugin_config)
        binding3 = G(PluginBinding, gateway=fake_gateway, scope_type="stage", scope_id=1, config=fake_plugin_config)
        binding4 = G(PluginBinding, gateway=fake_gateway, scope_type="stage", scope_id=2, config=fake_plugin_config)

        result = PluginBinding.objects.query_scope_id_to_bindings(
            fake_gateway.id, scope_type=PluginBindingScopeEnum.STAGE
        )
        assert result == {1: [binding3], 2: [binding4]}

        result = PluginBinding.objects.query_scope_id_to_bindings(
            fake_gateway.id, scope_type=PluginBindingScopeEnum.RESOURCE
        )
        assert result == {1: [binding1], 2: [binding2]}

        result = PluginBinding.objects.query_scope_id_to_bindings(
            fake_gateway.id, scope_type=PluginBindingScopeEnum.RESOURCE, scope_ids=[1]
        )
        assert result == {1: [binding1]}


class TestPluginFormManager:
    def test_with_language_found(self, echo_plugin_default_form, echo_plugin_en_form):
        with override(echo_plugin_en_form.language):
            assert echo_plugin_en_form == PluginForm.objects.with_language().first()

    def test_with_language_not_found(self, echo_plugin_default_form, echo_plugin_en_form):
        with override("cantonese"):
            assert echo_plugin_default_form == PluginForm.objects.with_language().first()
