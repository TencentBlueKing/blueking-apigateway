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
from django.test import TestCase
from django_dynamic_fixture import G

from apigateway.common.contexts import (
    APIAuthContext,
    ResourceAuthContext,
    StageProxyHTTPContext,
    StageRateLimitContext,
)
from apigateway.core.models import Context, Gateway


class TestAPIAuthContext(TestCase):
    @pytest.fixture(autouse=True)
    def context_fixture(self, meta_schemas):
        self.context = APIAuthContext()

    def test_property(self):
        self.assertEqual(self.context.scope_type, "api")
        self.assertEqual(self.context.type, "api_auth")

    def test_save(self):
        gateway = G(Gateway)

        data = [
            {
                "config": {
                    "user_auth_type": "ieod",
                    "api_type": 10,
                    "unfiltered_sensitive_keys": [],
                    "uin_conf": {},
                    "rtx_conf": {
                        "user_type": "rtx",
                        "from_operator": False,
                        "from_bk_ticket": False,
                        "from_auth_token": False,
                    },
                }
            },
            {
                "config": {
                    "user_auth_type": "tencent",
                    "api_type": 10,
                    "unfiltered_sensitive_keys": [],
                    "uin_conf": {},
                    "rtx_conf": {
                        "user_type": "uin",
                        "from_uin_skey": False,
                        "skey_type": 1,
                        "domain_id": 285,
                        "search_rtx": False,
                        "search_rtx_source": 0,
                        "from_auth_token": False,
                    },
                }
            },
        ]

        for test in data:
            self.context.save(gateway.id, test["config"])
            self.assertEqual(self.context.get_config(gateway.id), test["config"])

    def test_delete(self):
        gateway = G(Gateway)
        G(Context, scope_id=gateway.id, scope_type="api", type="api_auth")

        self.context.delete(scope_ids=[gateway.id])
        self.assertFalse(Context.objects.filter(scope_id__in=[gateway.id]).exists())


class TestResourceAuthContext(TestCase):
    @pytest.fixture(autouse=True)
    def context_fixture(self, meta_schemas):
        self.context = ResourceAuthContext()

    def test_property(self):
        self.assertEqual(self.context.scope_type, "resource")
        self.assertEqual(self.context.type, "resource_auth")


class TestStageProxyHTTPContext:
    @pytest.fixture
    def context(self, meta_schemas):
        return StageProxyHTTPContext()

    def test_property(self, context):
        assert context.scope_type == "stage"
        assert context.type == "stage_proxy_http"

    @pytest.mark.parametrize(
        "hosts,expected",
        [
            ([], False),
            ([{"host": ""}], False),
            ([{"host": "https://example.com"}], True),
        ],
    )
    def test_contain_hosts(self, hosts, expected, context: StageProxyHTTPContext, fake_stage):
        context.save(
            fake_stage.id,
            config={
                "upstreams": {"hosts": hosts, "loadbalance": "roundrobin"},
                "timeout": 60,
                "transform_headers": {},
            },
        )
        assert context.contain_hosts(fake_stage.id) is expected


class TestStageRateLimitContext(TestCase):
    @pytest.fixture(autouse=True)
    def context_fixture(self, meta_schemas):
        self.context = StageRateLimitContext()

    def test_property(self):
        self.assertEqual(self.context.scope_type, "stage")
        self.assertEqual(self.context.type, "stage_rate_limit")
