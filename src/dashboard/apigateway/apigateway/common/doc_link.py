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
from django.conf import settings

from apigateway.common.django.translation import get_current_language_code
from apigateway.conf.utils import get_doc_links


def get_doc_link(name: str) -> str:
    """从 get_doc_links 中获取指定文档地址，用于模板渲染。

    文档站语言由当前请求语言决定：en -> EN，其余 -> ZH。
    """
    lang = "EN" if get_current_language_code() == "en" else "ZH"
    return get_doc_links(
        settings.BK_APIGATEWAY_VERSION,
        settings.BK_DOCS_URL_PREFIX,
        lang,
    )[name]
