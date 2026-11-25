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
"""Skill 下载包：SKILL.md（frontmatter + 正文）和 references/ 下按部署环境填好的说明文件；
网关 Skill 管理页下载时另带按库里数据生成的 declaration.yaml，改声明后可以原样上传。

同一版本、同一份基本信息每次打出的 ZIP 字节相同：frontmatter 的 datetime 取版本的 created_time，
ZIP 条目顺序、时间和权限位固定。
"""

import io
import zipfile
from functools import lru_cache
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

import yaml
from django.conf import settings
from django.utils.translation import gettext as _

from apigateway.apps.skill.constants import SkillTypeEnum

from .constants import (
    PLATFORM_SKILL_AUTHOR,
    SKILL_DECLARATION_FILE_NAME,
    SKILL_DECLARATION_PACKAGE_SUFFIX,
    SKILL_FILE_NAME,
    SKILL_REFERENCE_FILE_NAMES,
    SKILL_REFERENCES_DIR,
    SKILL_REFERENCES_PATH,
    SKILL_SOURCE,
    SkillReferencePlaceholderEnum,
)
from .declaration import SkillOrchestration
from .frontmatter import render_frontmatter

if TYPE_CHECKING:
    from apigateway.apps.skill.models import SkillMetadata, SkillVersion

TITLE_PREFIX = "# "
# ZIP 不能表示 1980 年以前的时间，条目时间统一固定为它，和版本时间无关
_ZIP_ENTRY_DATE_TIME = (1980, 1, 1, 0, 0, 0)
_ZIP_ENTRY_MODE = 0o100644
# create_system 默认随运行平台变化，固定为 Unix，权限位才会被解压工具采用
_ZIP_CREATE_SYSTEM_UNIX = 3
_EXAMPLE_GATEWAY, _EXAMPLE_STAGE, _EXAMPLE_PATH = "bk-sops", "prod", "/get_task_list/2/?limit=5"


class _DeclarationDumper(yaml.SafeDumper):
    """声明 YAML 的输出格式：不输出锚点和别名（上传时会拒绝），多行字符串用 | 块"""

    def ignore_aliases(self, data: Any) -> bool:
        """所有节点都不生成锚点和别名

        例如：两个步骤引用同一个 dict -> 各自完整输出，不出现 &id001 / *id001
        """
        return True


def _represent_str(dumper: yaml.SafeDumper, data: str) -> yaml.ScalarNode:
    """含换行的字符串用 | 块输出，其他同 SafeDumper

    例如："第一行\\n第二行\\n" -> "|\\n  第一行\\n  第二行"；"单行" -> 单行
    """
    style = "|" if "\n" in data else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style=style)


_DeclarationDumper.add_representer(str, _represent_str)


def split_title(body: str) -> Tuple[Optional[str], str]:
    """正文 -> (一级标题文字, 标题之后的内容)；第一行不是一级标题时标题为 None、内容原样返回

    例如：
        "# 执行作业方案\\n\\n## 输入\\n" -> ("执行作业方案", "\\n## 输入\\n")
        "## 输入\\n" -> (None, "## 输入\\n")
    """
    first, sep, rest = body.partition("\n")
    if first.startswith(TITLE_PREFIX):
        return first[len(TITLE_PREFIX) :].strip(), rest
    return None, body


def replace_title(body: str, title: str) -> str:
    """把正文第一行的一级标题换成 title；没有一级标题时原样返回

    例如：("# 旧名\\n\\n正文", "新名") -> "# 新名\\n\\n正文"
    """
    old_title, rest = split_title(body)
    if old_title is None:
        return body
    return f"{TITLE_PREFIX}{title}\n{rest}"


@lru_cache(maxsize=1)
def _load_reference_templates() -> Tuple[Tuple[str, str], ...]:
    """读取 references 模板原文，进程内只读一次；返回 (包内路径, 原文)

    例如：-> (("references/how-to-call-apis.md", "..."), ("references/permissions.md", "..."))
    """
    templates = []
    for name in SKILL_REFERENCE_FILE_NAMES:
        text = (SKILL_REFERENCES_DIR / name).read_text(encoding="utf-8")
        templates.append((f"{SKILL_REFERENCES_PATH}/{name}", text if text.endswith("\n") else text + "\n"))
    return tuple(templates)


def get_reference_placeholder_values() -> Dict[str, str]:
    """references 占位符 -> 按当前部署环境的设置填充的值；设置项没配时填可读的默认文字

    例如：BK_API_URL_TMPL 为 "http://bkapi.example.com/api/{api_name}" ->
        gateway_url_template: "http://bkapi.example.com/api/{gateway_name}/<stage><path>"
        example_url: "http://bkapi.example.com/api/bk-sops/prod/get_task_list/2/?limit=5"
    """
    url_tmpl = settings.BK_API_URL_TMPL
    if url_tmpl:
        gateway_url_template = url_tmpl.replace("{api_name}", "{gateway_name}") + "/<stage><path>"
        example_url = f"{url_tmpl.replace('{api_name}', _EXAMPLE_GATEWAY)}/{_EXAMPLE_STAGE}{_EXAMPLE_PATH}"
    else:
        gateway_url_template = example_url = _("网关访问地址")
    developer_center_url = (
        f"{settings.BK_PAAS3_URL}/developer-center" if settings.BK_PAAS3_URL else _("蓝鲸开发者中心地址")
    )
    return {
        SkillReferencePlaceholderEnum.GATEWAY_URL_TEMPLATE.value: gateway_url_template,
        SkillReferencePlaceholderEnum.EXAMPLE_URL.value: example_url,
        SkillReferencePlaceholderEnum.DEVELOPER_CENTER_URL.value: developer_center_url,
    }


def load_references() -> List[Tuple[str, str]]:
    """references 两个文件按部署环境填好占位符；模板原文缓存，填充每次都做，设置变化时跟着变

    例如：-> [("references/how-to-call-apis.md", "...http://bkapi.example.com/api/{gateway_name}/..."), ...]
    """
    values = get_reference_placeholder_values()
    references = []
    for path, template in _load_reference_templates():
        text = template
        for name, value in values.items():
            text = text.replace(f"{{{{ {name} }}}}", value)
        references.append((path, text))
    return references


def render_declaration_yaml(metadata: SkillMetadata, version: SkillVersion) -> str:
    """按库里的数据生成声明 YAML：基本信息取 metadata 当前值，version、changelog、orchestration 取该版本

    字段顺序同 SkillDeclaration，display_name_en 为空时不写，标签按名称排序；编排按声明模型的字段顺序输出，
    只输出声明里写了的字段。同一版本、同一份基本信息每次生成的文本相同，经上传的 YAML 读取和声明校验能原样读回。

    例如：release-check 1.2.0 ->
        "name: release-check\\ndisplay_name: 发布核对\\ndescription: ...\\ntags:\\n- 只读\\nversion: 1.2.0\\n
         changelog:\\n  date: '2026-11-17'\\n  content: ...\\norchestration:\\n  description: |\\n ..."
    """
    data: Dict[str, Any] = {
        "name": metadata.name,
        "display_name": metadata.display_name,
    }
    if metadata.display_name_en:
        data["display_name_en"] = metadata.display_name_en
    orchestration = SkillOrchestration.model_validate(version.orchestration)
    data.update(
        {
            "description": metadata.description,
            "tags": sorted(tag.name for tag in metadata.tags.all()),
            "version": version.version,
            "changelog": {
                "date": version.changelog.get("date"),
                "content": version.changelog.get("content"),
            },
            "orchestration": orchestration.model_dump(mode="json", by_alias=True, exclude_unset=True),
        }
    )
    # 不按宽度折行，长描述和 ${{ }} 引用保持在一行
    return yaml.dump(data, Dumper=_DeclarationDumper, allow_unicode=True, sort_keys=False, width=float("inf"))


def build_skill_package_files(
    metadata: SkillMetadata, version: SkillVersion, with_declaration: bool = False
) -> List[Tuple[str, str]]:
    """生成下载包的文件：[(包内相对路径, 内容)]，路径相对 {name}/

    frontmatter 的名称、描述、展示名取 metadata 当前值，版本号、author、datetime 取打包的版本；
    正文取版本冻结的正文，一级标题换成 metadata 当前的 display_name。
    with_declaration 为 True 时（网关 Skill 管理页）另带 declaration.yaml，见 render_declaration_yaml。

    例如：网关 Skill 版本 1.2.0、由 admin 发布 ->
        [("SKILL.md", "---\\nname: ...\\n  author: \\"admin\\"..."), ("references/how-to-call-apis.md", ...),
         ("references/permissions.md", ...)]；with_declaration 时末尾多一项 ("declaration.yaml", ...)
    """
    author = PLATFORM_SKILL_AUTHOR if metadata.type == SkillTypeEnum.PLATFORM.value else version.created_by
    frontmatter = render_frontmatter(
        name=metadata.name,
        description=metadata.description,
        display_name=metadata.display_name,
        display_name_en=metadata.display_name_en,
        type=metadata.type,
        version=version.version,
        author=author or "",
        source=SKILL_SOURCE,
        published_at=version.created_time,
    )
    body = replace_title(version.artifact.get(SKILL_FILE_NAME, ""), metadata.display_name)
    files = [(SKILL_FILE_NAME, f"{frontmatter}\n{body}"), *load_references()]
    if with_declaration:
        files.append((SKILL_DECLARATION_FILE_NAME, render_declaration_yaml(metadata, version)))
    return files


def build_skill_package_zip(metadata: SkillMetadata, version: SkillVersion, with_declaration: bool = False) -> bytes:
    """生成下载包 ZIP 字节，解压为 {name}/SKILL.md、{name}/references/*.md，
    with_declaration 时另有 {name}/declaration.yaml

    例如：同一版本、基本信息没改时打两次 -> 字节相同；只改了 display_name -> SKILL.md 变了，字节不同
    """
    files = build_skill_package_files(metadata, version, with_declaration=with_declaration)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for path, content in sorted(files):
            info = zipfile.ZipInfo(f"{metadata.name}/{path}", date_time=_ZIP_ENTRY_DATE_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = _ZIP_CREATE_SYSTEM_UNIX
            info.external_attr = _ZIP_ENTRY_MODE << 16
            archive.writestr(info, content.encode("utf-8"))
    return buffer.getvalue()


def get_skill_package_filename(metadata: SkillMetadata, version: SkillVersion, with_declaration: bool = False) -> str:
    """下载包文件名：{skill_id}-{version}.zip，带声明时为 {skill_id}-{version}-with-declaration.zip；
    skill_id 区分不同网关的同名 Skill

    例如：网关 demo 的 release-check 1.2.0 -> "g_demo_release-check-1.2.0.zip"；
    带声明 -> "g_demo_release-check-1.2.0-with-declaration.zip"
    """
    suffix = SKILL_DECLARATION_PACKAGE_SUFFIX if with_declaration else ""
    return f"{metadata.code}-{version.version}{suffix}.zip"
