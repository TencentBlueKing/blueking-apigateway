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
import copy

import pytest
from ddf import G

from apigateway.apps.plugin.models import PluginBinding, PluginConfig
from apigateway.biz.resource.importer.legacy_synchronizers import (
    LegacyBackendCreator,
    LegacyTransformHeadersToPluginSynchronizer,
    LegacyUpstream,
    LegacyUpstreamToBackendSynchronizer,
)
from apigateway.core.constants import DEFAULT_BACKEND_NAME
from apigateway.core.models import Backend, BackendConfig, Stage


class TestLegacyUpstream:
    def test_get_stage_id_to_backend_config(self, fake_gateway):
        s1 = G(Stage, gateway=fake_gateway, _vars='{"foo": "bar.com"}')
        s2 = G(Stage, gateway=fake_gateway, _vars='{"foo": "baz.com"}')

        upstreams = {
            "hosts": [{"host": "https://{env.foo}/", "weight": 10}],
            "loadbalance": "roundrobin",
        }
        stage_id_to_timeout = {s1.id: 20, s2.id: 30}

        result = LegacyUpstream(upstreams).get_stage_id_to_backend_config([s1, s2], stage_id_to_timeout)
        assert result == {
            s1.id: {
                "type": "node",
                "timeout": {"connect": 20, "read": 20, "send": 20},
                "loadbalance": "roundrobin",
                "hosts": [{"scheme": "https", "host": "bar.com", "weight": 10}],
            },
            s2.id: {
                "type": "node",
                "timeout": {"connect": 30, "read": 30, "send": 30},
                "loadbalance": "roundrobin",
                "hosts": [{"scheme": "https", "host": "baz.com", "weight": 10}],
            },
        }

    @pytest.mark.parametrize(
        "vars, host, expected",
        [
            ({"foo": "bar.com"}, "https://{env.foo}/", "https://bar.com/"),
            ({"foo1": "bar.com", "foo2": "baz.com"}, "https://{env.foo1}/{env.foo2}", "https://bar.com/baz.com"),
            ({}, "https://{env.foo}/", "https://{env.foo}/"),
            ({"color": "green"}, "https://{env.foo}/", "https://{env.foo}/"),
        ],
    )
    def test_render_host(self, vars, host, expected):
        result = LegacyUpstream({})._render_host(vars, host)
        assert result == expected


class TestLegacyBackendCreator:
    def test_match_or_create_backend(self, fake_gateway, fake_stage):
        stage_id_to_backend_config = {
            fake_stage.id: {
                "type": "node",
                "timeout": {"connect": 50, "read": 50, "send": 50},
                "loadbalance": "roundrobin",
                "hosts": [{"scheme": "https", "host": "foo.com", "weight": 10}],
                "retries": 0,
                "retry_timeout": 0,
                "hash_on": "",
                "key": "",
            }
        }
        creator = LegacyBackendCreator(fake_gateway, "admin")
        result = creator.match_or_create_backend(stage_id_to_backend_config)
        assert result.name == "backend-1"
        assert BackendConfig.objects.get(backend=result).config == stage_id_to_backend_config[fake_stage.id]

        result = creator.match_or_create_backend(stage_id_to_backend_config)
        assert result.name == "backend-1"

        stage_id_to_backend_config_2 = copy.deepcopy(stage_id_to_backend_config)
        stage_id_to_backend_config_2[fake_stage.id]["timeout"] = {"connect": 10, "read": 10, "send": 10}

        result = creator.match_or_create_backend(stage_id_to_backend_config_2)
        assert result.name == "backend-2"

        result = creator.match_or_create_backend(stage_id_to_backend_config)
        assert result.name == "backend-1"

    @pytest.mark.parametrize(
        "existing_backend_configs, stage_id_to_backend_config, expected",
        [
            (
                {
                    1: {
                        1: {
                            "type": "node",
                            "timeout": 50,
                            "loadbalance": "roundrobin",
                            "hosts": [
                                {"scheme": "https", "host": "foo.com", "weight": 10},
                                {"scheme": "http", "host": "bar.com", "weight": 10},
                            ],
                        },
                        2: {
                            "type": "node",
                            "timeout": 50,
                            "loadbalance": "roundrobin",
                            "hosts": [
                                {"scheme": "http", "host": "foo.com", "weight": 20},
                                {"scheme": "http", "host": "bar.com", "weight": 20},
                            ],
                        },
                    },
                },
                {
                    1: {
                        "type": "node",
                        "timeout": 50,
                        "loadbalance": "roundrobin",
                        "hosts": [
                            {"scheme": "https", "host": "foo.com", "weight": 10},
                            {"scheme": "http", "host": "bar.com", "weight": 10},
                        ],
                    },
                    2: {
                        "type": "node",
                        "timeout": 50,
                        "loadbalance": "roundrobin",
                        "hosts": [
                            {"scheme": "http", "host": "foo.com", "weight": 20},
                            {"scheme": "http", "host": "bar.com", "weight": 20},
                        ],
                    },
                },
                1,
            ),
            (
                {
                    1: {
                        1: {
                            "type": "node",
                            "timeout": 50,
                            "loadbalance": "roundrobin",
                            "hosts": [
                                {"scheme": "http", "host": "foo.com", "weight": 10},
                                {"scheme": "http", "host": "bar.com", "weight": 10},
                            ],
                        },
                    },
                },
                {
                    1: {
                        "type": "node",
                        "timeout": 50,
                        "loadbalance": "roundrobin",
                        "hosts": [
                            {"scheme": "http", "host": "bar.com", "weight": 10},
                            {"scheme": "http", "host": "foo.com", "weight": 10},
                        ],
                    },
                },
                None,
            ),
            (
                {
                    1: {
                        1: {
                            "type": "node",
                            "timeout": 50,
                            "loadbalance": "roundrobin",
                            "hosts": [
                                {"scheme": "https", "host": "foo.com", "weight": 10},
                            ],
                        },
                    },
                },
                {
                    1: {
                        "type": "node",
                        "timeout": 50,
                        "loadbalance": "roundrobin",
                        "hosts": [
                            {"scheme": "http", "host": "foo.com", "weight": 10},
                        ],
                    },
                },
                None,
            ),
        ],
    )
    def test_match_existing_backend(
        self,
        fake_gateway,
        existing_backend_configs,
        stage_id_to_backend_config,
        expected,
    ):
        creator = LegacyBackendCreator(fake_gateway, "admin")
        creator._existing_backend_configs = existing_backend_configs

        result = creator._match_existing_backend(stage_id_to_backend_config)
        assert result == expected

    def test_get_existing_backend_configs(self, fake_gateway, fake_stage):
        b1 = G(Backend, name="default", gateway=fake_gateway)
        b2 = G(Backend, name="backend-1", gateway=fake_gateway)

        G(
            BackendConfig,
            backend=b1,
            gateway=fake_gateway,
            stage=fake_stage,
            config={
                "type": "node",
                "timeout": 50,
                "loadbalance": "roundrobin",
                "hosts": [{"scheme": "http", "host": "foo.com", "weight": 100}],
            },
        )
        G(
            BackendConfig,
            backend=b2,
            gateway=fake_gateway,
            stage=fake_stage,
            config={
                "type": "node",
                "timeout": 50,
                "loadbalance": "roundrobin",
                "hosts": [{"scheme": "http", "host": "bar.com", "weight": 100}],
            },
        )

        creator = LegacyBackendCreator(fake_gateway, "admin")
        result = creator._get_existing_backend_configs()
        assert result == {
            b1.id: {
                fake_stage.id: {
                    "type": "node",
                    "timeout": {"connect": 50, "read": 50, "send": 50},
                    "loadbalance": "roundrobin",
                    "hosts": [{"scheme": "http", "host": "foo.com", "weight": 100}],
                    "retries": 0,
                    "retry_timeout": 0,
                    "hash_on": "",
                    "key": "",
                }
            },
            b2.id: {
                fake_stage.id: {
                    "type": "node",
                    "timeout": {"connect": 50, "read": 50, "send": 50},
                    "loadbalance": "roundrobin",
                    "hosts": [{"scheme": "http", "host": "bar.com", "weight": 100}],
                    "retries": 0,
                    "retry_timeout": 0,
                    "hash_on": "",
                    "key": "",
                }
            },
        }

    def test_generate_new_backend_name(self, fake_gateway):
        creator = LegacyBackendCreator(fake_gateway, "admin")
        result = creator._generate_new_backend_name()
        assert result == "backend-1"

        creator._max_legacy_backend_number = 100
        result = creator._generate_new_backend_name()
        assert result == "backend-101"

    def test_create_backend_and_backend_configs(self, fake_gateway, fake_stage):
        creator = LegacyBackendCreator(fake_gateway, "admin")
        creator._create_backend_and_backend_configs(
            "backend-1",
            {
                fake_stage.id: {
                    "type": "node",
                    "timeout": 50,
                    "loadbalance": "roundrobin",
                    "hosts": [{"scheme": "http", "host": "foo.com", "weight": 100}],
                }
            },
        )
        assert Backend.objects.filter(name="backend-1", gateway=fake_gateway).exists()
        assert BackendConfig.objects.filter(backend__name="backend-1", gateway=fake_gateway).exists()

    @pytest.mark.parametrize(
        "hosts, expected",
        [
            (
                [
                    {"scheme": "http", "host": "foo.com", "weight": 10},
                    {"scheme": "http", "host": "bar.com", "weight": 10},
                    {"scheme": "http", "host": "baz.com", "weight": 10},
                ],
                [
                    {"scheme": "http", "host": "bar.com", "weight": 10},
                    {"scheme": "http", "host": "baz.com", "weight": 10},
                    {"scheme": "http", "host": "foo.com", "weight": 10},
                ],
            ),
        ],
    )
    def test_sort_hosts(self, fake_gateway, hosts, expected):
        creator = LegacyBackendCreator(fake_gateway, "admin")
        result = creator._sort_hosts(hosts)
        assert result == expected

    def test_get_max_legacy_backend_number(self, fake_gateway):
        creator = LegacyBackendCreator(fake_gateway, "admin")
        result = creator._get_max_legacy_backend_number()
        assert result == 0

        G(Backend, name="backend-1", gateway=fake_gateway)
        G(Backend, name="backend-10", gateway=fake_gateway)
        G(Backend, name="foo", gateway=fake_gateway)
        G(Backend, name="backend-2", gateway=fake_gateway)

        result = creator._get_max_legacy_backend_number()
        assert result == 10


class TestLegacyUpstreamToBackendSynchronizer:
    def test_sync_backends_and_replace_resource_backend__no_upstreams(self, fake_gateway, fake_resource_data):
        synchronizer = LegacyUpstreamToBackendSynchronizer(fake_gateway, [fake_resource_data], "admin")
        synchronizer.sync_backends_and_replace_resource_backend()
        assert fake_resource_data.backend is None

    def test_sync_backends_and_replace_resource_backend__has_upstreams(
        self,
        fake_gateway,
        fake_stage,
        fake_resource_data,
    ):
        backend = G(Backend, name=DEFAULT_BACKEND_NAME, gateway=fake_gateway)
        G(
            BackendConfig,
            gateway=fake_gateway,
            stage=fake_stage,
            backend=backend,
            config={
                "type": "node",
                "timeout": 30,
                "loadbalance": "roundrobin",
                "hosts": [{"scheme": "http", "host": "foo.com", "weight": 100}],
            },
        )
        fake_resource_data.backend_config.legacy_upstreams = {
            "loadbalance": "roundrobin",
            "hosts": [{"host": "https://bar.com", "weight": 10}],
        }

        synchronizer = LegacyUpstreamToBackendSynchronizer(fake_gateway, [fake_resource_data], "admin")
        synchronizer.sync_backends_and_replace_resource_backend()

        backend = Backend.objects.get(gateway=fake_gateway, name="backend-1")
        backend_config = BackendConfig.objects.get(gateway=fake_gateway, backend__name="backend-1")
        assert fake_resource_data.backend == backend
        assert backend_config.config == {
            "type": "node",
            "timeout": {"connect": 30, "read": 30, "send": 30},
            "loadbalance": "roundrobin",
            "hosts": [{"scheme": "https", "host": "bar.com", "weight": 10}],
            "retries": 0,
            "retry_timeout": 0,
            "hash_on": "",
            "key": "",
        }


class TestLegacyTransformHeadersToPluginSynchronizer:
    def test_sync_plugins(self, fake_gateway, fake_resource, fake_resource_data, fake_plugin_type_bk_header_rewrite):
        fake_resource_data.resource = fake_resource
        synchronizer = LegacyTransformHeadersToPluginSynchronizer(fake_gateway, [fake_resource_data], "admin")

        synchronizer.sync_plugins()
        assert not PluginConfig.objects.filter(gateway=fake_gateway).exists()
        assert not PluginBinding.objects.filter(gateway=fake_gateway).exists()

        # add
        fake_resource_data.backend_config.legacy_transform_headers = {
            "set": {"x-token": "test"},
            "delete": ["x-token"],
        }
        synchronizer.sync_plugins()
        plugin_config = PluginConfig.objects.get(gateway=fake_gateway, type__code="bk-header-rewrite")
        assert plugin_config.config == {"set": [{"key": "x-token", "value": "test"}], "remove": [{"key": "x-token"}]}
        assert PluginBinding.objects.filter(
            gateway=fake_gateway, scope_type="resource", scope_id=fake_resource.id
        ).exists()

        # update
        fake_resource_data.backend_config.legacy_transform_headers = {
            "set": {"x-foo": "test"},
            "delete": ["x-bar"],
        }
        synchronizer.sync_plugins()
        plugin_config = PluginConfig.objects.get(gateway=fake_gateway, type__code="bk-header-rewrite")
        assert plugin_config.config == {"set": [{"key": "x-foo", "value": "test"}], "remove": [{"key": "x-bar"}]}
        assert PluginBinding.objects.filter(
            gateway=fake_gateway, scope_type="resource", scope_id=fake_resource.id
        ).exists()

        # delete
        fake_resource_data.backend_config.legacy_transform_headers = {}
        synchronizer.sync_plugins()
        assert not PluginConfig.objects.filter(gateway=fake_gateway).exists()
        assert not PluginBinding.objects.filter(gateway=fake_gateway).exists()
