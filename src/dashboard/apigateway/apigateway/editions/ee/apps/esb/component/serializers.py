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
from typing import Any, Dict, List, Optional

from django.conf import settings
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from tencent_apigateway_common.i18n.field import SerializerTranslatedField

from apigateway.apps.esb.bkcore.models import ComponentSystem, ESBChannel, ESBChannelExtend
from apigateway.apps.esb.component.config_fields import enrich_config_fields
from apigateway.apps.esb.constants import (
    CHANNEL_PATH_PATTERN,
    COMPONENT_CODENAME_PATTERN,
    COMPONENT_NAME_PATTERN,
    MethodEnum,
)
from apigateway.apps.esb.helpers import get_component_doc_link
from apigateway.apps.esb.mixins import OfficialWriteFields
from apigateway.biz.resource_version import ResourceVersionHandler
from apigateway.common.fields import TimestampField


class ESBChannelSLZ(OfficialWriteFields, serializers.ModelSerializer):

    board = serializers.HiddenField(default="")
    system_id = serializers.IntegerField(min_value=1)
    system_name = serializers.CharField(source="system.name", read_only=True)
    config = serializers.DictField(allow_empty=True, required=False, write_only=True)
    api_url = serializers.SerializerMethodField()
    doc_link = serializers.SerializerMethodField()
    is_official = serializers.BooleanField(read_only=True)
    method = serializers.ChoiceField(choices=MethodEnum.get_django_choices())
    path = serializers.RegexField(CHANNEL_PATH_PATTERN, label="请求路径", max_length=255)
    component_codename = serializers.RegexField(COMPONENT_CODENAME_PATTERN, label="组件类代号", max_length=255)
    name = serializers.RegexField(COMPONENT_NAME_PATTERN, max_length=128)
    is_created = serializers.SerializerMethodField(help_text="新建且未同步")
    has_updated = serializers.SerializerMethodField(help_text="相对上次同步，有更新")
    description = SerializerTranslatedField(default_field="description_i18n", max_length=128)

    class Meta:
        model = ESBChannel
        _fields = [
            "board",
            "id",
            "system_id",
            "system_name",
            "name",
            "description",
            "method",
            "path",
            "component_codename",
            "permission_level",
            "verified_user_required",
            "timeout",
            "config",
            "is_active",
            "api_url",
            "doc_link",
            "is_official",
            "updated_time",
        ]
        fields = _fields + ["is_created", "has_updated"]
        official_write_fields = [
            "permission_level",
            "verified_user_required",
            "timeout",
            "config",
            "is_active",
        ]
        lookup_field = "id"
        validators = [
            UniqueTogetherValidator(
                queryset=ESBChannel.objects.all(),
                fields=["board", "method", "path"],
                message=gettext_lazy("组件的请求方法+请求路径需唯一。"),
            ),
            UniqueTogetherValidator(
                queryset=ESBChannel.objects.all(),
                fields=["system_id", "name"],
                message=gettext_lazy("同一个组件系统下，组件名称需唯一。"),
            ),
        ]

    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        self._validate_method(data["board"], data["method"], data["path"])
        return data

    def validate_path(self, value):
        return "/%s/" % value.strip("/")

    def get_api_url(self, obj):
        host = getattr(settings, "BK_COMPONENT_API_URL", "").rstrip("/")
        return f"{host}/api/c/compapi{obj.path}"

    def get_doc_link(self, obj):
        return get_component_doc_link(obj.board, obj.system.name, obj.name)

    def get_has_updated(self, obj):
        latest_release_time = self.context["latest_release_time"]
        return not latest_release_time or latest_release_time < obj.updated_time

    def get_is_created(self, obj):
        """未同步，且新创建的组件，展示“新创建”标记"""
        if not self.get_has_updated(obj):
            return False

        # 更新时间与创建时间差别不到 1 秒，则认为是新创建
        return (obj.updated_time - obj.created_time).total_seconds() < 1

    def to_internal_value(self, data):
        data = super().to_internal_value(data)
        system = self._get_system(data["system_id"])
        data.update(
            {
                "system": system,
                "board": system.board,
            }
        )
        return data

    def _get_system(self, system_id: int) -> ComponentSystem:
        try:
            return ComponentSystem.objects.get(id=system_id)
        except ComponentSystem.DoesNotExist:
            raise serializers.ValidationError({"system_id": f"系统【id={system_id}】不存在。"})

    def _validate_method(self, board: str, method: str, path: str):
        if method == "":
            queryset = ESBChannel.objects.filter(board=board, path=path)
            queryset = self._exclude_current_instance(queryset)
            if queryset.exists():
                raise serializers.ValidationError(_("当前指定的请求方法为 GET/POST，但相同请求路径下，其它请求方法已存在。"))
        else:
            queryset = ESBChannel.objects.filter(board=board, path=path, method="")
            queryset = self._exclude_current_instance(queryset)
            if queryset.exists():
                raise serializers.ValidationError(
                    _("当前请求方法为 {method}，但相同请求路径下，请求方法 GET/POST 已存在。").format(method=method),
                )

    def _exclude_current_instance(self, queryset):
        if self.instance is not None:
            return queryset.exclude(pk=self.instance.pk)
        return queryset

    def update(self, instance, validated_data):
        if not ESBChannelExtend.objects.get_config_fields(instance.id):
            validated_data.pop("config", None)

        return super().update(instance, validated_data)


class ESBChannelDetailSLZ(ESBChannelSLZ):
    config_fields = serializers.SerializerMethodField()
    is_created = None
    has_updated = None

    class Meta(ESBChannelSLZ.Meta):
        fields: List[str] = ESBChannelSLZ.Meta._fields + ["config_fields"]

    def get_config_fields(self, obj) -> Optional[List[dict]]:
        config_fields = ESBChannelExtend.objects.get_config_fields(obj.id)
        if not config_fields:
            return None

        return enrich_config_fields(config_fields, obj.config)


class ESBChannelBatchSLZ(serializers.Serializer):
    ids = serializers.ListField(child=serializers.IntegerField(min_value=1))


class ComponentResourceBindingSLZ(serializers.Serializer):
    resource_id = serializers.IntegerField(source="id", read_only=True)
    resource_name = serializers.CharField(source="name", read_only=True)
    system_name = serializers.CharField(source="extend_data.system_name", read_only=True)
    component_id = serializers.IntegerField(source="extend_data.component_id", read_only=True)
    component_name = serializers.CharField(source="extend_data.component_name", read_only=True)
    component_method = serializers.CharField(source="extend_data.component_method", read_only=True)
    component_path = serializers.CharField(source="extend_data.component_path", read_only=True)
    component_permission_level = serializers.CharField(source="extend_data.component_permission_level", read_only=True)


class QueryComponentReleaseHistorySLZ(serializers.Serializer):
    time_start = TimestampField(allow_null=True, required=False)
    time_end = TimestampField(allow_null=True, required=False)


class ComponentReleaseHistorySLZ(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    created_time = serializers.DateTimeField(read_only=True)
    resource_version_name = serializers.SerializerMethodField()
    resource_version_title = serializers.SerializerMethodField()
    resource_version_display = serializers.SerializerMethodField()
    created_by = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    message = serializers.CharField(read_only=True)

    def get_resource_version_name(self, obj):
        resource_version_id = obj.get("resource_version_id")
        return self.context["resource_version_id_to_fields"].get(resource_version_id, {}).get("name")

    def get_resource_version_title(self, obj):
        resource_version_id = obj.get("resource_version_id")
        return self.context["resource_version_id_to_fields"].get(resource_version_id, {}).get("title")

    def get_resource_version_display(self, obj):
        resource_version_id = obj.get("resource_version_id")
        if resource_version_id not in self.context["resource_version_id_to_fields"]:
            return ""

        return ResourceVersionHandler.get_resource_version_display(
            self.context["resource_version_id_to_fields"][resource_version_id]
        )
