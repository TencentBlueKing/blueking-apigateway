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

from apigateway.biz.released_resource_doc.constants import (
    BKAPI_AUTHORIZATION_DESCRIPTION_EN,
    BKAPI_AUTHORIZATION_DESCRIPTION_ZH,
)
from apigateway.utils.jinja2 import render_to_string


def test_bkapi_authorization_description():
    result = render_to_string(
        BKAPI_AUTHORIZATION_DESCRIPTION_ZH,
        verified_app_required=True,
        verified_user_required=True,
        docs_urls={},
        settings=settings,
    )
    assert result

    result = render_to_string(
        BKAPI_AUTHORIZATION_DESCRIPTION_EN,
        verified_app_required=True,
        verified_user_required=True,
        docs_urls={
            "USE_GATEWAY_API": "",
            "ACCESS_TOKEN_API": "",
        },
        settings=settings,
    )
    assert result
