#  -*- coding: utf-8 -*-
#  #
#  TencentBlueKing is pleased to support the open source community by making
#  蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
#  Copyright (C) 2017 THL A29 Limited, a Tencent company. All rights reserved.
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
import logging
from urllib.parse import urlparse

import requests

logger = logging.getLogger(__name__)


def check_git_credentials(repo_url: str, username: str, token: str) -> bool:
    """
    通过 HTTP Basic Auth 验证 Git 仓库权限
    :param repo_url: 仓库地址（必须为 HTTPS，如 https://github.com/user/repo.git）
    :param username: 用户名（GitHub 等平台传空字符串，使用 token 即可）
    :param token: 密码/访问令牌（推荐使用 OAuth2 token 或 PAT）
    :return: 是否验证成功
    """
    # 标准化 URL（处理 .git 结尾和路径分隔符）
    parsed = urlparse(repo_url)
    original_path = parsed.path

    # 精确删除末尾的 .git（若存在）
    modified_path = original_path[:-4] if original_path.endswith(".git") else original_path

    # 构造新路径
    service_path = f"{modified_path}/info/refs?service=git-upload-pack"
    target_url = parsed._replace(path=service_path).geturl()

    try:
        # 添加 Basic Auth 并禁止重定向（精准捕获认证失败）
        response = requests.get(target_url, auth=(username, token), allow_redirects=False, timeout=10)

        # 认证成功特征：200 或 401 转为 200 的探测（不同平台差异处理）
        if response.status_code == 200:
            return True
        if 300 <= response.status_code < 400:
            # 某些平台重定向后会带认证（如 GitLab）
            redirected = requests.get(response.headers["Location"], auth=(username, token), timeout=10)
            return redirected.ok
        return False

    except requests.RequestException:
        logger.exception("Failed to check credentials for %s", repo_url)
        return False
