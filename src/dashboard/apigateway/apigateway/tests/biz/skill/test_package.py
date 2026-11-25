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
import datetime
import hashlib
import io
import zipfile

import pytest
import yaml
from ddf import G

from apigateway.apps.skill.constants import SkillTypeEnum
from apigateway.apps.skill.models import SkillMetadata, SkillVersion
from apigateway.biz.skill.constants import SkillReferencePlaceholderEnum
from apigateway.biz.skill.declaration import parse_declaration
from apigateway.biz.skill.package import (
    build_skill_package_files,
    build_skill_package_zip,
    get_skill_package_filename,
    load_references,
    render_declaration_yaml,
    replace_title,
    split_title,
)
from apigateway.biz.skill.uploader import load_declaration_yaml
from apigateway.biz.skill.writer import save_skill_version
from apigateway.core.models import Gateway
from apigateway.tests.biz.skill.conftest import set_version

BODY = "# 执行作业方案\n\n## 输入\n\n正文\n"


def _frontmatter(files) -> dict:
    text = dict(files)["SKILL.md"]
    return yaml.safe_load(text.split("---\n")[1])


@pytest.fixture
def platform_metadata(job_plan_data):
    return save_skill_version(
        parse_declaration(job_plan_data),
        BODY,
        skill_type=SkillTypeEnum.PLATFORM.value,
        gateway=None,
        operator="admin",
    ).metadata


@pytest.fixture
def gateway_metadata(job_plan_data):
    gateway = G(Gateway, name="demo")
    return save_skill_version(
        parse_declaration(job_plan_data),
        BODY,
        skill_type=SkillTypeEnum.GATEWAY.value,
        gateway=gateway,
        operator="alice",
    ).metadata


class TestTitle:
    @pytest.mark.parametrize(
        "body, expected",
        [
            ("# 名称\n\n正文\n", ("名称", "\n正文\n")),
            ("## 输入\n", (None, "## 输入\n")),
            ("# 名称", ("名称", "")),
        ],
    )
    def test_split_title(self, body, expected):
        assert split_title(body) == expected

    def test_replace_title(self):
        assert replace_title("# 旧名\n\n正文\n", "新名") == "# 新名\n\n正文\n"
        assert replace_title("正文\n", "新名") == "正文\n"


class TestLoadReferences:
    def test_placeholders_filled(self, settings):
        settings.BK_API_URL_TMPL = "http://bkapi.example.com/api/{api_name}"
        settings.BK_PAAS3_URL = "http://paas.example.com"

        references = dict(load_references())

        assert sorted(references) == ["references/how-to-call-apis.md", "references/permissions.md"]
        text = "".join(references.values())
        for name in SkillReferencePlaceholderEnum.get_values():
            assert f"{{{{ {name} }}}}" not in text
        assert "http://bkapi.example.com/api/{gateway_name}/<stage><path>" in text
        assert "http://bkapi.example.com/api/bk-sops/prod/get_task_list/2/?limit=5" in text
        assert "http://paas.example.com/developer-center" in text

    def test_settings_not_configured(self, settings):
        settings.BK_API_URL_TMPL = ""
        settings.BK_PAAS3_URL = ""

        text = "".join(content for _, content in load_references())

        assert "{{ gateway_url_template }}" not in text
        assert "网关访问地址" in text
        assert "蓝鲸开发者中心地址" in text


@pytest.mark.django_db
class TestBuildSkillPackageFiles:
    def test_platform(self, platform_metadata):
        version = platform_metadata.current_version
        files = build_skill_package_files(platform_metadata, version)

        assert [path for path, _ in files] == [
            "SKILL.md",
            "references/how-to-call-apis.md",
            "references/permissions.md",
        ]
        data = _frontmatter(files)
        assert tuple(data) == ("name", "description", "display_name", "display_name_en", "metadata")
        assert data["name"] == platform_metadata.name
        assert data["metadata"]["type"] == "platform"
        assert data["metadata"]["author"] == "apigateway"
        assert data["metadata"]["source"] == "apigateway"
        assert data["metadata"]["version"] == version.version
        expected_datetime = version.created_time.astimezone(datetime.timezone.utc).replace(microsecond=0)
        assert data["metadata"]["datetime"] == expected_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")
        body = dict(files)["SKILL.md"].split("---\n", 2)[2].lstrip("\n")
        assert body == BODY.replace("执行作业方案", platform_metadata.display_name)
        assert "bk-apigw-skill-id" not in dict(files)["SKILL.md"]

    def test_gateway_author_is_version_creator(self, gateway_metadata):
        files = build_skill_package_files(gateway_metadata, gateway_metadata.current_version)

        data = _frontmatter(files)
        assert data["metadata"]["type"] == "gateway"
        assert data["metadata"]["author"] == "alice"

    def test_basic_info_changes(self, platform_metadata):
        platform_metadata.display_name = "新名称"
        platform_metadata.display_name_en = None
        platform_metadata.description = "新的描述"
        platform_metadata.save()

        files = build_skill_package_files(platform_metadata, platform_metadata.current_version)

        data = _frontmatter(files)
        assert (data["display_name"], data["display_name_en"], data["description"]) == ("新名称", "", "新的描述")
        assert "\n# 新名称\n" in dict(files)["SKILL.md"]
        assert platform_metadata.current_version.artifact["SKILL.md"] == BODY

    def test_specified_version(self, platform_metadata, job_plan_data):
        old_version = platform_metadata.current_version
        save_skill_version(
            parse_declaration(set_version(job_plan_data, "9.0.0")),
            BODY,
            skill_type=SkillTypeEnum.PLATFORM.value,
            gateway=None,
            operator="admin",
        )
        platform_metadata.refresh_from_db()

        files = build_skill_package_files(platform_metadata, old_version)

        assert _frontmatter(files)["metadata"]["version"] == old_version.version

    def test_with_declaration(self, gateway_metadata):
        version = gateway_metadata.current_version
        files = build_skill_package_files(gateway_metadata, version, with_declaration=True)

        assert [path for path, _ in files][-1] == "declaration.yaml"
        assert dict(files)["declaration.yaml"] == render_declaration_yaml(gateway_metadata, version)
        plain = build_skill_package_files(gateway_metadata, version)
        assert "declaration.yaml" not in dict(plain)


@pytest.mark.django_db
class TestRenderDeclarationYaml:
    def test_round_trip(self, gateway_metadata, job_plan_data):
        """经上传的 YAML 读取和声明校验后，和写库时的声明一致"""
        version = gateway_metadata.current_version
        text = render_declaration_yaml(gateway_metadata, version)

        declaration = parse_declaration(load_declaration_yaml(text))
        expected = parse_declaration(job_plan_data)
        assert declaration.name == gateway_metadata.name
        assert declaration.display_name == expected.display_name
        assert declaration.display_name_en == expected.display_name_en
        assert declaration.description == expected.description
        assert declaration.tags == sorted(expected.normalized_tags)
        assert declaration.changelog_data() == version.changelog
        assert declaration.orchestration_data() == version.orchestration
        assert list(yaml.safe_load(text)) == [
            "name",
            "display_name",
            "display_name_en",
            "description",
            "tags",
            "version",
            "changelog",
            "orchestration",
        ]

    def test_current_basic_info(self, gateway_metadata):
        gateway_metadata.display_name = "新名称"
        gateway_metadata.display_name_en = None
        gateway_metadata.save()

        data = yaml.safe_load(render_declaration_yaml(gateway_metadata, gateway_metadata.current_version))

        assert data["display_name"] == "新名称"
        assert "display_name_en" not in data

    def test_no_alias_and_block_strings(self, gateway_metadata):
        version = gateway_metadata.current_version
        step = version.orchestration["steps"][0]
        version.orchestration["steps"].append({**step, "id": "run-plan-again"})
        version.orchestration["steps"][-1]["with"] = step["with"]

        text = render_declaration_yaml(gateway_metadata, version)

        assert "&id" not in text
        assert "*id" not in text
        assert "not_for: |" in text

    def test_deterministic(self, gateway_metadata):
        first = render_declaration_yaml(gateway_metadata, gateway_metadata.current_version)
        metadata = SkillMetadata.objects.get(id=gateway_metadata.id)

        assert render_declaration_yaml(metadata, metadata.current_version) == first


@pytest.mark.django_db
class TestBuildSkillPackageZip:
    def test_structure(self, platform_metadata):
        version = platform_metadata.current_version
        content = build_skill_package_zip(platform_metadata, version)

        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            names = archive.namelist()
            assert names == [
                f"{platform_metadata.name}/SKILL.md",
                f"{platform_metadata.name}/references/how-to-call-apis.md",
                f"{platform_metadata.name}/references/permissions.md",
            ]
            files = build_skill_package_files(platform_metadata, version)
            for path, text in files:
                assert archive.read(f"{platform_metadata.name}/{path}").decode("utf-8") == text

    def test_with_declaration(self, gateway_metadata):
        content = build_skill_package_zip(gateway_metadata, gateway_metadata.current_version, with_declaration=True)

        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            assert f"{gateway_metadata.name}/declaration.yaml" in archive.namelist()

    @pytest.mark.parametrize("with_declaration", [False, True])
    def test_deterministic(self, gateway_metadata, with_declaration):
        first = build_skill_package_zip(
            gateway_metadata, gateway_metadata.current_version, with_declaration=with_declaration
        )
        metadata = SkillMetadata.objects.get(id=gateway_metadata.id)
        second = build_skill_package_zip(metadata, metadata.current_version, with_declaration=with_declaration)

        assert hashlib.sha256(first).hexdigest() == hashlib.sha256(second).hexdigest()

    def test_filename(self, gateway_metadata):
        version = SkillVersion.objects.get(id=gateway_metadata.current_version_id)

        assert get_skill_package_filename(gateway_metadata, version) == f"g_demo_{gateway_metadata.name}-1.0.0.zip"
        assert (
            get_skill_package_filename(gateway_metadata, version, with_declaration=True)
            == f"g_demo_{gateway_metadata.name}-1.0.0-with-declaration.zip"
        )
