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
import struct
import zipfile

import pytest

from apigateway.biz.skill.archive import SkillArchiveError, read_skill_package

pytestmark = pytest.mark.no_meta_schema

FILES = {"declaration.yaml": "name: demo\n"}


def _zip(entries, compression=zipfile.ZIP_DEFLATED) -> io.BytesIO:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=compression) as archive:
        for name, content in entries.items():
            if isinstance(content, zipfile.ZipInfo):
                archive.writestr(content, b"target")
            else:
                archive.writestr(name, content)
    buffer.seek(0)
    return buffer


def _package(root="demo", **overrides):
    files = {**FILES, **overrides}
    return {f"{root}/{path}": content for path, content in files.items() if content is not None}


def _errors(fileobj):
    with pytest.raises(SkillArchiveError) as err:
        read_skill_package(fileobj)
    return [(item.file, item.message) for item in err.value.errors]


class TestReadSkillPackage:
    def test_ok(self):
        entries = {"demo/": "", **_package()}
        package = read_skill_package(_zip(entries))

        assert package.root == "demo"
        assert package.declaration == FILES["declaration.yaml"]
        assert package.ignored == []
        assert package.path_of("declaration.yaml") == "demo/declaration.yaml"

    def test_not_zip(self):
        assert _errors(io.BytesIO(b"not a zip")) == [(None, "不是合法的 zip 文件")]

    def test_empty(self):
        assert _errors(_zip({})) == [(None, "压缩包是空的")]

    def test_too_many_entries(self):
        entries = _package(**{f"assets/{index}.txt": "" for index in range(1000)})
        assert _errors(_zip(entries)) == [(None, "压缩包里的条目不能超过 1000 个")]

    def test_missing_declaration(self):
        errors = _errors(_zip(_package(**{"declaration.yaml": None, "SKILL.md": "# 标题\n"})))
        assert errors == [("demo/declaration.yaml", "缺少文件，网关按 declaration.yaml 校验并生成 SKILL.md")]

    def test_other_files_ignored(self):
        """SKILL.md、references 等不读取，不检查编码和大小，列在 ignored 里"""
        extra = {
            "SKILL.md": "标题".encode("gbk"),
            "references/permissions.md": "权限\n",
            ".DS_Store": b"\xff" * (2 * 1024 * 1024),
        }
        package = read_skill_package(_zip(_package(**extra)))

        assert package.declaration == FILES["declaration.yaml"]
        assert package.ignored == [".DS_Store", "SKILL.md", "references/permissions.md"]

    def test_macosx_ignored(self):
        entries = {**_package(), "__MACOSX/": "", "__MACOSX/demo/._declaration.yaml": b"\x00\x05"}
        package = read_skill_package(_zip(entries))

        assert package.root == "demo"
        assert package.ignored == []

    @pytest.mark.parametrize(
        "entries",
        [
            pytest.param({**_package("a"), **_package("b")}, id="two-roots"),
            pytest.param(dict(FILES), id="no-root"),
            pytest.param({**_package(), "readme.md": "x"}, id="root-file"),
            pytest.param({"__MACOSX/demo/._x": "x"}, id="only-macosx"),
        ],
    )
    def test_one_root(self, entries):
        assert _errors(_zip(entries)) == [(None, "压缩包里应只有一个顶层目录，目录名为 Skill 的 name")]

    @pytest.mark.parametrize(
        "name", ["../evil.md", "demo/../evil.md", "/etc/passwd", "C:/x", "demo\\x", "__MACOSX/../x"]
    )
    def test_unsafe_path(self, name):
        errors = _errors(_zip({**_package(), name: "x"}))
        assert errors == [(name, "路径不合法，不能是绝对路径或包含 ..")]

    def test_symlink(self):
        info = zipfile.ZipInfo("demo/link")
        info.create_system = 3
        info.external_attr = 0o120777 << 16
        assert _errors(_zip({**_package(), "demo/link": info})) == [("demo/link", "不能包含符号链接")]

    def test_not_utf8(self):
        errors = _errors(_zip(_package(**{"declaration.yaml": "名称".encode("gbk")})))
        assert errors == [("demo/declaration.yaml", "文件不是 UTF-8 编码")]

    def test_file_too_large(self):
        errors = _errors(_zip(_package(**{"declaration.yaml": "a" * (2 * 1024 * 1024 + 1)})))
        assert errors == [("demo/declaration.yaml", "文件解压后超过 2 MB")]

    def test_declared_size_smaller_than_actual(self):
        """ZIP 头声明的大小比实际小：只解压出声明的字节数，CRC 不符，按文件损坏报错"""
        buffer = _zip(_package(**{"declaration.yaml": b"a" * (3 * 1024 * 1024)}))
        data = bytearray(buffer.getvalue())
        _patch_declared_size(data, b"demo/declaration.yaml", 10)

        errors = _errors(io.BytesIO(bytes(data)))
        assert errors == [("demo/declaration.yaml", "文件已损坏")]


def _patch_declared_size(data: bytearray, name: bytes, size: int) -> None:
    """把本地文件头和中央目录里 name 的未压缩大小都改成 size"""
    local = data.find(b"PK\x03\x04")
    while local != -1:
        name_length = struct.unpack("<H", data[local + 26 : local + 28])[0]
        if data[local + 30 : local + 30 + name_length] == name:
            data[local + 22 : local + 26] = struct.pack("<I", size)
        local = data.find(b"PK\x03\x04", local + 4)
    central = data.find(b"PK\x01\x02")
    while central != -1:
        name_length = struct.unpack("<H", data[central + 28 : central + 30])[0]
        if data[central + 46 : central + 46 + name_length] == name:
            data[central + 24 : central + 28] = struct.pack("<I", size)
        central = data.find(b"PK\x01\x02", central + 4)
