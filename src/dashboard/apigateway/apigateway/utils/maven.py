#  -*- coding: utf-8 -*-
#  #
#  TencentBlueKing is pleased to support the open source community by making
#  蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
#  Copyright (C) 2017 THL A29 Limited, a Tencent company. All rights reserved.
#  Licensed under the MIT License (the "License"); you may not use this file except
#  in compliance with the License. You may obtain a copy of the License at
#  #
#      http://opensource.org/licenses/MIT
#  #
#  Unless required by applicable law or agreed to in writing, software distributed under
#  the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
#  either express or implied. See the License for the specific language governing permissions and
#  limitations under the License.
#  #
#  We undertake not to change the open source license (MIT license) applicable
#  to the current version of the project delivered to anyone in the future.
#  #
from dataclasses import dataclass

from django.conf import settings


@dataclass
class RepositoryConfig:
    repository_url: str
    repository_id: str
    username: str
    password: str

    @classmethod
    def by_name(cls, name: str):
        mirrors_config = getattr(settings, "MAVEN_MIRRORS_CONFIG", None) or {}
        maven_config = mirrors_config.get(name) or {}

        return cls(
            repository_url=maven_config.get("repository_url", ""),
            repository_id=maven_config.get("repository_id", ""),
            username=maven_config.get("username", ""),
            password=maven_config.get("password", ""),
        )
