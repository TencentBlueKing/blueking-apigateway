from __future__ import annotations

from typing import TYPE_CHECKING

from apigateway.biz.sdk.builders.common import collect_artifacts, run_build, write_deterministic_zip

if TYPE_CHECKING:
    from pathlib import Path

    from apigateway.biz.sdk.artifacts import BuiltArtifact


def build(source_dir: Path, output_dir: Path) -> list[BuiltArtifact]:
    output_dir.mkdir(parents=True, exist_ok=True)
    library_dir = output_dir / "lib"
    run_build(
        [
            "mvn",
            "-B",
            "clean",
            "package",
            "source:jar-no-fork",
            "dependency:copy-dependencies",
            f"-DoutputDirectory={library_dir}",
        ],
        cwd=source_dir,
    )
    target = source_dir / "target"
    sources = sorted(target.glob("*-sources.jar"))
    jars = sorted(
        path
        for path in target.glob("*.jar")
        if not path.name.endswith(("-sources.jar", "-javadoc.jar")) and not path.name.startswith("original-")
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
