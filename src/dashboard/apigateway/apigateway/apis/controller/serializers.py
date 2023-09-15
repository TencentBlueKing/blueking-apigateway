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
from rest_framework import serializers


class GatewayStatusInfoSLZ(serializers.Serializer):
    """网关信息"""

    stage_name = serializers.CharField(help_text="微网关环境名称")
    namespace = serializers.CharField(help_text="命名空间")
    chart_name = serializers.CharField(help_text="Chart 名称", required=False)
    chart_version = serializers.CharField(help_text="Chart 版本", required=False)
    release_name = serializers.CharField(help_text="Release 名称", required=False)
    release_version = serializers.CharField(help_text="Release 版本", required=False)


class ReplicasStatusSLZ(serializers.Serializer):
    id = serializers.CharField(max_length=64, help_text="微网关副本 ID")
    control_plane_version = serializers.CharField(max_length=64, help_text="控制面版本")
    control_plane_status_code = serializers.IntegerField(help_text="控制平面状态码")
    control_plane_status_message = serializers.CharField(help_text="控制平面状态消息", required=False)
    data_plane_version = serializers.CharField(max_length=64, help_text="数据面版本")
    data_plane_type = serializers.CharField(max_length=64, help_text="数据面类型")
    data_plane_status_code = serializers.IntegerField(help_text="数据平面状态码")
    data_plane_status_message = serializers.CharField(help_text="数据平面状态消息", required=False)


class MicroGatewayStatusSLZ(serializers.Serializer):
    gateway = GatewayStatusInfoSLZ(help_text="网关信息")
    replicas = serializers.ListField(help_text="副本状态", child=ReplicasStatusSLZ())


class MicroGatewayRelatedInfoSLZ(serializers.Serializer):
    gateway_name = serializers.CharField(help_text="网关名称")
    stage_name = serializers.CharField(help_text="环境名称")


class MicroGatewayInfoSLZ(serializers.Serializer):
    name = serializers.CharField(help_text="微网关名称")
    related_infos = serializers.ListField(child=MicroGatewayRelatedInfoSLZ(), help_text="关联信息")
