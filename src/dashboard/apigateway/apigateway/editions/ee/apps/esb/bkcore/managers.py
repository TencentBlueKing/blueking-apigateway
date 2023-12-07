# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2017 THL A29 Limited, a Tencent company. All rights reserved.
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
import datetime
import itertools
import json
import operator
from typing import Any, Dict, List, Optional, Tuple

from django.db import models
from django.db.models import Count, Q
from django.utils.encoding import smart_str
from django.utils.translation import gettext as _

from apigateway.apps.esb.constants import DEFAULT_DOC_CATEGORY, DataTypeEnum, FunctionControllerCodeEnum
from apigateway.apps.permission.utils import calculate_expires
from apigateway.common.constants import LanguageCodeEnum
from apigateway.core.constants import ReleaseStatusEnum
from apigateway.utils.time import to_datetime_from_now


class ComponentSystemManager(models.Manager):
    def allow_delete(self, ids: List[int]) -> Tuple[bool, str]:
        if self.filter(id__in=ids).exclude(data_type=DataTypeEnum.CUSTOM.value).exists():
            return False, _("官方系统，不能删除。")
        return True, ""

    def delete_custom_systems(self, ids: List[int]):
        from apigateway.apps.esb.bkcore.models import ESBChannel, SystemDocCategory

        custom_ids = list(self.filter(id__in=ids, data_type=DataTypeEnum.CUSTOM.value).values_list("id", flat=True))
        ESBChannel.objects.filter(system_id__in=custom_ids).delete()
        SystemDocCategory.objects.filter(system_id__in=custom_ids).delete()
        self.filter(id__in=custom_ids).delete()

    def get_by_name(self, board: str, system_name: str):
        return self.filter(board=board, name=system_name).first()

    def get_id_to_fields_map(self) -> Dict[int, dict]:
        fields = ["id", "name", "description", "comment", "description_en", "comment_en"]

        return {item["id"]: item for item in self.values(*fields)}


class ESBChannelManager(models.Manager):
    def allow_delete(self, ids: List[int]) -> Tuple[bool, str]:
        if self.filter(id__in=ids).exclude(data_type=DataTypeEnum.CUSTOM.value).exists():
            return False, _("官方组件，不能删除。")
        return True, ""

    def delete_custom_channels(self, ids: List[int]):
        self.filter(id__in=ids, data_type=DataTypeEnum.CUSTOM.value).delete()

    def calculate_channel_count_per_system(self):
        counts = self.values("system_id").annotate(count=Count("system_id"))
        return {i["system_id"]: i["count"] for i in counts}

    def filter_active_and_public_system_ids(
        self,
        boards: Optional[List[str]] = None,
        allow_apply_permission: Optional[bool] = None,
    ) -> List[int]:
        qs = self.filter(is_active=True, is_public=True)
        if boards:
            qs = qs.filter(board__in=boards)

        return list(qs.values_list("system_id", flat=True).distinct())

    def filter_active_and_public_components(
        self,
        system_id: Optional[int] = None,
        ids: Optional[List[int]] = None,
        allow_apply_permission: Optional[bool] = None,
    ):
        qs = self.filter(is_active=True, is_public=True)

        if system_id is not None:
            qs = qs.filter(system_id=system_id)

        if ids is not None:
            qs = qs.filter(id__in=ids)

        return qs

    def filter_public_components(
        self,
        board: str,
        system_name: Optional[str] = None,
        query: Optional[str] = None,
        order_by: Optional[tuple] = None,
    ):
        qs = self.filter(board=board, is_active=True, is_public=True)

        if system_name:
            qs = qs.filter(system__name__iexact=system_name)

        if query:
            qs = qs.filter(
                Q(name__icontains=query) | Q(description__icontains=query) | Q(system__name__icontains=query)
            )

        if order_by:
            qs = qs.order_by(*order_by)

        return qs

    def filter_ids(self, system_id: int) -> List[int]:
        return list(self.filter(system_id=system_id).values_list("id", flat=True))

    def group_by_permission_level(self, component_ids: List[int]) -> List[List[int]]:
        if not component_ids:
            return []

        data = self.filter(id__in=component_ids).values("permission_level", "id").order_by("permission_level")
        return [
            [item["id"] for item in group]
            for _, group in itertools.groupby(data, key=operator.itemgetter("permission_level"))
        ]

    def get_components(self, queryset) -> List[dict]:
        data = list(
            queryset.values(
                "id",
                "board",
                "name",
                "description",
                "description_en",
                "permission_level",
                "system__name",
            )
        )
        return [
            {
                "id": item["id"],
                "board": item["board"],
                "name": item["name"],
                "description": item["description"],
                "description_en": item["description_en"],
                "permission_level": item["permission_level"],
                "system_name": item["system__name"],
            }
            for item in data
        ]

    def get_component_map_by_ids(self, ids: List[int]) -> Dict[int, dict]:
        qs = self.filter(id__in=ids)
        return {component["id"]: component for component in self.get_components(qs)}

    def filter_valid_ids(self, board: str, ids: List[int]) -> List[int]:
        return list(self.filter(board=board, id__in=ids).values_list("id", flat=True))

    def get_latest_updated_time(self) -> Optional[datetime.datetime]:
        return self.order_by("-updated_time").values_list("updated_time", flat=True).first()

    def get_public_component(self, board: str, system_name: str, component_name: str):
        return self.filter(
            board=board,
            system__name__iexact=system_name,
            name=component_name,
            is_active=True,
            is_public=True,
        ).first()


class ESBChannelExtendManager(models.Manager):
    def get_config_fields(self, component_id: int):
        try:
            return self.get(component_id=component_id).config_fields
        except self.model.DoesNotExist:
            return None


class ComponentResourceBindingManager(models.Manager):
    def get_component_key_to_resource_id(self) -> Dict[str, int]:
        return {binding.component_key: binding.resource_id for binding in self.all()}

    def sync(self, imported_resources: List[Dict[str, Any]]):
        resource_ids = [resource["id"] for resource in imported_resources]

        # 删除不存在资源的绑定关系
        self.exclude(resource_id__in=resource_ids).delete()

        for resource in imported_resources:
            extend_data = resource["extend_data"]
            self.update_or_create(
                resource_id=resource["id"],
                defaults={
                    "component_id": extend_data.get("component_id") or 0,
                    "component_method": extend_data["component_method"],
                    "component_path": extend_data["component_path"],
                },
            )


class ComponentReleaseHistoryManager(models.Manager):
    def get_histories(self, time_start=None, time_end=None, order_by=None) -> List[Dict[str, Any]]:
        queryset = self.all()

        if time_start and time_end:
            queryset = queryset.filter(created_time__range=(time_start, time_end))

        if order_by:
            queryset = queryset.order_by(order_by)

        return list(
            queryset.values("id", "resource_version_id", "comment", "status", "message", "created_time", "created_by")
        )

    def need_new_release(self) -> bool:
        """是否需要同步并发布到网关"""
        from apigateway.apps.esb.bkcore.models import ESBChannel

        latest_release_time = self.get_latest_release_time()
        latest_component_updated_time = ESBChannel.objects.get_latest_updated_time()
        if not (latest_release_time or latest_component_updated_time):
            return False

        if not latest_release_time:
            return True

        if latest_component_updated_time and latest_component_updated_time > latest_release_time:
            return True

        # 删除组件，不需要同步到网关，此种情况，即使网关请求通过检验，组件后端也会处理此组件不可访问
        return False

    def get_latest_release_time(self) -> Optional[datetime.datetime]:
        """获取最新的发布时间

        - 忽略发布失败的记录，因发布失败时，需要继续同步组件到网关
        """
        return (
            self.filter(status__in=[ReleaseStatusEnum.SUCCESS.value, ReleaseStatusEnum.PENDING.value])
            .values_list("created_time", flat=True)
            .last()
        )


class DocCategoryManager(models.Manager):
    def allow_delete(self, ids: List[int]) -> Tuple[bool, str]:
        from apigateway.apps.esb.bkcore.models import SystemDocCategory

        if self.filter(id__in=ids).exclude(data_type=DataTypeEnum.CUSTOM.value).exists():
            return False, _("官方文档分类，不能删除。")

        if SystemDocCategory.objects.filter(doc_category_id__in=ids).exists():
            return False, _("文档分类存在关联的系统，不能删除。")

        return True, ""

    def delete_custom_doc_category(self, id: int):
        self.filter(id=id, data_type=DataTypeEnum.CUSTOM.value).delete()

    def get_default_doc_category(self, board: str) -> Dict[str, Any]:
        instance, _ = self.get_or_create(
            board=board,
            name=DEFAULT_DOC_CATEGORY,
            defaults={
                "data_type": DataTypeEnum.OFFICIAL_PUBLIC.value,
                "name_en": "Default",
            },
        )
        return {
            "id": instance.id,
            "name": instance.name,
            "name_en": instance.name_en,
        }

    def get_id_to_fields_map(self) -> Dict[int, dict]:
        fields = ["id", "name", "priority", "name_en"]

        return {item["id"]: item for item in self.all().values(*fields)}


class SystemDocCategoryManager(models.Manager):
    def calculate_system_count_per_doc_category(self):
        counts = self.values("doc_category_id").annotate(count=Count("doc_category_id"))
        return {i["doc_category_id"]: i["count"] for i in counts}

    def get_system_id_to_doc_category_map(self, system_ids: Optional[List[int]] = None) -> Dict[int, dict]:
        qs = self.all()

        if system_ids is not None:
            qs = self.filter(system_id__in=system_ids)

        return {
            item["system_id"]: {
                "id": item["doc_category_id"],
                "name": item["doc_category__name"],
                "name_en": item["doc_category__name_en"],
            }
            for item in qs.values("system_id", "doc_category_id", "doc_category__name", "doc_category__name_en")
        }

    def group_category_id_by_board(self):
        data = self.values("doc_category_id", "board").distinct().order_by("board")
        return {
            board: [item["doc_category_id"] for item in group]
            for board, group in itertools.groupby(data, key=operator.itemgetter("board"))
        }

    def group_system_id_by_category_id(self):
        data = self.values("doc_category_id", "system_id").order_by("doc_category_id")
        return {
            category_id: [item["system_id"] for item in group]
            for category_id, group in itertools.groupby(data, key=operator.itemgetter("doc_category_id"))
        }


class AppComponentPermissionManager(models.Manager):
    def filter_permission(
        self,
        bk_app_code: Optional[str] = None,
        system_id: Optional[int] = None,
        component_id: Optional[int] = None,
    ):
        qs = self.all()

        if bk_app_code:
            qs = qs.filter(bk_app_code=bk_app_code)

        if system_id is not None:
            from apigateway.apps.esb.bkcore.models import ESBChannel

            qs = qs.filter(component_id__in=ESBChannel.objects.filter_ids(system_id=system_id))

        if component_id is not None:
            qs = qs.filter(component_id=component_id)

        return qs

    def filter_component_ids(
        self,
        bk_app_code: str,
        expire_days_range: Optional[int] = None,
    ) -> List[int]:
        qs = self.filter(bk_app_code=bk_app_code)

        if expire_days_range is not None:
            qs = qs.filter(expires__range=(to_datetime_from_now(), to_datetime_from_now(expire_days_range)))

        return list(qs.values_list("component_id", flat=True))

    def renew_permissions(
        self,
        bk_app_code: str,
        component_ids: List[int],
        expire_days: int,
    ):
        queryset = self.filter(bk_app_code=bk_app_code, component_id__in=component_ids)
        # 仅续期权限期限小于待续期时间的权限
        expires = to_datetime_from_now(days=expire_days)
        queryset = queryset.filter(expires__lt=expires)
        queryset.update(expires=expires)

    def renew_permission_by_ids(self, ids: List[int], expire_days: int):
        self.filter(id__in=ids).update(
            expires=to_datetime_from_now(days=expire_days),
        )

    def delete_permission_by_ids(self, ids: List[int]):
        self.filter(id__in=ids).delete()

    def save_permissions(
        self,
        board: str,
        component_ids: List[int],
        bk_app_code: str,
        grant_type: str,
        expire_days: Optional[int] = None,
    ):
        from apigateway.apps.esb.bkcore.models import ESBChannel

        expires = calculate_expires(expire_days)
        for component_id in ESBChannel.objects.filter_valid_ids(board, component_ids):
            self.update_or_create(
                board=board,
                bk_app_code=bk_app_code,
                component_id=component_id,
                defaults={
                    "expires": expires,
                },
            )


class AppPermissionApplyRecordManager(models.Manager):
    def filter_record(
        self,
        queryset,
        bk_app_code: str = "",
        applied_by: str = "",
        applied_time_start: Optional[datetime.datetime] = None,
        applied_time_end: Optional[datetime.datetime] = None,
        handled_time_start: Optional[datetime.datetime] = None,
        handled_time_end: Optional[datetime.datetime] = None,
        status: Optional[str] = None,
        query: str = "",
        order_by: str = "",
    ):
        if bk_app_code:
            queryset = queryset.filter(bk_app_code=bk_app_code)

        if applied_by:
            queryset = queryset.filter(applied_by=applied_by)

        if applied_time_start and applied_time_end:
            queryset = queryset.filter(applied_time__range=(applied_time_start, applied_time_end))

        if handled_time_start and handled_time_end:
            queryset = queryset.filter(handled_time__range=(handled_time_start, handled_time_end))

        if status:
            queryset = queryset.filter(status=status)

        if query:
            queryset = queryset.filter(system__name__icontains=query)

        if order_by:
            queryset = queryset.order_by(order_by)

        return queryset

    def create_record(
        self,
        board: str,
        bk_app_code: str,
        applied_by: str,
        system,
        component_ids: List[int],
        status: str,
        reason: str,
        expire_days: int,
    ):
        return self.create(
            board=board,
            bk_app_code=bk_app_code,
            applied_by=applied_by,
            system=system,
            component_ids=component_ids,
            status=status,
            reason=reason,
            expire_days=expire_days,
        )

    def get_component_permisson_status(
        self,
        bk_app_code: str,
        system_id: Optional[int],
        statuses: List[str],
    ) -> dict:
        from apigateway.apps.esb.bkcore.models import AppPermissionApplyStatus

        if system_id is None:
            return {}

        return {
            item.component_id: item.status
            for item in AppPermissionApplyStatus.objects.filter(
                bk_app_code=bk_app_code,
                system_id=system_id,
            )
        }


class AppPermissionApplyStatusManager(models.Manager):
    def batch_create(self, record, bk_app_code: str, system, component_ids: List[int], status: str):
        from apigateway.apps.esb.bkcore.models import ESBChannel

        self.bulk_create(
            [
                self.model(
                    record=record,
                    bk_app_code=bk_app_code,
                    system=system,
                    component=component,
                    status=status,
                )
                for component in ESBChannel.objects.filter(system_id=system.id, id__in=component_ids)
            ],
            len(component_ids),
        )


class FunctionControllerManager(models.Manager):
    def _get_by_func_code(self, func_code: str):
        return self.filter(func_code=func_code).first()

    def get_jwt_key(self):
        instance = self._get_by_func_code(FunctionControllerCodeEnum.JWT_KEY.value)
        if not instance:
            return None

        return json.loads(instance.wlist)

    def save_jwt_key(self, private_key: bytes, public_key: bytes):
        private_key = smart_str(private_key)
        public_key = smart_str(public_key)

        self.get_or_create(
            func_code=FunctionControllerCodeEnum.JWT_KEY.value,
            defaults={
                "func_name": _("JWT私钥公钥"),
                "switch_status": True,
                "wlist": json.dumps({"private_key": private_key, "public_key": public_key}),
            },
        )


class ComponentDocManager(models.Manager):
    def get_api_doc(self, component_id: Optional[int], language_code: str = LanguageCodeEnum.ZH_HANS.value):
        if component_id is None:
            return None
        return self.filter(component_id=component_id, language=language_code).first()
