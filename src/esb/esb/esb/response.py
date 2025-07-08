# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2025 Tencent. All rights reserved.
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


from builtins import object


class CompResponse(object):
    """
    Response class for Component
    """

    def __init__(self):
        self.payload = {}
        self.headers = {}

    def get_payload(self):
        return self.payload


def format_resp_dict(resp_data):
    """
    根据给定的数据生成一个标准的HttpResponse数据
    """
    resp_data.setdefault("result", False)
    resp_data.setdefault("data", None)
    resp_data.setdefault("message", "")
    resp_data.setdefault("code", 0 if resp_data["result"] else 1306000)
    return resp_data
