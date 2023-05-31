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

from apigateway.apps.resource.mixins import CreateResourceMixin, UpdateResourceMixin
from apigateway.biz.resource import ResourceHandler
from apigateway.core import constants
from apigateway.core.models import Context, Proxy, Resource

pytestmark = pytest.mark.django_db


class TestCreateResourceMixin:
    @pytest.mark.parametrize(
        "resource, expected_context_config",
        [
            (
                {
                    "name": "post_echo",
                    "description": "desc",
                    "is_public": True,
                    "method": "POST",
                    "path": "/echo/",
                    "match_subpath": True,
                    "label_ids": [],
                    "proxy_type": "http",
                    "proxy_configs": {
                        "http": {
                            "method": "GET",
                            "path": "/echo/",
                            "match_subpath": True,
                            "timeout": 30,
                            "upstreams": {
                                "loadbalance": "roundrobin",
                                "hosts": [
                                    {
                                        "host": "http://www.a.com",
                                        "weight": 100,
                                    }
                                ],
                            },
                            "transform_headers": {},
                        }
                    },
                    "auth_config": {
                        "auth_verified_required": False,
                        "app_verified_required": True,
                        "resource_perm_required": True,
                    },
                    "disabled_stage_ids": [],
                },
                {
                    "skip_auth_verification": False,
                    "auth_verified_required": False,
                    "app_verified_required": True,
                    "resource_perm_required": True,
                },
            ),
            # ok, proxy-config 不覆盖环境配置
            (
                {
                    "name": "get_echo_2",
                    "description": "desc",
                    "is_public": True,
                    "method": "GET",
                    "path": "/echo/2/",
                    "match_subpath": False,
                    "label_ids": [],
                    "proxy_type": "http",
                    "proxy_configs": {
                        "http": {
                            "method": "GET",
                            "path": "/echo/",
                            "match_subpath": False,
                            "timeout": 0,
                            "upstreams": {},
                            "transform_headers": {},
                        }
                    },
                    "auth_config": {
                        "auth_verified_required": False,
                        "app_verified_required": True,
                        "resource_perm_required": True,
                    },
                    "disabled_stage_ids": [],
                },
                {
                    "skip_auth_verification": False,
                    "auth_verified_required": False,
                    "app_verified_required": True,
                    "resource_perm_required": True,
                },
            ),
        ],
    )
    def test_create_resource(self, fake_gateway, resource, expected_context_config):
        mixin = CreateResourceMixin()
        mixin._create_resource(fake_gateway, resource, "admin")

        instance = Resource.objects.get(api=fake_gateway, method=resource["method"], path=resource["path"])
        assert instance.is_public == resource["is_public"]
        assert instance.match_subpath == resource["match_subpath"]

        proxy = Proxy.objects.get(type=resource["proxy_type"], resource=instance)
        assert instance.proxy_id == proxy.id
        assert proxy.config == resource["proxy_configs"][resource["proxy_type"]]

        # check resource auth config
        context = Context.objects.get(
            scope_type=constants.ContextScopeTypeEnum.RESOURCE.value,
            scope_id=instance.id,
            type=constants.ContextTypeEnum.RESOURCE_AUTH.value,
        )
        assert context.config == expected_context_config


class TestUpdateResourceMixin:
    @pytest.mark.parametrize(
        "resource, will_error",
        [
            (
                {
                    "name": "post_echo",
                    "description": "desc",
                    "is_public": True,
                    "method": "POST",
                    "path": "/echo/",
                    "label_ids": [],
                    "proxy_type": "http",
                    "proxy_configs": {
                        "http": {
                            "method": "GET",
                            "path": "/echo/",
                            "timeout": 30,
                            "upstreams": {
                                "loadbalance": "roundrobin",
                                "hosts": [
                                    {
                                        "host": "http://www.a.com",
                                        "weight": 100,
                                    }
                                ],
                            },
                            "transform_headers": {},
                        }
                    },
                    "auth_config": {
                        "auth_verified_required": False,
                        "app_verified_required": True,
                        "resource_perm_required": True,
                    },
                    "disabled_stage_ids": [],
                },
                False,
            ),
            # resource label_id exceed the maximum
            (
                {
                    "name": "post_echo",
                    "description": "desc",
                    "is_public": True,
                    "method": "POST",
                    "path": "/echo/",
                    "label_ids": list(range(11)),
                    "proxy_type": "http",
                    "proxy_configs": {
                        "http": {
                            "method": "GET",
                            "path": "/echo/",
                            "timeout": 30,
                            "upstreams": {"loadbalance": "roundrobin", "hosts": [{"host": "http://www.a.com"}]},
                            "transform_headers": {},
                        }
                    },
                    "auth_config": {
                        "auth_verified_required": False,
                        "app_verified_required": True,
                        "resource_perm_required": True,
                    },
                    "disabled_stage_ids": [],
                },
                True,
            ),
        ],
    )
    def test_update_resource(self, fake_gateway, resource, will_error):
        instance = G(Resource, api=fake_gateway)
        ResourceHandler().save_auth_config(
            instance.id,
            {
                "skip_auth_verification": False,
                "auth_verified_required": False,
                "app_verified_required": True,
                "resource_perm_required": True,
            },
        )

        mixin = UpdateResourceMixin()

        if will_error:
            with pytest.raises(Exception):
                mixin._update_resource(fake_gateway, instance, resource, "admin")
            return

        mixin._update_resource(fake_gateway, instance, resource, "admin")

        instance = Resource.objects.get(api=fake_gateway, method=resource["method"], path=resource["path"])
        assert instance.is_public == resource["is_public"]

        proxy = Proxy.objects.get(type=resource["proxy_type"], resource=instance)
        assert instance.proxy_id == proxy.id
        assert proxy.config == resource["proxy_configs"][resource["proxy_type"]]

        # check resource auth config
        context = Context.objects.get(
            scope_type=constants.ContextScopeTypeEnum.RESOURCE.value,
            scope_id=instance.id,
            type=constants.ContextTypeEnum.RESOURCE_AUTH.value,
        )
        assert context.config == {
            "skip_auth_verification": False,
            "auth_verified_required": False,
            "app_verified_required": True,
            "resource_perm_required": True,
        }
