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

from apigateway.controller.helm.values_generator import MicroGatewayValuesGenerator


class TestMicroGatewayValuesGenerator:
    @pytest.fixture(autouse=True)
    def setup_micro_gateway(self, micro_gateway):
        micro_gateway.config = {
            "bcs": {
                "project_name": "testing",
                "project_id": "b37778ec757544868a01e1f01f07037f",
                "cluster_id": "BCS-K8S-00000",
                "namespace": "testing",
                "release_name": "gateway-testing",
                "chart_name": "micro-gateway-operator",
                "chart_version": "0.0.3",
            },
            "http": {"http_url": "http://test.example.com/path/prefix/"},
            "jwt_auth": {"secret_key": "jwt_secret_key"},
        }

    @pytest.fixture(autouse=True)
    def setup_settings(self, settings, faker):
        settings.BCS_MICRO_GATEWAY_IMAGE_REGISTRY = faker.url()
        settings.BCS_MICRO_GATEWAY_SENTRY_DSN = faker.pystr()
        settings.BK_API_URL_TMPL = faker.url()
        settings.EDGE_CONTROLLER_API_BASE_PATH = "/"

    def test_generate_values(self, mocker, micro_gateway, settings):
        settings.APISIX_CONFIG = {
            "plugin_attr": {
                "log-rotate": {
                    # 每间隔多长时间切分一次日志，秒为单位
                    "interval": 60 * 60,
                    # 最多保留多少份历史日志，超过指定数量后，自动删除老文件
                    "max_kept": 24 * 7,
                },
                "prometheus": {
                    "export_addr": {
                        "ip": "0.0.0.0",
                    },
                },
            },
        }

        generator = MicroGatewayValuesGenerator(micro_gateway)
        values = generator.generate_values()

        assert values == {
            "global": {
                "imageRegistry": settings.BCS_MICRO_GATEWAY_IMAGE_REGISTRY,
                "serviceMonitor": {
                    "enabled": True,
                },
            },
            "sentry": {
                "enabled": settings.BCS_MICRO_GATEWAY_SENTRY_DSN != "",
                "dsn": settings.BCS_MICRO_GATEWAY_SENTRY_DSN,
            },
            "replicaCount": 2,
            "gatewayStageEnabled": False,
            "service": {
                "type": "NodePort",
            },
            "gatewayConfigEnabled": True,
            "gatewayConfig": {
                "instance_id": micro_gateway.instance_id,
                "controller": {
                    "endpoints": [settings.BK_API_URL_TMPL.format(api_name="bk-apigateway")],
                    "base_path": settings.EDGE_CONTROLLER_API_BASE_PATH,
                    "jwt_auth": {
                        "secret": "jwt_secret_key",
                    },
                },
            },
            "gomicro-discovery-operator": {
                "enabled": False,
            },
            "apisixConfig": {
                "plugin_attr": {
                    "log-rotate": {
                        "interval": 60 * 60,
                        "max_kept": 24 * 7,
                    },
                    "prometheus": {
                        "export_addr": {
                            "ip": "0.0.0.0",
                        },
                    },
                },
                "bk_gateway": {
                    "instance_id": micro_gateway.instance_id,
                    "controller": {
                        "endpoints": [settings.BK_API_URL_TMPL.format(api_name="bk-apigateway")],
                        "base_path": settings.EDGE_CONTROLLER_API_BASE_PATH,
                        "jwt_auth": {"secret": "jwt_secret_key"},
                    },
                },
            },
        }

    def test_generate_values_with_extra_config(self, micro_gateway):
        micro_gateway.config = {
            **micro_gateway.config,
            "values": {
                "extraEnvVarsSecret": "env-vars-secret",
                "replicaCount": 1,
                "gatewayConfigEnabled": True,
                "gatewayConfig": {
                    "instance_id": "not-allowed",
                },
            },
        }

        generator = MicroGatewayValuesGenerator(micro_gateway)
        values = generator.generate_values()

        assert values["replicaCount"] == 1
        assert values["extraEnvVarsSecret"] == "env-vars-secret"
        assert values["gatewayConfig"]["instance_id"] == micro_gateway.instance_id
