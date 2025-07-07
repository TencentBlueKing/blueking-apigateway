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
import os
from functools import lru_cache
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import urlparse

from cachetools import TTLCache, cached
from django.conf import settings

from apigateway.common.error_codes import error_codes
from apigateway.common.tenant.constants import (
    TENANT_ID_OPERATION,
)
from apigateway.common.tenant.request import gen_tenant_header, get_tenant_id_for_gateway_maintainers
from apigateway.common.tenant.user_credentials import UserCredentials
from apigateway.utils.local import local
from apigateway.utils.url import url_join

from .bkauth import get_app_tenant_info as bkauth_get_app_tenant_info
from .http import http_get, http_post
from .utils import gen_gateway_headers

logger = logging.getLogger(__name__)

REQ_PAAS_API_TIMEOUT = 10


@lru_cache(maxsize=1)
def get_paas3_url_prefix() -> str:
    """
    获取 paas url
    """
    gateway_name = "bkpaas3"
    if settings.EDITION == "te":
        gateway_name = "paasv3"

    custom_paas3_url_prefix = os.environ.get("BK_PAASV3_URL_PREFIX", "")
    if custom_paas3_url_prefix:
        return custom_paas3_url_prefix

    return settings.BK_API_URL_TMPL.format(api_name=gateway_name) + "/prod"


def _call_paasv3_uni_apps_query_by_id(
    tenant_id: str,
    app_codes: List[str],
) -> List[Dict[str, Any]]:
    data = {
        "id": ",".join(app_codes),
    }

    headers = gen_gateway_headers()
    headers.update(gen_tenant_header(tenant_id))

    url = url_join(get_paas3_url_prefix(), "/system/uni_applications/query/by_id/")

    ok, resp_data = http_get(url, data, headers=headers, timeout=REQ_PAAS_API_TIMEOUT)
    if not ok:
        logger.error(
            "%s api failed! %s %s, data: %s, request_id: %s, error: %s",
            "paasv3",
            "http_get",
            url,
            data,
            local.request_id,
            resp_data["error"],
        )
        raise error_codes.REMOTE_REQUEST_ERROR.format(
            f"request paasv3 fail! "
            f"Request=[http_get {urlparse(url).path} request_id={local.request_id}]"
            f"error={resp_data['error']}"
        )
    # response:
    # - tenant_id is the owner(user tenant_id) of the app, global app is owned by system
    # - app_tenant_id is the tenant_id of the app, global app is empty
    # DONT USE tenant_id, app_tenant_id of paas, use the bkauth app_tenant_info instead !!!!!!

    return resp_data


def _get_app_no_cache(tenant_id: str, app_code: str) -> Optional[Dict[str, Any]]:
    result_data = _call_paasv3_uni_apps_query_by_id(tenant_id, [app_code])
    apps: Iterable[Dict] = filter(None, result_data)

    result = {app["code"]: app for app in apps} or {}

    return result.get(app_code)


@cached(cache=TTLCache(maxsize=2000, ttl=300))
def _get_app_with_cache(tenant_id: str, app_code: str) -> Optional[Dict[str, Any]]:
    """get app info from paasv3

    Args:
        tenant_id (str): the tenant id
        app_code (str): the app code

    Returns:
        Optional[Dict[str, Any]]: the app info

    only called when ENABLE_MULTI_TENANT_MODE is True
    """
    return _get_app_no_cache(tenant_id, app_code)


def is_app_code_occupied(gateway_tenant_mode: str, gateway_tenant_id: str, app_code: str) -> bool:
    owner_tenant_id = get_tenant_id_for_gateway_maintainers(gateway_tenant_mode, gateway_tenant_id)
    app = _get_app_no_cache(owner_tenant_id, app_code)
    return app is not None


def get_tenant_id_for_app_developers(bk_app_code: str) -> str:
    _, tenant_id = bkauth_get_app_tenant_info(bk_app_code)

    # if the tenant_id is empty, it means the app is a global app
    # so the cmsi use could only be the `system`
    # equals to, while the tenant_id is empty if the app is a global app
    # if tenant_mode == TenantModeEnum.GLOBAL.value:
    #     tenant_id = TENANT_ID_OPERATION
    return tenant_id or TENANT_ID_OPERATION


def get_app_maintainers(bk_app_code: str) -> List[str]:
    """获取应用负责人"""
    # NOTE: here we need to get maintainers from paasv3
    #       but the X-Bk-Tenant-Id required
    #       so, we query it from bkauth first
    tenant_id = get_tenant_id_for_app_developers(bk_app_code)

    app = _get_app_with_cache(tenant_id, bk_app_code)
    if not app:
        return []

    if app.get("developers"):
        return app["developers"]

    if app.get("creator"):
        return [app["creator"]]

    return []


def create_paas_app(
    app_code: str,
    language: str,
    git_info: Optional[Dict[str, Any]] = None,
    user_credentials: Optional[UserCredentials] = None,
) -> bool:
    """
    创建应用
    """
    url = url_join(get_paas3_url_prefix(), "/bkapps/cloud-native/")
    headers = gen_gateway_headers(user_credentials)
    source_init_template = "bk-apigw-plugin-python"
    build_method = "buildpack"
    if language == "go":
        source_init_template = "bk-apigw-plugin-go"
        build_method = "dockerfile"
    data = {
        "is_plugin_app": False,
        "region": "default",
        "code": app_code,
        "name": app_code,
        "source_config": {
            "source_init_template": source_init_template,
            "source_control_type": "bare_git",
            "source_repo_url": git_info.get("repository", "") if git_info else "",
            "source_origin": 1,
            "source_dir": "",
            "auto_create_repo": not git_info,
            "write_template_to_repo": not git_info,
            "source_repo_auth_info": {
                "username": git_info.get("account", "") if git_info else "",
                "password": git_info.get("password", "") if git_info else "",
            },
        },
        "bkapp_spec": {"build_config": {"build_method": build_method}},
    }
    ok, resp_data = http_post(url, data, headers=headers, timeout=REQ_PAAS_API_TIMEOUT)
    if not ok:
        logger.error(
            "%s api failed! %s %s, data: %s, request_id: %s, error: %s",
            "paasv3",
            "http_get",
            url,
            data,
            local.request_id,
            resp_data["error"],
        )
        raise error_codes.REMOTE_REQUEST_ERROR.format(
            f"request paasv3 fail! "
            f"Request=[http_get {urlparse(url).path} request_id={local.request_id}]"
            f"error={resp_data['error']}"
        )
    return True


def deploy_paas_app(
    app_code: str,
    module: str,
    env: str,
    revision: str,
    branch: str,
    version_type: str,
    user_credentials: Optional[UserCredentials] = None,
) -> str:
    """
    部署应用：
    params:
        app_code: 应用ID
        module: 模块名
        env: 环境
        branch: 分支
        version_type: 版本类型
    return: deployment id
    """
    url = url_join(get_paas3_url_prefix(), f"/bkapps/applications/{app_code}/modules/{module}/envs/{env}/deployments/")
    headers = gen_gateway_headers(user_credentials)
    data = {
        "revision": revision,
        "version_name": branch,
        "version_type": version_type,
    }
    ok, resp_data = http_post(url, data, headers=headers, timeout=REQ_PAAS_API_TIMEOUT)
    if not ok:
        logger.error(
            "%s api failed! %s %s, data: %s, request_id: %s, error: %s",
            "paasv3",
            "http_get",
            url,
            data,
            local.request_id,
            resp_data["error"],
        )
        raise error_codes.REMOTE_REQUEST_ERROR.format(
            f"request paasv3 fail! "
            f"Request=[http_get {urlparse(url).path} request_id={local.request_id}]"
            f"error={resp_data['error']}"
        )
    return resp_data["deployment_id"]


def paas_app_module_offline(app_code: str, module: str, env: str, user_credentials: Optional[UserCredentials] = None):
    """
    下线应用
    """
    url = url_join(get_paas3_url_prefix(), f"/bkapps/applications/{app_code}/modules/{module}/envs/{env}/offlines/")
    headers = gen_gateway_headers(user_credentials)
    ok, resp_data = http_post(url, None, headers=headers, timeout=REQ_PAAS_API_TIMEOUT)
    if not ok:
        logger.error(
            "%s api failed! %s %s, data: %s, request_id: %s, error: %s",
            "paasv3",
            "http_get",
            url,
            {},
            local.request_id,
            resp_data["error"],
        )
    return resp_data.get("offline_operation_id", "")


def set_paas_stage_env(
    app_code: str, module: str, stage: str, env: Dict[str, Any], user_credentials: Optional[UserCredentials] = None
):
    """
    设置应用环境变量
    """
    url_prefix = get_paas3_url_prefix()
    for config_var_key, config_var_value in env.items():
        url = url_join(url_prefix, f"/bkapps/applications/{app_code}/modules/{module}/config_vars/{config_var_key}/")
        headers = gen_gateway_headers(user_credentials)
        data = {
            "environment_name": stage,  # 环境：stag、prod
            "value": config_var_value,
        }
        ok, resp_data = http_post(url, data=data, headers=headers, timeout=REQ_PAAS_API_TIMEOUT)
        if not ok:
            logger.error(
                "%s api failed! %s %s, data: %s, request_id: %s, error: %s",
                "paasv3",
                "http_get",
                url,
                data,
                local.request_id,
                resp_data["error"],
            )

    return True


def get_paas_deploy_phases_framework(
    app_code: str, module: str, env: str, user_credentials: Optional[UserCredentials] = None
):
    """
    获取部署阶段整体框架
    """
    url = url_join(
        get_paas3_url_prefix(), f"/bkapps/applications/{app_code}/modules/{module}/envs/{env}/deploy_phases/"
    )
    headers = gen_gateway_headers(user_credentials)
    ok, resp_data = http_get(url, data={}, headers=headers, timeout=REQ_PAAS_API_TIMEOUT)
    if not ok:
        logger.error(
            "%s api failed! %s %s, data: %s, request_id: %s, error: %s",
            "paasv3",
            "http_get",
            url,
            "",
            local.request_id,
            resp_data["error"],
        )
    return resp_data


def get_paas_deploy_phases_instance(
    app_code: str, module: str, env: str, deploy_id: str, user_credentials: Optional[UserCredentials] = None
):
    """
    获取部署实例阶段详情
    """
    url = url_join(
        get_paas3_url_prefix(),
        f"/bkapps/applications/{app_code}/modules/{module}/envs/{env}/deploy_phases/{deploy_id}/",
    )
    headers = gen_gateway_headers(user_credentials=user_credentials)
    ok, resp_data = http_get(url, data={}, headers=headers, timeout=REQ_PAAS_API_TIMEOUT)
    if not ok:
        logger.error(
            "%s api failed! %s %s, data: %s, request_id: %s, error: %s",
            "paasv3",
            "http_get",
            url,
            "",
            local.request_id,
            resp_data["error"],
        )
    return resp_data


def get_pass_deploy_streams_history_events(deploy_id: str, user_credentials: Optional[UserCredentials] = None):
    """
    获取部署实例阶段详情
    """
    url = url_join(get_paas3_url_prefix(), f"/streams/{deploy_id}/history_events")
    headers = gen_gateway_headers(user_credentials)
    ok, resp_data = http_get(url, data={}, headers=headers, timeout=REQ_PAAS_API_TIMEOUT)
    if not ok:
        logger.error(
            "%s api failed! %s %s, data: %s, request_id: %s, error: %s",
            "paasv3",
            "http_get",
            url,
            "",
            local.request_id,
            resp_data["error"],
        )
    return resp_data


def get_paas_deployment_result(
    app_code: str, module: str, deploy_id: str, user_credentials: Optional[UserCredentials] = None
):
    """
    获取部署详情
    """
    url = url_join(
        get_paas3_url_prefix(), f"/bkapps/applications/{app_code}/modules/{module}/deployments/{deploy_id}/result/"
    )
    headers = gen_gateway_headers(user_credentials)
    ok, resp_data = http_get(url, data={}, headers=headers, timeout=REQ_PAAS_API_TIMEOUT)
    if not ok:
        logger.error(
            "%s api failed! %s %s, data: %s, request_id: %s, error: %s",
            "paasv3",
            "http_get",
            url,
            "",
            local.request_id,
            resp_data["error"],
        )
    return resp_data


def get_paas_offline_result(
    app_code: str, module: str, deploy_id: str, user_credentials: Optional[UserCredentials] = None
):
    """
    获取部署详情
    """
    url = url_join(
        get_paas3_url_prefix(), f"/bkapps/applications/{app_code}/modules/{module}/offlines/{deploy_id}/result/"
    )
    headers = gen_gateway_headers(user_credentials)
    ok, resp_data = http_get(url, data={}, headers=headers, timeout=REQ_PAAS_API_TIMEOUT)
    if not ok:
        logger.error(
            "%s api failed! %s %s, data: %s, request_id: %s, error: %s",
            "paasv3",
            "http_get",
            url,
            "",
            local.request_id,
            resp_data["error"],
        )
    return resp_data


def get_paas_runtime_info(app_code: str, module: str, user_credentials: Optional[UserCredentials] = None):
    """
    获取运行时信息
    """
    url = url_join(get_paas3_url_prefix(), f"/bkapps/applications/{app_code}/modules/{module}/runtime/overview/")
    headers = gen_gateway_headers(user_credentials)
    ok, resp_data = http_get(url, data={}, headers=headers, timeout=REQ_PAAS_API_TIMEOUT)
    if not ok:
        logger.error(
            "%s api failed! %s %s, data: %s, request_id: %s, error: %s",
            "paasv3",
            "http_get",
            url,
            "",
            local.request_id,
            resp_data["error"],
        )
    return resp_data


def get_paas_repo_branch_info(app_code: str, module: str, user_credentials: Optional[UserCredentials] = None):
    """
    获取应用代码仓库信息
    """
    url = url_join(get_paas3_url_prefix(), f"/bkapps/applications/{app_code}/modules/{module}/repo/branches/")
    headers = gen_gateway_headers(user_credentials)
    ok, resp_data = http_get(url, data={}, headers=headers, timeout=REQ_PAAS_API_TIMEOUT)
    if not ok:
        logger.error(
            "%s api failed! %s %s, data: %s, request_id: %s, error: %s",
            "paasv3",
            "http_get",
            url,
            "",
            local.request_id,
            resp_data["error"],
        )
    branch_list = []
    branch_commit_info = {}
    for branch in resp_data.get("results", []):
        branch_name = branch.get("name")
        branch_list.append(branch_name)
        branch_commit_info[branch_name] = {
            "commit_id": branch.get("revision", ""),
            "last_update": branch.get("last_update", ""),
            "message": branch.get("message", ""),
            "type": branch.get("type", ""),
            "extra": branch.get("extra", {}),
        }

    repo_info = get_paas_runtime_info(app_code, module, user_credentials).get("repo", {})
    return {
        "repo_url": repo_info.get("repo_url", ""),
        "branch_list": branch_list,
        "branch_commit_info": branch_commit_info,
    }


def update_app_maintainers(app_code: str, maintainers: List[str]):
    """
    更新 paas 的 app 成员
    """
    url = url_join(get_paas3_url_prefix(), f"/sys/shim/plugins_center/bk_plugins/{app_code}/members/")
    headers = gen_gateway_headers()

    data = [
        {
            "username": m,
            "role": {
                "name": "管理员",
                "id": "2",
            },
        }
        for m in maintainers
    ]

    ok, resp_data = http_post(url, data, headers=headers, timeout=REQ_PAAS_API_TIMEOUT)
    if not ok:
        logger.error(
            "%s api failed! %s %s, data: %s, request_id: %s, error: %s",
            "paasv3",
            "http_post",
            url,
            data,
            local.request_id,
            resp_data["error"],
        )
        raise error_codes.REMOTE_REQUEST_ERROR.format(
            f"request paasv3 fail! "
            f"Request=[http_post {urlparse(url).path} request_id={local.request_id}]"
            f"error={resp_data['error']}"
        )
    return True
