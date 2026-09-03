import hashlib
from pathlib import Path

import pytest
from blue_krill.storages.blobstore.exceptions import ObjectAlreadyExists
from ddf import G

from apigateway.apps.support.constants import SDKDistributorEnum, SDKGenerationStatusEnum
from apigateway.apps.support.models import SDKArtifact, SDKGenerationItem, SDKGenerationTask
from apigateway.biz.sdk.artifacts import build_manifest, create_built_artifact
from apigateway.biz.sdk.exceptions import SDKArtifactConflict
from apigateway.biz.sdk.storage import (
    commit_generic_artifacts,
    delete_incomplete_artifacts,
    generic_prefix,
    manifest_key,
    restore_generic_artifacts,
)
from apigateway.core.models import ResourceVersion

pytestmark = pytest.mark.django_db


class FakeBKRepo:
    def __init__(self):
        self.files = {}
        self.operations = []

    def upload_generic_file(self, filepath, key, allow_overwrite=True):
        self.operations.append(("upload", key, allow_overwrite))
        if key in self.files and not allow_overwrite:
            raise ObjectAlreadyExists("exists")
        self.files[key] = Path(filepath).read_bytes()

    def download_generic_file(self, key, filepath):
        self.operations.append(("download", key))
        Path(filepath).write_bytes(self.files[key])
        return Path(filepath)

    def get_generic_file_metadata(self, key):
        return {"Content-Length": str(len(self.files[key]))} if key in self.files else None

    def delete_generic_file(self, key):
        self.operations.append(("delete", key))
        self.files.pop(key, None)

    def generate_generic_download_url(self, key):
        return f"https://repo/{key}"


@pytest.fixture
def generation_item(fake_gateway, fake_resource_version):
    fake_resource_version.version = "1.2.3"
    fake_resource_version.save(update_fields=["version"])
    task = G(SDKGenerationTask, gateway=fake_gateway, resource_version=fake_resource_version)
    return G(SDKGenerationItem, task=task, language="python", input_fingerprint="fingerprint")


def built_manifest(tmp_path, generation_item, content=b"wheel"):
    path = tmp_path / "demo.whl"
    path.write_bytes(content)
    artifact = create_built_artifact("wheel", path, allowed_roots=(tmp_path,))
    manifest = build_manifest(
        generation_item.task.gateway.name,
        generation_item.task.resource_version.version,
        generation_item.language,
        "1.2.3",
        generation_item.input_fingerprint,
        {"openapi-generator": "7.23.0"},
        [artifact],
    )
    return artifact, manifest


def another_generation_item(generation_item):
    resource_version = G(
        ResourceVersion,
        gateway=generation_item.task.gateway,
        version="1.2.4",
        _data="[]",
    )
    task = G(
        SDKGenerationTask,
        gateway=generation_item.task.gateway,
        resource_version=resource_version,
    )
    return G(
        SDKGenerationItem,
        task=task,
        language=generation_item.language,
        input_fingerprint=generation_item.input_fingerprint,
    )


def test_commit_uploads_artifacts_before_manifest(tmp_path, generation_item):
    artifact, manifest = built_manifest(tmp_path, generation_item)
    bkrepo = FakeBKRepo()

    records = commit_generic_artifacts(generation_item, bkrepo, manifest, [artifact])

    prefix = generic_prefix(
        generation_item.task.gateway.name,
        "python",
        "1.2.3",
        generation_item.input_fingerprint,
        generation_item.id,
    )
    uploaded = [operation[1] for operation in bkrepo.operations if operation[0] == "upload"]
    assert uploaded == [f"{prefix}/demo.whl", manifest_key(prefix)]
    assert all(operation[2] is False for operation in bkrepo.operations if operation[0] == "upload")
    assert {record.status for record in records} == {SDKGenerationStatusEnum.SUCCESS.value}
    assert {record.artifact_type for record in records} == {"wheel", "manifest"}
    assert generation_item.artifacts.filter(filename="manifest.json").exists()
    assert all(record.url.startswith("https://repo/sdks/") for record in records)
    assert "sdk-password" not in " ".join(record.url for record in records)


def test_commit_reuses_matching_manifest_and_recovers_database(tmp_path, generation_item):
    artifact, manifest = built_manifest(tmp_path, generation_item)
    bkrepo = FakeBKRepo()
    commit_generic_artifacts(generation_item, bkrepo, manifest, [artifact])
    SDKArtifact.objects.filter(item=generation_item).delete()
    bkrepo.operations.clear()

    records = commit_generic_artifacts(generation_item, bkrepo, manifest, [artifact])

    assert {record.filename for record in records} == {"demo.whl", "manifest.json"}
    assert not [operation for operation in bkrepo.operations if operation[0] == "upload"]


def test_commit_rejects_different_manifest_at_same_coordinate(tmp_path, generation_item):
    artifact, manifest = built_manifest(tmp_path, generation_item)
    bkrepo = FakeBKRepo()
    commit_generic_artifacts(generation_item, bkrepo, manifest, [artifact])
    different_artifact, different_manifest = built_manifest(tmp_path, generation_item, b"changed")

    with pytest.raises(SDKArtifactConflict, match="different content"):
        commit_generic_artifacts(generation_item, bkrepo, different_manifest, [different_artifact])


def test_incomplete_artifacts_do_not_poison_another_item(tmp_path, generation_item):
    artifact, manifest = built_manifest(tmp_path, generation_item)
    bkrepo = FakeBKRepo()
    original_upload = bkrepo.upload_generic_file

    def fail_manifest(filepath, key, allow_overwrite=True):
        if key.endswith("/manifest.json"):
            raise RuntimeError("manifest upload failed")
        return original_upload(filepath, key, allow_overwrite)

    bkrepo.upload_generic_file = fail_manifest
    with pytest.raises(RuntimeError, match="manifest upload failed"):
        commit_generic_artifacts(generation_item, bkrepo, manifest, [artifact])

    other_item = another_generation_item(generation_item)
    other_artifact, other_manifest = built_manifest(tmp_path, other_item, b"changed")
    bkrepo.upload_generic_file = original_upload

    records = commit_generic_artifacts(other_item, bkrepo, other_manifest, [other_artifact])

    payload = next(record for record in records if record.filename == "demo.whl")
    assert bkrepo.files[payload.remote_key] == b"changed"


def test_cleanup_cannot_delete_another_items_in_flight_upload(tmp_path, generation_item):
    artifact, manifest = built_manifest(tmp_path, generation_item)
    bkrepo = FakeBKRepo()
    commit_generic_artifacts(generation_item, bkrepo, manifest, [artifact])
    bkrepo.files.clear()

    other_item = another_generation_item(generation_item)
    other_artifact, other_manifest = built_manifest(tmp_path, other_item)
    original_upload = bkrepo.upload_generic_file
    cleanup_called = False

    def cleanup_during_payload_upload(filepath, key, allow_overwrite=True):
        nonlocal cleanup_called
        result = original_upload(filepath, key, allow_overwrite)
        if not key.endswith("/manifest.json") and not cleanup_called:
            cleanup_called = True
            delete_incomplete_artifacts(generation_item, bkrepo)
        return result

    bkrepo.upload_generic_file = cleanup_during_payload_upload
    records = commit_generic_artifacts(other_item, bkrepo, other_manifest, [other_artifact])

    payload = next(record for record in records if record.filename == "demo.whl")
    assert cleanup_called is True
    assert bkrepo.files[payload.remote_key] == b"wheel"


def test_restore_verifies_manifest_and_artifacts(tmp_path, generation_item):
    artifact, manifest = built_manifest(tmp_path, generation_item)
    bkrepo = FakeBKRepo()
    commit_generic_artifacts(generation_item, bkrepo, manifest, [artifact])
    destination = tmp_path / "restored"

    restored_manifest, restored = restore_generic_artifacts(generation_item, bkrepo, destination)

    assert restored_manifest.to_json() == manifest.to_json()
    assert restored[0].sha256 == hashlib.sha256(b"wheel").hexdigest()


def test_cleanup_deletes_only_recorded_incomplete_keys(tmp_path, generation_item):
    bkrepo = FakeBKRepo()
    prefix = generic_prefix(
        generation_item.task.gateway.name,
        "python",
        "1.2.3",
        generation_item.input_fingerprint,
        generation_item.id,
    )
    key = f"{prefix}/partial.whl"
    bkrepo.files[key] = b"partial"
    G(
        SDKArtifact,
        item=generation_item,
        distributor=SDKDistributorEnum.BKREPO_GENERIC.value,
        filename="partial.whl",
        remote_key=key,
    )

    assert delete_incomplete_artifacts(generation_item, bkrepo) == 1
    assert key not in bkrepo.files
    assert not generation_item.artifacts.exists()


def test_cleanup_with_lease_guard_does_not_delete_new_worker_artifacts(tmp_path, generation_item):
    generation_item.status = SDKGenerationStatusEnum.RUNNING.value
    generation_item.lease_token = "new-worker"
    generation_item.save(update_fields=["status", "lease_token"])
    bkrepo = FakeBKRepo()
    prefix = generic_prefix(
        generation_item.task.gateway.name,
        "python",
        "1.2.3",
        generation_item.input_fingerprint,
        generation_item.id,
    )
    key = f"{prefix}/partial.whl"
    bkrepo.files[key] = b"partial"
    G(
        SDKArtifact,
        item=generation_item,
        distributor=SDKDistributorEnum.BKREPO_GENERIC.value,
        filename="partial.whl",
        remote_key=key,
    )

    assert delete_incomplete_artifacts(generation_item, bkrepo, expected_lease_token="old-worker") == 0
    assert bkrepo.files[key] == b"partial"
    assert generation_item.artifacts.filter(filename="partial.whl").exists()
