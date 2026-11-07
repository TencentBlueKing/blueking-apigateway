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


def restrict_current_version(collector, field, sub_objs, using):
    """单独删当前版本时按 RESTRICT 拒绝；连同 SkillMetadata 一起删时先置空 current_version，再删版本。"""
    deleting = collector.data.get(field.model, ())
    blocked = []
    clearing = []
    for obj in sub_objs:
        if obj in deleting:
            clearing.append(obj)
        else:
            blocked.append(obj)
    if clearing:
        collector.add_field_update(field, None, clearing)
    if blocked:
        collector.add_restricted_objects(field, blocked)
        collector.add_dependency(field.remote_field.model, field.model)
