# paas via apigateway

import logging
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import urlparse

from cachetools import TTLCache, cached
from django.conf import settings

from apigateway.common.error_codes import error_codes
from apigateway.utils.local import local
from apigateway.utils.user_credentials import UserCredentials

from .http import http_get, http_post
from .utils import gen_gateway_headers

logger = logging.getLogger(__name__)


def url_join(host: str, path: str) -> str:
    """
    拼接 host, path 生成 url

    处理 host, path 有多余/的情况
    """
    return "{}/{}".format(host.rstrip("/"), path.lstrip("/"))


def get_paas_host() -> str:
    """
    获取 paas url
    """
    gateway_name = "paasv3"
    # if settings.EDITION == "te":
    #     gateway_name = "paasv3"
    return settings.BK_API_URL_TMPL.format(api_name=gateway_name)


def _call_paasv3_uni_apps_query_by_id(
    app_codes: List[str],
) -> List[Dict[str, Any]]:
    data = {
        "id": ",".join(app_codes),
    }

    headers = gen_gateway_headers()
    # headers.update(gen_tenant_header(tenant_id))

    url = url_join(get_paas_host(), "/prod/system/uni_applications/query/by_id/")
    timeout = 10

    ok, resp_data = http_get(url, data, headers=headers, timeout=timeout)
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

    return resp_data


def is_app_code_occupied(app_code: str) -> bool:
    app = get_app_no_cache(app_code)
    return app is not None


def get_app_no_cache(app_code: str) -> Optional[Dict[str, Any]]:
    result_data = _call_paasv3_uni_apps_query_by_id([app_code])
    apps: Iterable[Dict] = filter(None, result_data)

    result = {app["code"]: app for app in apps} or {}

    return result.get(app_code)


@cached(cache=TTLCache(maxsize=2000, ttl=300))
def get_app(app_code: str) -> Optional[Dict[str, Any]]:
    return get_app_no_cache(app_code)


def get_app_maintainers(bk_app_code: str) -> List[str]:
    """获取应用负责人"""
    # NOTE: here we need to get maintainers from paasv3
    #       but the X-Bk-Tenant-Id required
    #       so, we query it from bkauth first
    app = get_app(bk_app_code)

    if not app:
        return []

    if app.get("developers"):
        return app["developers"]

    if app.get("creator"):
        return [app["creator"]]

    return []


def create_paas_app(app_code: str) -> bool:
    """
    创建应用
    """
    return True


def deploy_paas_app(
    app_code: str,
    module: str,
    env: str,
    revision: str,
    branch: str,
    user_credentials: Optional[UserCredentials] = None,
) -> str:
    """
    部署应用
    return: deployment id
    """
    host = get_paas_host()
    url = url_join(host, f"/prod/bkapps/applications/{app_code}/modules/{module}/envs/{env}/deployments/")
    timeout = 10
    headers = gen_gateway_headers(user_credentials)
    data = {
        "revision": revision,
        "version_name": branch,
        "version_type": "branch",
    }

    ok, resp_data = http_post(url, data, headers=headers, timeout=timeout)
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


def module_offline(app_code: str, module: str, env: str, user_credentials: Optional[UserCredentials] = None):
    """
    下线应用
    """
    host = get_paas_host()
    url = url_join(host, f"prod/bkapps/applications/{app_code}/modules/{module}/envs/{env}/offlines/")
    timeout = 10
    headers = gen_gateway_headers(user_credentials)
    ok, resp_data = http_post(url, None, headers=headers, timeout=timeout)
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


def set_paas_stage_env(app_code: str, module: str, env: Dict[str, Any]):
    """
    设置应用环境变量
    """

    return True


def get_deploy_phases_framework(
    app_code: str, module: str, env: str, user_credentials: Optional[UserCredentials] = None
):
    """
    获取部署阶段整体框架
    """
    host = get_paas_host()
    url = url_join(host, f"prod/bkapps/applications/{app_code}/modules/{module}/envs/{env}/deploy_phases/")
    timeout = 10
    headers = gen_gateway_headers(user_credentials)
    ok, resp_data = http_get(url, data={}, headers=headers, timeout=timeout)
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


def get_deploy_phases_instance(
    app_code: str, module: str, env: str, deploy_id: str, user_credentials: Optional[UserCredentials] = None
):
    """
    获取部署实例阶段详情
    """
    host = get_paas_host()
    url = url_join(
        host, f"/prod/bkapps/applications/{app_code}/modules/{module}/envs/{env}/deploy_phases/{deploy_id}/"
    )
    timeout = 10
    headers = gen_gateway_headers(user_credentials)
    ok, resp_data = http_get(url, data={}, headers=headers, timeout=timeout)
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
    host = get_paas_host()
    url = url_join(host, f"/prod/streams/{deploy_id}/history_events")
    timeout = 10
    headers = gen_gateway_headers(user_credentials)
    ok, resp_data = http_get(url, data={}, headers=headers, timeout=timeout)
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


def get_deployment_result(
    app_code: str, module: str, deploy_id: str, user_credentials: Optional[UserCredentials] = None
):
    """
    获取部署详情
    """
    host = get_paas_host()
    url = url_join(host, f"/prod/bkapps/applications/{app_code}/modules/{module}/deployments/{deploy_id}/result/")
    timeout = 10
    headers = gen_gateway_headers(user_credentials)
    ok, resp_data = http_get(url, data={}, headers=headers, timeout=timeout)
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
