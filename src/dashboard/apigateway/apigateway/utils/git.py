#  -*- coding: utf-8 -*-
#  #
#  TencentBlueKing is pleased to support the open source community by making
#  蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
#  Copyright (C) Tencent. All rights reserved.
#  Licensed under the MIT License (the "License"); you may not use this file except
#  in compliance with the License. You may obtain a copy of the License at
#  #
#      http://opensource.org/licenses/MIT
#  #
#  Unless required by applicable law or agreed to in writing, software distributed under
#  the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
#  either express or implied. See the License for the specific language governing permissions and
#  limitations under the License.
#  #
#  We undertake not to change the open source license (MIT license) applicable
#  to the current version of the project delivered to anyone in the future.
#  #
from typing import Tuple
from urllib.parse import urlsplit

import requests
from django.utils.translation import gettext_lazy as _

HTTP_ERROR_MESSAGES = {
    401: _("认证未通过，请检查所填账号、密码或访问令牌是否正确、有效。"),
    403: _("访问被拒绝，请检查仓库权限及 Git 服务访问限制。"),
    404: _("仓库不存在或当前账号无权访问，请检查仓库地址和权限。"),
    429: _("Git 服务请求受限，请稍后重试。"),
}


def check_git_credentials(repo_url: str, username: str, token: str) -> Tuple[bool, str]:
    """
    通过 HTTP Basic Auth 验证 Git 仓库权限
    :param repo_url: 仓库地址（必须为 HTTPS，如 https://github.com/user/repo.git）
    :param username: 用户名（GitHub 等平台传空字符串，使用 token 即可）
    :param token: 密码/访问令牌（推荐使用 OAuth2 token 或 PAT）
    :return: (是否成功, 失败时的错误信息)
    """
    try:
        parsed = urlsplit(repo_url)
        # 精确删除末尾的 .git（若存在）
        modified_path = parsed.path.removesuffix(".git")
        target_url = parsed._replace(
            path=f"{modified_path}/info/refs", query="service=git-upload-pack", fragment=""
        ).geturl()

        # 最多跟随一次重定向；Requests 准备下一跳请求时会处理认证头。
        with requests.Session() as session:
            response = session.get(target_url, auth=(username, token), allow_redirects=False, timeout=10)
            if response.next is not None:
                response = session.send(response.next, allow_redirects=False, timeout=10)
        host = urlsplit(response.url).hostname
    except requests.exceptions.RequestException, ValueError:
        # 原始异常可能包含凭据或完整 URL，不直接返回，也不记录其堆栈。
        return False, str(_("无法连接 Git 服务，请检查仓库地址和网络连接，或稍后重试。"))

    reason = HTTP_ERROR_MESSAGES.get(response.status_code, _("请求 Git 服务失败，请检查仓库地址和服务状态。"))
    if response.status_code == 200:
        content_type = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
        # 服务声明的换行符可省略；仅有 HTTP 200 可能是登录页。
        if content_type == "application/x-git-upload-pack-advertisement" and response.content.startswith(
            (b"001e# service=git-upload-pack\n0000", b"001d# service=git-upload-pack0000")
        ):
            return True, ""
        reason = _("响应不是 Git Smart HTTP 格式，请检查仓库地址。")
    elif 500 <= response.status_code < 600:
        reason = _("Git 服务返回异常，请稍后重试或联系 Git 服务管理员。")
    elif 300 <= response.status_code < 400:
        reason = _("Git 服务重定向异常，请检查仓库地址或联系 Git 服务管理员。")
    return False, _("%(host)s 返回 HTTP %(status_code)s，%(reason)s") % {
        "host": host,
        "status_code": response.status_code,
        "reason": reason,
    }
