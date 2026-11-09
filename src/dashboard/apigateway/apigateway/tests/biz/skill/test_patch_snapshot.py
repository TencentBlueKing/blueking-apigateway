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
import yaml

from apigateway.biz.skill.patch_snapshot import PatchSnapshotStore, SkillSnapshotError
from apigateway.biz.skill.resource_definition import ResourceParam, ResponseField

pytestmark = pytest.mark.no_meta_schema

SNAPSHOT = {
    "gateway": "bk-sops",
    "resources": [
        {
            "resource": "get_task_status",
            "reason": "网关未导入 schema",
            "source_date": "2026-10-29",
            "source": "标准运维 API 文档",
            "params": [{"name": "task_id", "in": "path", "type": "integer", "required": True}],
            "responses": [{"field": "data.state", "type": "string", "description": "任务状态"}],
        }
    ],
}


@pytest.fixture
def write_snapshot(tmp_path):
    def write(data, gateway="bk-sops"):
        (tmp_path / f"{gateway}.yaml").write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
        return PatchSnapshotStore(tmp_path)

    return write


class TestPatchSnapshotStore:
    def test_get(self, write_snapshot):
        snapshot = write_snapshot(SNAPSHOT).get("bk-sops", "get_task_status")

        assert snapshot.to_params() == [ResourceParam(name="task_id", location="path", type="integer", required=True)]
        assert snapshot.to_responses() == [ResponseField(field="data.state", type="string", description="任务状态")]

    def test_not_found(self, write_snapshot):
        store = write_snapshot(SNAPSHOT)

        assert store.get("bk-sops", "get_task_list") is None
        assert store.get("bk-job", "get_job") is None

    def test_gateway_mismatch(self, write_snapshot):
        store = write_snapshot(SNAPSHOT, gateway="bk-job")

        with pytest.raises(SkillSnapshotError, match="gateway 应为 bk-job"):
            store.get("bk-job", "get_task_status")

    @pytest.mark.parametrize(
        "patch",
        [
            {"reason": " "},
            {"source": ""},
            {"extra": 1},
            {"params": [{"name": "task_id", "location": "path"}]},
        ],
    )
    def test_invalid(self, write_snapshot, patch):
        data = {"gateway": "bk-sops", "resources": [{**SNAPSHOT["resources"][0], **patch}]}

        with pytest.raises(SkillSnapshotError):
            write_snapshot(data).get("bk-sops", "get_task_status")

    def test_invalid_yaml(self, tmp_path):
        (tmp_path / "bk-sops.yaml").write_text("gateway: [\n", encoding="utf-8")

        with pytest.raises(SkillSnapshotError):
            PatchSnapshotStore(tmp_path).get("bk-sops", "get_task_status")
