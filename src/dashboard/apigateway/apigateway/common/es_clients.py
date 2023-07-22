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
from typing import Any, Dict

from blue_krill.data_types.enum import EnumField, StructuredEnum
from django.conf import settings
from django.utils.translation import gettext as _
from elasticsearch.client import Elasticsearch
from elasticsearch.exceptions import AuthenticationException, ConnectionError, ConnectionTimeout, NotFoundError
from elasticsearch_dsl import Search
from urllib3.exceptions import ConnectTimeoutError

from apigateway.common.error_codes import error_codes
from apigateway.components.bk_log import bk_log_component
from apigateway.components.exceptions import RemoteAPIResultError, RemoteRequestError

logger = logging.getLogger(__name__)


class ESClientTypeEnum(StructuredEnum):
    ELASTICSEARCH = EnumField("elasticsearch")
    BK_LOG = EnumField("bk_log")


class ElasticsearchGetter:
    _hosts = getattr(settings, "ELASTICSEARCH_HOSTS", None)
    _search_timeout = settings.DEFAULT_ES_SEARCH_TIMEOUT

    def _get_elasticsearch(self) -> Elasticsearch:
        if not self._hosts:
            raise error_codes.ES_HOST_EMPTY_ERROR.format(message=_("项目配置 ELASTICSEARCH_HOSTS 不能为空。"))

        try:
            return Elasticsearch(self._hosts, timeout=self._get_es_search_timeout(), max_retries=0)
        except Exception as err:
            logger.exception("failed to connect elasticsearch.")
            raise error_codes.ES_CONNECTION_ERROR.format(es_hosts_display=self._get_es_hosts_display(), err=err)

    def _get_es_hosts_display(self) -> str:
        return ",".join(getattr(settings, "ELASTICSEARCH_HOSTS_WITHOUT_AUTH", None) or [])

    def _get_es_search_timeout(self):
        return self._search_timeout


class BaseESClient:
    def __init__(self, es_index):
        self._es_index = es_index

    def _get_es_index(self) -> str:
        return self._es_index

    def execute_search(self, body: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError()


class DslESClient(ElasticsearchGetter, BaseESClient):
    """Use Elasticsearch DSL"""

    def execute_search_with_dsl_search(self, s: Search):
        try:
            response = s.execute()
        except ConnectionError as err:
            logger.exception("failed to connect elasticsearch.")
            raise error_codes.ES_CONNECTION_ERROR.format(es_hosts_display=self._get_es_hosts_display(), err=err)
        except (ConnectionTimeout, ConnectTimeoutError):
            logger.error(
                "connect to elasticsearch timeout. timeout=%s, index=%s, body=%s",
                self._get_es_search_timeout(),
                self._get_es_index(),
                json.dumps(s.to_dict()),
            )
            raise error_codes.ES_CONNECTION_TIMEOUT.format(
                es_hosts_display=self._get_es_hosts_display(), timeout=self._get_es_search_timeout()
            )
        except NotFoundError:
            logger.error("elasticsearch index not found. index=%s", self._get_es_index())
            raise error_codes.ES_INDEX_NOT_FOUND.format(
                es_hosts_display=self._get_es_hosts_display(), index=self._get_es_index()
            )
        except AuthenticationException:
            raise error_codes.ES_AUTHENTICATION_ERROR.format(es_hosts_display=self._get_es_hosts_display())
        except Exception as err:
            logger.exception(
                "request elasticsearch error. index=%s, body=%s",
                self._get_es_index(),
                json.dumps(s.to_dict()),
            )
            raise error_codes.ES_SEARCH_ERROR.format(es_hosts_display=self._get_es_hosts_display(), err=err)

        if not response.success():
            logger.error("request elasticsearch fail. body=%s, response=%s", json.dumps(s.to_dict()), response)
            raise error_codes.ES_SEARCH_ERROR.format(
                es_hosts_display=self._get_es_hosts_display(),
                err="response check fail, total and successful are not equal.",
            )

        return response

    def complete_search(self, search: Search) -> Search:
        return (
            search.using(self._get_elasticsearch())
            .index(self._get_es_index())
            .params(request_timeout=self._get_es_search_timeout())
        )


class RawESClient(ElasticsearchGetter, BaseESClient):
    """Use Elasticsearch directly"""

    def execute_search(self, body: Dict[str, Any]) -> Dict[str, Any]:
        try:
            return self._get_elasticsearch().search(index=self._get_es_index(), body=body)
        except ConnectionError as err:
            logger.exception("failed to connect elasticsearch.")
            raise error_codes.ES_CONNECTION_ERROR.format(es_hosts_display=self._get_es_hosts_display(), err=err)
        except (ConnectionTimeout, ConnectTimeoutError):
            logger.error(
                "connect to elasticsearch timeout. timeout=%s, index=%s, body=%s",
                self._get_es_search_timeout(),
                self._get_es_index(),
                json.dumps(body),
            )
            raise error_codes.ES_CONNECTION_TIMEOUT.format(
                es_hosts_display=self._get_es_hosts_display(), timeout=self._get_es_search_timeout()
            )
        except NotFoundError:
            logger.error("elasticsearch index not found. index=%s", self._get_es_index())
            raise error_codes.ES_INDEX_NOT_FOUND.format(
                es_hosts_display=self._get_es_hosts_display(), index=self._get_es_index()
            )
        except AuthenticationException:
            raise error_codes.ES_AUTHENTICATION_ERROR.format(es_hosts_display=self._get_es_hosts_display())
        except Exception as err:
            logger.exception("request elasticsearch error. index=%s, body=%s", self._get_es_index(), json.dumps(body))
            raise error_codes.ES_SEARCH_ERROR.format(es_hosts_display=self._get_es_hosts_display(), err=err)


class BKLogESClient(BaseESClient):
    def execute_search(self, body: Dict[str, Any]) -> Dict[str, Any]:
        try:
            return bk_log_component.esquery_dsl(
                index=self._get_es_index(),
                body=body,
            )
        except (RemoteRequestError, RemoteAPIResultError) as err:
            raise error_codes.REMOTE_REQUEST_ERROR.format(message=str(err))


class ESClientFactory:
    @classmethod
    def get_es_client(cls, es_index: str) -> BaseESClient:
        es_client_type = settings.ACCESS_LOG_CONFIG["es_client_type"]
        if es_client_type == ESClientTypeEnum.BK_LOG.value:
            return BKLogESClient(es_index)

        elif es_client_type == ESClientTypeEnum.ELASTICSEARCH.value:
            return RawESClient(es_index)

        raise ValueError(f"unsupported es_client_type: {es_client_type}")
