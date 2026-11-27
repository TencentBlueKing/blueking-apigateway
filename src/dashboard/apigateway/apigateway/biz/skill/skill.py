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
"""Skill 读侧：Skill 市场、网关 Skill 和免登录下载（web 接口，给 npx 临时使用）的查询、统计和下载计数"""

from typing import Any, Dict, List, Optional, Sequence, Tuple

from django.conf import settings
from django.db.models import Count, Exists, F, OuterRef, Q, QuerySet
from django.utils.translation import gettext as _

from apigateway.apps.skill.constants import SKILL_CODE_PREFIXES, SkillStatusEnum, SkillTypeEnum
from apigateway.apps.skill.models import SkillMetadata, SkillTag, SkillVersion, SkillVersionRelation
from apigateway.common.error_codes import error_codes
from apigateway.common.tenant.query import skill_filter_by_user_tenant_id
from apigateway.common.tenant.validators import check_user_can_access_gateway
from apigateway.core.constants import GatewayStatusEnum
from apigateway.core.models import Gateway

from .constants import SKILL_NAME_PATTERN
from .declaration import normalize_tag_name, parse_version, split_uses

# 列表不读版本的大字段，只要版本号和发布时间
_LIST_DEFERRED_FIELDS = ("current_version__artifact", "current_version__orchestration", "current_version__changelog")

# 接口的 order_by -> 排序字段；-published_time 是线上版本的发布时间，并列时按 id 保证分页稳定
_ORDER_FIELDS = {
    "-published_time": ("-current_version__created_time", "-id"),
    "-updated_time": ("-updated_time", "-id"),
    "-download_count": ("-download_count", "-id"),
    "name": ("name", "id"),
}


def _market_visible_condition() -> Q:
    """Skill 市场和免登录下载的可见范围：使用中，网关 Skill 另外要求所属网关启用中

    例如：内置 Skill 都可见；已归档的、网关停用的网关 Skill 不可见
    """
    return Q(status=SkillStatusEnum.PUBLISHED.value) & (
        Q(type=SkillTypeEnum.PLATFORM.value) | Q(gateway__status=GatewayStatusEnum.ACTIVE.value)
    )


def _skill_id_lookup(skill_id: str) -> Dict[str, Any]:
    """对外 ID -> SkillMetadata 的查询条件；ID 解析失败抛 NOT_FOUND

    例如：
        "g_demo_release-check" -> {"type": "gateway", "name": "release-check", "gateway__name": "demo"}
        "p_job-plan" -> {"type": "platform", "name": "job-plan", "gateway__isnull": True}
        "x_bad" -> 404
    """
    parsed = SkillHandler.parse_skill_id(skill_id)
    if parsed is None:
        raise _skill_not_found(skill_id)
    skill_type, gateway_name, name = parsed
    if skill_type == SkillTypeEnum.GATEWAY.value:
        return {"type": skill_type, "name": name, "gateway__name": gateway_name}
    return {"type": skill_type, "name": name, "gateway__isnull": True}


def _skill_not_found(skill_id: str):
    """对外 ID 对应的 Skill 不存在时的 NOT_FOUND"""
    return error_codes.NOT_FOUND.format(_("Skill {skill_id} 不存在").format(skill_id=skill_id), replace=True)


def _tag_condition(tag: str) -> Exists:
    """带某个标签：按规范化后的标签名精确匹配

    例如：tag="JOB"、" job " -> 带标签 job 的 Skill
    """
    return Exists(SkillTag.objects.filter(metadata_set=OuterRef("pk"), name=normalize_tag_name(tag)))


def _keyword_condition(keyword: str, match_gateway_name: bool) -> Q:
    """关键词匹配名称、展示名、描述、标签名，以及当前版本调用的接口名

    match_gateway_name 为真时还匹配当前版本调用的网关名（网关 Skill 只调本网关，匹配它没有意义）。

    例如：
        "sops" -> 名称、展示名、描述、标签名含 sops，或当前版本调用了 bk-sops 网关的接口
        "get_task_status" -> 当前版本用到 get_task_status 的 Skill；只在历史版本里用过的不算
    """
    api_condition = Q(resource_name__icontains=keyword)
    if match_gateway_name:
        api_condition |= Q(gateway_name__icontains=keyword)
    return (
        Q(name__icontains=keyword)
        | Q(display_name__icontains=keyword)
        | Q(display_name_en__icontains=keyword)
        | Q(description__icontains=keyword)
        | Exists(SkillTag.objects.filter(metadata_set=OuterRef("pk"), name__icontains=keyword))
        | Exists(SkillVersionRelation.objects.filter(version_id=OuterRef("current_version_id")).filter(api_condition))
    )


class SkillHandler:
    @staticmethod
    def parse_skill_id(skill_id: str) -> Optional[Tuple[str, Optional[str], str]]:
        """对外 ID -> (type, 网关名, name)；前缀不认识或格式不对时返回 None

        网关名和 Skill 名都不含下划线，按第一个下划线能唯一拆开。

        例如：
            "p_job-plan-run-and-log" -> ("platform", None, "job-plan-run-and-log")
            "g_demo_release-check" -> ("gateway", "demo", "release-check")
            "x_demo"、"g_demo"、"p_Bad_Name" -> None
        """
        for skill_type, prefix in SKILL_CODE_PREFIXES.items():
            if not skill_id.startswith(prefix):
                continue
            rest = skill_id[len(prefix) :]
            gateway_name: Optional[str] = None
            if skill_type == SkillTypeEnum.GATEWAY.value:
                gateway_name, sep, rest = rest.partition("_")
                if not sep or not gateway_name:
                    return None
            if not SKILL_NAME_PATTERN.fullmatch(rest):
                return None
            return skill_type, gateway_name, rest
        return None

    @staticmethod
    def list_market_skills(
        user_tenant_id: Optional[str],
        keyword: Optional[str] = None,
        tag: Optional[str] = None,
        skill_type: Optional[str] = None,
        order_by: str = "-published_time",
    ) -> QuerySet:
        """Skill 市场列表：可见范围内按租户、类型、标签、关键词筛选并排序，带上列表要用的关联

        例如：
            用户在租户 a -> 内置 Skill、全租户网关和租户 a 网关下使用中的网关 Skill
            keyword="sops"、tag="JOB" -> 带标签 job、且名称等字段或当前版本调用的接口匹配 sops 的 Skill
            order_by="-published_time" -> 最近发布线上版本的在前
        """
        queryset = SkillMetadata.objects.filter(_market_visible_condition())
        if user_tenant_id:
            queryset = skill_filter_by_user_tenant_id(queryset, user_tenant_id)
        if skill_type:
            queryset = queryset.filter(type=skill_type)
        if tag:
            queryset = queryset.filter(_tag_condition(tag))
        if keyword:
            queryset = queryset.filter(_keyword_condition(keyword, match_gateway_name=True))
        return (
            queryset.select_related("gateway", "current_version")
            .defer(*_LIST_DEFERRED_FIELDS)
            .prefetch_related("tags")
            .order_by(*_ORDER_FIELDS[order_by])
        )

    @staticmethod
    def count_market_skills(
        user_tenant_id: Optional[str], keyword: Optional[str] = None, tag: Optional[str] = None
    ) -> Dict[str, int]:
        """Skill 市场各类型的数量：筛选条件同列表（不含类型），没有的类型为 0

        例如：可见的有 3 条内置、1 条网关 Skill -> {"platform": 3, "gateway": 1}
        """
        queryset = SkillMetadata.objects.filter(_market_visible_condition())
        if user_tenant_id:
            queryset = skill_filter_by_user_tenant_id(queryset, user_tenant_id)
        if tag:
            queryset = queryset.filter(_tag_condition(tag))
        if keyword:
            queryset = queryset.filter(_keyword_condition(keyword, match_gateway_name=True))

        counts = dict.fromkeys(SkillTypeEnum.get_values(), 0)
        for item in queryset.values("type").annotate(count=Count("id")):
            counts[item["type"]] = item["count"]
        return counts

    @staticmethod
    def list_market_tags(
        user_tenant_id: Optional[str], skill_type: Optional[str] = None, keyword: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Skill 市场可见的 Skill 用到的标签和各自的 Skill 数，按数量降序、名字升序；keyword 搜标签名

        例如：两条可见 Skill 都带「日志」，一条带「只读」 ->
            [{"name": "日志", "skill_count": 2}, {"name": "只读", "skill_count": 1}]
        """
        metadata_queryset = SkillMetadata.objects.filter(_market_visible_condition())
        if user_tenant_id:
            metadata_queryset = skill_filter_by_user_tenant_id(metadata_queryset, user_tenant_id)
        if skill_type:
            metadata_queryset = metadata_queryset.filter(type=skill_type)

        relations = SkillMetadata.tags.through.objects.filter(skillmetadata__in=metadata_queryset.values("id"))
        if keyword:
            relations = relations.filter(skilltag__name__icontains=keyword)
        rows = (
            relations.values("skilltag__name")
            .annotate(skill_count=Count("skillmetadata", distinct=True))
            .order_by("-skill_count", "skilltag__name")
        )
        return [{"name": row["skilltag__name"], "skill_count": row["skill_count"]} for row in rows]

    @staticmethod
    def list_gateway_skills(
        gateway: Gateway,
        keyword: Optional[str] = None,
        tag: Optional[str] = None,
        status: Optional[str] = None,
        order_by: str = "-updated_time",
    ) -> QuerySet:
        """网关下的网关 Skill 列表，不限状态；按状态、标签、关键词筛选并排序，带上列表要用的关联

        关键词不匹配当前版本调用的网关名：网关 Skill 只调本网关。

        例如：
            网关 demo 下 2 条使用中、1 条已归档 -> 3 条；status="archived" -> 1 条
            keyword="demo" -> 不会因为调用了 demo 网关的接口就全部命中
        """
        queryset = SkillMetadata.objects.filter(type=SkillTypeEnum.GATEWAY.value, gateway=gateway)
        if status:
            queryset = queryset.filter(status=status)
        if tag:
            queryset = queryset.filter(_tag_condition(tag))
        if keyword:
            queryset = queryset.filter(_keyword_condition(keyword, match_gateway_name=False))
        return (
            queryset.select_related("gateway", "current_version")
            .defer(*_LIST_DEFERRED_FIELDS)
            .prefetch_related("tags")
            .order_by(*_ORDER_FIELDS[order_by])
        )

    @staticmethod
    def get_market_skill(skill_id: str, user_tenant_id: Optional[str]) -> SkillMetadata:
        """Skill 市场里按对外 ID 取 Skill；已归档、网关停用、不存在抛 NOT_FOUND，其他租户的网关 Skill 抛 NO_PERMISSION

        例如：用户在租户 a，网关 demo 属于租户 b -> "g_demo_release-check" 返回 403
        """
        metadata = (
            SkillMetadata.objects.filter(_market_visible_condition(), **_skill_id_lookup(skill_id))
            .select_related("gateway", "current_version")
            .first()
        )
        if metadata is None:
            raise _skill_not_found(skill_id)
        # 不在查询里按租户过滤：其他租户的网关 Skill 返回 403 而不是 404
        if metadata.gateway is not None and user_tenant_id:
            check_user_can_access_gateway(metadata.gateway.tenant_mode, metadata.gateway.tenant_id, user_tenant_id)
        return metadata

    @staticmethod
    def list_market_versions(skill_id: str, user_tenant_id: Optional[str]) -> Tuple[SkillMetadata, List[SkillVersion]]:
        """Skill 市场的历史版本：按对外 ID 取 Skill（含租户校验），返回 metadata 和降序的版本列表

        例如：用户在租户 a，网关 demo 属于租户 b -> 403；已有 1.9.0、1.10.0 -> (metadata, [1.10.0, 1.9.0])
        """
        metadata = SkillHandler.get_market_skill(skill_id, user_tenant_id)
        return metadata, SkillHandler.list_versions(metadata)

    @staticmethod
    def get_market_version(
        skill_id: str, version: Optional[str], user_tenant_id: Optional[str]
    ) -> Tuple[SkillMetadata, SkillVersion]:
        """Skill 市场取 Skill 的某个版本：按对外 ID 取 Skill（含租户校验），version 为空时取线上版本

        例如：用户在租户 a，网关 demo 属于租户 b -> 403；version=None -> (metadata, 线上版本)；version="9.9.9" -> 404
        """
        metadata = SkillHandler.get_market_skill(skill_id, user_tenant_id)
        return metadata, SkillHandler.get_version(metadata, version)

    @staticmethod
    def get_public_skill(skill_id: str) -> SkillMetadata:
        """免登录下载（web 接口，给 npx 临时使用）按对外 ID 取 Skill：可见范围同 Skill 市场，但没有登录用户、不按租户过滤

        例如：其他租户网关下使用中的网关 Skill 也能取到；已归档的抛 NOT_FOUND
        """
        metadata = (
            SkillMetadata.objects.filter(_market_visible_condition(), **_skill_id_lookup(skill_id))
            .select_related("gateway", "current_version")
            .first()
        )
        if metadata is None:
            raise _skill_not_found(skill_id)
        return metadata

    @staticmethod
    def get_gateway_skill(gateway: Gateway, skill_id: str) -> SkillMetadata:
        """网关 Skill 接口按对外 ID 取 Skill，不限状态；ID 不属于这个网关时抛 NOT_FOUND

        例如：路径是网关 demo，ID 为 "g_other_release-check" -> 404，即使 other 下有这条 Skill
        """
        metadata = (
            SkillMetadata.objects.filter(type=SkillTypeEnum.GATEWAY.value, gateway=gateway)
            .filter(**_skill_id_lookup(skill_id))
            .select_related("gateway", "current_version")
            .first()
        )
        if metadata is None:
            raise _skill_not_found(skill_id)
        return metadata

    @staticmethod
    def get_version(metadata: SkillMetadata, version: Optional[str] = None) -> SkillVersion:
        """取 Skill 的某个版本；version 为空时取线上版本；不存在抛 NOT_FOUND

        例如：version=None -> 线上版本；version="9.9.9" 不存在 -> 404
        """
        if not version:
            if metadata.current_version is None:
                raise error_codes.NOT_FOUND.format(
                    _("Skill {name} 没有线上版本").format(name=metadata.name), replace=True
                )
            return metadata.current_version
        found = SkillVersion.objects.filter(metadata=metadata, version=version).first()
        if found is None:
            raise error_codes.NOT_FOUND.format(_("版本 {version} 不存在").format(version=version), replace=True)
        return found

    @staticmethod
    def list_versions(metadata: SkillMetadata) -> List[SkillVersion]:
        """Skill 的全部版本，按 major.minor.patch 的整数大小降序；不读正文和编排

        例如：已有 1.9.0、1.10.0、1.2.0 -> [1.10.0, 1.9.0, 1.2.0]
        """
        versions = SkillVersion.objects.filter(metadata=metadata).defer("artifact", "orchestration")
        return sorted(versions, key=lambda item: parse_version(item.version), reverse=True)

    @staticmethod
    def get_latest_version(metadata: SkillMetadata) -> Optional[str]:
        """已有的最高版本号，没有版本时为 None

        例如：已有 1.1.0、1.2.0，线上切回 1.1.0 -> "1.2.0"
        """
        versions = SkillVersion.objects.filter(metadata=metadata).values_list("version", flat=True)
        return max(versions, key=parse_version, default=None)

    @staticmethod
    def build_list_context(metadata_list: Sequence[SkillMetadata]) -> Dict[str, Any]:
        """列表序列化需要的上下文：每条 Skill 线上版本调用到的网关（按网关名去重，带展示名）

        查询次数固定：一次查 relation，一次批量查网关展示名。

        例如：两条 Skill 都调用 bk-sops -> {"related_gateways": {1: [{"name": "bk-sops", ...}], 2: [...]}}；
        bk-sops 在本环境不存在时 display_name 用网关名
        """
        version_ids = [item.current_version_id for item in metadata_list if item.current_version_id]
        gateway_names_by_version: Dict[int, List[str]] = {}
        for version_id, gateway_name in (
            SkillVersionRelation.objects.filter(version_id__in=version_ids)
            .order_by("id")
            .values_list("version_id", "gateway_name")
        ):
            names = gateway_names_by_version.setdefault(version_id, [])
            if gateway_name not in names:
                names.append(gateway_name)

        all_names = {name for names in gateway_names_by_version.values() for name in names}
        display_names = {
            gateway.name: gateway.display_name_or_name for gateway in Gateway.objects.filter(name__in=all_names)
        }
        return {
            "related_gateways": {
                item.id: [
                    {"name": name, "display_name": display_names.get(name, name)}
                    for name in gateway_names_by_version.get(item.current_version_id, [])
                ]
                for item in metadata_list
            }
        }

    @staticmethod
    def build_detail_context(metadata: SkillMetadata) -> Dict[str, Any]:
        """详情序列化需要的上下文：线上版本调用的接口、环境、版本数

        例如：网关 Skill 线上版本调用 demo 的 prod 环境两个接口 ->
            {"apis": [{"gateway_name": "demo", "resource_name": "a"}, ...], "stage": "prod", "version_count": 2}
        内置 Skill 的 stage 为 None
        """
        version = metadata.current_version
        apis = []
        stage = None
        if version is not None:
            apis = list(
                SkillVersionRelation.objects.filter(version=version)
                .order_by("id")
                .values("gateway_name", "resource_name")
            )
            steps = version.orchestration.get("steps") or []
            if metadata.type == SkillTypeEnum.GATEWAY.value and steps:
                stage = split_uses(steps[0]["uses"])[1]
        return {
            "apis": apis,
            "stage": stage,
            "version_count": SkillVersion.objects.filter(metadata=metadata).count(),
        }

    @staticmethod
    def build_gateway_download_url(metadata: SkillMetadata) -> str:
        """网关 Skill 管理页的下载地址（需登录，包内含 declaration.yaml）"""
        return f"{settings.DASHBOARD_URL}/gateways/{metadata.gateway_id}/skills/{metadata.code}/download/"

    @staticmethod
    def build_market_download_url(metadata: SkillMetadata) -> str:
        """Skill 市场的下载地址（需登录）"""
        return f"{settings.DASHBOARD_URL}/skill-marketplace/skills/{metadata.code}/download/"

    @staticmethod
    def build_public_download_url(metadata: SkillMetadata) -> Optional[str]:
        """免登录下载地址（给 npx 临时使用）；不是使用中时为 None"""
        if metadata.status != SkillStatusEnum.PUBLISHED.value:
            return None
        return f"{settings.DASHBOARD_URL}/skill-marketplace/skills/{metadata.code}/public-download/"

    @staticmethod
    def increase_download_count(metadata_id: int) -> None:
        """下载数原子加一；不经过 save()，不改 updated_time、updated_by，并发下载不会丢计数

        例如：ZIP 生成成功后调用；同时下载 10 次 -> download_count 正好加 10
        """
        SkillMetadata.objects.filter(id=metadata_id).update(download_count=F("download_count") + 1)
