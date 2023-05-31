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

import functools
import os

from django.conf import settings
from django.http import Http404

from common.errors import error_codes
from esb.channel import get_channel_manager
from esb.component import get_components_manager

# 把当前目录切换到项目目录，因为后面用到的路径都是相对路径
try:
    os.chdir(settings.BASE_DIR)
except Exception:
    pass


def router_view(channel_type, request, path):
    components_manager = get_components_manager()
    channel_manager = get_channel_manager()

    path = "/%s/" % path.strip("/")
    path = channel_manager.get_rewrite_path_by_path(path) or path
    request.g.comp_path = path

    # Get ESBChannel by path
    channel_conf = get_channel_conf(path, request)
    channel_route = channel_conf["channel_route"]
    # Check if channel is active
    if not channel_route.is_active:
        raise error_codes.INACTIVE_CHANNEL

    # Check if channel's component class exists
    comp_cls = components_manager.get_comp_by_name(channel_route.component_codename)
    if not comp_cls:
        raise error_codes.COMPONENT_NOT_FOUND.format_prompt(channel_route.component_codename)

    # Dynamic contribute channel object
    channel_class = channel_conf["classes"][channel_type]
    channel_obj = channel_class(
        comp_cls,
        path=path,
        is_active=True,
        comp_conf=channel_conf.get("comp_conf"),
        channel_conf=channel_conf.get("channel_conf", {}),
    )

    # 判断该channel是否拥有自定义的validators
    if getattr(channel_route, "request_validators", None) is not None:
        channel_obj.set_request_validators(channel_route.request_validators)
    if getattr(channel_route, "append_request_validators", None) is not None:
        channel_obj.append_request_validators(channel_route.append_request_validators)

    # 针对本次请求存储timeout和系统名
    # 系统名用于访问频率控制
    request.g.timeout = channel_route.timeout
    request.g.sys_name = comp_cls.sys_name

    return channel_obj.handle_request(request)


api_router_view = functools.partial(router_view, "api")


def get_channel_conf(path, request):
    channel_manager = get_channel_manager()

    channel_conf = channel_manager.get_channel_by_path(path, request.method)
    if channel_conf:
        return channel_conf

    # 添加可变参数的正则匹配
    channel_conf, path_vars = channel_manager.search_channel_by_repath(path, request.method)
    if channel_conf:
        request.g.path_vars = path_vars
        return channel_conf

    raise Http404


def buffet_component_view(request, path):
    """
    处理自助接入组件的View
    """
    raise error_codes.INACTIVE_CHANNEL.format_prompt("Not found, inactive buffet component", replace=True)
