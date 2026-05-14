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
import importlib

import pytest
from django.test import override_settings
from django.urls import NoReverseMatch, clear_url_caches, reverse, set_urlconf

import apigateway.urls


class TestUrls:
    def test_urls_disabled_when_debug_is_false(self):
        try:
            with override_settings(DEBUG=False):
                clear_url_caches()
                importlib.reload(apigateway.urls)
                set_urlconf(None)

                with pytest.raises(NoReverseMatch):
                    reverse("schema-swagger-ui")
        finally:
            importlib.reload(apigateway.urls)
            clear_url_caches()
            set_urlconf(None)
