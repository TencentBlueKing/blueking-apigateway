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
import re
from builtins import object

from common.base_loggers import BasicRequestLogger
from common.errors import error_codes
from esb.bkapp.validators import AppAuthValidator, AppCodeWhiteListValidator
from esb.bkauth.validators import UserAuthValidator
from esb.channel import ApiChannel
from esb.component import BaseComponent
from esb.compperm.validators import ComponentPermValidator
from esb.gateway.validators import APIGatewayAdapter
from esb.utils.base import RE_PATH_VARIABLE, SmartHost


class ApiChannelForAPIS(ApiChannel):
    request_loggers = [
        BasicRequestLogger(),
    ]

    request_validators = [
        APIGatewayAdapter(),
        AppAuthValidator(),
        UserAuthValidator(),
        ComponentPermValidator(),
    ]


class ESBApiChannelForAPIS(ApiChannel):
    request_validators = [
        APIGatewayAdapter(),
        AppAuthValidator(),
        AppCodeWhiteListValidator(
            (
                "bk_paas",
                "bk_console",
                "bk_apigateway",
            )
        ),
    ]


class FTAApiChannelForAPIS(ApiChannel):
    request_loggers = [
        BasicRequestLogger(),
    ]
    request_validators = [
        APIGatewayAdapter(),
    ]


class Component(BaseComponent):
    """Component class"""

    pass


class SetupConfMixin(object):
    def setup_conf(self, conf):
        self.__dict__.update(conf)
        if "host" in conf:
            self.set_host(conf["host"])

    def set_host(self, host):
        if isinstance(host, dict):
            self.host = SmartHost(**host)
        elif isinstance(host, SmartHost):
            self.host = host
        else:
            self.host = None


class ConfComponent(BaseComponent, SetupConfMixin):
    """Component for confapis"""

    def get_request_info(self, extra_params=None):
        # 替换目标地址中的变量模版
        path = self.dest_path

        # 获取路径变量，并格式化目标路径
        dest_path_var_fields = RE_PATH_VARIABLE.findall(self.dest_path)
        if dest_path_var_fields:
            path_vars = self.request.path_vars and self.request.path_vars.val_dict or self.request.kwargs
            try:
                path = self.dest_path.format(**path_vars)
            except KeyError as e:
                raise error_codes.ARGUMENT_ERROR.format_prompt("param %s is required" % e.args[0])

        # 获取参数，并去除bk_app_code、bk_app_secret等参数
        params = self.request.get_strict_clean_params()
        bk_supplier_account = params.pop("bk_supplier_account", "0")

        # 将路径变量从参数中去除
        for key in dest_path_var_fields:
            params.pop(key, None)

        # 处理额外字段，将扩展字段添加到参数
        extra_param_fields = self.get_extra_param_fields()
        if "creator" in extra_param_fields:
            params["creator"] = self.current_user.username
        if "bk_supplier_account" in extra_param_fields:
            params["bk_supplier_account"] = bk_supplier_account

        # 添加系统默认的额外参数
        if extra_params:
            params.update(extra_params)

        if self.dest_http_method == "GET":
            params, data = params, None
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
        else:
            params, data = None, json.dumps(params)
            headers = {"Content-Type": "application/json"}
        return {
            "path": path,
            "params": params,
            "data": data,
            "headers": headers,
        }

    def get_extra_param_fields(self):
        extra_param_fields = getattr(self, "extra_param_fields", "") or ""
        return re.findall(r"[^,; ]+", extra_param_fields)
