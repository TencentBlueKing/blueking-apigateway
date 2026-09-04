"""Manifest-last BKRepo Generic persistence for generated SDK artifacts."""

from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

from blue_krill.storages.blobstore.exceptions import ObjectAlreadyExists
from django.db import transaction

from apigateway.apps.support.constants import (
    SDKArtifactStatusEnum,
    SDKArtifactTypeEnum,
    SDKDistributorEnum,
    SDKGenerationItemStatusEnum,
)
from apigateway.apps.support.models import SDKArtifact, SDKGenerationItem
from apigateway.biz.sdk.artifacts import (
    ArtifactManifest,
    BuiltArtifact,
    ManifestFile,
    create_built_artifact,
)
from apigateway.biz.sdk.exceptions import SDKArtifactConflict

if TYPE_CHECKING:
    from datetime import datetime

    from apigateway.components.bkrepo import BKRepoComponent


def generic_prefix(gateway_name: str, language: str, version: str, fingerprint: str, item_id: int) -> str:
    segments = (gateway_name, language, version, fingerprint, str(item_id))
    if any(not segment or "/" in segment or segment in {".", ".."} for segment in segments):
        raise ValueError("invalid SDK Generic key segment")
    return f"sdks/{gateway_name}/{language}/{version}/{fingerprint}/{item_id}"


def manifest_key(prefix: str) -> str:
    return f"{prefix}/manifest.json"


def _prefix_for_item(item: SDKGenerationItem) -> str:
    return generic_prefix(
        item.task.gateway.name,
        item.language,
        item.task.resource_version.version,
        item.input_fingerprint,
        item.id,
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_manifest(path: Path) -> ArtifactManifest:
    payload = json.loads(path.read_text())
    return ArtifactManifest(
        gateway_name=payload["gateway_name"],
        resource_version=payload["resource_version"],
        language=payload["language"],
        package_version=payload["package_version"],
        input_fingerprint=payload["input_fingerprint"],
        tool_versions=payload["tool_versions"],
        files=tuple(ManifestFile(**file) for file in payload["files"]),
    )


def _record_artifact(
    item: SDKGenerationItem,
    *,
    artifact_type: str,
    filename: str,
    remote_key: str,
    size: int,
    sha256: str,
    package_version: str,
) -> SDKArtifact:
    artifact, _ = SDKArtifact.objects.update_or_create(
        item=item,
        distributor=SDKDistributorEnum.BKREPO_GENERIC.value,
        filename=filename,
        defaults={
            "artifact_type": artifact_type,
            "remote_key": remote_key,
            "size": size,
            "sha256": sha256,
            "original_version": item.task.resource_version.version,
            "package_version": package_version,
            "status": SDKArtifactStatusEnum.RUNNING.value,
        },
    )
    return artifact


def _verify_or_upload(
    bkrepo: BKRepoComponent,
    path: Path,
    key: str,
    expected_sha256: str,
) -> None:
    try:
        bkrepo.upload_generic_file(str(path), key, allow_overwrite=False)
        return
    except ObjectAlreadyExists:
        pass

    with tempfile.TemporaryDirectory(prefix="sdk-existing-") as directory:
        existing = Path(directory) / path.name
        bkrepo.download_generic_file(key, str(existing))
        if _sha256(existing) != expected_sha256:
            raise SDKArtifactConflict(f"remote SDK artifact has different content: {key}")


def commit_generic_artifacts(
    item: SDKGenerationItem,
    bkrepo: BKRepoComponent,
    manifest: ArtifactManifest,
    artifacts: list[BuiltArtifact],
) -> list[SDKArtifact]:
    prefix = _prefix_for_item(item)
    committed_key = manifest_key(prefix)
    if bkrepo.get_generic_file_metadata(committed_key) is not None:
        with tempfile.TemporaryDirectory(prefix="sdk-restore-") as directory:
            restored_manifest, _ = restore_generic_artifacts(item, bkrepo, Path(directory))
            if restored_manifest.to_json() != manifest.to_json():
                raise SDKArtifactConflict("SDK manifest location already contains different content")
        return list(item.artifacts.filter(distributor=SDKDistributorEnum.BKREPO_GENERIC.value))

    by_name = {artifact.filename: artifact for artifact in artifacts}
    if set(by_name) != {file.filename for file in manifest.files}:
        raise ValueError("SDK manifest files do not match built artifacts")

    records: list[SDKArtifact] = []
    for file in manifest.files:
        artifact = by_name[file.filename]
        if (artifact.size, artifact.sha256) != (file.size, file.sha256):
            raise ValueError(f"SDK manifest metadata mismatch: {file.filename}")
        if (artifact.path.stat().st_size, _sha256(artifact.path)) != (file.size, file.sha256):
            raise ValueError(f"SDK artifact changed after its manifest was built: {file.filename}")
        key = f"{prefix}/{file.filename}"
        record = _record_artifact(
            item,
            artifact_type=file.artifact_type,
            filename=file.filename,
            remote_key=key,
            size=file.size,
            sha256=file.sha256,
            package_version=manifest.package_version,
        )
        _verify_or_upload(bkrepo, artifact.path, key, file.sha256)
        record.status = SDKArtifactStatusEnum.SUCCESS.value
        record.url = bkrepo.generate_generic_download_url(key)
        record.save(update_fields=["status", "url", "updated_time"])
        records.append(record)

    manifest_bytes = manifest.to_json().encode()
    manifest_sha256 = hashlib.sha256(manifest_bytes).hexdigest()
    with tempfile.TemporaryDirectory(prefix="sdk-manifest-") as directory:
        path = Path(directory) / "manifest.json"
        path.write_bytes(manifest_bytes)
        record = _record_artifact(
            item,
            artifact_type=SDKArtifactTypeEnum.MANIFEST.value,
            filename=path.name,
            remote_key=committed_key,
            size=len(manifest_bytes),
            sha256=manifest_sha256,
            package_version=manifest.package_version,
        )
        _verify_or_upload(bkrepo, path, committed_key, manifest_sha256)
        record.status = SDKArtifactStatusEnum.SUCCESS.value
        record.url = bkrepo.generate_generic_download_url(committed_key)
        record.save(update_fields=["status", "url", "updated_time"])
        records.append(record)
    return records


def restore_generic_artifacts(
    item: SDKGenerationItem,
    bkrepo: BKRepoComponent,
    destination: Path,
) -> tuple[ArtifactManifest, list[BuiltArtifact]]:
    destination.mkdir(parents=True, exist_ok=True)
    prefix = _prefix_for_item(item)
    local_manifest = destination / "manifest.json"
    bkrepo.download_generic_file(manifest_key(prefix), str(local_manifest))
    manifest = _load_manifest(local_manifest)
    if (
        manifest.gateway_name != item.task.gateway.name
        or manifest.resource_version != item.task.resource_version.version
        or manifest.language != item.language
        or manifest.input_fingerprint != item.input_fingerprint
    ):
        raise SDKArtifactConflict("SDK manifest does not match the generation item")

    manifest_bytes = local_manifest.read_bytes()
    SDKArtifact.objects.update_or_create(
        item=item,
        distributor=SDKDistributorEnum.BKREPO_GENERIC.value,
        filename="manifest.json",
        defaults={
            "artifact_type": SDKArtifactTypeEnum.MANIFEST.value,
            "remote_key": manifest_key(prefix),
            "size": len(manifest_bytes),
            "sha256": hashlib.sha256(manifest_bytes).hexdigest(),
            "original_version": item.task.resource_version.version,
            "package_version": manifest.package_version,
            "status": SDKArtifactStatusEnum.SUCCESS.value,
            "url": bkrepo.generate_generic_download_url(manifest_key(prefix)),
        },
    )

    artifacts = []
    for file in manifest.files:
        path = destination / file.filename
        if path.parent != destination or path.name != file.filename:
            raise SDKArtifactConflict("SDK manifest contains an unsafe filename")
        bkrepo.download_generic_file(f"{prefix}/{file.filename}", str(path))
        artifact = create_built_artifact(file.artifact_type, path, allowed_roots=(destination,))
        if (artifact.size, artifact.sha256) != (file.size, file.sha256):
            raise SDKArtifactConflict(f"restored SDK artifact checksum mismatch: {file.filename}")
        artifacts.append(artifact)

        SDKArtifact.objects.update_or_create(
            item=item,
            distributor=SDKDistributorEnum.BKREPO_GENERIC.value,
            filename=file.filename,
            defaults={
                "artifact_type": file.artifact_type,
                "remote_key": f"{prefix}/{file.filename}",
                "size": file.size,
                "sha256": file.sha256,
                "original_version": item.task.resource_version.version,
                "package_version": manifest.package_version,
                "status": SDKArtifactStatusEnum.SUCCESS.value,
                "url": bkrepo.generate_generic_download_url(f"{prefix}/{file.filename}"),
            },
        )
    return manifest, artifacts


@transaction.atomic
def delete_incomplete_artifacts(
    item: SDKGenerationItem,
    bkrepo: BKRepoComponent,
    *,
    expected_lease_token: str | None = None,
    expected_fingerprint: str | None = None,
    stale_before: datetime | None = None,
    expired_before: datetime | None = None,
) -> int:
    item = (
        SDKGenerationItem.objects.select_for_update()
        .select_related("task__gateway", "task__resource_version")
        .get(id=item.id)
    )
    if expected_lease_token is not None and (
        item.status != SDKGenerationItemStatusEnum.RUNNING.value or item.lease_token != expected_lease_token
    ):
        return 0
    if expected_fingerprint is not None and item.input_fingerprint != expected_fingerprint:
        return 0
    if stale_before is not None:
        cleanup_eligible = item.updated_time < stale_before and (
            item.status == SDKGenerationItemStatusEnum.FAILED.value
            or (
                item.status == SDKGenerationItemStatusEnum.RUNNING.value
                and item.lease_expires_at is not None
                and expired_before is not None
                and item.lease_expires_at <= expired_before
            )
        )
        if not item.input_fingerprint or not cleanup_eligible:
            return 0
    prefix = _prefix_for_item(item)
    if bkrepo.get_generic_file_metadata(manifest_key(prefix)) is not None:
        return 0
    records = list(item.artifacts.select_for_update().filter(distributor=SDKDistributorEnum.BKREPO_GENERIC.value))
    for artifact in records:
        if artifact.remote_key:
            bkrepo.delete_generic_file(artifact.remote_key)
    SDKArtifact.objects.filter(id__in=[artifact.id for artifact in records]).delete()
    return len(records)
