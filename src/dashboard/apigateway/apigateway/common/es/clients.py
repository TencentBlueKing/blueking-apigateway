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
import json
import logging
import re
import warnings
from typing import Any, Dict

from blue_krill.data_types.enum import EnumField, StructuredEnum
from django.conf import settings
from django.utils.translation import gettext as _
from elasticsearch.client import Elasticsearch
from elasticsearch.exceptions import (
    AuthenticationException,
    ConnectionError,
    ConnectionTimeout,
    ElasticsearchDeprecationWarning,
    NotFoundError,
)
from urllib3.exceptions import ConnectTimeoutError

from apigateway.common.error_codes import APIError, error_codes
from apigateway.components.bk_log import esquery_dsl

logger = logging.getLogger(__name__)

warnings.filterwarnings("ignore", category=ElasticsearchDeprecationWarning)


class ESClientTypeEnum(StructuredEnum):
    ELASTICSEARCH = EnumField("elasticsearch")
    BK_LOG = EnumField("bk_log")


class BaseESClient:
    def __init__(self, es_index):
        self._es_index = es_index

    def execute_search(self, body: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError()


class RawESClient(BaseESClient):
    """Use Elasticsearch directly"""

    _hosts = getattr(settings, "ELASTICSEARCH_HOSTS", None)
    _hosts_display = ",".join(getattr(settings, "ELASTICSEARCH_HOSTS_WITHOUT_AUTH", None) or [])

    _search_timeout = settings.DEFAULT_ES_SEARCH_TIMEOUT

    def _get_elasticsearch(self) -> Elasticsearch:
        if not self._hosts:
            raise error_codes.INTERNAL.format(message=_("项目配置 ELASTICSEARCH_HOSTS 不能为空。"))

        try:
            return Elasticsearch(self._hosts, timeout=self._search_timeout, max_retries=0)
        except Exception as err:
            logger.exception("failed to connect elasticsearch.")
            raise error_codes.INTERNAL.format(es_hosts_display=self._hosts_display, err=err)

    def execute_search(self, body: Dict[str, Any]) -> Dict[str, Any]:
        try:
            result = self._get_elasticsearch().search(index=self._es_index, body=body)
            return self._to_compatible_result(result)
        except ConnectionError as err:
            logger.exception("failed to connect elasticsearch.")
            raise error_codes.INTERNAL.format(es_hosts_display=self._hosts_display, err=err)
        except (ConnectionTimeout, ConnectTimeoutError):
            logger.exception(
                "connect to elasticsearch timeout. timeout=%s, index=%s, body=%s",
                self._search_timeout,
                self._es_index,
                json.dumps(body),
            )
            raise error_codes.INTERNAL.format(es_hosts_display=self._hosts_display, timeout=self._search_timeout)
        except NotFoundError:
            logger.exception("elasticsearch index not found. index=%s", self._es_index)
            raise error_codes.INTERNAL.format(es_hosts_display=self._hosts_display, index=self._es_index)
        except AuthenticationException:
            raise error_codes.INTERNAL.format(es_hosts_display=self._hosts_display)
        except Exception as err:
            logger.exception("request elasticsearch error. index=%s, body=%s", self._es_index, json.dumps(body))
            raise error_codes.INTERNAL.format(es_hosts_display=self._hosts_display, err=err)

    def _to_compatible_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        # 修改结果中 count，使其与 bklog 保持一致
        if "hits" in result and "total" in result["hits"] and isinstance(result["hits"]["total"], dict):
            result["hits"]["total"] = result["hits"]["total"]["value"]
        return result


class BKLogESClient(BaseESClient):
    def execute_search(self, body: Dict[str, Any]) -> Dict[str, Any]:
        try:
            return esquery_dsl(
                index=self._es_index,
                body=body,
            )
        except APIError as err:
            # 去除 err 敏感信息
            err_raw_msg = str(err)
            err_msg = re.sub(r'\\"bk_app_secret\\":\s*\\".*?\\"', r'\\"bk_app_secret\\": \\"******\\"', err_raw_msg)
            raise error_codes.INTERNAL.format(message=err_msg)


class ESClientFactory:
    @classmethod
    def get_es_client(cls, es_index: str) -> BaseESClient:
        es_client_type = settings.ACCESS_LOG_CONFIG["es_client_type"]
        if es_client_type == ESClientTypeEnum.BK_LOG.value:
            return BKLogESClient(es_index)

        if es_client_type == ESClientTypeEnum.ELASTICSEARCH.value:
            return RawESClient(es_index)

        raise ValueError(f"unsupported es_client_type: {es_client_type}")
