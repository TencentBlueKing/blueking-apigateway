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
import logging
import re
import warnings
from typing import Any, Dict

from elasticsearch.exceptions import (
    ElasticsearchDeprecationWarning,
)

from apigateway.common.error_codes import error_codes
from apigateway.components.bk_log import bk_log_component
from apigateway.components.exceptions import RemoteAPIResultError, RemoteRequestError

logger = logging.getLogger(__name__)

warnings.filterwarnings("ignore", category=ElasticsearchDeprecationWarning)


class BaseESClient:
    def __init__(self, es_index):
        self._es_index = es_index

    def execute_search(self, body: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError()


class BKLogESClient(BaseESClient):
    def execute_search(self, body: Dict[str, Any]) -> Dict[str, Any]:
        try:
            return bk_log_component.esquery_dsl(
                index=self._es_index,
                body=body,
            )
        except (RemoteRequestError, RemoteAPIResultError) as err:
            # 去除 err 敏感信息
            err_raw_msg = str(err)
            err_msg = re.sub(r'\\"bk_app_secret\\":\s*\\".*?\\"', r'\\"bk_app_secret\\": \\"******\\"', err_raw_msg)
            raise error_codes.INTERNAL.format(message=err_msg)
