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

from apigateway.apps.skill.constants import SkillStatusEnum
from apigateway.apps.skill.models import SkillMetadata, SkillVersion
from apigateway.biz.skill.uploader import (
    SkillPackageInvalidError,
    SkillUploadForm,
    check_skill_package,
    load_declaration_yaml,
    publish_gateway_skill,
    split_field_message,
)
from apigateway.biz.skill.writer import SkillArchivedError, SkillVersionExistsError, SkillVersionNotNewerError
from apigateway.core.models import Gateway
from apigateway.tests.biz.skill.conftest import (
    build_skill_zip,
    gateway_skill_data,
    release_fixture_gateway,
    set_version,
)

pytestmark = pytest.mark.django_db

NAME = "job-plan-run-and-log"
SKILL_FILE = f"{NAME}/SKILL.md"
DECLARATION_FILE = f"{NAME}/declaration.yaml"
IGNORED_HINT = "只导入 declaration.yaml，以下文件不导入："


@pytest.fixture
def gateway(resources_data) -> Gateway:
    release_fixture_gateway(resources_data, "jobv3-cloud")
    return Gateway.objects.get(name="jobv3-cloud")


@pytest.fixture
def data(job_plan_data):
    return gateway_skill_data(job_plan_data)


def _form(data, **kwargs) -> SkillUploadForm:
    params = {
        "display_name": data["display_name"],
        "display_name_en": data.get("display_name_en"),
        "description": data["description"],
        "tags": data["tags"],
        "version": data["version"],
    }
    params.update(kwargs)
    return SkillUploadForm(**params)


def _check(gateway, fileobj, **kwargs):
    return check_skill_package(gateway, fileobj, **kwargs)


def _errors(result):
    return [(item.file, item.field, item.message) for item in result.errors]


def _publish_errors(gateway, fileobj, form, **kwargs):
    with pytest.raises(SkillPackageInvalidError) as err:
        publish_gateway_skill(gateway, fileobj, form, operator="admin", **kwargs)
    return [(item.file, item.field, item.message) for item in err.value.errors]


class TestHelpers:
    @pytest.mark.parametrize(
        "text, expected",
        [
            ("version: 版本号不合规", ("version", "版本号不合规")),
            ("run-plan：参数 foo 不在资源定义中", ("run-plan", "参数 foo 不在资源定义中")),
            ("orchestration.steps[0].with.id: 未知字段", ("orchestration.steps[0].with.id", "未知字段")),
            ("资源不可编排", (None, "资源不可编排")),
        ],
    )
    def test_split_field_message(self, text, expected):
        assert split_field_message(text) == expected

    def test_load_declaration_yaml_rejects_alias(self):
        with pytest.raises(ValueError, match="锚点和别名"):
            load_declaration_yaml("a: &x [1, 2]\nb: *x\n")
        with pytest.raises(ValueError, match="键值对"):
            load_declaration_yaml("- 1\n")
        assert load_declaration_yaml("name: demo\n") == {"name": "demo"}


class TestCheckSkillPackage:
    def test_ok(self, gateway, data):
        result = _check(gateway, build_skill_zip(data))

        assert result.errors == []
        assert not any(item.message.startswith(IGNORED_HINT) for item in result.warnings)
        assert result.package["name"] == NAME
        assert result.package["version"] == "1.0.0"
        assert result.package["stage"] == "prod"
        assert result.package["apis"][0] == {"gateway_name": "jobv3-cloud", "resource_name": "execute_job_plan"}
        assert result.existing_skill is None
        assert result.basic_info_diffs == []
        assert not SkillMetadata.objects.exists()

    def test_archive_error(self, gateway, data):
        result = _check(
            gateway, build_skill_zip(data, extra_files={"SKILL.md": "# 标题\n"}, exclude=("declaration.yaml",))
        )

        assert _errors(result) == [(DECLARATION_FILE, None, "缺少文件，网关按 declaration.yaml 校验并生成 SKILL.md")]
        assert result.package is None

    def test_root_and_name_mismatch(self, gateway, data):
        result = _check(gateway, build_skill_zip(data, root="other"))
        assert [item.field for item in result.errors] == ["name"]
        assert "顶层目录名 other" in result.errors[0].message

        result = _check(gateway, build_skill_zip(data), skill_name="release-check")
        assert [item.message for item in result.errors] == [
            f"包里的 name {NAME} 与要更新的 Skill release-check 不一致"
        ]

    def test_declaration_alias(self, gateway, data):
        result = _check(gateway, build_skill_zip(data, declaration_text="a: &x 1\nb: *x\n"))
        assert result.errors[0].file == DECLARATION_FILE
        assert "锚点和别名" in result.errors[0].message

    def test_declaration_field_error(self, gateway, data):
        data["version"] = "1.0"
        result = _check(gateway, build_skill_zip(data))
        assert [(item.file, item.field) for item in result.errors] == [(DECLARATION_FILE, "version")]

    def test_other_gateway(self, gateway, data):
        data["orchestration"]["steps"][1]["uses"] = "bk-sops/get_task_status@prod"
        result = _check(gateway, build_skill_zip(data))

        assert _errors(result) == [
            (
                DECLARATION_FILE,
                "orchestration.steps[1].uses",
                "只能调用当前网关 jobv3-cloud 的接口：bk-sops/get_task_status@prod",
            )
        ]

    def test_multiple_stages(self, gateway, data):
        data["orchestration"]["steps"][1]["uses"] = "jobv3-cloud/get_job_instance_status@test"
        result = _check(gateway, build_skill_zip(data))
        assert _errors(result) == [(DECLARATION_FILE, "orchestration.steps", "所有步骤应使用同一个环境：prod, test")]

    def test_missing_resource(self, gateway, data):
        data["orchestration"]["steps"][1]["uses"] = "jobv3-cloud/not_released@prod"
        result = _check(gateway, build_skill_zip(data))

        assert len(result.errors) == 1
        assert "jobv3-cloud.not_released（环境 prod）不可编排" in result.errors[0].message

    def test_validation_error(self, gateway, data):
        data["orchestration"]["steps"][0]["with"]["foo"] = 1
        result = _check(gateway, build_skill_zip(data))
        assert _errors(result) == [(DECLARATION_FILE, "run-plan", "参数 foo 不在资源定义中")]

    def test_ignored_files_warning(self, gateway, data):
        """包里的 SKILL.md、references 不读取：过期的 SKILL.md 不报错，给一条 warning 列出不导入的文件"""
        extra = {"SKILL.md": "---\nname: old\n---\n# 旧正文\n", "references/permissions.md": "权限\n"}
        result = _check(gateway, build_skill_zip(data, extra_files=extra))

        assert result.errors == []
        ignored = [item for item in result.warnings if item.message.startswith(IGNORED_HINT)]
        assert [(item.file, item.field, item.message) for item in ignored] == [
            (None, None, f"{IGNORED_HINT}{SKILL_FILE}、{NAME}/references/permissions.md")
        ]

    def test_ignored_files_warning_truncated(self, gateway, data):
        extra = {f"assets/{index:02d}.txt": "" for index in range(12)}
        result = _check(gateway, build_skill_zip(data, extra_files=extra))

        ignored = [item.message for item in result.warnings if item.message.startswith(IGNORED_HINT)]
        listed = "、".join(f"{NAME}/assets/{index:02d}.txt" for index in range(10))
        assert ignored == [f"{IGNORED_HINT}{listed} 等 12 个文件"]

    def test_existing_skill(self, gateway, data):
        publish_gateway_skill(gateway, build_skill_zip(data), _form(data), operator="admin")
        set_version(data, "1.1.0")
        publish_gateway_skill(gateway, build_skill_zip(data), _form(data), operator="admin")
        metadata = SkillMetadata.objects.get(name=NAME)
        metadata.current_version = metadata.versions.get(version="1.0.0")
        metadata.save(update_fields=["current_version"])

        data.update(description="新的描述", tags=[*data["tags"], "新标签"])
        set_version(data, "1.0.0")
        result = _check(gateway, build_skill_zip(data), skill_name=NAME)

        assert result.errors == []
        assert result.existing_skill == {
            "skill_id": f"g_jobv3-cloud_{NAME}",
            "current_version": "1.0.0",
            "latest_version": "1.1.0",
            "status": SkillStatusEnum.PUBLISHED.value,
        }
        assert result.basic_info_diffs == ["description", "tags"]


class TestPublishGatewaySkill:
    def test_create_with_form_values(self, gateway, data):
        form = _form(data, display_name="发布核对", display_name_en=None, tags=["只读"], version="1.2.0")
        saved = publish_gateway_skill(gateway, build_skill_zip(data), form, operator="alice")

        metadata = saved.metadata
        assert saved.created is True
        assert metadata.code == f"g_jobv3-cloud_{NAME}"
        assert metadata.display_name == "发布核对"
        assert metadata.display_name_en is None
        assert [tag.name for tag in metadata.tags.all()] == ["只读"]
        assert saved.version.version == "1.2.0"
        assert saved.version.created_by == "alice"
        assert saved.version.changelog["content"] == "发布 1.0.0"
        assert saved.version.artifact["SKILL.md"].startswith("# 发布核对\n")
        assert list(saved.version.relations.values_list("resource_name", flat=True)) == [
            "execute_job_plan",
            "get_job_instance_status",
            "batch_get_job_instance_ip_log",
        ]

    def test_stale_skill_md_ignored(self, gateway, data):
        extra = {"SKILL.md": "# 手改的正文\n"}
        saved = publish_gateway_skill(gateway, build_skill_zip(data, extra_files=extra), _form(data), operator="admin")

        body = saved.version.artifact["SKILL.md"]
        assert body.startswith(f"# {data['display_name']}\n")
        assert "手改的正文" not in body

    def test_invalid_form_value(self, gateway, data):
        errors = _publish_errors(gateway, build_skill_zip(data), _form(data, version="v1"))
        assert [(file, field) for file, field, _ in errors] == [(None, "version")]

    def test_skill_name_mismatch(self, gateway, data):
        errors = _publish_errors(gateway, build_skill_zip(data), _form(data), skill_name="release-check")
        assert [field for _, field, _ in errors] == ["name"]

    def test_version_rules(self, gateway, data):
        publish_gateway_skill(gateway, build_skill_zip(data), _form(data), operator="admin")
        publish_gateway_skill(gateway, build_skill_zip(data), _form(data, version="1.2.0"), operator="admin")

        with pytest.raises(SkillVersionNotNewerError):
            publish_gateway_skill(gateway, build_skill_zip(data), _form(data, version="1.1.0"), operator="admin")
        with pytest.raises(SkillVersionExistsError) as err:
            publish_gateway_skill(gateway, build_skill_zip(data), _form(data), operator="admin")
        assert err.value.version.version == "1.0.0"

    def test_package_error_wins_over_existing_version(self, gateway, data):
        publish_gateway_skill(gateway, build_skill_zip(data), _form(data), operator="admin")
        errors = _publish_errors(
            gateway,
            build_skill_zip(data, extra_files={"SKILL.md": "# 标题\n"}, exclude=("declaration.yaml",)),
            _form(data),
        )
        assert errors == [(DECLARATION_FILE, None, "缺少文件，网关按 declaration.yaml 校验并生成 SKILL.md")]

    def test_overwrite(self, gateway, data):
        first = publish_gateway_skill(gateway, build_skill_zip(data), _form(data), operator="alice")
        publish_gateway_skill(gateway, build_skill_zip(data), _form(data, version="1.1.0"), operator="alice")

        saved = publish_gateway_skill(gateway, build_skill_zip(data), _form(data), operator="bob", overwrite=True)

        version = SkillVersion.objects.get(id=first.version.id)
        assert saved.created is False
        assert saved.version.id == version.id
        assert version.created_by == "alice"
        assert version.created_time == first.version.created_time
        assert version.updated_by == "bob"
        metadata = SkillMetadata.objects.get(id=first.metadata.id)
        assert metadata.current_version_id == version.id
        assert metadata.updated_by == "bob"

    def test_archived(self, gateway, data):
        saved = publish_gateway_skill(gateway, build_skill_zip(data), _form(data), operator="admin")
        SkillMetadata.objects.filter(id=saved.metadata.id).update(status=SkillStatusEnum.ARCHIVED.value)

        with pytest.raises(SkillArchivedError):
            publish_gateway_skill(gateway, build_skill_zip(data), _form(data, version="2.0.0"), operator="admin")
