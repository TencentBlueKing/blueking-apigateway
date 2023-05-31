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
from typing import Dict, Generic, Type, TypeVar

FACTORY_TYPE = TypeVar("FACTORY_TYPE")


class TypeFactory(Generic[FACTORY_TYPE]):
    def __init__(self):
        self.__types__: Dict[str, Type[FACTORY_TYPE]] = {}

    def register(self, name: str, type_: Type[FACTORY_TYPE]):
        self.__types__[name] = type_

    def deregister(self, name: str):
        del self.__types__[name]

    def create(self, name: str, **kwargs) -> FACTORY_TYPE:
        type_ = self.__types__[name]
        return type_(name=name, **kwargs)  # type: ignore
