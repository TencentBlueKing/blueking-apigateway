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
import io
import zipfile

import pytest
from ddf import G
from django.contrib.auth.models import AnonymousUser
from django.utils import translation

from apigateway.apps.skill.constants import SkillStatusEnum
from apigateway.apps.skill.models import SkillMetadata
from apigateway.common.tenant.constants import TenantModeEnum
from apigateway.core.constants import GatewayStatusEnum
from apigateway.core.models import Gateway
from apigateway.tests.biz.skill.conftest import create_skill

pytestmark = pytest.mark.django_db


@pytest.fixture
def demo_gateway():
    return G(
        Gateway,
        name="demo",
        display_name="演示网关",
        status=GatewayStatusEnum.ACTIVE.value,
        tenant_mode=TenantModeEnum.SINGLE.value,
        tenant_id="default",
    )


@pytest.fixture
def other_tenant_gateway():
    return G(
        Gateway,
        name="other",
        status=GatewayStatusEnum.ACTIVE.value,
        tenant_mode=TenantModeEnum.SINGLE.value,
        tenant_id="other",
    )


@pytest.fixture
def skills(demo_gateway, other_tenant_gateway):
    create_skill("platform-skill", tags=["日志"])
    create_skill("release-check", gateway=demo_gateway, version="1.1.0")
    gateway_skill = create_skill(
        "release-check",
        gateway=demo_gateway,
        version="1.2.0",
        display_name="发布核对",
        display_name_en="Release Check",
        tags=["日志", "只读"],
    )
    create_skill("hidden", gateway=other_tenant_gateway)
    archived = create_skill("archived", gateway=demo_gateway)
    SkillMetadata.objects.filter(id=archived.id).update(status=SkillStatusEnum.ARCHIVED.value)
    return gateway_skill


def _skill_path(skill_id="g_demo_release-check", **kwargs):
    return {"skill_id": skill_id, **kwargs}


class TestSkillMarketplaceSkillListApi:
    def test_list(self, request_view, skills):
        resp = request_view("GET", "skill_marketplace.skill.list")
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["count"] == 2
        items = {item["skill_id"]: item for item in result["data"]["results"]}
        assert set(items) == {"p_platform-skill", "g_demo_release-check"}
        item = items["g_demo_release-check"]
        assert item["display_name"] == "发布核对"
        assert item["version"] == "1.2.0"
        assert item["gateway"] == {"name": "demo", "display_name": "演示网关"}
        assert item["related_gateways"] == [{"name": "jobv3-cloud", "display_name": "jobv3-cloud"}]
        assert sorted(item["tags"]) == ["只读", "日志"]
        assert items["p_platform-skill"]["gateway"] is None

    def test_filter(self, request_view, skills):
        resp = request_view("GET", "skill_marketplace.skill.list", data={"type": "platform"})
        assert [item["skill_id"] for item in resp.json()["data"]["results"]] == ["p_platform-skill"]

        resp = request_view("GET", "skill_marketplace.skill.list", data={"tag": "只读", "order_by": "name"})
        assert [item["skill_id"] for item in resp.json()["data"]["results"]] == ["g_demo_release-check"]

    def test_english_display_name(self, request_view, skills):
        with translation.override("en"):
            resp = request_view("GET", "skill_marketplace.skill.list", data={"type": "gateway"})
        assert resp.json()["data"]["results"][0]["display_name"] == "Release Check"


class TestSkillMarketplaceSkillCountApi:
    def test_counts(self, request_view, skills):
        resp = request_view("GET", "skill_marketplace.skill.counts")
        assert resp.json()["data"] == {"platform": 1, "gateway": 1}

        resp = request_view("GET", "skill_marketplace.skill.counts", data={"tag": "只读"})
        assert resp.json()["data"] == {"platform": 0, "gateway": 1}


class TestSkillMarketplaceTagListApi:
    def test_tags(self, request_view, skills):
        resp = request_view("GET", "skill_marketplace.tag.list")
        assert resp.json()["data"] == [{"name": "日志", "skill_count": 2}, {"name": "只读", "skill_count": 1}]

        resp = request_view("GET", "skill_marketplace.tag.list", data={"type": "platform"})
        assert resp.json()["data"] == [{"name": "日志", "skill_count": 1}]


class TestSkillMarketplaceSkillRetrieveApi:
    def test_retrieve(self, settings, request_view, skills):
        settings.DASHBOARD_URL = "https://apigw.example.com/backend"
        resp = request_view("GET", "skill_marketplace.skill.retrieve", path_params=_skill_path())
        data = resp.json()["data"]

        assert resp.status_code == 200
        assert data["skill_id"] == "g_demo_release-check"
        assert data["current_version"]["version"] == "1.2.0"
        assert data["current_version"]["is_current"] is True
        assert data["current_version"]["changelog"] == {"date": "2026-11-12", "content": "发布 1.2.0"}
        assert data["stage"] == "prod"
        assert data["version_count"] == 2
        assert data["download_url"] == (
            "https://apigw.example.com/backend/skill-marketplace/skills/g_demo_release-check/download/"
        )
        assert data["public_download_url"] == (
            "https://apigw.example.com/backend/skill-marketplace/skills/g_demo_release-check/public-download/"
        )
        assert "created_by" not in data
        assert "updated_time" not in data

    @pytest.mark.parametrize(
        "skill_id, status_code",
        [
            ("g_demo_archived", 404),
            ("g_demo_unknown", 404),
            ("bad", 404),
            ("g_other_hidden", 403),
        ],
    )
    def test_not_visible(self, request_view, skills, skill_id, status_code):
        resp = request_view("GET", "skill_marketplace.skill.retrieve", path_params=_skill_path(skill_id))
        assert resp.status_code == status_code

    def test_inactive_gateway(self, request_view, skills, demo_gateway):
        Gateway.objects.filter(id=demo_gateway.id).update(status=GatewayStatusEnum.INACTIVE.value)
        resp = request_view("GET", "skill_marketplace.skill.retrieve", path_params=_skill_path())
        assert resp.status_code == 404


class TestSkillMarketplaceSkillVersionListApi:
    def test_list(self, request_view, skills):
        resp = request_view("GET", "skill_marketplace.skill.version.list", path_params=_skill_path())
        data = resp.json()["data"]

        assert [(item["version"], item["is_current"]) for item in data] == [("1.2.0", True), ("1.1.0", False)]
        assert data[0]["published_by"] == "admin"


class TestSkillMarketplaceSkillFileListApi:
    def test_current_version(self, request_view, skills):
        resp = request_view("GET", "skill_marketplace.skill.file.list", path_params=_skill_path())
        data = resp.json()["data"]

        assert data["name"] == "release-check"
        assert data["version"] == "1.2.0"
        assert [item["path"] for item in data["files"]] == [
            "SKILL.md",
            "references/how-to-call-apis.md",
            "references/permissions.md",
        ]
        assert "# 发布核对" in data["files"][0]["content"]

    def test_specified_version(self, request_view, skills):
        resp = request_view(
            "GET", "skill_marketplace.skill.version.file.list", path_params=_skill_path(version="1.1.0")
        )
        assert resp.json()["data"]["version"] == "1.1.0"

        resp = request_view(
            "GET", "skill_marketplace.skill.version.file.list", path_params=_skill_path(version="9.9.9")
        )
        assert resp.status_code == 404


class TestSkillMarketplaceSkillDownloadApi:
    def test_download(self, request_view, skills):
        resp = request_view("GET", "skill_marketplace.skill.download", path_params=_skill_path())

        assert resp.status_code == 200
        assert resp["Content-Disposition"] == 'attachment;filename="g_demo_release-check-1.2.0.zip"'
        with zipfile.ZipFile(io.BytesIO(b"".join(resp.streaming_content))) as archive:
            names = archive.namelist()
        assert "release-check/SKILL.md" in names
        assert "release-check/declaration.yaml" not in names
        assert SkillMetadata.objects.get(id=skills.id).download_count == 1

    def test_specified_version(self, request_view, skills):
        resp = request_view(
            "GET", "skill_marketplace.skill.version.download", path_params=_skill_path(version="1.1.0")
        )
        assert resp["Content-Disposition"] == 'attachment;filename="g_demo_release-check-1.1.0.zip"'

    def test_not_found_does_not_count(self, request_view, skills):
        resp = request_view(
            "GET", "skill_marketplace.skill.version.download", path_params=_skill_path(version="9.9.9")
        )
        assert resp.status_code == 404
        assert SkillMetadata.objects.get(id=skills.id).download_count == 0


class TestSkillMarketplaceSkillPublicDownloadApi:
    def _download(self, request_view, skill_id="g_demo_release-check"):
        return request_view(
            "GET",
            "skill_marketplace.skill.public_download",
            path_params=_skill_path(skill_id),
            user=AnonymousUser(),
        )

    def test_download_without_login(self, request_view, skills):
        resp = self._download(request_view)

        assert resp.status_code == 200
        assert resp["Content-Disposition"] == 'attachment;filename="g_demo_release-check-1.2.0.zip"'
        with zipfile.ZipFile(io.BytesIO(b"".join(resp.streaming_content))) as archive:
            names = archive.namelist()
        assert "release-check/SKILL.md" in names
        assert "release-check/declaration.yaml" not in names
        assert SkillMetadata.objects.get(id=skills.id).download_count == 1

    def test_ignores_tenant(self, request_view, skills):
        assert self._download(request_view, "g_other_hidden").status_code == 200

    def test_archived(self, request_view, skills):
        assert self._download(request_view, "g_demo_archived").status_code == 404

    def test_inactive_gateway(self, request_view, skills, demo_gateway):
        Gateway.objects.filter(id=demo_gateway.id).update(status=GatewayStatusEnum.INACTIVE.value)

        assert self._download(request_view).status_code == 404
        assert SkillMetadata.objects.get(id=skills.id).download_count == 0
