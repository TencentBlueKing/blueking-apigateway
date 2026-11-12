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
import copy
import json
import shutil
from io import StringIO

import pytest
import yaml
from django.core.management import call_command

from apigateway.apps.skill.models import SkillMetadata
from apigateway.biz.skill import SKILL_DECLARATIONS_DIR
from apigateway.tests.biz.skill.conftest import (
    DECLARATIONS_DIR,
    FIXTURES_DIR,
    release_fixture_gateway,
)

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def te_edition(settings):
    """fixture 资源和声明用的是内部名 jobv3-cloud"""
    settings.EDITION_GATEWAY_NAMES = {"jobv3-cloud": "jobv3-cloud", "bk-job": "jobv3-cloud"}


def _call(*args) -> str:
    out = StringIO()
    call_command("sync_platform_skills", *args, stdout=out, no_color=True)
    return out.getvalue()


@pytest.fixture
def declarations_dir(tmp_path):
    directory = tmp_path / "declarations"
    directory.mkdir()
    source = DECLARATIONS_DIR / "job-plan-run-and-log.yaml"
    shutil.copy(source, directory)
    missing = copy.deepcopy(yaml.safe_load(source.read_text(encoding="utf-8")))
    missing["name"] = "job-plan-missing"
    missing["orchestration"]["steps"][0]["uses"] = "jobv3-cloud/not_released@prod"
    (directory / "job-plan-missing.yaml").write_text(
        yaml.safe_dump(missing, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    (directory / "broken.yaml").write_text("name: [\n", encoding="utf-8")
    return directory


@pytest.fixture
def published_resources():
    resources_data = json.loads((FIXTURES_DIR / "resources.json").read_text(encoding="utf-8"))
    release_fixture_gateway(resources_data, "jobv3-cloud")


class TestSyncPlatformSkillsCommand:
    def test_sync(self, declarations_dir, published_resources):
        output = _call("--dir", str(declarations_dir))

        lines = output.splitlines()
        assert lines[0].startswith("[跳过] broken：")
        assert lines[1].startswith("[跳过] job-plan-missing：")
        assert lines[2] == "[新建] job-plan-run-and-log"
        assert "total 3：新建 1，跳过 2" in output
        assert "changed metadata ids" not in output
        assert SkillMetadata.objects.filter(name="job-plan-run-and-log").exists()

    def test_dry_run_and_name(self, declarations_dir, published_resources):
        output = _call(
            "--dir",
            str(declarations_dir),
            "--name",
            "job-plan-run-and-log",
            "--dry-run",
        )

        assert output.splitlines() == [
            "[新建] job-plan-run-and-log：dry-run，未写库",
            "dry-run total 1：新建 1",
        ]
        assert not SkillMetadata.objects.exists()

    def test_empty_dir(self, tmp_path):
        assert _call("--dir", str(tmp_path)) == f"No skill declarations found in {tmp_path}, skip.\n"
        assert _call("--dir", str(tmp_path / "missing")).startswith("No skill declarations found")

    def test_default_dir_skips_without_released_resources(self):
        names = sorted(path.stem for path in SKILL_DECLARATIONS_DIR.glob("*.yaml"))
        assert names == [
            "devops-pipeline-app-build-detail",
            "devops-pipeline-build-artifact-url",
            "job-plan-run-and-log",
            "sops-create-and-start",
            "sops-task-list-and-status",
        ]

        output = _call()

        lines = [line.split("：", 1)[0] for line in output.splitlines() if line.startswith("[")]
        assert lines == [f"[跳过] {name}" for name in names]
        assert "total 5：跳过 5" in output
        assert "changed metadata ids" not in output
        assert not SkillMetadata.objects.exists()

    def test_name_not_found(self, declarations_dir):
        output = _call(
            "--dir",
            str(declarations_dir),
            "--name",
            "missing-skill",
        )

        assert output == f"No skill declaration named missing-skill in {declarations_dir}.\n"
