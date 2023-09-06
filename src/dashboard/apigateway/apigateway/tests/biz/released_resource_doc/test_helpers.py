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
import pytest
from django.utils.translation import override

from apigateway.apps.docs.gateway.resource_doc import helpers


class TestResourceDocHelper:
    @pytest.mark.parametrize(
        "stage_name, resource, doc, resource_url, api_maintainers, expected",
        [
            (
                "prod",
                {
                    "id": 8241,
                    "name": "echo",
                    "description": "",
                    "method": "GET",
                    "path": "/echo/",
                    "match_subpath": False,
                    "is_public": True,
                    "allow_apply_permission": True,
                    "app_verified_required": True,
                    "resource_perm_required": False,
                    "user_verified_required": True,
                },
                {
                    "resource_id": 8241,
                    "type": "markdown",
                    "content": "test",
                    "created_time": "2020-06-10 23:17:00+0800",
                    "updated_time": "2020-11-06 16:11:59+0800",
                },
                "http://bking.com/prod/echo/",
                ["admin"],
                {
                    "type": "markdown",
                    "updated_time": "2020-11-06 16:11:59+0800",
                },
            ),
            (
                "prod",
                {},
                {},
                "",
                ["admin"],
                {},
            ),
        ],
    )
    def test_get_doc(
        self,
        stage_name,
        resource,
        doc,
        resource_url,
        api_maintainers,
        expected,
    ):
        helper = helpers.ResourceDocHelper(stage_name, resource, doc, resource_url, api_maintainers)
        doc = helper.get_doc()
        doc.pop("content", None)

        assert expected == doc

    @pytest.mark.parametrize(
        "resource, language, expected",
        [
            (
                {},
                "en",
                False,
            ),
            (
                {
                    "method": "POST",
                },
                "en",
                True,
            ),
            (
                {
                    "method": "POST",
                },
                "zh-cn",
                True,
            ),
            (
                {
                    "method": "POST",
                },
                "fr",
                False,
            ),
        ],
    )
    def test_get_resource_url_part(self, resource, language, expected):
        with override(language):
            helper = helpers.ResourceDocHelper("prod", resource, {}, "/test/", ["admin"])
            part = helper._get_resource_url_part()
            assert bool(part) is expected

    @pytest.mark.parametrize(
        "resource, language, expected",
        [
            (
                {
                    "app_verified_required": True,
                },
                "en",
                True,
            ),
            (
                {
                    "user_verified_required": True,
                },
                "en",
                True,
            ),
            (
                {
                    "app_verified_required": False,
                    "user_verified_required": False,
                },
                "en",
                False,
            ),
            (
                {
                    "app_verified_required": True,
                },
                "zh-hans",
                True,
            ),
            (
                {
                    "app_verified_required": True,
                },
                "fr",
                False,
            ),
        ],
    )
    def test_get_common_request_params_part(self, resource, language, expected):
        with override(language):
            helper = helpers.ResourceDocHelper("prod", resource, {}, "/test/", ["admin"])
            part = helper._get_common_request_params_part()
            assert bool(part) is expected
