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
from django.conf import settings

from apigateway.utils.http import http_post

from .component import BaseComponent

BK_APP_CODE = getattr(settings, "BK_APP_CODE", "")
BK_APP_SECRET = getattr(settings, "BK_APP_SECRET", "")

BKDATA_DATA_TOKEN = getattr(settings, "BKDATA_DATA_TOKEN", "")


class BKDataComponent(BaseComponent):

    HOST = getattr(settings, "BKDATA_HOST", "")

    def get_data(self, prefer_storage, sql):
        params = {
            "prefer_storage": prefer_storage,
            "sql": sql,
            "bk_app_code": BK_APP_CODE,
            "bk_app_secret": BK_APP_SECRET,
            "bkdata_data_token": BKDATA_DATA_TOKEN,
            "bkdata_authentication_method": "token",
        }
        return self._call_api(http_post, "/prod/get_data", params)


bkdata_component = BKDataComponent()
