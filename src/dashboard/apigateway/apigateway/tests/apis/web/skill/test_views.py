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
import json
import zipfile

import pytest
from ddf import G
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import translation

from apigateway.apps.audit.constants import OpObjectTypeEnum, OpTypeEnum
from apigateway.apps.audit.models import AuditEventLog
from apigateway.apps.skill.constants import SkillStatusEnum
from apigateway.apps.skill.models import SkillMetadata, SkillVersion
from apigateway.biz.gateway import replace_gateway_administrators
from apigateway.core.constants import GatewayStatusEnum
from apigateway.core.models import Gateway
from apigateway.tests.biz.skill.conftest import (
    FIXTURES_DIR,
    build_skill_zip,
    create_skill,
    gateway_skill_data,
    load_declaration_data,
    release_fixture_gateway,
    set_version,
)
from apigateway.tests.conftest import FAKE_USERNAME

pytestmark = pytest.mark.django_db

NAME = "job-plan-run-and-log"
SKILL_ID = f"g_jobv3-cloud_{NAME}"


@pytest.fixture
def gateway() -> Gateway:
    resources_data = json.loads((FIXTURES_DIR / "resources.json").read_text(encoding="utf-8"))
    release_fixture_gateway(resources_data, "jobv3-cloud")
    gateway = Gateway.objects.get(name="jobv3-cloud")
    replace_gateway_administrators(gateway, [FAKE_USERNAME], FAKE_USERNAME)
    return gateway


@pytest.fixture
def data(gateway):
    return gateway_skill_data(load_declaration_data(NAME))


def _upload_file(data) -> SimpleUploadedFile:
    content = build_skill_zip(data).getvalue()
    return SimpleUploadedFile("skill.zip", content, content_type="application/zip")


def _form(data, **kwargs) -> dict:
    form = {
        "display_name": data["display_name"],
        "display_name_en": data.get("display_name_en") or "",
        "description": data["description"],
        "tags": data["tags"],
        "version": data["version"],
        "overwrite": False,
    }
    form.update(kwargs)
    if "file" not in form:
        form["file"] = _upload_file(data)
    return form


def _path(gateway, skill_id=SKILL_ID, **kwargs):
    return {"gateway_id": gateway.id, "skill_id": skill_id, **kwargs}


@pytest.fixture
def upload(request_view, gateway, data):
    def fn(view_name="skill.list_create", path_params=None, **kwargs):
        return request_view(
            "POST",
            view_name,
            path_params=path_params or {"gateway_id": gateway.id},
            gateway=gateway,
            data=_form(data, **kwargs),
            format="multipart",
        )

    return fn


@pytest.fixture
def skill(upload):
    assert upload().status_code == 201
    return SkillMetadata.objects.get(gateway__name="jobv3-cloud", name=NAME)


def _audit_comments(metadata_id):
    return list(
        AuditEventLog.objects.filter(
            op_object_type=OpObjectTypeEnum.SKILL.value, op_object_id=str(metadata_id)
        ).values_list("op_type", "comment")
    )


class TestSkillListCreateApi:
    def test_upload_creates_skill(self, upload, data):
        resp = upload(display_name="发布核对", tags=["作业", "日志"])

        assert resp.status_code == 201
        assert resp.json()["data"] == {"skill_id": SKILL_ID}
        metadata = SkillMetadata.objects.get(gateway__name="jobv3-cloud", name=NAME)
        assert metadata.display_name == "发布核对"
        assert sorted(metadata.tags.values_list("name", flat=True)) == ["作业", "日志"]
        assert metadata.current_version.version == "1.0.0"
        assert _audit_comments(metadata.id) == [(OpTypeEnum.CREATE.value, "创建 Skill")]

    def test_upload_new_version_and_overwrite(self, upload, skill, data):
        resp = upload(version="1.1.0")
        assert resp.status_code == 201
        skill.refresh_from_db()
        assert skill.current_version.version == "1.1.0"

        resp = upload(version="1.0.0")
        assert resp.status_code == 409
        body = resp.json()["error"]
        assert body["code"] == "CONFLICT"
        assert body["data"]["version"] == "1.0.0"
        assert body["data"]["is_current"] is False

        resp = upload(version="1.0.0", overwrite=True)
        assert resp.status_code == 201
        skill.refresh_from_db()
        assert skill.current_version.version == "1.0.0"
        assert SkillVersion.objects.filter(metadata=skill).count() == 2
        assert [comment for _, comment in _audit_comments(skill.id)] == [
            "创建 Skill",
            "发布 Skill 新版本",
            "覆盖 Skill 版本",
        ]

    def test_upload_version_not_newer(self, upload, skill):
        assert upload(version="1.2.0").status_code == 201

        resp = upload(version="1.1.0")

        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "INVALID_ARGUMENT"

    def test_upload_invalid_package(self, request_view, gateway, data):
        data = set_version(data, "1.0.0")
        data["orchestration"]["steps"][0]["uses"] = "bk-cmdb/search_business@prod"

        resp = request_view(
            "POST",
            "skill.list_create",
            path_params={"gateway_id": gateway.id},
            gateway=gateway,
            data=_form(data, file=SimpleUploadedFile("skill.zip", build_skill_zip(data).getvalue())),
            format="multipart",
        )

        assert resp.status_code == 400
        error = resp.json()["error"]
        assert error["code"] == "INVALID_ARGUMENT"
        assert error["data"]["errors"]
        assert set(error["data"]) == {"errors", "warnings"}

    def test_upload_archived(self, upload, skill):
        SkillMetadata.objects.filter(id=skill.id).update(status=SkillStatusEnum.ARCHIVED.value)

        resp = upload(version="1.1.0")

        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "FAILED_PRECONDITION"

    def test_upload_file_too_large(self, upload):
        resp = upload(file=SimpleUploadedFile("skill.zip", b"0" * (2 * 1024 * 1024 + 1)))

        assert resp.status_code == 400

    def test_list(self, request_view, gateway, skill):
        other = G(Gateway, name="other", status=GatewayStatusEnum.ACTIVE.value)
        create_skill("other-skill", gateway=other)
        create_skill("platform-skill")
        archived = create_skill("archived", gateway=gateway, tags=["归档"])
        SkillMetadata.objects.filter(id=archived.id).update(status=SkillStatusEnum.ARCHIVED.value)

        with translation.override("en"):
            resp = request_view("GET", "skill.list_create", path_params={"gateway_id": gateway.id}, gateway=gateway)
        result = resp.json()["data"]

        assert resp.status_code == 200
        assert result["count"] == 2
        item = next(item for item in result["results"] if item["skill_id"] == SKILL_ID)
        assert item["display_name"] == skill.display_name
        assert item["version"] == "1.0.0"

        resp = request_view(
            "GET",
            "skill.list_create",
            path_params={"gateway_id": gateway.id},
            gateway=gateway,
            data={"status": SkillStatusEnum.ARCHIVED.value},
        )
        assert [item["skill_id"] for item in resp.json()["data"]["results"]] == ["g_jobv3-cloud_archived"]

        resp = request_view(
            "GET",
            "skill.list_create",
            path_params={"gateway_id": gateway.id},
            gateway=gateway,
            data={"keyword": "archived"},
        )
        assert [item["skill_id"] for item in resp.json()["data"]["results"]] == ["g_jobv3-cloud_archived"]


class TestSkillTagListApi:
    def test_list(self, request_view, gateway, skill):
        create_skill("platform-skill", tags=["平台"])
        archived = create_skill("archived", gateway=gateway, tags=["归档"])
        SkillMetadata.objects.filter(id=archived.id).update(status=SkillStatusEnum.ARCHIVED.value)

        resp = request_view(
            "GET", "skill.tag.list", path_params={"gateway_id": gateway.id}, gateway=gateway, data={"status": "x"}
        )

        assert resp.status_code == 200
        names = [item["name"] for item in resp.json()["data"]]
        assert "归档" in names
        assert "平台" not in names


class TestSkillPackageCheckApi:
    def test_check(self, request_view, gateway, data, skill):
        resp = request_view(
            "POST",
            "skill.package.check",
            path_params={"gateway_id": gateway.id},
            gateway=gateway,
            data={"file": _upload_file(data), "skill_id": SKILL_ID},
            format="multipart",
        )

        assert resp.status_code == 200
        result = resp.json()["data"]
        assert result["errors"] == []
        assert result["package"]["name"] == NAME
        assert result["existing_skill"]["skill_id"] == SKILL_ID
        assert SkillVersion.objects.filter(metadata=skill).count() == 1

    def test_check_name_mismatch(self, request_view, gateway, data):
        create_skill("another", gateway=gateway)

        resp = request_view(
            "POST",
            "skill.package.check",
            path_params={"gateway_id": gateway.id},
            gateway=gateway,
            data={"file": _upload_file(data), "skill_id": "g_jobv3-cloud_another"},
            format="multipart",
        )

        assert resp.status_code == 200
        assert resp.json()["data"]["errors"]

    def test_check_other_gateway_skill(self, request_view, gateway, data):
        other = G(Gateway, name="other", status=GatewayStatusEnum.ACTIVE.value)
        create_skill("another", gateway=other)

        resp = request_view(
            "POST",
            "skill.package.check",
            path_params={"gateway_id": gateway.id},
            gateway=gateway,
            data={"file": _upload_file(data), "skill_id": "g_other_another"},
            format="multipart",
        )

        assert resp.status_code == 404


class TestSkillRetrieveUpdateDestroyApi:
    def test_retrieve(self, settings, request_view, gateway, skill):
        settings.BK_API_URL_TMPL = "https://bkapi.example.com/api/{api_name}"

        resp = request_view("GET", "skill.retrieve_update_destroy", path_params=_path(gateway), gateway=gateway)

        assert resp.status_code == 200
        result = resp.json()["data"]
        assert result["skill_id"] == SKILL_ID
        assert result["current_version"]["version"] == "1.0.0"
        assert result["stage"] == "prod"
        assert result["version_count"] == 1
        assert result["download_url"] == (
            f"https://bkapi.example.com/api/bk-apigateway/prod/api/v2/open/skills/{SKILL_ID}/download/"
        )

    def test_retrieve_other_gateway(self, request_view, gateway):
        other = G(Gateway, name="other", status=GatewayStatusEnum.ACTIVE.value)
        create_skill("another", gateway=other)

        resp = request_view(
            "GET",
            "skill.retrieve_update_destroy",
            path_params=_path(gateway, skill_id="g_other_another"),
            gateway=gateway,
        )

        assert resp.status_code == 404

    def test_update(self, request_view, gateway, skill):
        resp = request_view(
            "PUT",
            "skill.retrieve_update_destroy",
            path_params=_path(gateway),
            gateway=gateway,
            data={"display_name": "新名称", "display_name_en": "", "description": "新描述", "tags": ["新标签"]},
            format="json",
        )

        assert resp.status_code == 204
        skill.refresh_from_db()
        assert skill.display_name == "新名称"
        assert skill.display_name_en is None
        assert list(skill.tags.values_list("name", flat=True)) == ["新标签"]
        assert SkillVersion.objects.filter(metadata=skill).count() == 1
        assert _audit_comments(skill.id)[-1] == (OpTypeEnum.MODIFY.value, "更新 Skill 基本信息")

    def test_update_archived(self, request_view, gateway, skill):
        SkillMetadata.objects.filter(id=skill.id).update(status=SkillStatusEnum.ARCHIVED.value)

        resp = request_view(
            "PUT",
            "skill.retrieve_update_destroy",
            path_params=_path(gateway),
            gateway=gateway,
            data={"display_name": "新名称", "description": "新描述", "tags": ["新标签"]},
            format="json",
        )

        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "FAILED_PRECONDITION"

    def test_destroy(self, request_view, gateway, skill):
        resp = request_view("DELETE", "skill.retrieve_update_destroy", path_params=_path(gateway), gateway=gateway)
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "FAILED_PRECONDITION"

        SkillMetadata.objects.filter(id=skill.id).update(status=SkillStatusEnum.ARCHIVED.value)
        resp = request_view("DELETE", "skill.retrieve_update_destroy", path_params=_path(gateway), gateway=gateway)

        assert resp.status_code == 204
        assert not SkillMetadata.objects.filter(id=skill.id).exists()
        assert not SkillVersion.objects.filter(metadata_id=skill.id).exists()
        assert _audit_comments(skill.id)[-1] == (OpTypeEnum.DELETE.value, "删除 Skill")


class TestSkillVersionListCreateApi:
    def test_create_and_list(self, request_view, upload, gateway, skill):
        resp = upload("skill.version.list_create", path_params=_path(gateway), version="1.1.0")
        assert resp.status_code == 201
        assert resp.json()["data"] == {"skill_id": SKILL_ID}

        resp = request_view("GET", "skill.version.list_create", path_params=_path(gateway), gateway=gateway)

        assert resp.status_code == 200
        versions = resp.json()["data"]
        assert [(item["version"], item["is_current"]) for item in versions] == [("1.1.0", True), ("1.0.0", False)]

    def test_create_name_mismatch(self, upload, gateway, skill):
        create_skill("another", gateway=gateway)

        resp = upload(
            "skill.version.list_create", path_params=_path(gateway, skill_id="g_jobv3-cloud_another"), version="1.1.0"
        )

        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "INVALID_ARGUMENT"
        assert SkillVersion.objects.filter(metadata=skill).count() == 1

    def test_create_archived(self, upload, gateway, skill):
        SkillMetadata.objects.filter(id=skill.id).update(status=SkillStatusEnum.ARCHIVED.value)

        resp = upload("skill.version.list_create", path_params=_path(gateway), version="1.1.0")

        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "FAILED_PRECONDITION"


class TestSkillCurrentVersionUpdateApi:
    def test_update(self, request_view, upload, gateway, skill):
        assert upload(version="1.1.0").status_code == 201

        resp = request_view(
            "PUT",
            "skill.current_version.update",
            path_params=_path(gateway),
            gateway=gateway,
            data={"version": "1.0.0"},
            format="json",
        )

        assert resp.status_code == 204
        skill.refresh_from_db()
        assert skill.current_version.version == "1.0.0"
        assert _audit_comments(skill.id)[-1] == (OpTypeEnum.MODIFY.value, "切换 Skill 线上版本")

    def test_update_version_not_found(self, request_view, gateway, skill):
        resp = request_view(
            "PUT",
            "skill.current_version.update",
            path_params=_path(gateway),
            gateway=gateway,
            data={"version": "9.9.9"},
            format="json",
        )

        assert resp.status_code == 404


class TestSkillUpdateStatusApi:
    def test_archive_and_restore(self, request_view, gateway, skill):
        for status, comment in [
            (SkillStatusEnum.ARCHIVED.value, "归档 Skill"),
            (SkillStatusEnum.PUBLISHED.value, "恢复 Skill"),
        ]:
            resp = request_view(
                "PUT",
                "skill.status.update",
                path_params=_path(gateway),
                gateway=gateway,
                data={"status": status},
                format="json",
            )

            assert resp.status_code == 204
            skill.refresh_from_db()
            assert skill.status == status
            assert _audit_comments(skill.id)[-1] == (OpTypeEnum.MODIFY.value, comment)


class TestSkillFileAndDownloadApi:
    def test_files(self, request_view, upload, gateway, skill):
        assert upload(version="1.1.0").status_code == 201

        resp = request_view(
            "GET", "skill.version.file.list", path_params=_path(gateway, version="1.0.0"), gateway=gateway
        )

        assert resp.status_code == 200
        result = resp.json()["data"]
        assert result["version"] == "1.0.0"
        paths = [item["path"] for item in result["files"]]
        assert "SKILL.md" in paths
        assert "declaration.yaml" in paths

    def test_download_archived(self, request_view, gateway, skill):
        SkillMetadata.objects.filter(id=skill.id).update(status=SkillStatusEnum.ARCHIVED.value)

        resp = request_view("GET", "skill.download", path_params=_path(gateway), gateway=gateway)

        assert resp.status_code == 200
        assert f"{SKILL_ID}-1.0.0-with-declaration.zip" in resp["Content-Disposition"]
        with zipfile.ZipFile(io.BytesIO(b"".join(resp.streaming_content))) as archive:
            names = archive.namelist()
        assert f"{NAME}/SKILL.md" in names
        assert f"{NAME}/declaration.yaml" in names
        skill.refresh_from_db()
        assert skill.download_count == 1

    def test_download_and_upload_again(self, request_view, upload, gateway, skill):
        """带声明的包原样上传：网关只导入声明，覆盖同一版本"""
        resp = request_view("GET", "skill.download", path_params=_path(gateway), gateway=gateway)
        content = b"".join(resp.streaming_content)

        resp = upload(file=SimpleUploadedFile("skill.zip", content), overwrite=True)

        assert resp.status_code == 201
        skill.refresh_from_db()
        assert skill.current_version.version == "1.0.0"
        assert SkillVersion.objects.filter(metadata=skill).count() == 1

    def test_download_version_not_found(self, request_view, gateway, skill):
        resp = request_view(
            "GET", "skill.version.download", path_params=_path(gateway, version="9.9.9"), gateway=gateway
        )

        assert resp.status_code == 404
