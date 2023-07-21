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
from operator import itemgetter
from typing import Any, Dict

from bkapi_client_core.apigateway import OperationGroup
from bkapi_client_core.apigateway.django_helper import get_client_by_username as get_client_by_username_for_apigateway
from django.conf import settings

from apigateway.components.bkapi_client.log_search import Client as LogSearchClient
from apigateway.components.esb_components import get_client_by_username as get_client_by_username_for_esb
from apigateway.components.handler import RequestAPIHandler
from apigateway.components.utils import inject_accept_language


class BKLogComponent:
    def __init__(self):
        self._api_client: OperationGroup = self._get_api_client()
        self._request_handler = RequestAPIHandler("bk-log")

    def esquery_dsl(self, index: str, body: Any) -> Dict[str, Any]:
        data = {
            "indices": index,
            "body": body,
        }

        headers = {"Content-Type": "application/json"}

        api_result, response = self._request_handler.call_api(self._api_client.esquery_dsl, data, headers=headers)
        return self._request_handler.parse_api_result(api_result, response, {"result": True}, itemgetter("data"))

    def _get_api_client(self) -> OperationGroup:
        # use gateway: log-search
        if settings.USE_BKAPI_BK_LOG:
            apigw_client = get_client_by_username_for_apigateway(LogSearchClient, username="admin")
            apigw_client.session.register_hook("request", inject_accept_language)
            return apigw_client.api

        esb_client = get_client_by_username_for_esb("admin")
        esb_client.session.register_hook("request", inject_accept_language)
        return esb_client.bk_log


bk_log_component = BKLogComponent()
