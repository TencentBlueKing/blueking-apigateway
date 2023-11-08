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
from unittest import mock

import pytest
from django.core.exceptions import ObjectDoesNotExist
from django_dynamic_fixture import G

from apigateway.apps.gateway.models import GatewayAppBinding
from apigateway.apps.monitor.models import AlarmStrategy
from apigateway.biz.gateway import GatewayHandler
from apigateway.core.constants import APITypeEnum, ContextScopeTypeEnum, ContextTypeEnum
from apigateway.core.models import (
    JWT,
    APIRelatedApp,
    Context,
    Gateway,
    Release,
    ResourceVersion,
    Stage,
)


class TestGatewayHandler:
    @pytest.fixture(autouse=True)
    def setup_fixtures(self):
        self.gateway = G(Gateway, created_by="admin")

    # FIXME: move to tests/biz/test_gateway.py
    def test_search_api_stages(self):
        gateway = G(Gateway)

        stage_prod = G(Stage, api=gateway, name="prod", status=1)
        stage_test = G(Stage, api=gateway, name="test", status=1)

        resource_version = G(ResourceVersion, api=gateway)
        G(Release, api=gateway, stage=stage_prod, resource_version=resource_version)

        data = [
            {
                "gateway_ids": [gateway.id],
                "expected": {
                    gateway.id: [
                        {
                            "stage_id": stage_prod.id,
                            "stage_name": "prod",
                            "stage_release_status": True,
                        },
                        {
                            "stage_id": stage_test.id,
                            "stage_name": "test",
                            "stage_release_status": False,
                        },
                    ]
                },
            }
        ]

        for test in data:
            result = GatewayHandler().search_gateway_stages(test["gateway_ids"])
            assert result == test["expected"]

    @pytest.mark.parametrize(
        "user_conf, api_type, allow_update_api_auth, unfiltered_sensitive_keys, expected",
        [
            # update user_conf
            (
                {
                    "from_username": False,
                },
                None,
                None,
                None,
                {
                    "user_auth_type": "default",
                    "api_type": APITypeEnum.CLOUDS_API.value,
                    "allow_update_api_auth": True,
                    "user_conf": {
                        "user_type": "default",
                        "from_bk_token": True,
                        "from_username": False,
                    },
                    "unfiltered_sensitive_keys": [],
                },
            ),
            # update api_type
            (
                None,
                APITypeEnum.OFFICIAL_API,
                None,
                None,
                {
                    "user_auth_type": "default",
                    "api_type": APITypeEnum.OFFICIAL_API.value,
                    "allow_update_api_auth": True,
                    "user_conf": {
                        "user_type": "default",
                        "from_bk_token": True,
                        "from_username": True,
                    },
                    "unfiltered_sensitive_keys": [],
                },
            ),
            # update allow_update_api_auth
            (
                None,
                None,
                False,
                None,
                {
                    "user_auth_type": "default",
                    "api_type": APITypeEnum.CLOUDS_API.value,
                    "allow_update_api_auth": False,
                    "user_conf": {
                        "user_type": "default",
                        "from_bk_token": True,
                        "from_username": True,
                    },
                    "unfiltered_sensitive_keys": [],
                },
            ),
            (
                {
                    "from_username": False,
                    "not_exist_field": True,
                },
                APITypeEnum.OFFICIAL_API,
                False,
                None,
                {
                    "user_auth_type": "default",
                    "api_type": APITypeEnum.OFFICIAL_API.value,
                    "allow_update_api_auth": False,
                    "user_conf": {
                        "user_type": "default",
                        "from_bk_token": True,
                        "from_username": False,
                    },
                    "unfiltered_sensitive_keys": [],
                },
            ),
            # update unfiltered_sensitive_keys
            (
                None,
                None,
                None,
                ["bk_token", "bk_app_secret"],
                {
                    "user_auth_type": "default",
                    "api_type": APITypeEnum.CLOUDS_API.value,
                    "allow_update_api_auth": True,
                    "user_conf": {
                        "user_type": "default",
                        "from_bk_token": True,
                        "from_username": True,
                    },
                    "unfiltered_sensitive_keys": ["bk_token", "bk_app_secret"],
                },
            ),
        ],
    )
    def test_save_auth_config(
        self, mocker, fake_gateway, user_conf, api_type, allow_update_api_auth, unfiltered_sensitive_keys, expected
    ):
        mocker.patch(
            "apigateway.biz.gateway.GatewayHandler.get_current_gateway_auth_config",
            return_value={
                "user_auth_type": "default",
                "api_type": APITypeEnum.CLOUDS_API.value,
                "unfiltered_sensitive_keys": [],
                "allow_update_api_auth": True,
                "user_conf": {
                    "user_type": "default",
                    "from_bk_token": True,
                    "from_username": True,
                },
            },
        )

        result, _ = GatewayHandler().save_auth_config(
            fake_gateway.id,
            user_auth_type="default",
            user_conf=user_conf,
            api_type=api_type,
            allow_update_api_auth=allow_update_api_auth,
            unfiltered_sensitive_keys=unfiltered_sensitive_keys,
        )
        assert result.scope_type == ContextScopeTypeEnum.API.value
        assert result.type == ContextTypeEnum.API_AUTH.value
        assert result.scope_id == fake_gateway.id
        assert result.config == expected

    def test_save_related_data(self, mocker, fake_gateway):
        mocker.patch(
            "apigateway.biz.gateway.APIAuthConfig.config",
            new_callable=mock.PropertyMock(
                return_value={
                    "user_auth_type": "default",
                    "api_type": APITypeEnum.CLOUDS_API.value,
                    "unfiltered_sensitive_keys": [],
                    "allow_update_api_auth": True,
                    "user_conf": {
                        "user_type": "default",
                        "from_bk_token": True,
                        "from_bk_username": False,
                    },
                }
            ),
        )
        GatewayHandler().save_related_data(fake_gateway, "default", "admin", "test", app_codes_to_binding=["app1"])

        assert Context.objects.filter(
            scope_type=ContextScopeTypeEnum.API.value, type=ContextTypeEnum.API_AUTH.value, scope_id=fake_gateway.id
        ).exists()

        assert JWT.objects.filter(api=fake_gateway).exists()
        assert Stage.objects.filter(api=fake_gateway).exists()
        assert AlarmStrategy.objects.filter(api=fake_gateway).exists()
        assert APIRelatedApp.objects.filter(api=fake_gateway, bk_app_code="test").exists()
        assert GatewayAppBinding.objects.filter(gateway=fake_gateway, bk_app_code="app1").exists()

    def test_delete_api(
        self,
        fake_gateway,
        fake_stage,
        fake_resource,
        fake_resource_version,
        fake_release,
        rate_limit_access_strategy,
        rate_limit_access_strategy_stage_binding,
        rate_limit_access_strategy_resource_binding,
        echo_plugin,
        echo_plugin_stage_binding,
        echo_plugin_resource_binding,
        fake_ssl_certificate,
    ):
        GatewayHandler().delete_gateway(gateway_id=fake_gateway.pk)

        for model in [
            fake_stage,
            fake_resource,
            fake_resource_version,
            fake_release,
            rate_limit_access_strategy,
            rate_limit_access_strategy_stage_binding,
            rate_limit_access_strategy_resource_binding,
            echo_plugin,
            echo_plugin_stage_binding,
            echo_plugin_resource_binding,
            fake_ssl_certificate,
        ]:
            with pytest.raises(ObjectDoesNotExist):
                model.refresh_from_db()
