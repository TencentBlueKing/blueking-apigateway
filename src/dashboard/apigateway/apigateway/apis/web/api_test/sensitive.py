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
import json
import re
import shlex
from http.cookies import CookieError, SimpleCookie
from urllib.parse import quote, quote_plus, urlsplit, urlunsplit

from django.conf import settings

from apigateway.common.constants import HEADER_BKAPI_AUTHORIZATION

SENSITIVE_KEYS = {
    "bk_app_secret",
    "app_secret",
    "bk_token",
    "bk_ticket",
    "skey",
    "access_token",
    "token",
    "refresh_token",
    "id_token",
    "password",
    "client_secret",
    "api_key",
}
SENSITIVE_HEADER_NAMES = {
    HEADER_BKAPI_AUTHORIZATION.lower(),
    "authorization",
    "proxy-authorization",
    "cookie",
    "set-cookie",
    "x-api-key",
    "x-auth-token",
    "x-token",
    "x-access-token",
}


def remove_sensitive_headers(headers):
    return {key: value for key, value in headers.items() if key.lower() not in SENSITIVE_HEADER_NAMES | SENSITIVE_KEYS}


class DebugDataSanitizer:
    """Keep credentials used for sending out of debug output and persistence."""

    def __init__(self):
        self._secrets: set[str] = set()

    def add_authorization(self, authorization):
        if isinstance(authorization, dict):
            for key, value in authorization.items():
                if key.lower() in SENSITIVE_KEYS:
                    self._add_secret(value)
                else:
                    self.add_authorization(value)
        elif isinstance(authorization, list):
            for value in authorization:
                self.add_authorization(value)
        elif isinstance(authorization, str):
            try:
                decoded = json.loads(authorization)
            except ValueError:
                return
            if isinstance(decoded, (dict, list)):
                self.add_authorization(decoded)

    def add_headers(self, headers):
        login_cookie_names = SENSITIVE_KEYS | {
            name.lower() for name in settings.BK_LOGIN_TICKET_KEY_TO_COOKIE_NAME.values()
        }
        for key, value in headers.items():
            name = key.lower()
            if name not in SENSITIVE_HEADER_NAMES | SENSITIVE_KEYS or not isinstance(value, str):
                continue
            if name == "cookie":
                for cookie in value.split(";"):
                    cookie_name, _, cookie_value = cookie.partition("=")
                    if cookie_name.strip().lower() in login_cookie_names:
                        self._add_secret(cookie_value.strip())
                continue
            if name == "set-cookie":
                self._add_set_cookie(value, login_cookie_names)
                continue
            if name == HEADER_BKAPI_AUTHORIZATION.lower():
                self._add_bkapi_authorization(value)
                continue
            self._add_secret(value)
            if name in {"authorization", "proxy-authorization"}:
                self._add_secret(value.partition(" ")[2])

    def _add_set_cookie(self, value, login_cookie_names):
        # Requests can join several Set-Cookie fields. Split at the next cookie
        # assignment, preserving the comma inside an Expires date.
        for header in re.split(r",\s*(?=[^\s;,=]+=)", value):
            cookies = SimpleCookie()
            try:
                cookies.load(header)
            except CookieError:
                continue
            for name, cookie in cookies.items():
                if name.lower() in login_cookie_names:
                    self._add_secret(cookie.value)

    def _add_bkapi_authorization(self, value):
        try:
            authorization = json.loads(value)
        except ValueError, TypeError:
            self._add_secret(value)
            return
        if isinstance(authorization, dict):
            self.add_authorization(authorization)
            # Do not register already-masked headers or application metadata as
            # secrets: later output/history cleanup must keep those fields visible.
            if self.clean(authorization) != authorization:
                self._add_secret(value)

    def _add_secret(self, value):
        if isinstance(value, dict):
            for item in value.values():
                self._add_secret(item)
        elif isinstance(value, list):
            for item in value:
                self._add_secret(item)
        elif isinstance(value, str) and value and value != "***":
            self._secrets.update({value, json.dumps(value)[1:-1], quote(value, safe=""), quote_plus(value)})

    def clean(self, data):
        if isinstance(data, dict):
            return {
                key: "***" if key.lower() in SENSITIVE_HEADER_NAMES | SENSITIVE_KEYS and value else self.clean(value)
                for key, value in data.items()
            }
        if isinstance(data, list):
            return [self.clean(value) for value in data]
        if isinstance(data, str):
            # Header JSON embedded in an echoed JSON body has another escaping layer.
            # Clean the decoded output copy by field meaning, preserving valid JSON.
            try:
                decoded = json.loads(data)
            except ValueError:
                pass
            else:
                if isinstance(decoded, (dict, list)):
                    cleaned = self.clean(decoded)
                    return json.dumps(cleaned, ensure_ascii=False) if cleaned != decoded else data
            if self._secrets:
                # Match complete values or delimited echoes, even for a one-character
                # credential. A substring inside an ordinary word is not an echo.
                values = "|".join(re.escape(secret) for secret in sorted(self._secrets, key=len, reverse=True))
                data = re.sub(r"(?<!\w)(?:" + values + r")(?!\w)", "***", data)
        return data

    def clean_url(self, url):
        if url is None:
            return None
        try:
            parsed = urlsplit(url)
        except ValueError:
            return ""
        path = "/".join(self.clean(segment) for segment in parsed.path.split("/"))
        query = []
        for item in parsed.query.split("&"):
            key, separator, value = item.partition("=")
            query.append(key + separator + self.clean(value))
        return urlunsplit(parsed._replace(path=path, query="&".join(query), fragment=self.clean(parsed.fragment)))

    def clean_request(self, request):
        request = dict(request, headers=self.clean(remove_sensitive_headers(request.get("headers", {}))))
        # Only user-provided payload fields may contain echoed credentials. Fixed
        # metadata (method/type/version/flags) must keep its schema-defined values.
        if "request_url" in request:
            request["request_url"] = self.clean_url(request["request_url"])
        for key in ("path_params", "query_params", "body", "subpath"):
            if key in request:
                request[key] = self.clean(request[key])
        return request

    def _clean_curl_header(self, header):
        name, _, value = header.partition(":")
        cleaned_value = self.clean(value.strip())
        if name.lower() in SENSITIVE_HEADER_NAMES | SENSITIVE_KEYS:
            cleaned_value = "***"
            if name.lower() == HEADER_BKAPI_AUTHORIZATION.lower():
                try:
                    authorization = json.loads(value)
                except ValueError:
                    pass
                else:
                    if isinstance(authorization, dict):
                        cleaned_value = json.dumps(self.clean(authorization), ensure_ascii=False)
        return f"{name}: {cleaned_value}"

    def clean_curl(self, curl):
        # Historical curls were generated by curlify with separate '-H' arguments.
        try:
            args = shlex.split(curl)
        except ValueError:
            return ""
        for index, arg in enumerate(args[:-1]):
            if arg in {"-H", "--header"}:
                name, _, value = args[index + 1].partition(":")
                self.add_headers({name: value.strip()})
        index = 1  # Preserve the executable and option names as curl syntax.
        while index < len(args):
            arg = args[index]
            if arg in {"-H", "--header"}:
                if index + 1 >= len(args):
                    return ""
                args[index + 1] = self._clean_curl_header(args[index + 1])
                index += 2
            elif arg in {"-d", "--data", "--data-raw", "--data-binary", "--data-ascii", "--data-urlencode"}:
                if index + 1 >= len(args):
                    return ""
                args[index + 1] = self.clean(args[index + 1])
                index += 2
            elif arg in {"-X", "--request"}:
                index += 2
            else:
                if not arg.startswith("-"):
                    args[index] = self.clean_url(arg)
                index += 1
        return shlex.join(args)

    def clean_response_data(self, data):
        data = dict(data)
        # Size/status/timing describe the transport, not user-provided values.
        for key in ("body", "headers"):
            if key in data:
                data[key] = self.clean(data[key])
        if data.get("curl"):
            data["curl"] = self.clean_curl(data["curl"])
        return data

    def clean_response(self, response):
        response = dict(response)
        if isinstance(response.get("data"), dict):
            response["data"] = self.clean_response_data(response["data"])
        if "error" in response:
            response["error"] = self.clean(response["error"])
        return response


def sanitize_history(request, response):
    sanitizer = DebugDataSanitizer()
    sanitizer.add_headers(request.get("headers", {}))
    sanitizer.add_authorization(request.get("query_params", {}))
    sanitizer.add_authorization(request.get("body", ""))
    response = dict(response)
    if isinstance(response.get("data"), dict):
        response["data"] = dict(response["data"])
        sanitizer.add_headers(response["data"].get("headers", {}))
        sanitizer.add_authorization(response["data"].get("body", ""))
        if response["data"].get("curl"):
            response["data"]["curl"] = sanitizer.clean_curl(response["data"]["curl"])
    return sanitizer.clean_request(request), sanitizer.clean_response(response)
