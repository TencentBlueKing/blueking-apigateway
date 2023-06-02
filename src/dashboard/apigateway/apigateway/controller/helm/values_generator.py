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
from copy import deepcopy
from typing import Any, Dict

from attrs import define, field
from django.conf import settings

from apigateway.controller.crds.config_controller import create_config_controller
from apigateway.core.micro_gateway_config import MicroGatewayHTTPInfo
from apigateway.core.models import MicroGateway, Stage


@define(slots=False)
class MicroGatewayValuesGenerator:
    micro_gateway: MicroGateway
    stage: Stage = field(init=False)
    micro_gateway_config: Dict[str, Any] = field(init=False)
    http_info: MicroGatewayHTTPInfo = field(init=False)
    values: Dict[str, Any] = field(init=False)

    def __attrs_post_init__(self):
        self.micro_gateway_config = self.micro_gateway.config
        self.stage = self.micro_gateway.stage_set.first()
        self.http_info = MicroGatewayHTTPInfo.from_micro_gateway_config(
            self.micro_gateway_config
        )  # NOTE 配置一个url, 用于状态上报
        self.values = self.micro_gateway_config.get("values", {})

    def _merge_dict(self, to: Dict[str, Any], from_: Dict[str, Any]):
        for k, v in from_.items():
            if isinstance(v, dict):
                to[k] = self._merge_dict(to.get(k, {}), v)
            else:
                to[k] = v

        return to

    def _get_stage_values(self):
        if not self.stage:
            return {}

        return {
            "desc": self.stage.description,
            "vars": self.stage.vars,
        }

    def generate_values(self) -> Dict[str, Any]:
        values = {
            "global": {
                "imageRegistry": settings.BCS_MICRO_GATEWAY_IMAGE_REGISTRY,
            },
            "serviceMonitor": {
                "enabled": True,
            },
            "replicaCount": 2,
            "operator": {
                "sentryDsn": settings.BCS_MICRO_GATEWAY_SENTRY_DSN,
            },
            "service": {
                "type": "NodePort",
            },
            "apisix": self._get_apisix_config(),
        }
        self._merge_dict(values, deepcopy(self.values))

        # TODO 暂时不支持配置, 等状态上报的方案确定
        # jwt_auth_info = MicroGatewayJWTAuth.from_micro_gateway_config(self.micro_gateway.config)
        # self._merge_dict(
        #     values,
        #     {
        #         "gatewayConfigEnabled": True,
        #         "gatewayConfig": {
        #             "instance_id": self.micro_gateway.instance_id,
        #             "controller": {
        #                 "endpoints": [settings.BK_API_URL_TMPL.format(api_name="bk-apigateway")],
        #                 "base_path": settings.EDGE_CONTROLLER_API_BASE_PATH,
        #                 "jwt_auth": {
        #                     "secret": jwt_auth_info.secret_key,
        #                 },
        #             },
        #         },
        #         "gatewayStageEnabled": False,
        #     },
        # )

        return values

    def _get_apisix_config(self) -> Dict[str, Any]:
        controller = create_config_controller(self.micro_gateway)
        config = {
            # TODO 后续需要支持bk_gateway的全套配置
            # "bk_gateway": {
            #     "instance_id": self.micro_gateway.instance_id,
            #     "controller": controller.dict(),
            # }
            "bkGateway": {
                "instance": {
                    "id": self.micro_gateway.instance_id,
                    "secret": controller.jwt_auth.secret_key,
                }
            }
        }

        return self._merge_dict(config, settings.APISIX_CONFIG)
