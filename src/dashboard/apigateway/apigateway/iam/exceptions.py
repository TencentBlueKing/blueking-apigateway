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
from django.utils.translation import gettext as _

from apigateway.iam.constants import UserRoleEnum


class IAMGradeManagerExistError(Exception):
    def __init__(self, gateway_id: int):
        self._gateway_id = gateway_id

    def __str__(self):
        return _("网关 (id={gateway_id}) 的 IAM 分级管理员已存在，请不要重复创建。").format(gateway_id=self._gateway_id)


class IAMGradeManagerNotExist(Exception):
    def __init__(self, gateway_id: int):
        self._gateway_id = gateway_id

    def __str__(self):
        return _("网关 (id={gateway_id}) 的 IAM 分级管理员不存在，请联系系统负责人初始化数据。").format(gateway_id=self._gateway_id)


class IAMUserRoleNotExist(Exception):
    def __init__(self, gateway_id: int, role: UserRoleEnum):
        self._gateway_id = gateway_id
        self._role = role

    def __str__(self):
        return _(
            _("网关 (id={gateway_id}) {role_label}的 IAM 用户组不存在，请联系系统负责人初始化数据。").format(
                gateway_id=self._gateway_id,
                role_label=UserRoleEnum.get_choice_label(self._role),
            )
        )
