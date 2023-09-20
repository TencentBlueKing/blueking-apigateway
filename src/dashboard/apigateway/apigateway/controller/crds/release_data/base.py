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
from dataclasses import dataclass
from typing import Any, ClassVar, Dict


@dataclass
class PluginData:
    type_code: str
    config: Dict[str, Any]
    binding_scope_type: str
    _type_code_to_name: ClassVar[Dict[str, str]] = {
        "bk-rate-limit:stage": "bk-stage-rate-limit",
        "bk-rate-limit:resource": "bk-resource-rate-limit",
        "bk-header-rewrite:stage": "bk-stage-header-rewrite",
        "bk-header-rewrite:resource": "bk-resource-header-rewrite",
    }

    @property
    def name(self) -> str:
        """
        插件信息中，type_code 为插件类型，一般情况下，此即为插件名；
        但是，频率控制插件绑定到环境、资源时，使用了不同的插件，所以要做一下转换
        """
        return self._type_code_to_name.get(f"{self.type_code}:{self.binding_scope_type}", self.type_code)
