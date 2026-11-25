# -*- coding: utf-8 -*-
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
"""
诊断 bkrepo 认证/上传问题

复现 blue_krill BKGenericRepo 的请求构造方式，打印出每一步请求的完整 URL、请求头、
状态码与响应体，用于定位 SDK 上传失败（如 "Failed to authenticate: Authorization
value check failed"）的原因。

用法示例：

    # 只做只读检查（项目/仓库信息 + 已存在文件的读取）
    python manage.py check_bkrepo

    # 带上传检查（上传一个几十字节的临时文件到 _healthz 目录）
    python manage.py check_bkrepo --upload

    # 复现具体失败的 key
    python manage.py check_bkrepo --upload --key sdks/golang/powerapp/bkapi-powerapp-0.0.1.tar.gz

    # 打印完整的 Authorization 头 / curl 命令（含明文凭证，谨慎使用）
    python manage.py check_bkrepo --upload --show-secret
"""

import base64
import json
import tempfile
import time
from urllib.parse import urljoin, urlparse

import requests
from django.conf import settings
from django.core.management.base import BaseCommand
from requests.auth import HTTPBasicAuth

MAX_BODY_CHARS = 2000


class Command(BaseCommand):
    help = "诊断 bkrepo 认证与上传（打印请求 URL、请求头、响应体）"

    def add_arguments(self, parser):
        parser.add_argument("--endpoint-url", default=None, help="覆盖 settings.BKREPO_ENDPOINT_URL")
        parser.add_argument("--username", default=None, help="覆盖 settings.BKREPO_USERNAME")
        parser.add_argument("--password", default=None, help="覆盖 settings.BKREPO_PASSWORD")
        parser.add_argument("--project", default=None, help="覆盖 settings.BKREPO_PROJECT")
        parser.add_argument("--bucket", default=None, help="覆盖 settings.BKREPO_GENERIC_BUCKET")
        parser.add_argument(
            "--key",
            default=None,
            help="要读/写的 generic 文件 key，默认 sdks/_healthz/check-<ts>.txt；只读检查时若指定，则尝试 GET 该 key",
        )
        parser.add_argument("--upload", action="store_true", help="执行 PUT 上传检查（会真实写入仓库）")
        parser.add_argument("--no-overwrite", action="store_true", help="上传时 X-BKREPO-OVERWRITE 置为 False")
        parser.add_argument("--timeout", type=float, default=30.0, help="请求超时，默认 30s")
        parser.add_argument("--show-secret", action="store_true", help="打印明文凭证与 Authorization 头")

    def handle(self, *args, **options):
        self.show_secret = options["show_secret"]
        self.timeout = options["timeout"]

        endpoint_url = (options["endpoint_url"] or settings.BKREPO_ENDPOINT_URL or "").rstrip("/")
        username = options["username"] or settings.BKREPO_USERNAME
        password = options["password"] or settings.BKREPO_PASSWORD
        project = options["project"] or settings.BKREPO_PROJECT
        bucket = options["bucket"] or settings.BKREPO_GENERIC_BUCKET

        if not endpoint_url:
            self.stderr.write("BKREPO_ENDPOINT_URL 为空，SDK 不会走 bkrepo 分发，无需检查")
            return

        self._print_config(endpoint_url, username, password, project, bucket)

        self.session = requests.session()
        self.session.auth = HTTPBasicAuth(username=username, password=password)

        # 1. 认证本身：查当前用户所属项目列表（只需认证，不需要仓库权限）
        self._request("GET", urljoin(endpoint_url, "/repository/api/project/list"), title="1) 认证检查 / 项目列表")

        # 2. 仓库信息：验证 project + bucket 是否存在、当前账号是否有权限
        self._request(
            "GET",
            urljoin(endpoint_url, f"/repository/api/repo/info/{project}/{bucket}"),
            title=f"2) 仓库信息 {project}/{bucket}",
        )

        key = options["key"] or f"sdks/_healthz/check-{int(time.time())}.txt"
        generic_url = urljoin(endpoint_url, f"/generic/{project}/{bucket}/{key}")
        self._warn_if_urljoin_drops_prefix(endpoint_url, generic_url)

        # 3. 读检查：GET generic 文件（文件不存在时返回 404/业务错误码，也能证明路由与认证通路）
        self._request("GET", generic_url, title=f"3) 读取 generic 文件 {key}", stream=True)

        # 4. 写检查
        if not options["upload"]:
            self.stdout.write("\n未指定 --upload，跳过上传检查（加 --upload 可复现 SDK 上传失败）")
            return

        allow_overwrite = not options["no_overwrite"]
        with tempfile.NamedTemporaryFile(mode="w+b", suffix=".txt") as fh:
            fh.write(f"bkrepo check at {time.time()}\n".encode())
            fh.flush()
            fh.seek(0)
            self._request(
                "PUT",
                generic_url,
                title=f"4) 上传 generic 文件 {key} (overwrite={allow_overwrite})",
                headers={"X-BKREPO-OVERWRITE": str(allow_overwrite)},
                data=fh,
            )

    # ------------------------------------------------------------------ helpers

    def _print_config(self, endpoint_url: str, username: str, password: str, project: str, bucket: str):
        self.stdout.write("=" * 78)
        self.stdout.write("bkrepo 配置")
        self.stdout.write("=" * 78)
        self.stdout.write(f"endpoint_url : {endpoint_url}")
        self.stdout.write(f"project      : {project!r}")
        self.stdout.write(f"bucket       : {bucket!r}")
        self.stdout.write(f"username     : {username!r} (len={len(username or '')})")
        if self.show_secret:
            self.stdout.write(f"password     : {password!r} (len={len(password or '')})")
        else:
            self.stdout.write(f"password     : {self._mask(password)} (len={len(password or '')})")

        # 凭证里的空白字符是 "Authorization value check failed" 的常见原因
        for name, value in (("username", username), ("password", password)):
            if value is None or value == "":
                self.stdout.write(self.style.ERROR(f"!! {name} 为空"))
            elif value != value.strip():
                self.stdout.write(self.style.ERROR(f"!! {name} 首尾含空白字符: {value!r}"))
            elif any(c in value for c in "\r\n"):
                self.stdout.write(self.style.ERROR(f"!! {name} 含换行符: {value!r}"))

        token = base64.b64encode(f"{username}:{password}".encode()).decode()
        if self.show_secret:
            self.stdout.write(f"Authorization: Basic {token}")
        else:
            self.stdout.write(f"Authorization: Basic {self._mask(token)}")

    def _warn_if_urljoin_drops_prefix(self, endpoint_url: str, generic_url: str):
        """blue_krill 用 urljoin(endpoint, '/generic/...')，会丢掉 endpoint 上的路径前缀"""
        prefix = urlparse(endpoint_url).path.strip("/")
        if not prefix:
            return
        self.stdout.write(
            self.style.WARNING(
                f"\n!! endpoint_url 带路径前缀 /{prefix}，而 blue_krill 用 urljoin(endpoint, '/generic/...') "
                f"构造地址，前缀会被丢弃：\n   实际请求 {generic_url}\n"
                f"   若网关要求前缀，应把 BKREPO_ENDPOINT_URL 配成不带前缀的直连地址，或由网关做路径重写"
            )
        )

    def _request(self, method: str, url: str, title: str, **kwargs):
        self.stdout.write("\n" + "=" * 78)
        self.stdout.write(title)
        self.stdout.write("=" * 78)
        self.stdout.write(f"{method} {url}")

        kwargs.setdefault("timeout", self.timeout)
        try:
            resp = self.session.request(method, url, **kwargs)
        except Exception as e:  # noqa: BLE001 — 诊断命令，需要打印任何异常
            self.stdout.write(self.style.ERROR(f"请求异常: {type(e).__name__}: {e}"))
            return None

        self.stdout.write(f"-> 最终 URL   : {resp.url}")
        if resp.history:
            self.stdout.write(f"-> 重定向链   : {[(r.status_code, r.url) for r in resp.history]}")
        self.stdout.write("-> 请求头     :")
        for k, v in resp.request.headers.items():
            shown = self._mask(v) if (k.lower() == "authorization" and not self.show_secret) else v
            self.stdout.write(f"     {k}: {shown}")

        self.stdout.write(f"-> 状态码     : {resp.status_code} {resp.reason}")
        self.stdout.write(f"-> 响应头     : {dict(resp.headers)}")
        self.stdout.write(f"-> 响应体     : {self._body(resp)}")

        code = None
        try:
            code = resp.json().get("code")
        except Exception:  # noqa: BLE001 — 非 JSON 响应
            self.stdout.write(
                self.style.ERROR("!! 响应不是 JSON，blue_krill 的 _validate_resp 会抛 RequestError(code=Unknown)")
            )

        if code is not None and code != 0:
            self.stdout.write(self.style.ERROR(f"!! 业务错误码 code={code}，blue_krill 会抛 RequestError"))
        elif resp.ok and code == 0:
            self.stdout.write(self.style.SUCCESS("OK"))

        return resp

    def _body(self, resp: requests.Response) -> str:
        try:
            text = resp.text
        except Exception as e:  # noqa: BLE001
            return f"<读取响应体失败: {e}>"
        if len(text) > MAX_BODY_CHARS:
            return text[:MAX_BODY_CHARS] + f"... <truncated, total {len(text)} chars>"
        try:
            return json.dumps(json.loads(text), ensure_ascii=False, indent=2)
        except Exception:  # noqa: BLE001
            return text

    @staticmethod
    def _mask(value: str) -> str:
        if not value:
            return "<empty>"
        if len(value) <= 8:
            return value[:2] + "***"
        return f"{value[:4]}***{value[-4:]}"
