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
from django.core.exceptions import ObjectDoesNotExist

from apigateway.apps.access_strategy.constants import AccessStrategyTypeEnum
from apigateway.apps.plugin.models import PluginBinding


class TestPluginBindingViewSet:
    def test_get(self, request_view, fake_gateway, fake_stage, echo_plugin, echo_plugin_stage_binding):
        response = request_view(
            "GET",
            "plugins.bindings.details",
            requested_api=fake_gateway,
            path_params={
                "pk": echo_plugin_stage_binding.pk,
                "gateway_id": fake_gateway.pk,
            },
        )
        result = response.json()

        assert result["code"] == 0

        binding = result["data"]
        assert binding["scope_type"] == "stage"
        assert binding["scope_id"] == fake_stage.pk
        assert binding["config_name"] == echo_plugin.name

    def test_delete(self, request_view, fake_gateway, fake_stage, echo_plugin, echo_plugin_stage_binding):
        response = request_view(
            "DELETE",
            "plugins.bindings.details",
            requested_api=fake_gateway,
            path_params={
                "pk": echo_plugin_stage_binding.pk,
                "gateway_id": fake_gateway.pk,
            },
        )

        assert response.status_code == 204

        with pytest.raises(ObjectDoesNotExist):
            echo_plugin_stage_binding.refresh_from_db()


class TestPluginBindingBatchViewSet:
    @pytest.fixture(autouse=True)
    def setup(
        self,
        mocker,
        request_view,
        fake_gateway,
        fake_stage,
        clone_model,
        echo_plugin,
        echo_plugin_stage_binding,
    ):
        self.request_view = request_view
        self.gateway = fake_gateway
        self.config = echo_plugin
        self.plugin_binding = echo_plugin_stage_binding

        fake_stage.name = "bound"
        fake_stage.save()

        self.stage_bound = fake_stage

        new_plugin = clone_model(echo_plugin, name="new_plugin")
        self.stage_overwrite = clone_model(fake_stage, name="overwrite")
        clone_model(echo_plugin_stage_binding, config=new_plugin, scope_id=self.stage_overwrite.pk)

        self.stage_unbound = clone_model(fake_stage, name="unbound")

        self.scope_mappings = {
            self.stage_bound.name: self.stage_bound.pk,
            self.stage_overwrite.name: self.stage_overwrite.pk,
            self.stage_unbound.name: self.stage_unbound.pk,
        }

    def check_plan(self, plan, binds, unbinds, overwrites):
        bind_scopes = set(self.scope_mappings[i] for i in binds)
        unbind_scopes = set(self.scope_mappings[i] for i in unbinds)
        overwrites_scopes = set(self.scope_mappings[i] for i in overwrites)

        for i in plan.get("binds") or []:
            assert i["scope_id"] in bind_scopes

        for i in plan.get("unbinds") or []:
            assert i["scope_id"] in unbind_scopes

        for i in plan.get("overwrites") or []:
            assert i["scope_id"] in overwrites_scopes

    def request_to_view(self, method, data):
        response = self.request_view(
            method,
            "plugins.config.bindings",
            requested_api=self.gateway,
            path_params={
                "config_id": self.config.pk,
                "gateway_id": self.gateway.pk,
            },
            data=data,
        )

        result = response.json()
        assert result["code"] == 0

        return result["data"]

    @pytest.mark.parametrize(
        "binds, unbinds, overwrites",
        [
            # diff
            [["bound"], [], []],  # 不修改
            [["bound", "unbound"], [], []],  # 增加环境
            [["unbound"], ["bound"], []],  # 更改环境
            [[], ["bound"], []],  # 解绑环境
            [["overwrite"], ["bound"], ["overwrite"]],  # 覆盖环境
            [["bound", "unbound", "overwrite"], [], ["overwrite"]],  # 所有环境
        ],
    )
    def test_bind(
        self,
        binds,
        unbinds,
        overwrites,
        mocker,
    ):
        mocker.patch(
            "apigateway.apps.plugin.binding.views.PluginBindingValidator._get_access_strategy_type",
            return_value=AccessStrategyTypeEnum("rate_limit"),
        )
        snapshot_qs = (
            PluginBinding.objects.filter(gateway=self.gateway)
            .order_by("pk")
            .values_list("pk", "config_id", "updated_time")
        )

        legacy_snapshots = list(snapshot_qs.all())
        request_data = {
            "dry_run": True,
            "scope_type": self.plugin_binding.scope_type,
            "scope_ids": [self.scope_mappings[n] for n in binds],
        }

        # diff only
        plan = self.request_to_view(method="POST", data=request_data)
        assert legacy_snapshots == list(snapshot_qs.all())

        # commit binding changes
        request_data["dry_run"] = False
        plan = self.request_to_view(method="POST", data=request_data)

        assert legacy_snapshots != list(snapshot_qs.all())

        self.check_plan(plan, binds, unbinds, overwrites)

    @pytest.mark.parametrize("dry_run", [True, False])
    def test_unbind(self, dry_run):
        plan = self.request_to_view(
            method="DELETE",
            data={
                "dry_run": dry_run,
                "scope_type": self.plugin_binding.scope_type,
                "scope_ids": [self.stage_bound.pk],
            },
        )

        if dry_run:
            self.plugin_binding.refresh_from_db()
        else:
            with pytest.raises(ObjectDoesNotExist):
                self.plugin_binding.refresh_from_db()

        self.check_plan(plan, [], [self.stage_bound.name], [])

    def test_list(self):
        plan = self.request_to_view(
            method="GET",
            data=None,
        )

        self.check_plan(plan, [self.stage_bound.name], [], [])
