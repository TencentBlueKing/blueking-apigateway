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
from django.conf import settings


def get_path_display(path, match_subpath):
    if not match_subpath:
        return path

    return f"{path.rstrip('/')}/*"


def get_resource_url(resource_url_tmpl: str, gateway_name: str, stage_name: str, resource_path: str):
    """
    拼接资源请求地址
    """
    return resource_url_tmpl.format(
        api_name=gateway_name,
        stage_name=stage_name,
        resource_path=resource_path.lstrip("/"),
    )


def get_resource_doc_link(api_name, stage_name, resource_name):
    """
    资源文档链接
    """
    return settings.RESOURCE_DOC_URL_TMPL.format(
        api_name=api_name,
        stage_name=stage_name,
        resource_name=resource_name,
    )
