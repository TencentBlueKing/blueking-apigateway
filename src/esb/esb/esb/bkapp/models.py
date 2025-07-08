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

BK_APP_JSON_VERSION = 1


class BaseBKApp(object):

    app_code = ""
    verified = False

    def as_json(self):
        return {
            "version": BK_APP_JSON_VERSION,
            "bk_app_code": self.app_code,
            "verified": self.verified,
        }


class BKApp(BaseBKApp):
    def __init__(self, app_code, verified=False):
        self.app_code = app_code
        self.verified = bool(app_code and verified)
