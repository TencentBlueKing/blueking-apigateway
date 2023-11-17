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

from django.http import Http404
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from apigateway.biz.release import ReleaseHandler
from apigateway.common.fields import CurrentGatewayDefault, TimestampField
from apigateway.core.constants import (
    PublishEventEnum,
    PublishEventNameTypeEnum,
    PublishEventStatusEnum,
    ReleaseHistoryStatusEnum,
)
from apigateway.core.models import PublishEvent, ReleaseHistory, ResourceVersion, Stage


class ReleaseInputSLZ(serializers.Serializer):
    gateway = serializers.HiddenField(default=CurrentGatewayDefault())
    stage_id = serializers.IntegerField(required=True, help_text="环境id")
    resource_version_id = serializers.IntegerField(required=True, help_text="资源版本id")
    comment = serializers.CharField(allow_blank=True, required=False, help_text="发布日志")

    def validate_stage_id(self, value):
        if not Stage.objects.filter(gateway=self.context["gateway"], id=value).exists():
            raise Http404

        return value

    def validate_resource_version_id(self, value):
        if not ResourceVersion.objects.filter(gateway=self.context["gateway"], id=value).exists():
            raise Http404

        return value


class ReleaseHistoryQueryInputSLZ(serializers.Serializer):
    keyword = serializers.CharField(allow_blank=True, required=False, help_text="查询参数关键字")
    stage_id = serializers.IntegerField(allow_null=True, required=False, help_text="环境id")
    created_by = serializers.CharField(allow_blank=True, required=False, help_text="创建者")
    time_start = TimestampField(allow_null=True, required=False, help_text="开始时间")
    time_end = TimestampField(allow_null=True, required=False, help_text="结束时间")


class ReleaseStageSLZ(serializers.Serializer):
    id = serializers.IntegerField(read_only=True, help_text="环境id")
    name = serializers.CharField(allow_blank=True, required=False, help_text="环境name")


class ReleaseHistoryOutputSLZ(serializers.Serializer):
    id = serializers.IntegerField(read_only=True, help_text="发布历史id")
    stage = ReleaseStageSLZ()
    resource_version_display = serializers.SerializerMethodField(read_only=True, help_text="发布资源版本")
    created_time = serializers.DateTimeField(read_only=True, help_text="发布创建事件")
    created_by = serializers.CharField(read_only=True, help_text="发布人")
    source = serializers.CharField(read_only=True, help_text="发布来源")
    duration = serializers.SerializerMethodField(read_only=True, help_text="发布耗时(s)")
    status = serializers.SerializerMethodField(read_only=True, help_text="发布状态")

    def get_resource_version_display(self, obj: ReleaseHistory) -> str:
        return obj.resource_version.object_display

    def get_status(self, obj: ReleaseHistory) -> str:
        event = self.context["release_history_events_map"].get(obj.id, None)
        if not event:
            # 兼容历史数据
            return obj.status

        # 通过最新的event获取release_history状态
        return ReleaseHandler.get_status(event)

    def get_duration(self, obj: ReleaseHistory) -> int:
        # 获取最新事件
        event = self.context["release_history_events_map"].get(obj.id, None)
        if not event:
            return 0

        # 如果失败，返回event的创建时间和release_history创建时间之差
        if event.status == PublishEventStatusEnum.FAILURE.value or (
            event.status != PublishEventStatusEnum.DOING.value
            and event.name == PublishEventNameTypeEnum.LOAD_CONFIGURATION.value
        ):
            return int((event.created_time - obj.created_time).total_seconds())

        # 0代表还没到达终态
        return 0


class ReleaseHistoryEventInfoSLZ(serializers.Serializer):
    id = serializers.IntegerField(read_only=True, help_text="发布事件id")
    release_history_id = serializers.IntegerField(source="publish_id", allow_null=False, help_text="发布历史id")
    name = serializers.SerializerMethodField(read_only=True, help_text="发布事件节点名称")
    step = serializers.IntegerField(read_only=True, help_text="发布事件节点所属步骤")
    status = serializers.ChoiceField(
        choices=ReleaseHistoryStatusEnum.get_choices(), read_only=True, help_text="发布事件状态:success/failure/doing"
    )
    created_time = serializers.DateTimeField(read_only=True, help_text="发布节点事件创建时间")
    detail = serializers.DictField(read_only=True, help_text="发布日志")

    def get_name(self, obj: PublishEvent) -> str:
        return _(obj.name)


class ReleaseHistoryEventRetrieveOutputSLZ(ReleaseHistoryOutputSLZ):
    events = serializers.ListField(child=ReleaseHistoryEventInfoSLZ(), allow_empty=True, help_text="发布事件列表")
    events_template = serializers.SerializerMethodField(read_only=True, help_text="发布事件模板")

    def to_representation(self, obj):
        obj.events = self.context["release_history_events"]
        return super().to_representation(obj)

    def get_events_template(self, obj):
        events_template = []
        choices = PublishEventEnum.get_choices()
        for step, (name, desc) in enumerate(choices):
            events_template.append({"name": name, "description": desc, "step": step})
        return events_template
