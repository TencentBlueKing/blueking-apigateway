import json
from types import SimpleNamespace

import pytest

from apigateway.biz.sdk.artifacts import (
    build_manifest,
    create_built_artifact,
    select_generic_artifact,
    validate_artifact_names,
)


def test_manifest_is_deterministic(tmp_path):
    first_path = tmp_path / "a.whl"
    second_path = tmp_path / "b.tar.gz"
    first_path.write_bytes(b"wheel")
    second_path.write_bytes(b"sdist")
    first = create_built_artifact("wheel", first_path, allowed_roots=(tmp_path,))
    second = create_built_artifact("sdist", second_path, allowed_roots=(tmp_path,))

    manifest = build_manifest("demo", "1.2.3", "python", "1.2.3", "abc", {"python": "3.14"}, [second, first])

    assert json.loads(manifest.to_json())["files"][0]["filename"] == "a.whl"
    assert (
        manifest.to_json()
        == build_manifest("demo", "1.2.3", "python", "1.2.3", "abc", {"python": "3.14"}, [first, second]).to_json()
    )


def test_artifact_rejects_symlink(tmp_path):
    target = tmp_path / "target"
    target.write_bytes(b"data")
    link = tmp_path / "link"
    link.symlink_to(target)

    with pytest.raises(ValueError, match="invalid SDK artifact"):
        create_built_artifact("archive", link, allowed_roots=(tmp_path,))


def test_artifact_names_are_case_insensitively_unique(tmp_path):
    upper = tmp_path / "SDK.zip"
    lower = tmp_path / "sdk.ZIP"
    upper.write_bytes(b"one")
    lower.write_bytes(b"two")
    artifacts = [
        create_built_artifact("archive", upper, allowed_roots=(tmp_path,)),
        create_built_artifact("archive", lower, allowed_roots=(tmp_path,)),
    ]

    with pytest.raises(ValueError, match="unique ignoring case"):
        validate_artifact_names(artifacts)


@pytest.mark.parametrize(
    ("language", "artifact_type"),
    [("python", "wheel"), ("java", "distribution_zip"), ("go", "go_zip"), ("javascript", "npm_tgz")],
)
def test_download_selection_prefers_successful_generic_artifact(language, artifact_type):
    def artifact(kind, filename, distributor="bkrepo_generic", status="success"):
        return SimpleNamespace(artifact_type=kind, filename=filename, distributor=distributor, status=status)

    preferred = artifact(artifact_type, "preferred")
    fallback = artifact("archive", "fallback")
    rows = [
        artifact(artifact_type, "native", distributor="pypi"),
        artifact(artifact_type, "failed", status="failed"),
        artifact("manifest", "manifest.json"),
        fallback,
        preferred,
    ]
    assert select_generic_artifact(language, rows) is preferred
    assert select_generic_artifact(language, list(reversed(rows))) is preferred
    assert select_generic_artifact(language, rows[:-1]) is fallback
    assert select_generic_artifact(language, rows[:3]) is None
