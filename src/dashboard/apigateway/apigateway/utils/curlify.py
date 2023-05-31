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
import curlify
from requests.structures import CaseInsensitiveDict

UNSET = object()


class WrappedRequest:
    def __init__(self, request, headers=UNSET, header_keys=UNSET):
        self.__request = request

        headers = self.__request.headers if headers is UNSET else headers or {}
        header_keys = headers.keys() if header_keys is UNSET else header_keys or {}
        self.headers = CaseInsensitiveDict({k: headers.get(k) for k in header_keys})

    def __getattr__(self, name):
        return getattr(self.__request, name)


def to_curl(request, verify=True, headers=UNSET, header_keys=UNSET):
    """增强 curlify.to_curl，仅追加指定的头部字段"""

    return curlify.to_curl(WrappedRequest(request, headers=headers, header_keys=header_keys), verify=verify)
