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
import os
from dataclasses import dataclass, field
from typing import List, Optional

from apigateway.apps.support.api_sdk.exceptions import DistributeError
from apigateway.apps.support.api_sdk.models import DistributeResult, Distributor
from apigateway.components.bkrepo import BKRepoComponent


@dataclass
class GenericDistributor(Distributor):
    bkrepo: Optional[BKRepoComponent] = field(default_factory=BKRepoComponent.default)

    def distribute(self, output_dir: str, files: List[str]) -> DistributeResult:
        if not self.bkrepo:
            raise DistributeError("bkrepo configuration is not set")

        result = DistributeResult(repository="bkrepo", is_local=True)

        if not files:
            return result

        language = self.context.language.value
        filepath = files[0]
        filename = os.path.basename(filepath)
        key = f"sdks/{language}/{self.context.package}/{filename}"
        self.context.update_language_config(
            {
                "is_uploaded_to_bkrepo": True,
                "bkrepo_project": self.bkrepo.project,
                "bkrepo_bucket": self.bkrepo.generic_bucket,
                "bkrepo_key": key,
            }
        )

        self.bkrepo.upload_generic_file(filepath, key)

        result.url = self.bkrepo.generate_generic_download_url(key)
        result.is_local = False

        return result

    def enabled(self) -> bool:
        return bool(self.bkrepo and self.bkrepo.endpoint_url and self.bkrepo.endpoint_url != "")
