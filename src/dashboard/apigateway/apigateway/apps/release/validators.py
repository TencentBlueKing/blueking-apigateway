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
from django.utils.translation import gettext as _

from apigateway.apps.stage.validators import StageVarsValuesValidator
from apigateway.common.contexts import StageProxyHTTPContext
from apigateway.core.models import Gateway, Stage


class ReleaseValidationError(Exception):
    """发布校验失败"""


class ReleaseValidator:
    """
    发布校验器
    - 1. 校验环境的代理配置中，上游主机地址有效
    - 2. 校验环境变量有效，且 resource version 中资源引用的环境变量有效
    """

    def __init__(self, gateway: Gateway, stage: Stage, resource_version_id: int):
        self.gateway = gateway
        self.stage = stage
        self.resource_version_id = resource_version_id

    def validate(self):
        self._validate_stage_upstreams()
        self._validate_stage_vars()

    def _validate_stage_upstreams(self):
        """检查环境的代理配置，如果未配置任何有效的上游主机地址（Hosts），则报错。

        :raise ReleaseValidationError: 当未配置 Hosts 时。
        """
        if not StageProxyHTTPContext().contain_hosts(self.stage.id):
            raise ReleaseValidationError(
                _("网关环境【{stage_name}】中代理配置 Hosts 未配置，请在网关 `基本设置 -> 环境管理` 中进行配置。").format(
                    stage_name=self.stage.name,
                )
            )

    def _validate_stage_vars(self):
        validator = StageVarsValuesValidator()
        validator(
            {
                "gateway": self.gateway,
                "stage_name": self.stage.name,
                "vars": self.stage.vars,
                "resource_version_id": self.resource_version_id,
            }
        )
