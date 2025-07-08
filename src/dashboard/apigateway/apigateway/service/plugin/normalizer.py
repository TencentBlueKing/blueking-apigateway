# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2025 Tencent. All rights reserved.
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
from typing import Any, Dict


def format_fault_injection_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """while the dynamic form input many empty values, should be normalized!"""
    if config.get("abort"):
        abort = config["abort"]
        if abort.get("body") == "":
            del abort["body"]
        if abort.get("vars") == "":
            del abort["vars"]
        if not abort:
            del config["abort"]

    if config.get("delay"):
        delay = config["delay"]
        if delay.get("vars") == "":
            del delay["vars"]
        if not delay:
            del config["delay"]

    return config


def format_response_rewrite_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """while the dynamic form input many empty values, should be normalized!"""
    if config.get("vars") == "":
        del config["vars"]

    if config.get("body") == "":
        del config["body"]

    headers = config["headers"]
    new_headers = {}
    if headers.get("add"):
        new_headers["add"] = headers["add"]
    if headers.get("remove"):
        new_headers["remove"] = headers["remove"]
    if headers.get("set"):
        new_headers["set"] = headers["set"]

    config["headers"] = new_headers

    return config
