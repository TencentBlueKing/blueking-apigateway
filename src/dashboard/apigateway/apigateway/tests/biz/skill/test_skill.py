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
import pytest
from ddf import G
from django.db import connection
from django.test.utils import CaptureQueriesContext

from apigateway.apps.skill.constants import SkillStatusEnum
from apigateway.apps.skill.models import SkillMetadata
from apigateway.biz.skill.skill import SkillHandler
from apigateway.common.error_codes import APIError
from apigateway.common.tenant.constants import TenantModeEnum
from apigateway.core.constants import GatewayStatusEnum
from apigateway.core.models import Gateway
from apigateway.tests.biz.skill.conftest import create_skill

pytestmark = pytest.mark.django_db


def _gateway(name, tenant_id="default", **kwargs) -> Gateway:
    params = {"status": GatewayStatusEnum.ACTIVE.value, "tenant_mode": TenantModeEnum.SINGLE.value}
    params.update(kwargs)
    return G(Gateway, name=name, tenant_id=tenant_id, **params)


def _codes(queryset):
    return sorted(item.code for item in queryset)


class TestParseSkillId:
    @pytest.mark.parametrize(
        "skill_id, expected",
        [
            ("p_job-plan", ("platform", None, "job-plan")),
            ("g_demo_release-check", ("gateway", "demo", "release-check")),
            ("g_demo-1_a", ("gateway", "demo-1", "a")),
            ("x_demo", None),
            ("g_demo", None),
            ("g__name", None),
            ("p_Bad_Name", None),
            ("g_demo_bad_name", None),
            ("", None),
        ],
    )
    def test_parse(self, skill_id, expected):
        assert SkillHandler.parse_skill_id(skill_id) == expected


class TestMarketQueryset:
    def test_visibility(self):
        create_skill("platform-skill")
        demo = _gateway("demo")
        create_skill("active", gateway=demo)
        archived = create_skill("archived", gateway=demo)
        SkillMetadata.objects.filter(id=archived.id).update(status=SkillStatusEnum.ARCHIVED.value)
        create_skill("inactive", gateway=_gateway("stopped", status=GatewayStatusEnum.INACTIVE.value))

        assert _codes(SkillHandler.get_market_queryset()) == ["g_demo_active", "p_platform-skill"]

    def test_tenant_filter(self):
        create_skill("platform-skill")
        create_skill("mine", gateway=_gateway("mine", tenant_id="a"))
        create_skill("other", gateway=_gateway("other", tenant_id="b"))
        create_skill("global", gateway=_gateway("global", tenant_id="", tenant_mode=TenantModeEnum.GLOBAL.value))

        assert _codes(SkillHandler.get_market_queryset("a")) == [
            "g_global_global",
            "g_mine_mine",
            "p_platform-skill",
        ]


class TestFilterQueryset:
    @pytest.fixture(autouse=True)
    def skills(self):
        self.platform = create_skill("platform-skill", tags=["作业平台", "JOB"])
        self.gateway = _gateway("demo")
        self.gateway_skill = create_skill(
            "release-check",
            gateway=self.gateway,
            display_name="发布核对",
            display_name_en="Release Check",
            description="核对环境差异",
            tags=["只读"],
        )

    def _filter(self, **kwargs):
        return _codes(SkillHandler.filter_queryset(SkillMetadata.objects.all(), **kwargs))

    @pytest.mark.parametrize(
        "keyword, expected",
        [
            ("release", ["g_demo_release-check"]),
            ("发布核对", ["g_demo_release-check"]),
            ("Release Check", ["g_demo_release-check"]),
            ("环境差异", ["g_demo_release-check"]),
            ("作业", ["p_platform-skill"]),
            ("jobv3", ["g_demo_release-check", "p_platform-skill"]),
            ("execute_job_plan", ["g_demo_release-check", "p_platform-skill"]),
            ("nothing", []),
        ],
    )
    def test_keyword(self, keyword, expected):
        assert self._filter(keyword=keyword) == expected

    def test_keyword_without_gateway_name(self):
        assert self._filter(keyword="jobv3-cloud", match_gateway_name=False) == []

    def test_keyword_only_current_version_relations(self):
        old_version_id = self.platform.current_version_id
        self.platform.current_version.relations.filter(resource_name="execute_job_plan").update(
            resource_name="old_resource"
        )
        create_skill("platform-skill", version="2.0.0", tags=["JOB"])
        assert SkillMetadata.objects.get(id=self.platform.id).current_version_id != old_version_id

        assert self._filter(keyword="old_resource") == []

    def test_tag_case_insensitive(self):
        assert self._filter(tag="job") == ["p_platform-skill"]
        assert self._filter(tag=" JOB ") == ["p_platform-skill"]

    def test_type_and_status(self):
        assert self._filter(skill_type="gateway") == ["g_demo_release-check"]
        assert self._filter(status=SkillStatusEnum.ARCHIVED.value) == []


class TestOrderQueryset:
    def test_orders(self):
        first = create_skill("b-skill")
        second = create_skill("a-skill")
        SkillMetadata.objects.filter(id=first.id).update(download_count=5)

        def order(order_by):
            return [item.name for item in SkillHandler.order_queryset(SkillMetadata.objects.all(), order_by)]

        assert order("name") == ["a-skill", "b-skill"]
        assert order("-download_count") == ["b-skill", "a-skill"]
        assert order("-published_time") == [second.name, first.name]


class TestCountsAndTags:
    def test_count_by_type(self):
        create_skill("platform-skill")
        assert SkillHandler.count_by_type(SkillMetadata.objects.all()) == {"platform": 1, "gateway": 0}

    def test_list_tags(self):
        create_skill("a", tags=["日志", "只读"])
        create_skill("b", tags=["日志"])

        assert SkillHandler.list_tags(SkillMetadata.objects.all()) == [
            {"name": "日志", "skill_count": 2},
            {"name": "只读", "skill_count": 1},
        ]
        assert SkillHandler.list_tags(SkillMetadata.objects.all(), keyword="只") == [
            {"name": "只读", "skill_count": 1}
        ]
        assert SkillHandler.list_tags(SkillMetadata.objects.filter(name="b")) == [{"name": "日志", "skill_count": 1}]


class TestGetSkill:
    def test_market(self):
        platform = create_skill("platform-skill")
        demo = _gateway("demo", tenant_id="a")
        gateway_skill = create_skill("release-check", gateway=demo)

        assert SkillHandler.get_market_skill("p_platform-skill", "a") == platform
        assert SkillHandler.get_market_skill("g_demo_release-check", "a") == gateway_skill

        with pytest.raises(APIError) as err:
            SkillHandler.get_market_skill("g_demo_release-check", "b")
        assert err.value.code.code_name == "NO_PERMISSION"

        SkillMetadata.objects.filter(id=gateway_skill.id).update(status=SkillStatusEnum.ARCHIVED.value)
        for skill_id in ["g_demo_release-check", "p_unknown", "x_bad"]:
            with pytest.raises(APIError) as err:
                SkillHandler.get_market_skill(skill_id, "a")
            assert err.value.code.code_name == "NOT_FOUND"

    def test_open_ignores_tenant(self):
        demo = _gateway("demo", tenant_id="a")
        gateway_skill = create_skill("release-check", gateway=demo)

        assert SkillHandler.get_open_skill("g_demo_release-check") == gateway_skill

    def test_gateway(self):
        demo = _gateway("demo")
        other = _gateway("other")
        skill = create_skill("release-check", gateway=demo)
        create_skill("release-check", gateway=other)
        SkillMetadata.objects.filter(id=skill.id).update(status=SkillStatusEnum.ARCHIVED.value)
        create_skill("release-check")

        assert SkillHandler.get_gateway_skill(demo, "g_demo_release-check").id == skill.id
        for skill_id in ["g_other_release-check", "p_release-check", "bad"]:
            with pytest.raises(APIError):
                SkillHandler.get_gateway_skill(demo, skill_id)


class TestVersions:
    @pytest.fixture
    def metadata(self):
        create_skill("demo-skill", version="1.2.0")
        create_skill("demo-skill", version="1.9.0")
        metadata = create_skill("demo-skill", version="1.10.0")
        metadata.current_version = metadata.versions.get(version="1.9.0")
        metadata.save(update_fields=["current_version"])
        return metadata

    def test_list_versions(self, metadata):
        assert [item.version for item in SkillHandler.list_versions(metadata)] == ["1.10.0", "1.9.0", "1.2.0"]

    def test_list_market_versions(self, metadata):
        found, versions = SkillHandler.list_market_versions("p_demo-skill", "a")
        assert found.id == metadata.id
        assert [item.version for item in versions] == ["1.10.0", "1.9.0", "1.2.0"]

        create_skill("release-check", gateway=_gateway("demo", tenant_id="a"))
        with pytest.raises(APIError) as err:
            SkillHandler.list_market_versions("g_demo_release-check", "b")
        assert err.value.code.code_name == "NO_PERMISSION"

    def test_get_market_version(self, metadata):
        found, version = SkillHandler.get_market_version("p_demo-skill", None, "a")
        assert found.id == metadata.id
        assert version.version == "1.9.0"
        assert SkillHandler.get_market_version("p_demo-skill", "1.2.0", "a")[1].version == "1.2.0"

        create_skill("release-check", gateway=_gateway("demo", tenant_id="a"))
        with pytest.raises(APIError) as err:
            SkillHandler.get_market_version("g_demo_release-check", None, "b")
        assert err.value.code.code_name == "NO_PERMISSION"

    def test_get_version(self, metadata):
        assert SkillHandler.get_version(metadata).version == "1.9.0"
        assert SkillHandler.get_version(metadata, "1.2.0").version == "1.2.0"
        with pytest.raises(APIError):
            SkillHandler.get_version(metadata, "9.9.9")

    def test_latest_version(self, metadata):
        assert SkillHandler.get_latest_version(metadata) == "1.10.0"


class TestContext:
    def test_build_list_context_query_count(self):
        G(Gateway, name="jobv3-cloud", display_name="作业平台")
        for index in range(3):
            create_skill(f"skill-{index}")
        queryset = SkillHandler.for_list(SkillMetadata.objects.all())

        with CaptureQueriesContext(connection) as small:
            SkillHandler.build_list_context(list(queryset[:1]))
        with CaptureQueriesContext(connection) as large:
            context = SkillHandler.build_list_context(list(queryset))

        assert len(small) == len(large)
        assert all(
            value == [{"name": "jobv3-cloud", "display_name": "作业平台"}]
            for value in context["related_gateways"].values()
        )

    def test_build_detail_context(self, settings):
        settings.BK_API_URL_TMPL = "https://bkapi.example.com/api/{api_name}"
        metadata = create_skill("release-check", gateway=_gateway("demo"))

        context = SkillHandler.build_detail_context(metadata)

        assert context["stage"] == "prod"
        assert context["version_count"] == 1
        assert {"gateway_name": "jobv3-cloud", "resource_name": "execute_job_plan"} in context["apis"]
        assert context["download_url"] == (
            "https://bkapi.example.com/api/bk-apigateway/prod/api/v2/open/skills/g_demo_release-check/download/"
        )

        metadata.status = SkillStatusEnum.ARCHIVED.value
        assert SkillHandler.build_detail_context(metadata)["download_url"] is None

    def test_download_url_without_url_tmpl(self, settings):
        settings.BK_API_URL_TMPL = ""
        metadata = create_skill("release-check", gateway=_gateway("demo"))

        assert SkillHandler.build_download_url(metadata) is None

    def test_platform_stage_is_none(self):
        assert SkillHandler.build_detail_context(create_skill("platform-skill"))["stage"] is None


class TestIncreaseDownloadCount:
    def test_increase(self):
        metadata = create_skill("platform-skill")
        updated_time = SkillMetadata.objects.get(id=metadata.id).updated_time

        for _ in range(3):
            SkillHandler.increase_download_count(metadata.id)

        metadata = SkillMetadata.objects.get(id=metadata.id)
        assert metadata.download_count == 3
        assert metadata.updated_time == updated_time
