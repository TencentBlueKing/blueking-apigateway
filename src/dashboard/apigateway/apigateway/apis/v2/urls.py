# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关 (BlueKing - APIGateway) available.
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
from django.urls import include, path

# NOTE:
# 1. 新版 http 协议
# 2. 统一注册到 bk-apigateway 网关，并且 inner api 需要隐藏 + 主动授权 (未来需要下掉 bk-apigateway-inner)
# 3. 三类 api 即使功能一模一样，也不允许复用代码 (这已经是最上层使用层，现在功能一致不代表随时间推移还会保持一致)

# FIXME: resource.yaml 改成新版格式，并且切换到 openapi3.0 协议，自动生成文档和示例

urlpatterns = [
    # /api/v2/sync/ 用于 SDK 同步网关; 鉴权：来自于网关+related_apps
    path("sync/", include("apigateway.apis.v2.sync.urls")),
    # /api/v2/inner/ 用于 paasv3 内部调用; 鉴权：来自于网关（主动授权）
    path("inner/", include("apigateway.apis.v2.inner.urls")),
    # /api/v2/open/ 用于普通开放 api；鉴权：来自于网关
    path("open/", include("apigateway.apis.v2.open.urls")),
]
