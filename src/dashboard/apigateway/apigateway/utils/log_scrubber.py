#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) Tencent. All rights reserved.
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
"""Bounded masking of log representations, independent of business/query modules."""

import json
import re
from typing import Any
from urllib.parse import parse_qsl, urlencode

from django.conf import settings
from django.utils.translation import gettext as _

SENSITIVE_KEYS = frozenset(
    {
        "skey",
        "openkey",
        "auth_token",
        "access_token",
        "bk_token",
        "bk_ticket",
        "oa_ticket",
        "app_secret",
        "signature",
        "bk_nonce",
        "bk_timestamp",
        "bk_app_secret",
        "bk_signature",
        "authorization",
        "proxy-authorization",
        "x-bkapi-authorization",
        "x-bkapi-jwt",
        "cookie",
        "set-cookie",
        "refresh_token",
        "client_secret",
        "inner_jwt",
        "token",
    }
)
SENSITIVE_KEYS_PART_MATCH_PATTERN = re.compile(
    "password|secret|passwd|api_key|apikey|credentials|mysql_pwd|stripetoken", re.IGNORECASE
)
SENSITIVE_KEYS_MATCH_PATTERN = re.compile(r"\b(?:" + "|".join(SENSITIVE_KEYS) + r")\b", re.IGNORECASE)
MASK = "***"
MAX_INPUT_LENGTH = 1024 * 1024
MAX_DEPTH = 32
MAX_STRING_DECODES = 4
MAX_NODES = 10000
# Only these fields carry serialized payloads; HTTP paths and tool names are metadata.
_BODY_FIELDS = {"body", "body_param", "response_body", "request_body", "request", "response", "result"}
_STRUCTURE_FIELDS = {
    "header",
    "headers",
    "header_param",
    "query",
    "query_param",
    "params",
    "arguments",
    "path_params",
    "path_param",
}
_INVALID_PERCENT = re.compile(r"%(?![0-9a-fA-F]{2})")


class UnsafeLogData(ValueError):
    """The value cannot be safely represented within the logging budget."""


class LogDataScrubber:
    """Return sanitized copies without mutating fetched logs or transport payloads."""

    def __init__(self):
        self._sensitive_keys = SENSITIVE_KEYS | {key.lower() for key in getattr(settings, "LOG_SENSITIVE_KEYS", [])}

    @staticmethod
    def hidden_body() -> str:
        return _("正文已屏蔽：截断或格式未知，无法可靠脱敏")

    def sensitive(self, key: str) -> bool:
        return key.lower() in self._sensitive_keys or bool(SENSITIVE_KEYS_PART_MATCH_PATTERN.search(key))

    @staticmethod
    def _empty(value: Any) -> bool:
        # Equality with 0/False must not accidentally preserve a credential.
        return value is None or isinstance(value, (str, list, dict)) and len(value) == 0

    def scrub_log(self, log: dict) -> dict:
        return {key: self._safe_field(key, value) for key, value in log.items()}

    def _safe_field(self, key: str, value: Any) -> Any:
        try:
            return self._field(key, value, 0, 0, [MAX_NODES, MAX_INPUT_LENGTH])
        except UnsafeLogData, ValueError, TypeError, RecursionError:
            return self.hidden_body()

    def _field(self, key: str, value: Any, depth: int, decodes: int, budget: list[int]) -> Any:
        if self.sensitive(key):
            return value if self._empty(value) else MASK
        name = key.lower()
        if name in _BODY_FIELDS:
            return self._payload(
                value,
                depth,
                decodes,
                budget,
                allow_form=name in {"body", "body_param", "request_body", "response_body"},
            )
        if name == "path" and isinstance(value, str) and value.lstrip().startswith(("{", "[")):
            return self._payload(value, depth, decodes, budget, allow_form=False)
        if name in _STRUCTURE_FIELDS and isinstance(value, str):
            return self._payload(value, depth, decodes, budget, allow_form=name in {"params", "query", "query_param"})
        if name == "__ext_json" and isinstance(value, str):
            return self._payload(value, depth, decodes, budget, allow_form=False)
        return self._walk(value, depth, decodes, budget)

    def _walk(self, value: Any, depth: int, decodes: int, budget: list[int]) -> Any:
        self._check(value, depth, budget)
        if isinstance(value, dict):
            result = {}
            for key, item in value.items():
                saved_budget = budget.copy()
                try:
                    self._check(key, depth, budget)
                    if key.lower() == "text" and value.get("type") == "text":
                        result[key] = self._payload(item, depth + 1, decodes, budget, allow_form=False)
                    else:
                        result[key] = self._field(key, item, depth + 1, decodes, budget)
                except UnsafeLogData, ValueError, TypeError, RecursionError:
                    if key.lower() not in _BODY_FIELDS | _STRUCTURE_FIELDS | {"text", "__ext_json"}:
                        raise
                    budget[:] = saved_budget
                    self._check(self.hidden_body(), min(depth + 1, MAX_DEPTH), budget)
                    result[key] = self.hidden_body()
            return result
        if isinstance(value, list):
            return [self._walk(item, depth + 1, decodes, budget) for item in value]
        return value

    @staticmethod
    def _check(value: Any, depth: int, budget: list[int]) -> None:
        budget[0] -= 1
        if depth > MAX_DEPTH or budget[0] < 0:
            raise UnsafeLogData()
        if isinstance(value, (list, dict)) and len(value) > MAX_NODES:
            raise UnsafeLogData()
        if isinstance(value, str) and len(value) > MAX_INPUT_LENGTH:
            raise UnsafeLogData()
        # Bound total string processing for object values as well as serialized bodies.
        if isinstance(value, str):
            budget[1] -= len(value.encode("utf-8"))
            if budget[1] < 0:
                raise UnsafeLogData()

    def _payload(self, value: Any, depth: int, decodes: int, budget: list[int], *, allow_form: bool) -> Any:
        self._check(value, depth, budget)
        if self._empty(value) or value == MASK or value == self.hidden_body():
            return value
        if isinstance(value, (dict, list)):
            return self._walk(value, depth, decodes, budget)
        if not isinstance(value, str) or decodes >= MAX_STRING_DECODES:
            raise UnsafeLogData()
        text = value.strip()
        try:
            parsed = json.loads(text)
        except ValueError, RecursionError:
            if allow_form and "=" in text and len(text.splitlines()) == 1 and not text.startswith(("{", "[", '"')):
                return self.scrub_form(text, depth, decodes, budget)
            raise UnsafeLogData() from None
        if isinstance(parsed, str):
            return json.dumps(
                self._payload(parsed, depth + 1, decodes + 1, budget, allow_form=allow_form), ensure_ascii=False
            )
        if parsed is None:
            return "null"
        if not isinstance(parsed, (dict, list)):
            raise UnsafeLogData()
        return json.dumps(self._walk(parsed, depth + 1, decodes + 1, budget), ensure_ascii=False)

    def scrub_form(self, value: str, depth: int = 0, decodes: int = 0, budget: list[int] | None = None) -> str:
        budget = budget if budget is not None else [MAX_NODES, MAX_INPUT_LENGTH]
        self._check(value, depth, budget)
        if _INVALID_PERCENT.search(value):
            raise UnsafeLogData()
        pairs = parse_qsl(
            value, keep_blank_values=True, strict_parsing=True, errors="strict", max_num_fields=MAX_NODES
        )
        return urlencode([(key, self._field(key, item, depth + 1, decodes, budget)) for key, item in pairs])

    def scrub_body(self, value: Any) -> Any:
        return self._payload(value, 0, 0, [MAX_NODES, MAX_INPUT_LENGTH], allow_form=True)

    def scrub_structure(self, value: Any) -> Any:
        return self._walk(value, 0, 0, [MAX_NODES, MAX_INPUT_LENGTH])
