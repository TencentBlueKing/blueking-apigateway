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
import copy
import json
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from django.utils.translation import gettext as _
from requests.structures import CaseInsensitiveDict

from apigateway.biz.resource_url import ResourceURLHandler
from apigateway.common.constants import HEADER_BKAPI_AUTHORIZATION
from apigateway.core.utils import get_resource_url
from apigateway.utils.sensitive_cleaner import SensitiveCleaner


def render_path(path, path_params):
    for key, value in path_params.items():
        tpl_key = "{%s}" % key
        if path.find(tpl_key) >= 0:
            path = path.replace(tpl_key, value)
    return path


class PreparedRequestHeaders:
    def __init__(self, headers=None):
        self._headers = CaseInsensitiveDict(headers or {})
        self._sensitive_cleaner = SensitiveCleaner(
            ["bk_app_secret", "app_secret", "bk_token", "bk_ticket", "skey", "access_token"]
        )

    def prepare_headers(
        self,
        headers: Optional[Dict[str, str]] = None,
        authorization: Optional[Dict[str, Any]] = None,
        authorization_from_cookies: Optional[Dict[str, Any]] = None,
    ):
        self._headers = CaseInsensitiveDict(headers or {})

        authorization = self._prepare_bkapi_authorization(authorization or {}, authorization_from_cookies or {})
        if authorization:
            self._headers[HEADER_BKAPI_AUTHORIZATION] = json.dumps(authorization)

    def _prepare_bkapi_authorization(self, authorization, authorization_from_cookies) -> Dict[str, Any]:
        authorization = copy.deepcopy(authorization)
        authorization.update(authorization_from_cookies)
        authorization.update(self._get_bkapi_authorization_from_headers())

        return authorization

    def _get_bkapi_authorization_from_headers(self) -> Dict[str, Any]:
        authorization = self._headers.get(HEADER_BKAPI_AUTHORIZATION)
        if not authorization:
            return {}

        try:
            return json.loads(authorization)
        except Exception:
            raise ValueError(_("Header X-Bkapi-Authorization 不是一个有效的 Json 格式字符串。"))

    @property
    def headers(self):
        return copy.deepcopy(self._headers)

    @property
    def headers_without_sensitive(self) -> CaseInsensitiveDict:
        headers = copy.deepcopy(self._headers)

        authorization = self._get_bkapi_authorization_from_headers()
        if authorization:
            headers[HEADER_BKAPI_AUTHORIZATION] = json.dumps(self._sensitive_cleaner.clean(authorization))

        return headers


@dataclass
class PreparedRequestURL:
    resource_path: str = ""
    subpath: str = ""
    match_subpath: bool = False
    path_params: Dict[str, Any] = field(default_factory=dict)
    gateway_name: str = ""
    stage_name: str = ""
    request_url: str = field(init=False)

    def __post_init__(self):
        self.request_url = self._prepare_request_url()

    def _prepare_request_url(self) -> str:
        resource_path = self._merge_subpath()

        if self.path_params:
            resource_path = render_path(resource_path, self.path_params)

        return get_resource_url(
            resource_url_tmpl=ResourceURLHandler.get_resource_url_tmpl(self.gateway_name, self.stage_name),
            gateway_name=self.gateway_name,
            stage_name=self.stage_name,
            resource_path=resource_path,
        )

    def _merge_subpath(self):
        """
        将请求路径与子路径合并，获取完整的请求路径
        """
        if self.match_subpath:
            return f"{self.resource_path.rstrip('/')}/{self.subpath.lstrip('/')}"

        return self.resource_path
