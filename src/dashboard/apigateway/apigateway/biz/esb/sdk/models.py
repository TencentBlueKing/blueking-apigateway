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
from dataclasses import asdict, dataclass, field

from django.conf import settings

from apigateway.biz.esb.board_config import BoardConfigManager


@dataclass
class SDKDocContext:
    board: str
    system_name: str
    component_name: str
    package_prefix: str = ""

    def __post_init__(self):
        board_config = BoardConfigManager.get_board_config(self.board)
        self.package_prefix = board_config.sdk_package_prefix

    def as_dict(self):
        return asdict(self)


@dataclass
class DummySDKDocContext(SDKDocContext):
    board: str = settings.ESB_DEFAULT_BOARD
    system_name: str = "cc"
    component_name: str = "search_business"


@dataclass
class DocTemplates:
    board: str
    language_code: str
    programming_language: str
    templates: dict = field(init=False, default_factory=dict)

    def __post_init__(self):
        self.board_config = BoardConfigManager.get_board_config(self.board)
        self.templates = {
            "sdk_usage_example": self._get_sdk_usage_example_template(),
            "sdk_doc": f"esb_sdk/{self.language_code}/{self.programming_language}_sdk_doc.md",
        }

    def _get_sdk_usage_example_template(self):
        template = self.board_config.sdk_doc_templates[f"{self.programming_language}_sdk_usage_example"]
        return f"esb_sdk/{self.language_code}/{template}"
