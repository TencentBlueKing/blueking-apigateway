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


class ComponentBaseException(Exception):
    pass


class ComponentAPIException(ComponentBaseException):
    """Exception for Component API"""

    def __init__(self, api_obj, error_message, resp=None):
        self.api_obj = api_obj
        self.error_message = error_message
        self.resp = resp

        if self.resp is not None:
            error_message = "%s, resp=%s" % (error_message, self.resp.text)
        super(ComponentAPIException, self).__init__(error_message)
