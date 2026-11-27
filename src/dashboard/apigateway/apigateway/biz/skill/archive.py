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
"""上传包的内存读取：只在内存里解压，不落盘；不依赖数据库，Skill Creator 的自查脚本照搬这里的规则。

包里只有一个顶层目录 {name}/（macOS 打包带的 __MACOSX/ 忽略），下面必须有 declaration.yaml；
其他文件（如 Skill Creator 一起打进来的 SKILL.md、references/）只做路径检查，不读取、不入库，列在 SkillPackage.ignored 里。
"""

import re
import stat
import zipfile
import zlib
from dataclasses import dataclass, field
from typing import IO, Dict, List, Optional, Tuple

from django.utils.translation import gettext as _

from .constants import SKILL_DECLARATION_FILE_NAME, SKILL_PACKAGE_MAX_ENTRIES, SKILL_PACKAGE_MAX_SIZE

_WINDOWS_DRIVE_PATTERN = re.compile(r"^[A-Za-z]:")
_MACOS_METADATA_DIR = "__MACOSX"


@dataclass(frozen=True)
class ValidationMessage:
    """上传校验的一条结果；file 是包内路径（如 release-check/SKILL.md），file、field 都可以为空"""

    file: Optional[str]
    field: Optional[str]
    message: str


@dataclass
class SkillPackage:
    """读出的上传包：root 为顶层目录名，declaration 为 declaration.yaml 的 UTF-8 文本，
    ignored 为不导入的其他文件（相对 root 的路径，按路径排序）"""

    root: str
    declaration: str = ""
    ignored: List[str] = field(default_factory=list)

    def path_of(self, relative_path: str) -> str:
        """包内完整路径，用作 ValidationMessage.file

        例如：root 为 release-check，"SKILL.md" -> "release-check/SKILL.md"
        """
        return f"{self.root}/{relative_path}"


class SkillArchiveError(Exception):
    def __init__(self, errors: List[ValidationMessage]):
        super().__init__("; ".join(error.message for error in errors))
        self.errors = errors


def read_skill_package(fileobj: IO[bytes]) -> SkillPackage:
    """读取上传的 zip；结构、路径、大小、编码不合规或文件损坏时抛 SkillArchiveError，errors 列出全部问题

    declaration.yaml 解压后也不超过 SKILL_PACKAGE_MAX_SIZE。

    例如：
        release-check/ 下有 SKILL.md、declaration.yaml 和 references/permissions.md
            -> SkillPackage(root="release-check", declaration="name: release-check\\n...",
                            ignored=["SKILL.md", "references/permissions.md"])
        少了 declaration.yaml -> error
        条目为 ../evil.md 或符号链接 -> error，不读取任何内容
    """
    try:
        archive = zipfile.ZipFile(fileobj)
    # 设置了 UTF-8 标志但文件名不是 UTF-8 时，读中央目录抛 UnicodeDecodeError
    except zipfile.BadZipFile, OSError, EOFError, UnicodeDecodeError:
        raise SkillArchiveError([ValidationMessage(None, None, _("不是合法的 zip 文件"))]) from None

    with archive:
        infos = archive.infolist()
        errors = _check_entries(infos)
        if errors:
            raise SkillArchiveError(errors)

        root, file_infos = _split_root(infos)
        errors = _check_required_files(root, file_infos)
        if errors:
            raise SkillArchiveError(errors)

        package = SkillPackage(
            root=root, ignored=sorted(path for path in file_infos if path != SKILL_DECLARATION_FILE_NAME)
        )
        declaration_file = package.path_of(SKILL_DECLARATION_FILE_NAME)
        info = file_infos[SKILL_DECLARATION_FILE_NAME]
        # zipfile 最多解压出 ZIP 头声明的字节数，实际更大时 CRC 不符、按损坏处理，所以只需检查声明的大小
        if info.file_size > SKILL_PACKAGE_MAX_SIZE:
            message = _("文件解压后超过 {size} MB").format(size=SKILL_PACKAGE_MAX_SIZE // (1024 * 1024))
            raise SkillArchiveError([ValidationMessage(declaration_file, None, message)])
        try:
            content = archive.read(info)
        except zipfile.BadZipFile, zlib.error, EOFError, NotImplementedError, RuntimeError:
            raise SkillArchiveError([ValidationMessage(declaration_file, None, _("文件已损坏"))]) from None
        try:
            package.declaration = content.decode("utf-8")
        except UnicodeDecodeError:
            raise SkillArchiveError([ValidationMessage(declaration_file, None, _("文件不是 UTF-8 编码"))]) from None
    return package


def _check_entries(infos: List[zipfile.ZipInfo]) -> List[ValidationMessage]:
    """逐条检查路径和类型：不能是绝对路径、不能含 .. 或反斜杠、不能是符号链接；包不能为空，条目数不超过 SKILL_PACKAGE_MAX_ENTRIES

    例如：合规 "release-check/declaration.yaml"；不合规 "/etc/passwd"、"release-check/../x"、"C:/x"、符号链接条目
    """
    if not infos:
        return [ValidationMessage(None, None, _("压缩包是空的"))]
    if len(infos) > SKILL_PACKAGE_MAX_ENTRIES:
        return [
            ValidationMessage(
                None, None, _("压缩包里的条目不能超过 {max_count} 个").format(max_count=SKILL_PACKAGE_MAX_ENTRIES)
            )
        ]
    errors = []
    for info in infos:
        name = info.filename
        parts = name.rstrip("/").split("/")
        if (
            name.startswith("/")
            or "\\" in name
            or _WINDOWS_DRIVE_PATTERN.match(name)
            or any(part in ("", ".", "..") for part in parts)
        ):
            errors.append(ValidationMessage(name, None, _("路径不合法，不能是绝对路径或包含 ..")))
        # ZIP 把 Unix st_mode 放在 external_attr 的高 16 位
        elif stat.S_ISLNK(info.external_attr >> 16):
            errors.append(ValidationMessage(name, None, _("不能包含符号链接")))
    return errors


def _split_root(infos: List[zipfile.ZipInfo]) -> Tuple[str, Dict[str, zipfile.ZipInfo]]:
    """按第一级目录拆开：(顶层目录名, {相对路径: 条目})；有多个顶层或文件在最外层时顶层名为空；__MACOSX/ 整个忽略

    例如：["demo/", "demo/declaration.yaml", "__MACOSX/demo/._declaration.yaml"] -> ("demo", {"declaration.yaml": ...})；
    ["a/x", "b/y"] -> ("", {...})
    """
    infos = [info for info in infos if info.filename.split("/", 1)[0] != _MACOS_METADATA_DIR]
    roots = {info.filename.split("/", 1)[0] for info in infos}
    has_root_file = any("/" not in info.filename for info in infos if not info.is_dir())
    root = roots.pop() if len(roots) == 1 and not has_root_file else ""
    files = {}
    for info in infos:
        if info.is_dir():
            continue
        relative = info.filename.split("/", 1)[1] if root else info.filename
        files[relative] = info
    return root, files


def _check_required_files(root: str, file_infos: Dict[str, zipfile.ZipInfo]) -> List[ValidationMessage]:
    """只有一个顶层目录，下面有 declaration.yaml；其他文件不检查

    例如：合规 demo/ 下只有 declaration.yaml，另有 SKILL.md、references/permissions.md 也合规；
    不合规 两个顶层目录、少了 declaration.yaml
    """
    if not root:
        return [ValidationMessage(None, None, _("压缩包里应只有一个顶层目录，目录名为 Skill 的 name"))]
    if SKILL_DECLARATION_FILE_NAME not in file_infos:
        return [
            ValidationMessage(
                f"{root}/{SKILL_DECLARATION_FILE_NAME}",
                None,
                _("缺少文件，网关按 declaration.yaml 校验并生成 SKILL.md"),
            )
        ]
    return []
