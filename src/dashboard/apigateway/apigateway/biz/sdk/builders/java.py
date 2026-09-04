from __future__ import annotations

import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

from apigateway.biz.sdk.builders.common import collect_artifacts, run_build, write_deterministic_zip
from apigateway.biz.sdk.maven_settings import write_maven_settings
from apigateway.biz.sdk.toolchain import validate_generated_dependency_inputs
from apigateway.utils.maven import RepositoryConfig

if TYPE_CHECKING:
    from apigateway.biz.sdk.artifacts import BuiltArtifact


def build(source_dir: Path, output_dir: Path) -> list[BuiltArtifact]:
    validate_generated_dependency_inputs("java", source_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    library_dir = output_dir / "lib"
    command = [
        "mvn",
        "-B",
        "clean",
        "package",
        "source:jar-no-fork",
        "dependency:copy-dependencies",
        f"-DoutputDirectory={library_dir}",
        "-DincludeScope=runtime",
    ]
    repository = RepositoryConfig.by_name("default")
    if repository.mirror_url:
        with tempfile.TemporaryDirectory(prefix="sdk-maven-build-") as directory:
            settings_path = Path(directory) / "settings.xml"
            write_maven_settings(settings_path, repository)
            run_build([*command[:2], "-s", str(settings_path), *command[2:]], cwd=source_dir)
    else:
        run_build(command, cwd=source_dir)
    target = source_dir / "target"
    sources = sorted(target.glob("*-sources.jar"))
    jars = sorted(
        path
        for path in target.glob("*.jar")
        if not path.name.endswith(("-sources.jar", "-javadoc.jar", "-tests.jar"))
        and not path.name.startswith("original-")
    )
    pom = source_dir / "pom.xml"
    if len(jars) != 1 or len(sources) != 1 or not pom.is_file():
        raise ValueError("Java SDK build did not produce the expected JAR, sources JAR, and POM")

    distribution = output_dir / f"{jars[0].stem}-distribution.zip"
    zip_entries = [(jars[0].name, jars[0]), (pom.name, pom), (sources[0].name, sources[0])]
    zip_entries.extend((f"lib/{path.name}", path) for path in sorted(library_dir.glob("*.jar")))
    readme = source_dir / "README.md"
    if readme.is_file():
        zip_entries.append((readme.name, readme))
    write_deterministic_zip(distribution, zip_entries)
    return collect_artifacts(
        [("jar", jars[0]), ("pom", pom), ("sources_jar", sources[0]), ("distribution_zip", distribution)],
        source_dir,
        output_dir,
    )
