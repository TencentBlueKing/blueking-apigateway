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
from typing import List, Optional

from apigateway.apps.access_strategy.constants import AccessStrategyTypeEnum
from apigateway.apps.access_strategy.models import IPGroup
from apigateway.apps.plugin.models import PluginConfig, PluginType
from apigateway.controller.crds.release_data.access_strategy import CorsASC
from apigateway.utils.ip import parse_ip_content_to_list
from apigateway.utils.yaml import yaml_dumps, yaml_dumps_multiline_string

from .models import AccessStrategy

# FIXME: 转换成 PluginConfig 对应的格式是 前端动态表单保存下来的格式
# - source: access_strategy.config
#     - the schema => and get real data from database online
# - target: plugin_config.yaml
#     - get the real format from database online


def _parse_ip_content_list(ip_content_list: List[str]) -> List[str]:
    ips = set()
    for ip_content in ip_content_list:
        ip_list = parse_ip_content_to_list(ip_content)
        ips.update(ip_list)

    # we are not going to do the merge now, we will do it in the future if that become a problem
    # TODO: merge by cidr
    return list(ips)


def parse_ip_access_control(access_strategy: AccessStrategy) -> Optional[PluginConfig]:
    """
    input:
        {"type": "allow", "ip_group_list": [23, 25, 16, 17, 18]}
        {"type": "allow", "ip_group_list": []}
        {"type": "deny", "ip_group_list": [26, 18, 3, 15, 11, 10, 8, 23]}

    output:
        whitelist: |-
            1.1.1.1
            2.2.2.2
            1.1.1.1/24

            # a.b.c.d

        blacklist: |-
            127.0.0.1
            # abc

            0.0.0.0
    """
    config = access_strategy.config

    # if got an empty ip list, unbind the plugin!!!!!!
    ip_group_list = config["ip_group_list"]
    if not ip_group_list:
        return None

    ip_content_list = [group._ips for group in IPGroup.objects.filter(id__in=ip_group_list)]
    ip_list = _parse_ip_content_list(ip_content_list)

    # NOTE: incase the 404 after upgrade(the apisix required at least 1 item, otherwise load fail)
    # if got an empty ip list, unbind the plugin!!!!!!
    if not ip_list:
        return None

    # keep the origin comments
    content = "\n".join(ip_content_list)

    # the access strategy will be remove soon, so use `allow` and `deny` here directly
    data = {}
    if config["type"] == "allow":
        data = {"whitelist": content}
    elif config["type"] == "deny":
        data = {"blacklist": content}
    else:
        return None

    return PluginConfig(
        gateway=access_strategy.api,
        name=access_strategy.name,
        type=PluginType.objects.get(code="bk-ip-restriction"),
        yaml=yaml_dumps_multiline_string(data),
    )


def parse_rate_limit(access_strategy: AccessStrategy) -> Optional[PluginConfig]:
    """
    input:
        {"rates": {"__default": [{"tokens": 100, "period": 3600}]}}
        {"rates": {"__default": [{"tokens": 10, "period": 1}], "a": [{"tokens": 10, "period": 1}]}}
        {"rates": {"__default": [{"tokens": 1000, "period": 60}], "test": [{"tokens": 200, "period": 1}], "abc": [{"tokens": 300, "period": 1}]}}

    output:
        rates:
        __default:
            - period: 1
              tokens: 100
    """
    return PluginConfig(
        gateway=access_strategy.api,
        name=access_strategy.name,
        type=PluginType.objects.get(code="bk-rate-limit"),
        yaml=yaml_dumps(access_strategy.config),
    )


def parse_user_verified_unrequired_apps(access_strategy: AccessStrategy) -> Optional[PluginConfig]:
    """
    input:
        {"bk_app_code_list": ["sss", "xxxdfd"]}
        {"bk_app_code_list": []}


    output:
        exempted_apps:
        - bk_app_code: bk_apigateway

        exempted_apps:
        - bk_app_code: bk_apigateway
        dimension: api
        resource_ids: []
        - bk_app_code: bk_bcs_app
        dimension: api
    """
    app_code_list = access_strategy.config.get("bk_app_code_list")
    if not app_code_list:
        return None

    data = {
        "exempted_apps": [
            {
                "bk_app_code": app_code,
                "dimension": "api",
                "resource_ids": [],
            }
            for app_code in app_code_list
        ]
    }
    return PluginConfig(
        gateway=access_strategy.api,
        name=access_strategy.name,
        type=PluginType.objects.get(code="bk-verified-user-exempted-apps"),
        yaml=yaml_dumps(data),
    )


def parse_error_status_code_200(access_strategy: AccessStrategy) -> Optional[PluginConfig]:
    """
    input:
        {"allow": true}

    output:
        {}
    """
    return PluginConfig(
        gateway=access_strategy.api,
        name=access_strategy.name,
        type=PluginType.objects.get(code="bk-status-rewrite"),
        yaml="{}",
    )


def parse_cors(access_strategy: AccessStrategy) -> Optional[PluginConfig]:
    """_summary_
    input:
        {"allowed_origins": ["sss"], "allowed_methods": ["GET", "POST", "PATCH"], "allowed_headers": ["Origin", "Accept", "Content-Type", "X-Requested-With"], "exposed_headers": [], "max_age": 86400, "allow_credentials": true, "option_passthrough": false}
        {"allowed_origins": ["http://testbking.com"], "allowed_methods": ["GET", "PUT"], "allowed_headers": ["http://testbking.com"], "exposed_headers": [], "max_age": 86400, "allow_credentials": false, "option_passthrough": false}
        {
            "allowed_origins": [
                "http://testbking.com"
            ],
            "allowed_methods": [
                "GET",
                "PUT"
            ],
            "allowed_headers": [
                "http://testbking.com"
            ],
            "exposed_headers": [],
            "max_age": 86400,
            "allow_credentials": false,

            "option_passthrough": false
        }

    output:
        allow_origins: http://www.test.com
        allow_origins_by_regex: []
        allow_methods: '**'
        allow_headers: '**'
        expose_headers: ''
        max_age: 86400
        allow_credential: true
    """
    data = CorsASC()._to_plugin_config(access_strategy)
    return PluginConfig(
        gateway=access_strategy.api,
        name=access_strategy.name,
        type=PluginType.objects.get(code="bk-cors"),
        yaml=yaml_dumps(data),
    )

    pass


parse_funcs = {
    AccessStrategyTypeEnum.IP_ACCESS_CONTROL.value: parse_ip_access_control,
    AccessStrategyTypeEnum.RATE_LIMIT.value: parse_rate_limit,
    AccessStrategyTypeEnum.USER_VERIFIED_UNREQUIRED_APPS.value: parse_user_verified_unrequired_apps,
    AccessStrategyTypeEnum.ERROR_STATUS_CODE_200.value: parse_error_status_code_200,
    AccessStrategyTypeEnum.CORS.value: parse_cors,
}


def parse_to_plugin_config(access_strategy: AccessStrategy) -> Optional[PluginConfig]:
    return parse_funcs[access_strategy.type](access_strategy)
